# app/crud.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models import Item, StockMovement
from app.schemas import ItemCreate, ItemBase, ItemUpdate, OutboundLine

def create_item(db: Session, household_id: str, item: ItemCreate) -> Item:
    # 创建新物品
    data = item.model_dump()
    if not data.get("recorded_at"):
        now = datetime.utcnow()
        data["recorded_at"] = now

    if (not data.get("location")) and data.get("room") and data.get("spot"):
        data["location"] = f"{data.get('room')}-{data.get('spot')}"

    if not data.get("code"):
        type_l1 = (data.get("type_l1") or "").strip() or (data.get("category") or "").strip() or "未分类"
        type_l2 = (data.get("type_l2") or "").strip() or "未分类"
        if not data.get("type_l1"):
            data["type_l1"] = type_l1
        if not data.get("type_l2"):
            data["type_l2"] = type_l2
        day_ymd = data["recorded_at"].date().isoformat()
        seq = (
            db.query(func.count(Item.id))
            .filter(
                Item.household_id == household_id,
                Item.type_l1 == type_l1,
                Item.type_l2 == type_l2,
                func.date(Item.recorded_at) == day_ymd,
            )
            .scalar()
            or 0
        )
        data["code"] = f"{type_l1}-{type_l2}-{data['recorded_at'].strftime('%Y%m%d')}-{seq + 1:03d}"

    db_item = Item(household_id=household_id, **data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_items(db: Session, household_id: str, skip: int = 0, limit: int = 100) -> List[Item]:
    # 获取所有物品
    return (
        db.query(Item)
        .filter(Item.household_id == household_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_item_by_id(db: Session, household_id: str, item_id: int) -> Optional[Item]:
    # 根据 ID 获取物品
    return db.query(Item).filter(Item.household_id == household_id, Item.id == item_id).first()

def update_item(db: Session, household_id: str, item_id: int, item: ItemUpdate) -> Optional[Item]:
    # 更新物品
    db_item = db.query(Item).filter(Item.household_id == household_id, Item.id == item_id).first()
    if db_item:
        for key, value in item.model_dump(exclude_unset=True).items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_item(db: Session, household_id: str, item_id: int) -> Optional[Item]:
    # 删除物品
    db_item = db.query(Item).filter(Item.household_id == household_id, Item.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item


def apply_outbound(db: Session, household_id: str, member_id: int, lines: List[OutboundLine]):
    qty_map = {}
    note_map = {}
    for ln in lines:
        item_id = int(ln.item_id)
        qty = int(ln.qty)
        if qty <= 0:
            continue
        qty_map[item_id] = qty_map.get(item_id, 0) + qty
        if ln.note:
            note_map[item_id] = ln.note

    item_ids = list(qty_map.keys())
    if not item_ids:
        return [], [], []

    items = (
        db.query(Item)
        .filter(Item.household_id == household_id, Item.id.in_(item_ids))
        .all()
    )
    found_ids = {int(it.id) for it in items}
    missing = [i for i in item_ids if i not in found_ids]
    if missing:
        raise ValueError(f"Items not found: {missing}")

    movements = []
    low_stock_item_ids = []
    try:
        for it in items:
            requested = qty_map.get(int(it.id), 0)
            before = int(it.quantity or 0)
            deduct = requested if requested <= before else before
            after = before - deduct
            it.quantity = after
            mv = StockMovement(
                household_id=household_id,
                item_id=int(it.id),
                member_id=int(member_id),
                action="outbound",
                delta=-int(deduct),
                before_qty=before,
                after_qty=after,
                note=note_map.get(int(it.id)),
                created_at=datetime.utcnow(),
            )
            db.add(mv)
            movements.append(mv)
        db.commit()
    except Exception:
        db.rollback()
        raise

    for it in items:
        db.refresh(it)
        min_q = int(it.min_quantity or 0)
        q = int(it.quantity or 0)
        if min_q > 0 and q <= min_q:
            low_stock_item_ids.append(int(it.id))
    for mv in movements:
        db.refresh(mv)

    return items, movements, low_stock_item_ids
