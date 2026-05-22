# app/database.py
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db_url = (os.getenv("DATABASE_URL") or "").strip()
if not db_url:
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    db_url = "sqlite:///./data/warehouse.db"

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
