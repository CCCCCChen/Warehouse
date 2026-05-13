from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(String, index=True, nullable=False, default="default")
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    quantity = Column(Integer, default=0)

    category = Column(String, nullable=True, index=True)
    location = Column(String, nullable=True, index=True)
    unit = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    min_quantity = Column(Integer, default=0)
    purchase_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    barcode = Column(String, nullable=True, index=True)
    tags = Column(String, nullable=True)
    notes = Column(String, nullable=True)


class Household(Base):
    __tablename__ = "households"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    members = relationship("HouseholdMember", back_populates="household")
    config = relationship("HouseholdConfig", back_populates="household", uselist=False)


class HouseholdMember(Base):
    __tablename__ = "household_members"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(String, ForeignKey("households.id"), index=True, nullable=False)
    role = Column(String, nullable=False, default="user")  # owner|user
    token_hash = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    household = relationship("Household", back_populates="members")


class HouseholdInvite(Base):
    __tablename__ = "household_invites"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(String, ForeignKey("households.id"), index=True, nullable=False)
    code_hash = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False, default="user")  # always user for now
    max_uses = Column(Integer, nullable=False, default=10)
    used_count = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    created_by_member_id = Column(Integer, nullable=True)


class HouseholdConfig(Base):
    __tablename__ = "household_config"

    household_id = Column(String, ForeignKey("households.id"), primary_key=True)
    categories_json = Column(Text, nullable=False, default="[]")
    locations_json = Column(Text, nullable=False, default="[]")
    units_json = Column(Text, nullable=False, default="[]")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by_member_id = Column(Integer, nullable=True)

    household = relationship("Household", back_populates="config")
