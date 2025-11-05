from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import time
import uuid

from .routers import orders, printers, rates, settings
from .storage import insert_one, upsert_single, clear_table
from .models import Order, Printer, Rates, Settings, Thresholds

app = FastAPI(title="PrintHub API", version="1.0.0")

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(orders.router)
app.include_router(printers.router)
app.include_router(rates.router)
app.include_router(settings.router)


@app.get("/")
async def root():
    return {"message": "PrintHub API", "version": "1.0.0"}


@app.post("/seed")
async def seed_data():
    """Seed the database with demo data."""
    now = int(time.time())
    
    # Clear existing data
    clear_table("orders")
    clear_table("printers")
    
    # Create default rates
    rates_data = {
        "bwSingleA4": 1.0,
        "bwDuplexA4": 0.75,
        "colorSingleA4": 5.0,
        "colorDuplexA4": 4.0,
        "minCharge": 5.0,
        "effectiveDate": now
    }
    upsert_single("rates", rates_data)
    
    # Create default settings with admin password hash for "printhub2025"
    admin_pass = "printhub2025"
    admin_hash = hashlib.sha256(admin_pass.encode()).hexdigest()
    
    settings_data = {
        "adminPassHash": admin_hash,
        "thresholds": {
            "smallPages": 15,
            "chunkPages": 100,
            "agingMinutes": 12
        }
    }
    upsert_single("settings", settings_data)
    
    # Create 2 printers
    printer1 = {
        "id": "printer-laser-a4",
        "name": "Laser-A4",
        "status": "idle",
        "ppm": 30,
        "color": False,
        "duplex": True,
        "a4": True,
        "a3": False,
        "currentJobId": None,
        "progressPct": 0,
        "updatedAt": now
    }
    insert_one("printers", printer1)
    
    printer2 = {
        "id": "printer-colorpro",
        "name": "ColorPro",
        "status": "idle",
        "ppm": 20,
        "color": True,
        "duplex": True,
        "a4": True,
        "a3": True,
        "currentJobId": None,
        "progressPct": 0,
        "updatedAt": now
    }
    insert_one("printers", printer2)
    
    # Create 4 sample orders
    # Order 1: Urgent (pickup in 30 minutes)
    order1 = {
        "id": str(uuid.uuid4()),
        "studentName": "Alice Johnson",
        "mobile": "9876543210",
        "fileName": "Assignment.pdf",
        "pages": 10,
        "copies": 1,
        "color": "bw",
        "sides": "duplex",
        "size": "A4",
        "pickupTime": now + 1800,  # 30 minutes from now
        "status": "Pending",
        "queueType": "urgent",
        "priorityIndex": now - 3000,
        "priorityScore": 5.0,
        "assignedPrinterId": None,
        "progressPct": 0,
        "estimatedSec": None,
        "priceTotal": 7.5,
        "createdAt": now - 3000,
        "updatedAt": now - 3000
    }
    insert_one("orders", order1)
    
    # Order 2: Normal (small job)
    order2 = {
        "id": str(uuid.uuid4()),
        "studentName": "Bob Smith",
        "mobile": "9876543211",
        "fileName": "Notes.pdf",
        "pages": 5,
        "copies": 2,
        "color": "bw",
        "sides": "single",
        "size": "A4",
        "pickupTime": None,
        "status": "Pending",
        "queueType": "normal",
        "priorityIndex": now - 2000,
        "priorityScore": 3.0,
        "assignedPrinterId": None,
        "progressPct": 0,
        "estimatedSec": None,
        "priceTotal": 10.0,
        "createdAt": now - 2000,
        "updatedAt": now - 2000
    }
    insert_one("orders", order2)
    
    # Order 3: Bulk (large job)
    order3 = {
        "id": str(uuid.uuid4()),
        "studentName": "Charlie Davis",
        "mobile": "9876543212",
        "fileName": "Thesis.pdf",
        "pages": 150,
        "copies": 1,
        "color": "bw",
        "sides": "duplex",
        "size": "A4",
        "pickupTime": None,
        "status": "Pending",
        "queueType": "bulk",
        "priorityIndex": now - 1000,
        "priorityScore": 1.0,
        "assignedPrinterId": None,
        "progressPct": 0,
        "estimatedSec": None,
        "priceTotal": 112.5,
        "createdAt": now - 1000,
        "updatedAt": now - 1000
    }
    insert_one("orders", order3)
    
    # Order 4: Normal (another small job)
    order4 = {
        "id": str(uuid.uuid4()),
        "studentName": "Diana Prince",
        "mobile": "9876543213",
        "fileName": "Report.pdf",
        "pages": 12,
        "copies": 1,
        "color": "color",
        "sides": "single",
        "size": "A4",
        "pickupTime": None,
        "status": "Pending",
        "queueType": "normal",
        "priorityIndex": now - 500,
        "priorityScore": 2.5,
        "assignedPrinterId": None,
        "progressPct": 0,
        "estimatedSec": None,
        "priceTotal": 60.0,
        "createdAt": now - 500,
        "updatedAt": now - 500
    }
    insert_one("orders", order4)
    
    return {
        "message": "Database seeded successfully",
        "printers": 2,
        "orders": 4,
        "adminPassword": "printhub2025"
    }
