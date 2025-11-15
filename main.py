from typing import Dict, List, Optional
from uuid import UUID, uuid4
import logging

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi-backend")

app = FastAPI(
    title="Example FastAPI Backend",
    version="0.1.0",
    description="A small example FastAPI backend with basic CRUD for items.",
)

# Enable CORS for development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ItemCreate(BaseModel):
    name: str = Field(..., example="Widget")
    description: Optional[str] = Field(None, example="A useful widget")
    price: float = Field(..., gt=0, example=9.99)
    in_stock: bool = Field(True, example=True)

class Item(ItemCreate):
    id: UUID

# Simple in-memory store
items: Dict[UUID, Item] = {}

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting FastAPI backend")
    # Optional: preload sample item
    sample_id = uuid4()
    items[sample_id] = Item(id=sample_id, name="Sample", description="Preloaded item", price=1.0, in_stock=True)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FastAPI backend")

# Root and health endpoints
@app.get("/", status_code=status.HTTP_200_OK)
async def read_root():
    return {"message": "FastAPI backend running"}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok"}

# CRUD endpoints for items
@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemCreate):
    item_id = uuid4()
    item = Item(id=item_id, **payload.dict())
    items[item_id] = item
    return item

@app.get("/items", response_model=List[Item], status_code=status.HTTP_200_OK)
async def list_items(skip: int = 0, limit: int = 100):
    all_items = list(items.values())
    return all_items[skip : skip + limit]

@app.get("/items/{item_id}", response_model=Item, status_code=status.HTTP_200_OK)
async def get_item(item_id: UUID):
    item = items.get(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=Item, status_code=status.HTTP_200_OK)
async def update_item(item_id: UUID, payload: ItemCreate):
    existing = items.get(item_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    updated = Item(id=item_id, **payload.dict())
    items[item_id] = updated
    return updated

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: UUID):
    if item_id not in items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    del items[item_id]
    return None

# Run with: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)