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


class InitHouseholdRequest(BaseModel):
    name: str
    template: Optional[str] = None


class InitHouseholdResponse(BaseModel):
    household_id: str
    owner_token: str


class JoinHouseholdRequest(BaseModel):
    household_id: str
    invite_code: str


class JoinHouseholdResponse(BaseModel):
    household_id: str
    token: str
    role: str


class HouseholdConfigResponse(BaseModel):
    household_id: str
    categories: list[str]
    locations: list[str]
    units: list[str]
    version: int = 1


class HouseholdConfigUpdate(BaseModel):
    categories: list[str]
    locations: list[str]
    units: list[str]


class InviteCreateRequest(BaseModel):
    max_uses: Optional[int] = None


class InviteResponse(BaseModel):
    id: int
    expires_at: str
    max_uses: int
    used_count: int
    revoked: bool


class InviteCreateResponse(InviteResponse):
    invite_code: str


class MemberResponse(BaseModel):
    id: int
    role: str
    created_at: str
    revoked: bool


class MeResponse(BaseModel):
    household_id: str
    household_name: str
    member_id: int
    role: str


class InitStatusResponse(BaseModel):
    default_household_exists: bool
    default_items_count: int
    has_any_member: bool
    can_adopt_default: bool
