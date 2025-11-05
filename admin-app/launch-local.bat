@echo off
title PrintHub Admin - Local Development
color 0B

echo.
echo ======================================
echo   PrintHub Admin - Local Dev
echo ======================================
echo.

REM Use localhost backend
set PRINTHUB_API_URL=http://localhost:8000

echo Connecting to: %PRINTHUB_API_URL%
echo.
echo Launching admin application...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    echo.
    pause
    exit /b 1
)

REM Launch the admin app
python main.py

REM Handle exit
if errorlevel 1 (
    echo.
    echo [ERROR] Admin app exited with an error
    echo Check the error messages above
    echo.
) else (
    echo.
    echo Admin app closed successfully
)

pause
