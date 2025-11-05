from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import hashlib
import time
import uuid

from .routers import orders, printers, rates, settings
from .storage import insert_one, upsert_single, clear_table
from .models import Order, Printer, Rates, Settings, Thresholds

app = FastAPI(title="PrintHub API", version="1.0.0")

# Add GZIP compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Performance monitoring middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header for monitoring performance."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    # Log slow requests (>1 second)
    if process_time > 1.0:
        print(f"⚠️  Slow request: {request.method} {request.url.path} took {process_time:.3f}s")
    return response

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
    # Order 1: Urgent (pickup in 30 minutes) - PAID
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
        "status": "Queued",
        "paymentStatus": "paid",
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
    
    # Order 2: Normal (small job) - PAID
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
        "status": "Queued",
        "paymentStatus": "paid",
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
    
    # Order 3: Bulk (large job) - UNPAID (Pending payment)
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
        "paymentStatus": "unpaid",
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
    
    # Order 4: Normal (another small job) - PAID
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
        "status": "Queued",
        "paymentStatus": "paid",
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
        "note": "3 orders are paid (Queued), 1 order is unpaid (Pending)",
        "adminPassword": "printhub2025"
    }
