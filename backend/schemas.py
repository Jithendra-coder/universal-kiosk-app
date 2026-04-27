from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

# --- ENUMS ---
class OrderStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderType(str, Enum):
    DINE_IN = "dine-in"
    TAKEAWAY = "takeaway"

# --- PRODUCT SCHEMAS ---
class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category_name: str 
    image_url: Optional[str] = None
    is_available: bool = True
    metadata: Optional[Dict[str, Any]] = {}

class ProductCreate(ProductBase):
    restaurant_id: UUID

# THIS IS THE ONE MAIN.PY WAS MISSING:
class Product(ProductBase):
    id: UUID
    restaurant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- ORDER SCHEMAS ---
class OrderItemSchema(BaseModel):
    product_id: UUID
    quantity: int = Field(1, gt=0)
    customizations: List[str] = []
    price_at_time_of_sale: float 

class OrderCreate(BaseModel):
    restaurant_id: UUID
    items: List[OrderItemSchema]
    order_type: OrderType = OrderType.DINE_IN
    total_amount: float

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class AvailabilityUpdate(BaseModel):
    is_available: bool

# --- RESPONSE WRAPPER ---
class StandardResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[Any] = None