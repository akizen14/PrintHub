from fastapi import APIRouter, HTTPException
from typing import List, Optional
import time
import uuid

from ..models import Printer, PrinterUpdate
from ..storage import insert_one, find_all, find_by_id, update_by_id, find_by_query
from ..printer_interface import (
    get_available_printers,
    print_pdf_file,
    get_printer_status,
    auto_select_printer
)

router = APIRouter(prefix="/printers", tags=["printers"])


@router.post("", response_model=Printer)
async def create_printer(printer: Printer):
    """Add a new printer."""
    printer_dict = printer.model_dump()
    printer_dict["updatedAt"] = int(time.time())
    
    # Ensure ID is set
    if not printer_dict.get("id"):
        printer_dict["id"] = str(uuid.uuid4())
    
    insert_one("printers", printer_dict)
    return Printer(**printer_dict)


@router.get("", response_model=List[Printer])
async def list_printers():
    """List all printers."""
    printers = find_all("printers")
    return [Printer(**p) for p in printers]


@router.get("/{printer_id}", response_model=Printer)
async def get_printer(printer_id: str):
    """Get a specific printer by ID."""
    printer = find_by_id("printers", printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return Printer(**printer)


@router.patch("/{printer_id}", response_model=Printer)
async def update_printer(printer_id: str, update: PrinterUpdate):
    """Update a printer."""
    printer = find_by_id("printers", printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    updates = update.model_dump(exclude_unset=True)
    updates["updatedAt"] = int(time.time())
    
    update_by_id("printers", printer_id, updates)
    
    updated_printer = find_by_id("printers", printer_id)
    return Printer(**updated_printer)


@router.get("/discover/system")
async def discover_system_printers():
    """
    Auto-discover printers from Windows system.
    Syncs with database and returns discovered printers.
    """
    try:
        # Get system printers
        system_printers = get_available_printers()
        
        discovered = []
        updated = []
        
        for sp in system_printers:
            # Check if printer already exists in database
            existing = find_by_query("printers", {"name": sp["name"]})
            
            if existing:
                # Update existing printer
                printer_id = existing[0]["id"]
                updates = {
                    "status": sp["status"],
                    "color": sp["color"],
                    "duplex": sp["duplex"],
                    "a4": sp["a4"],
                    "a3": sp["a3"],
                    "updatedAt": int(time.time())
                }
                update_by_id("printers", printer_id, updates)
                updated.append(sp["name"])
            else:
                # Add new printer
                printer = {
                    "id": str(uuid.uuid4()),
                    "name": sp["name"],
                    "status": sp["status"],
                    "ppm": 20,  # Default, can be configured later
                    "color": sp["color"],
                    "duplex": sp["duplex"],
                    "a4": sp["a4"],
                    "a3": sp["a3"],
                    "currentJobId": None,
                    "progressPct": 0,
                    "updatedAt": int(time.time())
                }
                insert_one("printers", printer)
                discovered.append(sp["name"])
        
        return {
            "discovered": len(discovered),
            "updated": len(updated),
            "total": len(system_printers),
            "printers": system_printers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover printers: {str(e)}")


@router.post("/{printer_id}/print")
async def send_to_printer(printer_id: str, order_id: str):
    """
    Send a print job to the actual printer.
    Requires order to have a file attached.
    """
    # Get printer
    printer = find_by_id("printers", printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    # Get order
    from ..storage import find_by_id as find_order
    order = find_order("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if file exists
    file_path = order.get("filePath")
    if not file_path:
        raise HTTPException(status_code=400, detail="No file attached to order")
    
    try:
        # Send to real printer
        success = print_pdf_file(
            printer["name"],
            file_path,
            order.get("copies", 1)
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send job to printer")
        
        # Update order status
        from ..storage import update_by_id as update_order
        update_order("orders", order_id, {
            "status": "Printing",
            "updatedAt": int(time.time())
        })
        
        # Update printer status
        update_by_id("printers", printer_id, {
            "status": "printing",
            "currentJobId": order_id,
            "updatedAt": int(time.time())
        })
        
        return {
            "success": True,
            "message": "Print job sent to printer",
            "printer": printer["name"],
            "order_id": order_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Print error: {str(e)}")


@router.get("/{printer_id}/status")
async def get_printer_real_status(printer_id: str):
    """
    Get real-time status from the actual printer.
    """
    printer = find_by_id("printers", printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    try:
        status = get_printer_status(printer["name"])
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get printer status: {str(e)}")


@router.post("/auto-assign/{order_id}")
async def auto_assign_printer_to_order(order_id: str):
    """
    Automatically assign the best available printer to an order
    based on job requirements (color, paper size).
    """
    # Get order
    from ..storage import find_by_id as find_order
    order = find_order("orders", order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get all printers from database
    db_printers = find_all("printers")
    
    # Determine requirements
    requires_color = order.get("color") == "color"
    requires_a3 = order.get("size") == "A3"
    
    # Auto-select best printer
    selected = auto_select_printer(db_printers, requires_color, requires_a3)
    
    if not selected:
        raise HTTPException(status_code=404, detail="No suitable printer available")
    
    # Assign printer to order
    from ..storage import update_by_id as update_order
    update_order("orders", order_id, {
        "assignedPrinterId": selected["id"],
        "status": "Queued",
        "updatedAt": int(time.time())
    })
    
    return {
        "success": True,
        "printer": selected["name"],
        "printer_id": selected["id"],
        "reason": f"Auto-selected based on requirements: color={requires_color}, a3={requires_a3}"
    }
