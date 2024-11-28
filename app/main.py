""" from fastapi import FastAPI
from app.models import Item
from app.crud import create_item, get_items, get_item_by_id, update_item, delete_item

app = FastAPI()

@app.post("/items/", response_model=Item)
async def create_new_item(item: Item):
    return create_item(item)

@app.get("/items/", response_model=list[Item])
async def read_items():
    return get_items()

@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    return get_item_by_id(item_id)

@app.put("/items/{item_id}", response_model=Item)
async def update_an_item(item_id: int, item: Item):
    return update_item(item_id, item)

@app.delete("/items/{item_id}")
async def delete_an_item(item_id: int):
    return delete_item(item_id)

# running command
uvicorn main:app --reload

    """

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
import os
import uvicorn
from dotenv import load_dotenv

import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)


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



@app.get("/api/random_numbers")  # API 路径前加 `/api`
async def get_random_numbers(count: int = 10):
    numbers = [random.randint(1, 100) for _ in range(count)]
    return {"numbers": numbers}


@app.get("/api/warehouse")  # API 路径前加 `/api`
async def read_warehouse():
    return {"message": "仓库主页"}


@app.get("/api")  # API 路径前加 `/api`
async def read_root():
    return {"message": "主页"}


@app.get("/api/warehouse/user")
async def read_warehouse_user():
    return {"message": "仓库用户管理页"}


@app.get("/api/warehouse/manage")
async def read_warehouse_manage():
    return {"message": "录入物品信息页"}

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 18808))  # Default to 8000 if not set
    print("port is ",port)
    uvicorn.run(app, host=host, port=port)