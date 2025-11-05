# Real Printer Integration Guide

## Current Status

PrintHub currently uses **simulated printing** with progress bars. To connect to real printers, you need to integrate with your operating system's print spooler.

## Windows Printer Integration

### Option 1: Using `win32print` (Recommended for Windows)

#### 1. Install Dependencies

```bash
pip install pywin32
```

#### 2. Create Printer Interface Module

Create `backend/app/printer_interface.py`:

```python
import win32print
import win32api
import os
from typing import List, Dict

def get_available_printers() -> List[Dict]:
    """Get list of all installed printers on Windows"""
    printers = []
    printer_enum = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
    
    for printer in printer_enum:
        printer_name = printer[2]
        handle = win32print.OpenPrinter(printer_name)
        printer_info = win32print.GetPrinter(handle, 2)
        
        printers.append({
            "name": printer_name,
            "status": "idle" if printer_info["Status"] == 0 else "busy",
            "port": printer_info["pPortName"],
            "driver": printer_info["pDriverName"],
        })
        
        win32print.ClosePrinter(handle)
    
    return printers


def print_file(printer_name: str, file_path: str, copies: int = 1) -> bool:
    """Send a file to the printer"""
    try:
        # For PDF files, use ShellExecute to print
        win32api.ShellExecute(
            0,
            "print",
            file_path,
            f'/d:"{printer_name}"',
            ".",
            0
        )
        return True
    except Exception as e:
        print(f"Print error: {e}")
        return False


def get_printer_status(printer_name: str) -> Dict:
    """Get detailed printer status"""
    try:
        handle = win32print.OpenPrinter(printer_name)
        printer_info = win32print.GetPrinter(handle, 2)
        jobs = win32print.EnumJobs(handle, 0, -1, 1)
        
        status = {
            "status": "idle" if printer_info["Status"] == 0 else "busy",
            "jobs_in_queue": len(jobs),
            "current_job": jobs[0] if jobs else None
        }
        
        win32print.ClosePrinter(handle)
        return status
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

#### 3. Update Backend to Use Real Printers

Modify `backend/app/routers/printers.py`:

```python
from ..printer_interface import get_available_printers, print_file, get_printer_status

@router.get("/discover")
async def discover_printers():
    """Auto-discover installed printers"""
    return get_available_printers()

@router.post("/{printer_id}/print")
async def send_to_printer(printer_id: str, file_path: str, copies: int = 1):
    """Send job to real printer"""
    printer = find_by_id("printers", printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    success = print_file(printer["name"], file_path, copies)
    return {"success": success}
```

### Option 2: Using CUPS (Linux/Mac)

```bash
pip install pycups
```

```python
import cups

def get_available_printers():
    conn = cups.Connection()
    printers = conn.getPrinters()
    return [{"name": name, **info} for name, info in printers.items()]

def print_file(printer_name, file_path):
    conn = cups.Connection()
    conn.printFile(printer_name, file_path, "PrintHub Job", {})
```

## File Upload Integration

To print real files, you need to add file upload capability:

### 1. Update Backend for File Upload

```python
from fastapi import UploadFile, File
import shutil
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/orders/upload")
async def create_order_with_file(
    file: UploadFile = File(...),
    studentName: str = Form(...),
    mobile: str = Form(...),
    # ... other fields
):
    # Save uploaded file
    file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create order with file path
    order = {
        # ... order fields
        "filePath": str(file_path),
        "fileName": file.filename
    }
    
    insert_one("orders", order)
    return Order(**order)
```

### 2. Update Web Frontend

```tsx
// In app/order/new/page.tsx
const [file, setFile] = useState<File | null>(null);

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  
  const formData = new FormData();
  if (file) formData.append('file', file);
  formData.append('studentName', formData.studentName);
  // ... other fields
  
  const response = await fetch('http://localhost:8000/orders/upload', {
    method: 'POST',
    body: formData,
  });
  
  // Handle response
};

// Add file input
<input 
  type="file" 
  accept=".pdf,.doc,.docx"
  onChange={(e) => setFile(e.target.files?.[0] || null)}
/>
```

## Complete Integration Steps

### Step 1: Install System Dependencies

```bash
# Backend
cd backend
pip install pywin32  # Windows
# OR
pip install pycups   # Linux/Mac

# Add to requirements.txt
echo "pywin32" >> requirements.txt  # Windows
```

### Step 2: Create Printer Discovery Endpoint

Add to `backend/app/main.py`:

```python
from .printer_interface import get_available_printers

