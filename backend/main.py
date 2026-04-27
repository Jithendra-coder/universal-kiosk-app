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
# In production, ALLOWED_ORIGINS should be: http://localhost:3000,https://your-app.vercel.app
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. ADMIN ENDPOINTS (The missing piece!) ---

@app.post("/products", response_model=schemas.Product)
async def create_product(product: schemas.ProductCreate):
    """Adds a new item to the menu and saves it to Supabase."""
    try:
        # We convert the Pydantic model to a dict for Supabase
        res = supabase.table("products").insert(product.dict()).execute()
        
        if not res.data:
            raise Exception("Supabase insert failed")
            
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not save product: {str(e)}")

# --- 3. KIOSK ENDPOINTS (Customer Facing) ---

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

# --- 4. KITCHEN & ADMIN ENDPOINTS ---

@app.patch("/orders/{order_id}/status")
async def update_order_status(order_id: UUID, update: schemas.OrderStatusUpdate):
    res = supabase.table("orders") \
        .update({"status": update.status}) \
        .eq("id", str(order_id)) \
        .execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"status": "updated", "new_status": update.status}

@app.patch("/products/{product_id}/availability")
async def toggle_availability(product_id: UUID, update: schemas.AvailabilityUpdate):
    res = supabase.table("products") \
        .update({"is_available": update.is_available}) \
        .eq("id", str(product_id)) \
        .execute()
    
    return {"status": "success", "is_available": update.is_available}

# --- 5. HEALTH CHECK ---
@app.get("/")
def home():
    return {
        "status": "Kiosk API is Online", 
        "version": "1.0.0",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)