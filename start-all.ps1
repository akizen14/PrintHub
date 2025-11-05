# PrintHub Quick Start Script
# This script starts all three components in separate windows

Write-Host "Starting PrintHub..." -ForegroundColor Green

# Start Backend
Write-Host "`nStarting Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; Write-Host 'Starting Backend API...' -ForegroundColor Green; .\\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000"

# Wait for backend to start
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Seed data
Write-Host "`nSeeding demo data..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Method POST -Uri "http://localhost:8000/seed" -ErrorAction Stop
    Write-Host "✓ Demo data seeded successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not seed data. Backend may still be starting..." -ForegroundColor Yellow
}

# Start Web Frontend
Write-Host "`nStarting Web Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\web'; Write-Host 'Starting Web Frontend...' -ForegroundColor Green; npm run dev"

Write-Host "`n✓ All services started!" -ForegroundColor Green
Write-Host "`nAccess points:" -ForegroundColor White
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor Gray
Write-Host "  API Docs:    http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  Web App:     http://localhost:3000" -ForegroundColor Gray
Write-Host "`nTo start Admin App:" -ForegroundColor White
Write-Host "  cd admin-app" -ForegroundColor Gray
Write-Host "  python main.py" -ForegroundColor Gray
Write-Host "`nAdmin Password: printhub2025" -ForegroundColor Yellow
Write-Host "`nPress any key to exit..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
