from pydantic import BaseModel
from typing import Optional
from datetime import date

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: int
    category: Optional[str] = None
    location: Optional[str] = None
    unit: Optional[str] = None
    brand: Optional[str] = None
    min_quantity: int = 0
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    barcode: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    category: Optional[str] = None
    location: Optional[str] = None
    unit: Optional[str] = None
    brand: Optional[str] = None
    min_quantity: Optional[int] = None
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    barcode: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None

class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True  # Pydantic v2 中替代 orm_mode 的配置
