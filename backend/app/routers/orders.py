from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from functools import lru_cache
import time
import uuid
import tempfile
from pathlib import Path
import json

from ..models import Order, OrderIn, OrderUpdate, PaymentConfirmation, BatchOrderUpdate
from ..storage import insert_one, find_all, find_by_id, update_by_id, find_by_query, get_single, batch_update_by_ids, batch_delete_by_ids
from ..scheduler import classify_queue, priority_score, normalize_priority
from ..file_handler import process_uploaded_file, FileValidationError, get_file_info
from ..constants import (
    STATUS_PENDING, STATUS_QUEUED, STATUS_PRINTING, STATUS_READY,
    STATUS_COLLECTED, STATUS_CANCELLED,
    PAYMENT_UNPAID, PAYMENT_PAID, PAYMENT_REFUNDED,
    CACHE_DURATION_SECONDS
)


router = APIRouter(prefix="/orders", tags=["orders"])

# Legacy constant aliases for backwards compatibility
ORDER_STATUS_PENDING = STATUS_PENDING
ORDER_STATUS_QUEUED = STATUS_QUEUED
ORDER_STATUS_PRINTING = STATUS_PRINTING
ORDER_STATUS_READY = STATUS_READY
ORDER_STATUS_COLLECTED = STATUS_COLLECTED
ORDER_STATUS_CANCELLED = STATUS_CANCELLED
PAYMENT_STATUS_UNPAID = PAYMENT_UNPAID
PAYMENT_STATUS_PAID = PAYMENT_PAID
PAYMENT_STATUS_REFUNDED = PAYMENT_REFUNDED


# Cache rates for 60 seconds to reduce disk reads
@lru_cache(maxsize=1)
def get_cached_rates(cache_key: int):
    """Cache rates data for CACHE_DURATION_SECONDS (cache_key is timestamp // CACHE_DURATION_SECONDS)."""
    return get_single("rates")


# Cache settings for 60 seconds to reduce disk reads
@lru_cache(maxsize=1)
def get_cached_settings(cache_key: int):
    """Cache settings data for CACHE_DURATION_SECONDS (cache_key is timestamp // CACHE_DURATION_SECONDS)."""
    return get_single("settings")


def calculate_price(order_data: dict, rates: dict) -> float:
    """Calculate price based on order specs and current rates."""
    pages = order_data["pages"]
    copies = order_data["copies"]
    color = order_data["color"]
    sides = order_data["sides"]
    size = order_data["size"]
    
    # Get base rate
    if size == "A4":
        if color == "bw":
            rate = rates["bwDuplexA4"] if sides == "duplex" else rates["bwSingleA4"]
        else:
            rate = rates["colorDuplexA4"] if sides == "duplex" else rates["colorSingleA4"]
    else:  # A3
        # A3 is typically 2x A4 price
        if color == "bw":
            rate = (rates["bwDuplexA4"] if sides == "duplex" else rates["bwSingleA4"]) * 2
        else:
            rate = (rates["colorDuplexA4"] if sides == "duplex" else rates["colorSingleA4"]) * 2
    
    total = pages * copies * rate
    min_charge = rates.get("minCharge", 0)
    
    return max(total, min_charge)


def update_order_with_validation(order_id: str, updates: dict) -> Order:
    """
    Helper function to update an order with validation and timestamp.
    Returns the updated order or raises HTTPException if not found.
    """
    order = find_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Add timestamp
    updates["updatedAt"] = int(time.time())
    
    # Perform update
    update_by_id("orders", order_id, updates)
    
    # Fetch and return updated order
    updated_order = find_by_id("orders", order_id)
    return Order(**updated_order)


