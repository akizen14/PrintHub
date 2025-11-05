# PrintHub - Technical Process Flow & PDF Rendering

## 📋 Table of Contents
1. [System Architecture](#system-architecture)
2. [Complete Order Lifecycle](#complete-order-lifecycle)
3. [File Upload & Processing](#file-upload--processing)
4. [PDF Rendering & Printing](#pdf-rendering--printing)
5. [Queue Management](#queue-management)
6. [Data Flow Diagrams](#data-flow-diagrams)

---

## 🏗️ System Architecture

### Components
```
┌─────────────────────────────────────────────────────────────┐
│                     PrintHub System                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Web App    │    │  Admin App   │    │   Backend    │  │
│  │  (Next.js)   │    │   (PyQt6)    │    │  (FastAPI)   │  │
│  │  Port 3000   │    │   Desktop    │    │  Port 8000   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                    │                    │          │
│         └────────────────────┴────────────────────┘          │
│                              │                               │
│                    ┌─────────▼─────────┐                    │
│                    │   TinyDB (JSON)   │                    │
│                    │   /data/*.json    │                    │
│                    └───────────────────┘                    │
│                                                               │
│                    ┌───────────────────┐                    │
│                    │  File Storage     │                    │
│                    │  C:/PrintHub/     │                    │
│                    │  Orders/{id}/     │                    │
│                    └───────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Order Lifecycle

### Phase 1: Order Creation (Web App → Backend)

```
Student (Web Browser)
    │
    ├─ 1. Navigate to /order/new
    │
    ├─ 2. Fill Form:
    │     • Student Name
    │     • Mobile Number
    │     • Upload File (PDF/DOCX/JPG/PNG)
    │     • Copies, Color, Sides, Size
    │     • Optional: Pickup Time
    │
    ├─ 3. Submit Form
    │     └─ Frontend validates file (max 50MB)
    │
    ├─ 4. POST /orders/upload (multipart/form-data)
    │     └─ File + Form Data
    │
    ▼
Backend (FastAPI)
    │
    ├─ 5. Receive Upload
    │     └─ Save to temp: /tmp/upload_{orderId}_{filename}
    │
    ├─ 6. Process File (file_handler.py)
    │     ├─ validate_file()
    │     │   • Check size (< 50MB)
    │     │   • Check extension (.pdf, .docx, .jpg, .png)
    │     │   • Check MIME type
    │     │
    │     ├─ Create order directory: C:/PrintHub/Orders/{orderId}/
    │     │
    │     └─ Convert to PDF if needed:
    │         ├─ PDF → Copy as-is
    │         ├─ DOCX → Convert using MS Word COM
    │         │   └─ docx2pdf or win32com.client
    │         └─ JPG/PNG → Convert using PIL
    │             └─ Image.save(pdf_path, 'PDF')
    │
    ├─ 7. Extract Page Count
    │     └─ PdfReader (pypdf/PyPDF2)
    │         └─ len(reader.pages)
    │
    ├─ 8. Calculate Price
    │     └─ pages × copies × rate
    │         └─ Based on: color, sides, size
    │
    ├─ 9. Classify Queue (scheduler.py)
    │     └─ classify_queue()
    │         ├─ Urgent: pickupTime < 60 min
    │         ├─ Normal: pages ≤ 15
    │         └─ Bulk: pages > 15
    │
    ├─ 10. Calculate Priority Score
    │      └─ 5×urgency + 3×(1/pages) + 2×aging + 8×manual
    │
    ├─ 11. Create Order Object
    │      {
    │        id, studentName, mobile, fileName, filePath,
    │        pages, copies, color, sides, size,
    │        status: "Pending",
    │        queueType, priorityIndex, priorityScore,
    │        priceTotal, progressPct: 0
    │      }
    │
    └─ 12. Save to Database
          └─ TinyDB: data/orders.json
```

### Phase 2: Admin Processing (Admin App → Backend → Printer)

```
Admin (Desktop App)
    │
    ├─ 1. Login with Password
    │     └─ SHA-256 hash verification
    │
    ├─ 2. View Orders Table
    │     └─ GET /orders?status=Pending|Queued|Printing|Ready
    │         └─ Auto-refresh every 5 seconds
    │
    ├─ 3. Select Order
    │     └─ Enable buttons based on status:
    │         • Pending/Queued → PRINT button
    │         • Printing → READY button
    │         • Ready → COLLECTED button
    │
    ├─ 4. Click PRINT Button
    │     │
    │     ├─ 4a. Fetch Printers
    │     │     └─ GET /printers
    │     │         └─ If empty: GET /printers/discover/system
    │     │
    │     ├─ 4b. Show Printer Selection Dialog
    │     │     └─ QInputDialog with printer names
    │     │
    │     ├─ 4c. Copy PDF to Temp
    │     │     └─ C:/PrintHub/TempPrint/{orderId}.pdf
    │     │
    │     └─ 4d. Send to Printer
    │           └─ system_print(pdf_path, printer_name)
    │
    ▼
Windows Print System
    │
    ├─ 5. PowerShell Command
    │     └─ Start-Process -FilePath '{pdf_path}' 
    │         -Verb PrintTo 
    │         -ArgumentList '{printer_name}' 
    │         -WindowStyle Hidden
    │
    ├─ 6. Windows Opens PDF
    │     └─ Default PDF viewer (Adobe, Edge, etc.)
    │
    ├─ 7. PDF Viewer Sends to Printer
    │     └─ Uses Windows Print Spooler
    │
    └─ 8. Print Spooler → Physical Printer
          └─ Renders PDF pages and sends to printer driver
```

### Phase 3: Status Updates

```
Admin App
    │
    ├─ During Print: PATCH /orders/{id}
    │     └─ { status: "Printing", progressPct: 50 }
    │
    ├─ After Print: Click READY
    │     └─ PATCH /orders/{id}
    │         └─ { status: "Ready", progressPct: 100 }
    │
    └─ After Pickup: Click COLLECTED
          └─ PATCH /orders/{id}
              └─ { status: "Collected" }
```

---

## 📁 File Upload & Processing

### Supported File Types

| Type | Extension | MIME Type | Conversion Method |
|------|-----------|-----------|-------------------|
| PDF | `.pdf` | `application/pdf` | None (direct copy) |
| Word | `.docx` | `application/vnd...document` | MS Word COM / docx2pdf |
| Image | `.jpg`, `.jpeg` | `image/jpeg` | PIL → PDF |
| Image | `.png` | `image/png` | PIL → PDF |

### File Processing Pipeline

```python
# 1. VALIDATION
def validate_file(file_path, original_filename):
    • Check file exists
    • Check size < 50MB
    • Check extension in ALLOWED_EXTENSIONS
    • Check MIME type in ALLOWED_MIME_TYPES
    • Return (ext, mime_type)

# 2. CONVERSION
def process_uploaded_file(file_path, filename, order_id):
    
    # Create directory
    order_dir = C:/PrintHub/Orders/{order_id}/
    
    # Convert based on type
    if ext == '.pdf':
        → shutil.move(file_path, final_pdf_path)
    
    elif ext in ['.jpg', '.jpeg', '.png']:
        → convert_image_to_pdf()
            • Open with PIL
            • Convert RGBA → RGB (white background)
            • Save as PDF with 100 DPI
    
    elif ext == '.docx':
        → convert_docx_to_pdf()
            • Try docx2pdf library
            • Fallback: win32com.client (MS Word COM)
            • Word.Application → Open → SaveAs(PDF)
    
    # Extract page count
    page_count = get_pdf_page_count(final_pdf_path)
    
    return (final_pdf_path, page_count)

# 3. PAGE COUNT EXTRACTION
def get_pdf_page_count(pdf_path):
    reader = PdfReader(pdf_path)  # pypdf or PyPDF2
    return len(reader.pages)
```

### Storage Structure

```
C:/PrintHub/
├── Orders/
│   ├── {order-id-1}/
│   │   └── document.pdf
│   ├── {order-id-2}/
│   │   └── report.pdf
│   └── {order-id-3}/
│       └── assignment.pdf
└── TempPrint/
    └── {order-id}.pdf  (temporary during printing)
```

---

## 🖨️ PDF Rendering & Printing

### Method: Windows PrintTo Verb

The system uses **Windows Shell PrintTo verb** for printing, which provides:
- ✅ Proper PDF rendering
- ✅ Native Windows print dialog handling
- ✅ Printer driver compatibility
- ✅ No manual PDF parsing required

### Technical Implementation

```python
def system_print(pdf_path, printer_name):
    """
    Print PDF using Windows PrintTo verb
    """
    subprocess.run([
        "powershell",
        "-Command",
        f"Start-Process -FilePath '{pdf_path}' "
        f"-Verb PrintTo "
        f"-ArgumentList '{printer_name}' "
        f"-WindowStyle Hidden"
    ])
```

### How PrintTo Works

```
1. PowerShell executes Start-Process
   ↓
2. Windows Shell receives PrintTo verb
   ↓
3. Shell finds default PDF handler (Adobe Reader, Edge PDF, etc.)
   ↓
4. PDF handler opens file in background
   ↓
5. Handler renders PDF pages to print format
   ↓
6. Sends rendered output to Windows Print Spooler
   ↓
7. Print Spooler queues job for specified printer
   ↓
8. Printer driver receives job
   ↓
9. Physical printer prints pages
```

### Why This Approach?

**Advantages:**
- ✅ Uses system's native PDF rendering engine
- ✅ Handles complex PDFs (fonts, images, vectors)
- ✅ Respects printer settings (duplex, color, etc.)
- ✅ No need to parse PDF internals
- ✅ Compatible with all Windows printers

**Alternatives (Not Used):**
- ❌ Direct printer driver communication (complex)
- ❌ Manual PDF parsing & rendering (error-prone)
- ❌ Third-party print libraries (dependencies)

---

## 📊 Queue Management

### Queue Classification Logic

```python
def classify_queue(order, thresholds):
    now = current_timestamp()
    
    # 1. Check if URGENT
    if order.pickupTime:
        if order.pickupTime - now <= 3600:  # 60 minutes
            return "urgent"
    
    # 2. Check if NORMAL (small job)
    if order.pages <= thresholds.smallPages:  # default: 15
        return "normal"
    
    # 3. Otherwise BULK
    return "bulk"
```

### Priority Score Calculation

```python
def priority_score(order, now, thresholds):
    score = 0.0
    
    # Urgency (5 points)
    if order.queueType == "urgent":
        score += 5.0
    
    # Job size (3 points max, inverse of pages)
    score += 3.0 * (1.0 / max(order.pages, 1))
    
    # Aging (2 points max)
    age_minutes = (now - order.createdAt) / 60
    aging_threshold = thresholds.agingMinutes  # default: 12
    if age_minutes > aging_threshold:
        score += 2.0
    
    # Manual boost (8 points if manually prioritized)
    if order.manualBoost:
        score += 8.0
    
    return score
```

### Queue Ordering

| Queue | Strategy | Sort By |
|-------|----------|---------|
| **Urgent** | FCFS | `priorityIndex` (timestamp) |
| **Normal** | SJF | `pages` ASC, then `priorityIndex` |
| **Bulk** | FCFS | `priorityIndex` (timestamp) |

---

## 📈 Data Flow Diagrams

### Order Creation Flow

```
┌─────────┐
│ Student │
└────┬────┘
     │ 1. Upload file + form data
     ▼
┌─────────────────┐
│   Web Frontend  │
│   (Next.js)     │
└────┬────────────┘
     │ 2. POST /orders/upload
     ▼
┌─────────────────┐
│   Backend API   │
│   (FastAPI)     │
└────┬────────────┘
     │ 3. Save temp file
     ▼
┌─────────────────┐
│  File Handler   │
│  (Python)       │
├─────────────────┤
│ • Validate      │
│ • Convert→PDF   │
│ • Count pages   │
└────┬────────────┘
     │ 4. Return (pdf_path, page_count)
     ▼
┌─────────────────┐
│   Scheduler     │
│  (Python)       │
├─────────────────┤
│ • Classify      │
│ • Calculate     │
│   priority      │
└────┬────────────┘
     │ 5. Create order object
     ▼
┌─────────────────┐
│   TinyDB        │
│  (orders.json)  │
└─────────────────┘
```

### Printing Flow

```
┌─────────┐
│  Admin  │
└────┬────┘
     │ 1. Select order & click PRINT
     ▼
┌─────────────────┐
│   Admin App     │
│   (PyQt6)       │
└────┬────────────┘
     │ 2. GET /printers
     ▼
┌─────────────────┐
│   Backend API   │
└────┬────────────┘
     │ 3. Return printer list
     ▼
┌─────────────────┐
│   Admin App     │
├─────────────────┤
│ • Show dialog   │
│ • Select printer│
└────┬────────────┘
     │ 4. Copy PDF to temp
     ▼
┌─────────────────┐
│  C:/PrintHub/   │
│  TempPrint/     │
└────┬────────────┘
     │ 5. Execute PowerShell
     ▼
┌─────────────────┐
│  Windows Shell  │
│  (PrintTo verb) │
└────┬────────────┘
     │ 6. Open with PDF viewer
     ▼
┌─────────────────┐
│  PDF Renderer   │
│  (Adobe/Edge)   │
└────┬────────────┘
     │ 7. Render pages
     ▼
┌─────────────────┐
│ Print Spooler   │
└────┬────────────┘
     │ 8. Send to driver
     ▼
┌─────────────────┐
│ Physical Printer│
└─────────────────┘
```

---

## 🔐 Security Considerations

### File Upload Security
- ✅ File size limit: 50MB
- ✅ Extension whitelist: `.pdf`, `.docx`, `.jpg`, `.png`
- ✅ MIME type validation
- ✅ Files stored in isolated directories per order
- ✅ Temp files cleaned up after processing

### Admin Access
- ✅ Password-protected (SHA-256 hash)
- ✅ No student authentication (by design)
- ✅ Local-only system (no external access)

---

## 📊 Performance Characteristics

### File Processing Times (Approximate)

| Operation | Time |
|-----------|------|
| PDF validation | < 100ms |
| PDF page count | 100-500ms |
| Image → PDF | 200-800ms |
| DOCX → PDF | 2-10 seconds (MS Word) |
| Print command | < 500ms |
| Actual printing | Depends on printer speed |

### Database Operations
- **TinyDB (JSON)**: In-memory with file persistence
- **Read**: < 10ms
- **Write**: < 50ms
- **Suitable for**: < 10,000 orders

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - REST API framework
- **TinyDB** - JSON-based database
- **pypdf/PyPDF2** - PDF page counting
- **PIL (Pillow)** - Image processing
- **docx2pdf / win32com** - DOCX conversion

### Frontend (Web)
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling

### Admin App
- **PyQt6** - Desktop GUI framework
- **requests** - HTTP client

### Printing
- **Windows Shell** - PrintTo verb
- **PowerShell** - Command execution
- **Windows Print Spooler** - Print queue management

---

## 📝 Key Files

| File | Purpose |
|------|---------|
| `backend/app/routers/orders.py` | Order creation & management API |
| `backend/app/file_handler.py` | File upload, validation, conversion |
| `backend/app/scheduler.py` | Queue classification & priority |
| `admin-app/main.py` | Desktop admin interface |
| `web/app/order/new/page.tsx` | Student order form |
| `data/orders.json` | Order database |
| `data/printers.json` | Printer configurations |

---

## 🎯 Summary

**PrintHub** is a local-first print management system that:

1. **Accepts** multiple file formats (PDF, DOCX, images)
2. **Converts** everything to PDF for consistent handling
3. **Classifies** orders into queues (Urgent/Normal/Bulk)
4. **Prints** using Windows native printing system
5. **Tracks** order status through the entire lifecycle

The system leverages **Windows Shell PrintTo verb** for reliable PDF rendering and printing, avoiding the complexity of direct printer driver communication or manual PDF parsing.
