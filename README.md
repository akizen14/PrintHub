# PrintHub 🖨️

A lightweight, local-first print management system with student ordering, admin queue management, and printer tracking.

![Status](https://img.shields.io/badge/status-ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Node](https://img.shields.io/badge/node-18+-green)

## 🎯 Features

- ✅ **Student Web Interface** - Easy print ordering with live price preview
- ✅ **UPI Payment Integration** - QR code-based payment with order tracking
- ✅ **Real-time Tracking** - Monitor order status and printing progress
- ✅ **Smart Queue System** - Urgent/Normal/Bulk queues with intelligent ordering
- ✅ **Payment-based Queue** - Only paid orders enter the print queue
- ✅ **Admin Desktop App** - Full control over printers and print jobs
- ✅ **Progress Simulation** - Visual progress bars for active print jobs
- ✅ **No Database Server** - Everything stored in JSON files (TinyDB)
- ✅ **Modern UI** - Clean, minimal design with Tailwind CSS

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Student Web   │      │  Admin Desktop  │      │   FastAPI       │
│   (Next.js)     │─────▶│   (PyQt6)       │─────▶│   Backend       │
│   Port 3000     │      │   Native App    │      │   Port 8000     │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                            │
                                                            ▼
                                                   ┌─────────────────┐
                                                   │  TinyDB (JSON)  │
                                                   │  /data/*.json   │
                                                   └─────────────────┘
```

### Components

- **backend/** → FastAPI + TinyDB (JSON storage)
- **web/** → Next.js 15 + TypeScript + Tailwind CSS
- **admin-app/** → Python + PyQt6 (desktop GUI)
- **data/** → JSON database files (orders, printers, rates, settings)

## 🚀 Quick Start

### Option 1: Quick Start Script (Windows)

```powershell
# Run the automated setup script
.\start-all.ps1
```

This will:
1. Start the backend API on port 8000
2. Seed demo data (2 printers, 4 orders)
3. Start the web frontend on port 3000
4. Display access URLs and credentials

### Option 2: Manual Setup

#### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

**Seed demo data:**
```powershell
Invoke-WebRequest -Method POST -Uri http://localhost:8000/seed
```

#### 2. Web Frontend (Next.js)

```bash
cd web
npm install
npm run dev
```

Access at: `http://localhost:3000`

#### 3. Admin Desktop App (PyQt6)

```bash
cd admin-app
pip install -r requirements.txt
python main.py
```

**Login:** `printhub2025`

## 📖 Usage Guide

### For Students (Web Interface)

1. Visit `http://localhost:3000`
2. Click **"New Order"**
3. Fill in your details:
   - Student name and mobile number
   - Upload file (PDF, DOCX, JPG, PNG)
   - Select copies, color/B&W, single/duplex, paper size
   - Optional: Pickup time (creates urgent order if within 60 min)
4. See **live price preview** as you change options
5. Submit order
6. **Complete UPI payment:**
   - Redirected to UPI payment page
   - Scan QR code or pay via UPI app
   - Click "I have paid" to confirm payment
7. Track your order in **"My Orders"**
8. View real-time progress when printing

### For Admins (Desktop App)

1. Launch admin app: `python main.py`
2. Login with passcode: `printhub2025`
3. View **paid orders** in the queue (Queued/Printing/Ready)
4. Orders appear after payment confirmation
5. Select an order to:
   - Print (only for Queued/paid orders)
   - Monitor progress
   - Mark as Ready or Collected
   - Cancel if needed
6. Manage printers:
   - View status and current jobs
   - Set idle/offline
   - Monitor progress bars

## 🎨 UI Design

### Student Web Interface
- **Clean & Minimal** - White/gray with teal accents
- **Responsive** - Works on mobile and desktop
- **Live Updates** - Polls every 3-5 seconds
- **Status Badges:**
  - Pending (gray)
  - Queued (blue)
  - Printing (amber)
  - Ready (green)
  - Collected (neutral)
  - Cancelled (red)

### Admin Desktop App
- **Native PyQt6** - Fast and responsive
- **Three-column layout** - Urgent/Normal/Bulk queues
- **Action panel** - All controls in one place
- **Real-time updates** - Polls every 2 seconds
- **Progress bars** - Visual feedback for printing jobs

## 🔄 Queue Logic

### Queue Classification

Orders are automatically classified based on:

- **Urgent:** `pickupTime` within 60 minutes of now
- **Normal:** Pages ≤ `smallPages` threshold (default: 15)
- **Bulk:** Pages > `smallPages` threshold

### Queue Ordering

Each queue has its own ordering strategy:

- **Urgent:** FCFS (First Come First Served)
  - Sorted by `priorityIndex` ascending
- **Normal:** SJF (Shortest Job First)
  - Sorted by `pages` ascending, then `priorityIndex`
- **Bulk:** FCFS (First Come First Served)
  - Sorted by `priorityIndex` ascending

### Priority Adjustment

Admins can manually adjust priority:
- **Move Up (↑):** Calculates midpoint with previous order
- **Move Down (↓):** Calculates midpoint with next order
- If collision occurs, queue is reindexed in steps of 1000

## 💰 Pricing

### Default Rates

| Type | Price |
|------|-------|
| B&W Single-sided A4 | ₹1.00/page |
| B&W Double-sided A4 | ₹0.75/page |
| Color Single-sided A4 | ₹5.00/page |
| Color Double-sided A4 | ₹4.00/page |
| A3 pages | 2× A4 price |
| Minimum charge | ₹5.00 |

### Updating Rates

Use the API endpoint:

```bash
curl -X PUT http://localhost:8000/rates \
  -H "Content-Type: application/json" \
  -d '{
    "bwSingleA4": 1.5,
    "bwDuplexA4": 1.0,
    "colorSingleA4": 6.0,
    "colorDuplexA4": 5.0,
    "minCharge": 10.0,
    "effectiveDate": 1730000000
  }'
```

## 🗄️ Data Storage

All data is stored in JSON files in the `/data` directory:

- **orders.json** - All print orders
- **printers.json** - Printer configurations
- **rates.json** - Current pricing
- **settings.json** - System settings and admin password hash

### Backup

Simply copy the `/data` folder:

```bash
cp -r data data_backup_$(date +%Y%m%d)
```

### Reset

Delete JSON files and re-seed:

```bash
rm data/*.json
curl -X POST http://localhost:8000/seed
```

## 🔧 Configuration

### Change Admin Password

1. Generate SHA-256 hash:
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
  -d '{
    "adminPassHash": "YOUR_HASH_HERE",
    "thresholds": {
      "smallPages": 15,
      "chunkPages": 100,
      "agingMinutes": 12
    }
  }'
```

### Adjust Queue Thresholds

- **smallPages:** Max pages for Normal queue (default: 15)
- **chunkPages:** Batch size for large jobs (default: 100)
- **agingMinutes:** Time before aging boost applies (default: 12)

Update via `/settings` endpoint.

## 📡 API Endpoints

### Orders
- `POST /orders` - Create new order
- `GET /orders` - List orders (filters: status, queueType)
- `GET /orders/{id}` - Get specific order
- `PATCH /orders/{id}` - Update order

### Printers
- `POST /printers` - Add printer
- `GET /printers` - List all printers
- `GET /printers/{id}` - Get specific printer
- `PATCH /printers/{id}` - Update printer

### System
- `GET /rates` - Get current rates
- `PUT /rates` - Update rates
- `GET /settings` - Get system settings
- `PUT /settings` - Update settings
- `POST /seed` - Seed demo data

**API Documentation:** Visit `http://localhost:8000/docs` for interactive Swagger UI

## 🧪 Testing

### End-to-End Test

1. **Start all services** (backend, web, admin)
2. **Seed data:** `POST http://localhost:8000/seed`
3. **Web:** Create a new order at `http://localhost:3000`
4. **Admin:** Login and see order in appropriate queue
5. **Admin:** Assign printer and start printing
6. **Web:** Watch order status update in real-time
7. **Admin:** Observe progress bar increase
8. **Both:** See job complete at 100%

### Test Scenarios

**Urgent Order:**
- Create order with pickup time 30 minutes from now
- Should appear in Urgent queue

**Normal Order:**
- Create order with 10 pages
- Should appear in Normal queue
- Should be ordered before 15-page orders (SJF)

**Bulk Order:**
- Create order with 50 pages
- Should appear in Bulk queue
- Ordered by creation time (FCFS)

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Verify Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Web frontend errors
```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run dev
```

### Admin app connection issues
- Ensure backend is running at `http://localhost:8000`
- Check firewall settings
- Verify no proxy interfering with localhost

### Orders not updating
- Check browser console for errors
- Verify polling is active (every 3-5s for web, 2s for admin)
- Ensure backend API is responding: `curl http://localhost:8000/orders`

## 📁 Project Structure

```
PrintHub/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── main.py         # FastAPI app & seed endpoint
│   │   ├── models.py       # Pydantic models
│   │   ├── storage.py      # TinyDB wrapper
│   │   ├── scheduler.py    # Queue logic
│   │   └── routers/        # API endpoints
│   │       ├── orders.py
│   │       ├── printers.py
│   │       ├── rates.py
│   │       └── settings.py
│   └── requirements.txt
├── web/                     # Next.js Frontend
│   ├── app/
│   │   ├── page.tsx        # Landing page
│   │   ├── layout.tsx      # Root layout
│   │   ├── globals.css     # Tailwind styles
│   │   ├── order/
│   │   │   └── new/
│   │   │       └── page.tsx # New order form
│   │   └── orders/
│   │       ├── page.tsx    # Orders list
│   │       └── [id]/
│   │           └── page.tsx # Order detail
│   ├── lib/
│   │   ├── api.ts          # API client
│   │   └── price.ts        # Price calculator
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
├── admin-app/               # PyQt6 Desktop App
│   ├── main.py             # Admin interface
│   └── requirements.txt
├── data/                    # JSON Database
│   ├── orders.json
│   ├── printers.json
│   ├── rates.json
│   └── settings.json
├── README.md               # This file
├── SETUP.md                # Detailed setup guide
└── start-all.ps1           # Quick start script
```

## 🚧 Non-Goals (Out of Scope)

- ❌ Real printer integration (spooler/driver control)
- ❌ Automated payment verification (currently manual confirmation)
- ❌ User authentication (students)
- ❌ Email/SMS notifications

These can be added as future enhancements.

## 🔮 Future Enhancements

- [ ] Real payment gateway integration (Razorpay, PayU)
- [ ] Automated payment verification via webhooks
- [ ] Actual printer driver integration
- [ ] Student authentication
- [ ] Email/SMS notifications
- [ ] Print job reports and analytics
- [ ] Printer maintenance tracking
- [ ] Multi-location support
- [ ] Mobile app (React Native)

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🤝 Contributing

This is a demonstration project. Feel free to fork and customize for your needs.

## 📞 Support

For issues or questions:
1. Check the [SETUP.md](SETUP.md) guide
2. Review [PAYMENT_INTEGRATION.md](PAYMENT_INTEGRATION.md) for payment flow details
3. Review API docs at `http://localhost:8000/docs`
4. Check browser/terminal console for errors

---

**Built with:** FastAPI • Next.js • PyQt6 • TinyDB • Tailwind CSS

**Status:** ✅ Production Ready