@router.post("/upload", response_model=Order)
async def create_order_with_file(
    file: UploadFile = File(...),
    studentName: str = Form(...),
    mobile: str = Form(...),
    copies: int = Form(1),
    color: str = Form("bw"),
    sides: str = Form("single"),
    size: str = Form("A4"),
    pickupTime: Optional[int] = Form(None),
):
    """
    Create order with file upload.
    File will be validated, converted to PDF if needed, and page count extracted.
    """
    # Generate order ID first
    order_id = str(uuid.uuid4())
    
    # Save uploaded file temporarily
    temp_file = Path(tempfile.gettempdir()) / f"upload_{order_id}_{file.filename}"
    
    try:
        # Save uploaded file
        with temp_file.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process file: validate, convert to PDF, extract page count
        final_pdf_path, page_count = process_uploaded_file(
            temp_file,
            file.filename,
            order_id
        )
        
        # Get current rates using cache
        cache_key = int(time.time() / CACHE_DURATION_SECONDS)
        rates_data = get_cached_rates(cache_key)
        if not rates_data:
            raise HTTPException(status_code=500, detail="Rates not configured")
        
        # Create order data
        order_data = {
            "studentName": studentName,
            "mobile": mobile,
            "fileName": file.filename,
            "filePath": str(final_pdf_path),
            "pages": page_count,  # Auto-detected from file
            "copies": copies,
            "color": color,
            "sides": sides,
            "size": size,
            "pickupTime": int(pickupTime) if pickupTime else None,
        }
        
        # Calculate price
        price_total = calculate_price(order_data, rates_data)
        
        # Classify queue
        queue_type = classify_queue(order_data, {})
        order_data["queueType"] = queue_type
        
        # Calculate priority score
        now = int(time.time())
        priority_score_value = priority_score(order_data, now, {})
        
        # Create full order
        order = {
            "id": order_id,
            **order_data,
            "status": ORDER_STATUS_PENDING,
            "paymentStatus": PAYMENT_STATUS_UNPAID,
            "queueType": queue_type,
            "priorityIndex": int(now),
            "priorityScore": priority_score_value,
            "priceTotal": price_total,
            "assignedPrinterId": None,
            "progressPct": 0,
            "estimatedSec": 0,
            "createdAt": int(time.time()),
            "updatedAt": int(time.time()),
        }
        
        # Normalize priority to ensure it's an integer
        order = normalize_priority(order)
        
        insert_one("orders", order)
        return Order(**order)
        
    except FileValidationError as e:
        # Clean up temp file if it exists
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        # Clean up temp file if it exists
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process order: {str(e)}")


@router.post("", response_model=Order)
async def create_order(order_in: OrderIn):
    """Create a new print order."""
    now = int(time.time())
    
    # Get current rates and settings using cache
    cache_key = int(now / CACHE_DURATION_SECONDS)
    rates_data = get_cached_rates(cache_key)
    if not rates_data:
        raise HTTPException(status_code=500, detail="Rates not configured")
    
    settings_data = get_cached_settings(cache_key)
    if not settings_data:
        raise HTTPException(status_code=500, detail="Settings not configured")
    
    thresholds = settings_data.get("thresholds", {"smallPages": 15, "chunkPages": 100, "agingMinutes": 12})
    
    # Create order dict
    order_dict = order_in.model_dump()
    order_dict["id"] = str(uuid.uuid4())
    order_dict["status"] = ORDER_STATUS_PENDING
    order_dict["paymentStatus"] = PAYMENT_STATUS_UNPAID
    order_dict["priorityIndex"] = now
    order_dict["createdAt"] = now
    order_dict["updatedAt"] = now
    order_dict["progressPct"] = 0
    order_dict["assignedPrinterId"] = None
    order_dict["estimatedSec"] = None
    
    # Classify queue type
    order_dict["queueType"] = classify_queue(order_dict, thresholds)
    
    # Calculate priority score
    order_dict["priorityScore"] = priority_score(order_dict, now, thresholds)
    
    # Calculate price
    order_dict["priceTotal"] = calculate_price(order_dict, rates_data)
    
    # Insert into database
    insert_one("orders", order_dict)
    
    return Order(**order_dict)


@router.get("", response_model=List[Order])
async def list_orders(status: Optional[str] = None, queueType: Optional[str] = None):
    """List all orders with optional filters."""
    orders = find_all("orders")
    
    # Apply filters
    if status:
        statuses = status.split("|")
        orders = [o for o in orders if o.get("status") in statuses]
    
    if queueType:
        orders = [o for o in orders if o.get("queueType") == queueType]
    
    # Normalize priorities before returning
    orders = [normalize_priority(o) for o in orders]
    
    # Ensure filePath is included
    for order in orders:
        if 'filePath' not in order or not order['filePath']:
            order_id = order.get('id')
            file_name = order.get('fileName', '')
            if file_name.lower().endswith('.pdf'):
                pdf_name = file_name
            else:
                pdf_name = file_name.rsplit('.', 1)[0] + '.pdf' if '.' in file_name else file_name + '.pdf'
            order['filePath'] = f"C:\\PrintHub\\Orders\\{order_id}\\{pdf_name}"
    
    return orders