@app.get("/printers/discover")
async def discover_system_printers():
    """Auto-discover printers from system"""
    system_printers = get_available_printers()
    
    # Sync with database
    for sp in system_printers:
        existing = find_by_query("printers", {"name": sp["name"]})
        if not existing:
            # Add new printer to database
            printer = {
                "id": str(uuid.uuid4()),
                "name": sp["name"],
                "status": sp["status"],
                "ppm": 20,  # Default, can be configured
                "color": True,  # Detect from driver if possible
                "duplex": True,
                "a4": True,
                "a3": False,
                "updatedAt": int(time.time())
            }
            insert_one("printers", printer)
    
    return {"discovered": len(system_printers)}
```

### Step 3: Update Admin App

Add printer discovery button in `admin-app/main.py`:

```python
def discover_printers(self):
    """Discover system printers"""
    try:
        response = requests.get(f"{API_BASE}/printers/discover")
        if response.status_code == 200:
            result = response.json()
            QMessageBox.information(
                self, 
                "Success", 
                f"Discovered {result['discovered']} printers"
            )
            self.poll_data()
        else:
            QMessageBox.warning(self, "Error", "Failed to discover printers")
    except Exception as e:
        QMessageBox.critical(self, "Error", str(e))

# Add button in printers tab
discover_btn = QPushButton("Discover System Printers")
discover_btn.clicked.connect(self.discover_printers)
```

### Step 4: Implement Real Printing

Update the start_printing method:

```python
def start_printing(self):
    """Start printing job on real printer"""
    if not self.selected_order:
        return
    
    order = self.selected_order
    
    # Check if file exists
    if not order.get('filePath'):
        QMessageBox.warning(self, "Error", "No file attached to this order")
        return
    
    printer = next((p for p in self.printers if p['id'] == order.get('assignedPrinterId')), None)
    
    if not printer:
        QMessageBox.warning(self, "Error", "No printer assigned")
        return
    
    try:
        # Send to real printer
        response = requests.post(
            f"{API_BASE}/printers/{printer['id']}/print",
            json={
                "file_path": order['filePath'],
                "copies": order['copies']
            }
        )
        
        if response.status_code == 200:
            # Update order status
            requests.patch(
                f"{API_BASE}/orders/{order['id']}",
                json={"status": "Printing"}
            )
            
            QMessageBox.information(self, "Success", "Job sent to printer")
            self.poll_data()
        else:
            QMessageBox.warning(self, "Error", "Failed to send to printer")
    except Exception as e:
        QMessageBox.critical(self, "Error", str(e))
```

## Monitoring Real Print Jobs

### Get Job Status from Spooler

```python
def monitor_print_job(printer_name: str, job_id: int):
    """Monitor real print job progress"""
    handle = win32print.OpenPrinter(printer_name)
    
    while True:
        jobs = win32print.EnumJobs(handle, 0, -1, 1)
        job = next((j for j in jobs if j["JobId"] == job_id), None)
        
        if not job:
            # Job completed
            break
        
        # Calculate progress
        pages_printed = job.get("PagesPrinted", 0)
        total_pages = job.get("TotalPages", 1)
        progress = int((pages_printed / total_pages) * 100)
        
        # Update database
        # ... update order progress
        
        time.sleep(1)
    
    win32print.ClosePrinter(handle)
```

## Testing with Real Printers

### 1. Test Printer Discovery

```bash
curl http://localhost:8000/printers/discover
```

### 2. Test File Upload

```bash
curl -X POST http://localhost:8000/orders/upload \
  -F "file=@test.pdf" \
  -F "studentName=Test Student" \
  -F "mobile=1234567890" \
  -F "pages=5" \
  -F "copies=1" \
  -F "color=bw" \
  -F "sides=single" \
  -F "size=A4"
```

### 3. Test Real Printing

```bash
curl -X POST http://localhost:8000/printers/{printer_id}/print \
  -H "Content-Type: application/json" \
  -d '{"file_path": "uploads/test.pdf", "copies": 1}'
```

## Security Considerations

1. **File Validation:** Only accept PDF, DOC, DOCX files
2. **File Size Limits:** Set max upload size (e.g., 50MB)
3. **Virus Scanning:** Integrate antivirus for uploaded files
4. **Access Control:** Restrict printer access by user/role
5. **Audit Logging:** Log all print jobs for tracking

## Limitations

- **Current Implementation:** Simulated printing only
- **Real Printing:** Requires OS-specific libraries
- **File Storage:** Need to implement upload/storage
- **Progress Tracking:** Depends on printer driver capabilities
- **Network Printers:** May require additional configuration

## Next Steps

1. Install `pywin32` (Windows) or `pycups` (Linux/Mac)
2. Create `printer_interface.py` module
3. Add file upload endpoints
4. Update frontend for file uploads
5. Test with a real printer
6. Implement job monitoring
7. Add error handling and logging

## Support

For printer-specific issues:
- Check printer drivers are installed
- Verify printer is online and accessible
- Test printing from other applications first
- Check Windows Print Spooler service is running
