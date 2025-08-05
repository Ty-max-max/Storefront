from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Digital Storefront API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "digital_storefront")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Pydantic models
class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    price: float
    image_url: str
    file_content: Optional[str] = None

class Product(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    image_url: str
    created_at: datetime
    file_content: Optional[str] = None

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1

class Order(BaseModel):
    id: str
    items: List[CartItem]
    total_amount: float
    customer_email: Optional[str] = None
    payment_status: str = "pending"
    created_at: datetime
    paypal_order_id: Optional[str] = None

class PayPalOrderRequest(BaseModel):
    items: List[CartItem]
    customer_email: Optional[str] = None

# Initialize sample products
@app.on_event("startup")
async def create_sample_products():
    """Initialize sample products if they don't exist"""
    try:
        existing_products = await db.products.count_documents({})
        if existing_products == 0:
            logger.info("Creating sample products...")
            sample_products = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Professional Resume Template",
                    "description": "Modern, ATS-friendly resume template perfect for job seekers. Includes cover letter template.",
                    "category": "resume",
                    "price": 5.0,
                    "image_url": "https://images.unsplash.com/photo-1743385779347-1549dabf1320",
                    "created_at": datetime.utcnow(),
                    "file_content": "Sample resume template content..."
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Creative Resume Template",
                    "description": "Eye-catching resume template for creative professionals. Stand out from the crowd!",
                    "category": "resume",
                    "price": 5.0,
                    "image_url": "https://images.unsplash.com/photo-1753161029492-0644556055cf",
                    "created_at": datetime.utcnow(),
                    "file_content": "Sample creative resume template..."
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Counting Fun eBook",
                    "description": "Interactive counting book for toddlers (ages 2-4). Learn numbers 1-20 with colorful illustrations.",
                    "category": "ebook",
                    "price": 5.0,
                    "image_url": "https://images.unsplash.com/photo-1718353097521-e47e1d67edc2",
                    "created_at": datetime.utcnow(),
                    "file_content": "Sample counting ebook content..."
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Alphabet Adventure eBook",
                    "description": "Learn the alphabet with fun characters and rhymes. Perfect for early readers!",
                    "category": "ebook",
                    "price": 5.0,
                    "image_url": "https://images.pexels.com/photos/7946399/pexels-photo-7946399.jpeg",
                    "created_at": datetime.utcnow(),
                    "file_content": "Sample alphabet ebook content..."
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "The Magic Forest Story",
                    "description": "An enchanting bedtime story about friendship and adventure in a magical forest.",
                    "category": "storybook",
                    "price": 10.0,
                    "image_url": "https://images.pexels.com/photos/6214388/pexels-photo-6214388.jpeg",
                    "created_at": datetime.utcnow(),
                    "file_content": "Sample storybook content..."
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Little Dragon's Big Day",
                    "description": "A heartwarming story about courage and friendship. Perfect for bedtime reading!",
                    "category": "storybook",
                    "price": 10.0,
                    "image_url": "https://images.pexels.com/photos/7946399/pexels-photo-7946399.jpeg",
                    "created_at": datetime.utcnow(),
                    "file_content": "Sample dragon storybook content..."
                }
            ]
            
            await db.products.insert_many(sample_products)
            logger.info(f"Created {len(sample_products)} sample products")
            
    except Exception as e:
        logger.error(f"Error creating sample products: {e}")

# API Routes
@app.get("/")
async def root():
    return {"message": "Digital Storefront API"}

@app.get("/api/products", response_model=List[Product])
async def get_products(category: Optional[str] = None):
    """Get all products or filter by category"""
    try:
        query = {}
        if category:
            query["category"] = category
            
        products = await db.products.find(query).to_list(length=None)
        return products
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch products")

@app.get("/api/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get a specific product by ID"""
    try:
        product = await db.products.find_one({"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch product")

@app.post("/api/orders/create")
async def create_order(order_request: PayPalOrderRequest):
    """Create a new order"""
    try:
        # Calculate total amount
        total_amount = 0.0
        order_items = []
        
        for item in order_request.items:
            product = await db.products.find_one({"id": item.product_id})
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            
            item_total = product["price"] * item.quantity
            total_amount += item_total
            order_items.append({
                "product_id": item.product_id,
                "product_name": product["name"],
                "price": product["price"],
                "quantity": item.quantity
            })
        
        # Create order
        order_id = str(uuid.uuid4())
        order = {
            "id": order_id,
            "items": order_items,
            "total_amount": total_amount,
            "customer_email": order_request.customer_email,
            "payment_status": "pending",
            "created_at": datetime.utcnow(),
            "paypal_order_id": None
        }
        
        await db.orders.insert_one(order)
        
        return {
            "order_id": order_id,
            "total_amount": total_amount,
            "items": order_items,
            "message": "Order created successfully. PayPal integration ready for credentials."
        }
        
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create order")

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Get order details"""
    try:
        order = await db.orders.find_one({"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except Exception as e:
        logger.error(f"Error fetching order: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch order")

@app.post("/api/paypal/create-order")
async def create_paypal_order(order_request: PayPalOrderRequest):
    """Create PayPal payment order - Ready for PayPal credentials"""
    try:
        # For now, return mock response until PayPal credentials are added
        order_id = str(uuid.uuid4())
        
        return {
            "status": "READY_FOR_PAYPAL_INTEGRATION",
            "message": "PayPal integration structure ready. Add PayPal Client ID and Secret to activate payments.",
            "order_id": order_id,
            "total_amount": sum([5.0 if item.product_id else 0.0 for item in order_request.items]),
            "next_steps": [
                "1. Get PayPal Client ID and Secret from https://developer.paypal.com/",
                "2. Add credentials to backend/.env file",
                "3. Restart backend service",
                "4. PayPal payments will be fully functional"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error creating PayPal order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create PayPal order")

@app.get("/api/categories")
async def get_categories():
    """Get all product categories"""
    return {
        "categories": [
            {
                "id": "resume",
                "name": "Resume Templates", 
                "description": "Professional resume templates for job seekers",
                "price": 5.0,
                "image_url": "https://images.unsplash.com/photo-1743385779347-1549dabf1320"
            },
            {
                "id": "ebook",
                "name": "Learning eBooks",
                "description": "Educational ebooks for toddlers learning to count and read",
                "price": 5.0,
                "image_url": "https://images.unsplash.com/photo-1718353097521-e47e1d67edc2"
            },
            {
                "id": "storybook", 
                "name": "Story Books",
                "description": "Engaging storybooks for bedtime and learning",
                "price": 10.0,
                "image_url": "https://images.pexels.com/photos/7946399/pexels-photo-7946399.jpeg"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)