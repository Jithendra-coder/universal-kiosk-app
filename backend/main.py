import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from uuid import UUID

# Import our custom logic and shapes
from database import supabase
import schemas

app = FastAPI(title="Universal Food Kiosk API")

# --- 1. SECURITY & CORS ---
# We pull the allowed origins from environment variables for security
# If no variable is found, it defaults to localhost for development
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. KIOSK ENDPOINTS (Customer Facing) ---

@app.get("/menu/{restaurant_id}", response_model=List[schemas.Product])
async def get_active_menu(restaurant_id: UUID):
    """Fetches only available items for the Kiosk display."""
    response = supabase.table("products") \
        .select("*") \
        .eq("restaurant_id", str(restaurant_id)) \
        .eq("is_available", True) \
        .execute()
    
    return response.data if response.data else []

@app.post("/orders", response_model=schemas.StandardResponse)
async def place_order(order: schemas.OrderCreate):
    """
    Receives order from Kiosk, saves to DB.
    This triggers the 'Realtime' listener on the Kitchen Screen!
    """
    try:
        # 1. Insert the main order record
        order_data = {
            "restaurant_id": str(order.restaurant_id),
            "total_amount": order.total_amount,
            "status": schemas.OrderStatus.PENDING,
            "order_type": order.order_type
        }
        
        res_order = supabase.table("orders").insert(order_data).execute()
        
        if not res_order.data:
            raise Exception("Failed to create order record")
            
        new_order_id = res_order.data[0]['id']

        # 2. Insert all items in that order
        items_to_insert = [
            {
                "order_id": new_order_id,
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "customizations": item.customizations,
                "price_at_time_of_sale": item.price_at_time_of_sale
            }
            for item in order.items
        ]
        
        supabase.table("order_items").insert(items_to_insert).execute()

        return schemas.StandardResponse(
            message="Order placed successfully!",
            data={"order_id": new_order_id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- 3. KITCHEN & ADMIN ENDPOINTS ---

@app.patch("/orders/{order_id}/status")
async def update_order_status(order_id: UUID, update: schemas.OrderStatusUpdate):
    """Kitchen staff uses this to move order from 'Pending' to 'Ready'."""
    res = supabase.table("orders") \
        .update({"status": update.status}) \
        .eq("id", str(order_id)) \
        .execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"status": "updated", "new_status": update.status}

@app.patch("/products/{product_id}/availability")
async def toggle_availability(product_id: UUID, update: schemas.AvailabilityUpdate):
    """Kitchen staff uses this to 'Sold Out' an item instantly."""
    res = supabase.table("products") \
        .update({"is_available": update.is_available}) \
        .eq("id", str(product_id)) \
        .execute()
    
    return {"status": "success", "is_available": update.is_available}

# --- 4. HEALTH CHECK ---
@app.get("/")
def home():
    return {
        "status": "Kiosk API is Online", 
        "version": "1.0.0",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }

if __name__ == "__main__":
    import uvicorn
    # Port is dynamically assigned by Railway via environment variable
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)