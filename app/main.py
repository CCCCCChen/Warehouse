from fastapi import FastAPI
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