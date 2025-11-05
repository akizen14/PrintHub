# PrintHub Setup Guide

## Prerequisites

- **Python 3.8+** (for backend and admin app)
- **Node.js 18+** (for web frontend)
- **Windows** (tested on Windows, but should work on other platforms)

## Installation Steps

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Web Frontend Setup

```bash
cd web
npm install
```

### 3. Admin App Setup

```bash
cd admin-app
pip install -r requirements.txt
```

## Running the Application

### Start Backend (Terminal 1)

```bash
cd backend
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

**API Documentation:** Visit `http://localhost:8000/docs` for interactive API docs

### Seed Demo Data

In a new terminal or browser:

```bash
# Using PowerShell
Invoke-WebRequest -Method POST -Uri http://localhost:8000/seed

# Or visit in browser
http://localhost:8000/seed
```

This creates:
- 2 printers (Laser-A4, ColorPro)
- 4 sample orders (urgent, normal, bulk)
- Default rates
- Admin credentials (password: `printhub2025`)

### Start Web Frontend (Terminal 2)

```bash
cd web
npm run dev
```

The student website will be available at `http://localhost:3000`

### Start Admin App (Terminal 3)

```bash
cd admin-app
python main.py
```

**Login credentials:** `printhub2025`

## Testing the System

### End-to-End Test Flow

1. **Backend:** Ensure backend is running and seeded
   - Visit `http://localhost:8000/orders` to see orders
   - Visit `http://localhost:8000/printers` to see printers

2. **Web (Student Interface):**
   - Visit `http://localhost:3000`
   - Click "New Order"
   - Fill in the form (try different page counts to see queue classification)
   - Submit order
   - View order in "My Orders"
   - Click on order to see details

3. **Admin App:**
   - Launch admin app
   - Login with `printhub2025`
   - See orders in three queues (Urgent/Normal/Bulk)
   - Select an order
   - Assign a printer
   - Start printing
   - Watch progress bar increase
   - Job auto-completes at 100% or manually complete

4. **Real-time Updates:**
   - Keep web order detail page open
   - Start printing from admin app
   - Watch status update in web interface in real-time

## Queue Logic

### Queue Classification

- **Urgent:** Orders with pickup time within 60 minutes
- **Normal:** Small jobs (≤15 pages by default)
- **Bulk:** Large jobs (>15 pages)

### Queue Ordering

- **Urgent:** FCFS (First Come First Served) by `priorityIndex`
- **Normal:** SJF (Shortest Job First) - sorted by pages, then `priorityIndex`
- **Bulk:** FCFS by `priorityIndex`

### Priority Adjustment

Use the ↑/↓ buttons in admin app to manually adjust order priority within its queue.

## Pricing

Default rates (can be changed via API):
- B&W Single-sided A4: ₹1.00/page
- B&W Double-sided A4: ₹0.75/page
- Color Single-sided A4: ₹5.00/page
- Color Double-sided A4: ₹4.00/page
- A3 pages: 2× A4 price
- Minimum charge: ₹5.00

## Data Persistence

All data is stored in JSON files in the `/data` directory:
- `orders.json` - Print orders
- `printers.json` - Printer configurations
- `rates.json` - Pricing information
- `settings.json` - System settings and admin password

**Backup:** Simply copy the `/data` folder to backup all data.

**Reset:** Delete JSON files in `/data` and re-run `/seed` endpoint.

## Troubleshooting

### Backend won't start
- Ensure Python virtual environment is activated
- Check port 8000 is not in use
- Verify all dependencies installed: `pip list`

### Web frontend errors
- Clear Next.js cache: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check backend is running at `http://localhost:8000`

### Admin app won't connect
- Verify backend is running
- Check firewall settings
- Ensure `http://localhost:8000` is accessible

### Orders not updating in real-time
- Web polls every 3-5 seconds
- Admin app polls every 2 seconds
- Check browser console for errors
- Verify backend API is responding

## Configuration

### Change Admin Password

1. Generate SHA-256 hash of new password:
   ```python
   import hashlib
   password = "your_new_password"
   hash = hashlib.sha256(password.encode()).hexdigest()
   print(hash)
   ```

2. Update via API:
   ```bash
   curl -X PUT http://localhost:8000/settings \
     -H "Content-Type: application/json" \
     -d '{"adminPassHash": "YOUR_HASH", "thresholds": {"smallPages": 15, "chunkPages": 100, "agingMinutes": 12}}'
   ```

### Change Queue Thresholds

Update via API:
```bash
curl -X PUT http://localhost:8000/settings \
  -H "Content-Type: application/json" \
  -d '{"adminPassHash": "CURRENT_HASH", "thresholds": {"smallPages": 20, "chunkPages": 100, "agingMinutes": 15}}'
```

### Update Rates

```bash
curl -X PUT http://localhost:8000/rates \
  -H "Content-Type: application/json" \
  -d '{"bwSingleA4": 1.5, "bwDuplexA4": 1.0, "colorSingleA4": 6.0, "colorDuplexA4": 5.0, "minCharge": 10.0, "effectiveDate": 1234567890}'
```

## Architecture

```
PrintHub/
├── backend/          # FastAPI + TinyDB
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── models.py         # Pydantic models
│   │   ├── storage.py        # TinyDB wrapper
│   │   ├── scheduler.py      # Queue logic
│   │   └── routers/          # API endpoints
│   └── requirements.txt
├── web/              # Next.js + Tailwind
│   ├── app/                  # Pages
│   ├── lib/                  # API client & utils
│   └── package.json
├── admin-app/        # PyQt6 desktop app
│   ├── main.py               # Admin interface
│   └── requirements.txt
└── data/             # JSON database files
    ├── orders.json
    ├── printers.json
    ├── rates.json
    └── settings.json
```

## API Endpoints

- `GET /` - API info
- `POST /seed` - Seed demo data
- `GET /orders` - List orders (filters: status, queueType)
- `POST /orders` - Create order
- `GET /orders/{id}` - Get order
- `PATCH /orders/{id}` - Update order
- `GET /printers` - List printers
- `POST /printers` - Add printer
- `PATCH /printers/{id}` - Update printer
- `GET /rates` - Get rates
- `PUT /rates` - Update rates
- `GET /settings` - Get settings
- `PUT /settings` - Update settings

## Features Implemented

✅ Student web interface for ordering
✅ Real-time order tracking with polling
✅ Live price preview
✅ Admin desktop app with PyQt6
✅ Three-queue system (Urgent/Normal/Bulk)
✅ Printer assignment and management
✅ Simulated printing with progress bars
✅ Manual priority adjustment
✅ Auto-completion of print jobs
✅ TinyDB JSON storage (no database server)
✅ Responsive Tailwind UI
✅ Status badges and visual feedback

## Next Steps (Optional Enhancements)

- Add file upload capability
- Implement actual printer integration
- Add payment processing
- Create user authentication
- Add email/SMS notifications
- Generate print job reports
- Add printer maintenance tracking
- Implement print history analytics
