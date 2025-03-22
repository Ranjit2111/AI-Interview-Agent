"""
Demo FastAPI application to show how docs_generator works.
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

# Create a simple FastAPI app
app = FastAPI(
    title="Demo API",
    description="A simple API to demonstrate documentation generation",
    version="0.1.0"
)

# Define a data model
class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    tags: List[str] = []

# Sample data
items = [
    Item(id=1, name="Laptop", description="A powerful computer", price=999.99, tags=["electronics", "computers"]),
    Item(id=2, name="Phone", description="Latest smartphone", price=699.99, tags=["electronics", "mobile"]),
]

@app.get("/")
def read_root():
    """
    Get a welcome message.
    
    Returns:
        A greeting message
    """
    return {"message": "Welcome to the Demo API"}

@app.get("/items/", response_model=List[Item])
def list_items(skip: int = 0, limit: int = 10):
    """
    Get a list of items.
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        List of items
    """
    return items[skip : skip + limit]

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    """
    Get an item by ID.
    
    Args:
        item_id: The ID of the item to retrieve
        
    Returns:
        The item with the specified ID
        
    Raises:
        HTTPException: If the item is not found
    """
    for item in items:
        if item.id == item_id:
            return item
    return {"error": "Item not found"}

@app.post("/items/", response_model=Item)
def create_item(item: Item):
    """
    Create a new item.
    
    Args:
        item: The item to create
        
    Returns:
        The created item
    """
    items.append(item)
    return item

@app.get("/search/")
def search_items(q: str = Query(..., description="Search query")):
    """
    Search for items by name or description.
    
    Args:
        q: Search query
        
    Returns:
        List of matching items
    """
    results = []
    for item in items:
        if q.lower() in item.name.lower() or (item.description and q.lower() in item.description.lower()):
            results.append(item)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 