@router.get("/{order_id}")
async def get_order(order_id: str):
    """Get a specific order by ID."""
    order = find_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order = normalize_priority(order)
    return order


@router.patch("/{order_id}", response_model=Order)
async def update_order(order_id: str, update: OrderUpdate):
    """Update an order."""
    order = find_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Prepare updates
    updates = update.model_dump(exclude_unset=True)
    
    # If priority changed, might need to reclassify
    if "priorityIndex" in updates:
        # Get settings for recalculation using cache
        now = int(time.time())
        cache_key = int(now / CACHE_DURATION_SECONDS)
        settings_data = get_cached_settings(cache_key)
        if settings_data:
            thresholds = settings_data.get("thresholds", {"smallPages": 15, "chunkPages": 100, "agingMinutes": 12})
            order.update(updates)
            order["priorityScore"] = priority_score(order, now, thresholds)
            updates["priorityScore"] = order["priorityScore"]
    
    # Use helper function to update
    return update_order_with_validation(order_id, updates)


@router.post("/{order_id}/confirm-payment", response_model=Order)
async def confirm_payment(order_id: str, payment_data: Optional[PaymentConfirmation] = None):
    """
    Confirm payment for an order and move it to Queued status.
    Optionally accepts transaction ID for payment tracking.
    """
    order = find_by_id("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order is in Pending status
    if order.get("status") != ORDER_STATUS_PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Order is already {order.get('status')}. Can only confirm payment for Pending orders."
        )
    
    # Check if payment is already confirmed
    if order.get("paymentStatus") == PAYMENT_STATUS_PAID:
        raise HTTPException(status_code=400, detail="Payment already confirmed")
    
    # Prepare updates
    now = int(time.time())
    updates = {
        "paymentStatus": PAYMENT_STATUS_PAID,
        "status": ORDER_STATUS_QUEUED,
        "paidAt": now
    }
    
    # Add transaction ID if provided
    if payment_data and payment_data.transactionId:
        updates["transactionId"] = payment_data.transactionId
    
    # Use helper function to update
    return update_order_with_validation(order_id, updates)


@router.post("/batch-update")
async def batch_update_orders(batch_update: BatchOrderUpdate):
    """
    Batch update multiple orders at once.
    Useful for bulk status changes, cancellations, etc.
    """
    if not batch_update.orderIds:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    
    # Prepare updates
    updates = batch_update.updates.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    updates["updatedAt"] = int(time.time())
    
    # Perform batch update
    count = batch_update_by_ids("orders", batch_update.orderIds, updates)
    
    return {
        "message": f"Successfully updated {count} orders",
        "updatedCount": count,
        "requestedCount": len(batch_update.orderIds)
    }


@router.post("/batch-delete")
async def batch_delete_orders(order_ids: List[str]):
    """
    Batch delete multiple orders at once.
    WARNING: This is a permanent deletion. Use batch cancel instead for soft delete.
    """
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    
    # Perform batch delete
    count = batch_delete_by_ids("orders", order_ids)
    
    return {
        "message": f"Successfully deleted {count} orders",
        "deletedCount": count,
        "requestedCount": len(order_ids)
    }


@router.post("/batch-cancel")
async def batch_cancel_orders(order_ids: List[str]):
    """
    Batch cancel multiple orders at once (soft delete).
    Sets status to Cancelled instead of permanently deleting.
    """
    if not order_ids:
        raise HTTPException(status_code=400, detail="No order IDs provided")
    
    # Update all to Cancelled status
    updates = {
        "status": ORDER_STATUS_CANCELLED,
        "updatedAt": int(time.time())
    }
    
    count = batch_update_by_ids("orders", order_ids, updates)
    
    return {
        "message": f"Successfully cancelled {count} orders",
        "cancelledCount": count,
        "requestedCount": len(order_ids)
    }
