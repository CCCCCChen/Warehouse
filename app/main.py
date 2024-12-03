"""
# running command
uvicorn main:app --reload
"""

from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
import os
import uvicorn
from dotenv import load_dotenv
import random
from sqlalchemy.orm import Session
from typing import List

from app.database import engine, Base, SessionLocal
from app import crud, models, schemas

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Warehouse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
        except WebSocketDisconnect as e:
            print(f"WebSocket disconnected: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break


@app.get("/api/random_numbers")
async def get_random_numbers(count: int = 10):
    numbers = [random.randint(1, 100) for _ in range(count)]
    return {"numbers": numbers}


@app.get("/api/warehouse")
async def read_warehouse():
    return {"message": "仓库主页"}


@app.get("/api")
async def read_root():
    return {"message": "主页"}


@app.get("/api/warehouse/user")
async def read_warehouse_user():
    return {"message": "仓库用户管理页"}


@app.get("/api/warehouse/manage")
async def read_warehouse_manage():
    return {"message": "录入物品信息页"}

# ================= CRUD API Endpoints =================

@app.post("/api/items", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db=db, item=item)

@app.get("/api/items", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@app.get("/api/items/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item_by_id(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/api/items/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item: schemas.ItemBase, db: Session = Depends(get_db)):
    db_item = crud.update_item(db, item_id=item_id, item=item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.delete("/api/items/{item_id}", response_model=schemas.Item)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.delete_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 18808))  # Default to 8000 if not set
    print("port is ", port)
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
