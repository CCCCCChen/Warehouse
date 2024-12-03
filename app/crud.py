# app/crud.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Item
from app.schemas import ItemCreate, ItemBase

def create_item(db: Session, item: ItemCreate) -> Item:
    # 创建新物品
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[Item]:
    # 获取所有物品
    return db.query(Item).offset(skip).limit(limit).all()

def get_item_by_id(db: Session, item_id: int) -> Optional[Item]:
    # 根据 ID 获取物品
    return db.query(Item).filter(Item.id == item_id).first()

def update_item(db: Session, item_id: int, item: ItemBase) -> Optional[Item]:
    # 更新物品
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item:
        for key, value in item.model_dump().items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int) -> Optional[Item]:
    # 删除物品
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item
