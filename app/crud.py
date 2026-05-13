# app/crud.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models import Item
from app.schemas import ItemCreate, ItemBase, ItemUpdate

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
