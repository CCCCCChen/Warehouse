from sqlalchemy import Column, Integer, String, Date
from app.database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
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
