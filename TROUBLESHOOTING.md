# Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "Failed to fetch" Error in Web App

**Symptom:**
```
TypeError: Failed to fetch
at fetchAPI (lib\api.ts:62:26)
```

**Cause:** CORS (Cross-Origin Resource Sharing) misconfiguration. The backend only allows specific ports, but the web app is running on a different port.

**Solution:**

1. Check which port the web app is using:
   - Look for: `Local: http://localhost:XXXX` in the terminal

2. Update backend CORS settings in `backend/app/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:3000",
           "http://localhost:3001",  # Add any additional ports
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. Restart the backend:
   ```bash
   # Stop with Ctrl+C, then restart
   cd backend
   .venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
   ```

**Quick Fix:** Allow all localhost origins (development only):
```python
allow_origins=["http://localhost:*"],  # Not recommended for production
```

### Issue 2: Port Already in Use

**Symptom:**
```
⚠ Port 3000 is in use by process 3280, using available port 3001 instead.
```

**Cause:** Another application is using the port.

**Solution:**

**Option 1: Kill the process (Windows)**
```powershell
# Find process using port 3000
netstat -ano | findstr :3000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Option 2: Use a different port**
```bash
# Web app will automatically use next available port
npm run dev
```

**Option 3: Specify a custom port**
```bash
# In package.json, change:
"dev": "next dev -p 3002"
```

### Issue 3: Backend Not Starting

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Cause:** Dependencies not installed or wrong Python environment.

**Solution:**

1. Activate virtual environment:
   ```bash
   cd backend
   .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify installation:
   ```bash
   pip list | findstr fastapi
   ```

### Issue 4: Admin App - "No module named 'PyQt6'"

**Symptom:**
```
ModuleNotFoundError: No module named 'PyQt6'
```

**Solution:**

```bash
cd admin-app
python -m pip install PyQt6 requests
```

**Verify:**
```bash
python -c "import PyQt6; print('PyQt6 installed')"
```

### Issue 5: Slow Performance

**Symptoms:**
- Pages take long to load
- UI feels laggy
- High CPU usage

**Solutions:**

**Quick Fix 1: Reduce Polling Frequency**

Web app (`web/app/orders/[id]/page.tsx`):
```typescript
// Change from 3000 to 10000 (10 seconds)
const interval = setInterval(loadOrder, 10000);
```

Admin app (`admin-app/main.py`):
```python
# Change from 2000 to 5000 (5 seconds)
self.poll_timer.start(5000)
```

**Quick Fix 2: Use Production Build**
```bash
cd web
npm run build
npm start  # Much faster than dev mode
```

**Quick Fix 3: Enable Compression**
```python
# backend/app/main.py
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

See [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) for more details.

### Issue 6: Database Errors

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/orders.json'
```

**Solution:**

1. Ensure data directory exists:
   ```bash
   mkdir data
   ```

2. Seed the database:
   ```bash
   curl -X POST http://localhost:8000/seed
   # Or in PowerShell:
   Invoke-WebRequest -Method POST -Uri http://localhost:8000/seed
   ```

### Issue 7: Admin App Won't Connect

**Symptom:**
- Login dialog appears but can't connect
- "Connection failed" error

**Solutions:**

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000
   # Should return: {"message":"PrintHub API","version":"1.0.0"}
   ```

2. **Check firewall:**
   - Windows Firewall might be blocking localhost connections
   - Add exception for Python and uvicorn

3. **Verify API_BASE in admin app:**
   ```python
   # admin-app/main.py
   API_BASE = "http://localhost:8000"  # Should match backend port
   ```

### Issue 8: Orders Not Appearing

**Symptom:**
- Created order but not showing in list
- Empty queue in admin app

**Solutions:**

1. **Check order status:**
   ```bash
   curl http://localhost:8000/orders
   ```

2. **Check filters:**
   - Web app filters by mobile number
   - Admin app filters by status (Pending/Queued/Printing)

3. **Clear localStorage:**
   ```javascript
   // In browser console
   localStorage.clear();
   location.reload();
   ```

### Issue 9: Price Not Calculating

**Symptom:**
- Price shows ₹0.00
- "Rates not configured" error

**Solution:**

1. **Seed rates:**
   ```bash
   curl -X POST http://localhost:8000/seed
   ```

2. **Manually set rates:**
   ```bash
   curl -X PUT http://localhost:8000/rates \
     -H "Content-Type: application/json" \
     -d '{
       "bwSingleA4": 1.0,
       "bwDuplexA4": 0.75,
       "colorSingleA4": 5.0,
       "colorDuplexA4": 4.0,
       "minCharge": 5.0,
       "effectiveDate": 1730000000
     }'
   ```

### Issue 10: Real Printer Integration

**Symptom:**
- Want to connect to actual printers
- Simulated printing not sufficient

**Solution:**

See [PRINTER_INTEGRATION.md](PRINTER_INTEGRATION.md) for complete guide.

**Quick summary:**
1. Install `pywin32` (Windows) or `pycups` (Linux/Mac)
2. Implement printer discovery
3. Add file upload capability
4. Send jobs to real print spooler

## Testing Connection

Use the included test file:

```bash
# Open in browser
start test-connection.html
```

This will test all API endpoints and show connection status.

## Diagnostic Commands

### Check Services Status

```bash
# Backend
curl http://localhost:8000

# Web app
curl http://localhost:3000  # or 3001

# Check ports in use
netstat -ano | findstr "8000 3000 3001"
```

### Check Logs

**Backend:**
- Look at terminal where uvicorn is running
- Check for error messages

**Web:**
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for failed requests

**Admin:**
- Check terminal output
- Look for Python tracebacks

### Health Check Endpoint

Add to `backend/app/main.py`:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "database": "connected" if os.path.exists("data/orders.json") else "not_found"
    }
```

Test:
```bash
curl http://localhost:8000/health
```

## Getting Help

1. **Check logs** - Most errors show in terminal output
2. **Test API directly** - Use curl or Postman to isolate issues
3. **Check browser console** - F12 → Console tab
4. **Verify services running** - All three components must be active
5. **Review documentation** - Check README.md and SETUP.md

## Quick Restart

If all else fails, restart everything:

```bash
# Stop all services (Ctrl+C in each terminal)

# Terminal 1 - Backend
cd backend
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# Terminal 2 - Web
cd web
npm run dev

# Terminal 3 - Admin
cd admin-app
python main.py
```

Or use the quick start script:
```bash
.\start-all.ps1
```

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Failed to fetch` | CORS issue | Update CORS origins in backend |
| `Port in use` | Port conflict | Kill process or use different port |
| `Module not found` | Missing dependency | Install with pip/npm |
| `Connection refused` | Backend not running | Start backend server |
| `404 Not Found` | Wrong endpoint | Check API documentation |
| `500 Internal Error` | Backend error | Check backend logs |
| `CORS error` | Origin not allowed | Add origin to CORS config |

## Prevention Tips

1. **Always start backend first** - Web and admin depend on it
2. **Use virtual environments** - Avoid dependency conflicts
3. **Check ports before starting** - Prevent port conflicts
4. **Keep dependencies updated** - But test after updates
5. **Monitor resource usage** - High CPU/memory indicates issues
6. **Regular backups** - Copy `/data` folder periodically

## Still Having Issues?

1. Check all three services are running
2. Verify ports: Backend (8000), Web (3000/3001)
3. Test API with curl/PowerShell
4. Check browser console for errors
5. Review this troubleshooting guide
6. Check SETUP.md for detailed instructions
