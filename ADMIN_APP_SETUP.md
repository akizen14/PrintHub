# Admin App Configuration Guide

The PrintHub Admin Desktop App is a Windows application (PyQt6) that connects to the backend API to manage print orders and printers.

## Quick Setup

### Local Development (Default)

```bash
cd admin-app
pip install -r requirements.txt
python main.py
```

By default, connects to `http://localhost:8000`

### Connect to Hosted Backend

Choose one of the following methods:

#### Method 1: Environment Variable (Recommended for Testing)

**PowerShell:**
```powershell
$env:PRINTHUB_API_URL="https://printhub-backend.onrender.com"
python main.py
```

**Command Prompt:**
```cmd
set PRINTHUB_API_URL=https://printhub-backend.onrender.com
python main.py
```

#### Method 2: Config File (Recommended for Permanent Setup)

1. Copy the example config:
   ```bash
   copy config.json.example config.json
   ```

2. Edit `config.json`:
   ```json
   {
     "api_url": "https://printhub-backend.onrender.com"
   }
   ```

3. Launch the app:
   ```bash
   python main.py
   ```

#### Method 3: Batch File Launcher (Easiest for End Users)

Create `launch-admin-prod.bat`:

```batch
@echo off
title PrintHub Admin - Production
echo ===================================
echo   PrintHub Admin (Production)
echo ===================================
echo.
echo Connecting to: https://printhub-backend.onrender.com
echo.
set PRINTHUB_API_URL=https://printhub-backend.onrender.com
python main.py
if errorlevel 1 (
    echo.
    echo Error launching admin app!
    echo Make sure Python is installed and in PATH.
    pause
)
```

Double-click `launch-admin-prod.bat` to start!

## Configuration Priority

The app checks for API URL in this order:

1. **Environment Variable** `PRINTHUB_API_URL` (highest priority)
2. **Config File** `config.json`
3. **Default** `http://localhost:8000` (fallback)

## Verifying Connection

When the app starts, look for this message:
```
🔗 Connecting to API: https://printhub-backend.onrender.com
```

If you see your hosted URL, the configuration is correct!

## System Requirements

- **OS:** Windows 10/11 (64-bit)
- **Python:** 3.8 or higher
- **Dependencies:** PyQt6, requests (see requirements.txt)
- **Network:** Internet connection for hosted backend

## Features

- ✅ View orders by queue (Urgent/Normal/Bulk)
- ✅ Assign printers to orders
- ✅ Start/stop printing
- ✅ Monitor print progress
- ✅ Mark orders as ready/collected
- ✅ Manage printer status
- ✅ Real-time updates (polls every 2 seconds)

## Admin Login

**Default Password:** `printhub2025`

⚠️ **Security:** Change this password in production!

To change password:
1. Generate hash:
   ```python
   import hashlib
   hashlib.sha256("new_password".encode()).hexdigest()
   ```

2. Update via API or directly in backend settings

## Printing

The admin app prints to **local Windows printers** installed on your machine.

**Print Flow:**
1. Order is submitted via web interface
2. Student completes payment
3. Order appears in admin app queue
4. Admin selects order and assigns printer
5. File is downloaded from backend API
6. File is sent to local Windows printer
7. Progress is tracked and updated

**Requirements:**
- Printers must be installed on the Windows machine
- Admin app downloads files to `C:\PrintHub\TempPrint`
- Requires Windows print drivers

## Troubleshooting

### "Cannot connect to API"

**Check:**
1. Backend is running and accessible
2. URL is correct (with https:// prefix)
3. No firewall blocking outbound connections
4. Test URL in browser: `https://your-backend.onrender.com/health`

**Test Connection:**
```powershell
curl https://your-backend.onrender.com/health
```

Should return: `{"status":"healthy","version":"1.0.0",...}`

### "Authentication failed"

**Check:**
1. Using correct password
2. Password wasn't changed on backend
3. Backend `/settings` endpoint is accessible

### "No printers found"

**Check:**
1. Printers are installed in Windows
2. Printers are set as "Ready" in Windows
3. Run `Get-Printer` in PowerShell to list printers

### "File download failed"

**Check:**
1. Backend is serving uploaded files
2. File paths are correct in order data
3. Network connection is stable
4. Check backend logs for errors

### App is slow or unresponsive

**Try:**
1. Check network latency to backend
2. Reduce polling interval (edit main.py)
3. Backend might be sleeping (Render free tier)
4. Check backend response times in logs

## Development Tips

### Testing with Local Backend

Leave default config to test locally:
```bash
# No config needed - uses localhost:8000 by default
python main.py
```

### Testing with Production Backend

Create `config.json` for production:
```json
{
  "api_url": "https://printhub-backend.onrender.com"
}
```

### Switching Between Environments

**Option 1:** Use different config files
```bash
# Test with local
copy config-local.json config.json
python main.py

# Test with production  
copy config-prod.json config.json
python main.py
```

**Option 2:** Use environment variable
```powershell
# Local
$env:PRINTHUB_API_URL="http://localhost:8000"
python main.py

# Production
$env:PRINTHUB_API_URL="https://printhub-backend.onrender.com"
python main.py
```

## Packaging as Executable (Optional)

To distribute as .exe without requiring Python:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name="PrintHub Admin" main.py
```

Creates `dist/PrintHub Admin.exe` that can run standalone.

**Note:** Include config.json in the same directory as the .exe

## Security Notes

- 🔒 Admin password is hashed (SHA-256) on backend
- 🔒 Use HTTPS for production backends
- 🔒 Change default admin password
- 🔒 Consider VPN for remote printer access
- 🔒 Protect config.json file permissions

## FAQ

**Q: Can I run the admin app on Mac/Linux?**
A: The app uses Windows-specific printer APIs. It won't work on Mac/Linux without modifications.

**Q: Can multiple admins connect to the same backend?**
A: Yes! Multiple admin apps can connect to the same hosted backend simultaneously.

**Q: Do I need the admin app to use PrintHub?**
A: No, for basic order submission and tracking, only the web interface is needed. The admin app is for managing print jobs and printers.

**Q: Can I print without the admin app?**
A: The admin app is needed for actual printing. You could build alternative integrations using the API directly.

**Q: Does the admin app work with Render's free tier?**
A: Yes, but expect 30-60 second delays on first request after backend sleeps.

## Support

- 📖 [Deployment Guide](DEPLOYMENT.md)
- 📖 [README](README.md)
- 🐛 [Report Issues](https://github.com/akizen14/PrintHub/issues)

---

**Status:** ✅ Ready for Production Use

**Last Updated:** November 2024
