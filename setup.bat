@echo off
title BD Job Finder - 1-Click Dependency Installer
cd /d "%~dp0"

echo ============================================================
echo       BD Job Finder - Portable Dependency Installer
echo ============================================================
echo.
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10+ from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

echo [OK] Python detected.
echo.
echo [2/3] Installing Python libraries from requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Some dependencies had warnings or issues. Attempting user install...
    python -m pip install --user -r requirements.txt
)

echo.
echo [3/3] Installing Playwright Chromium browser for ATS Autopilot...
python -m playwright install chromium
if %ERRORLEVEL% neq 0 (
    echo [NOTICE] Playwright browser install notice. You can still use Direct Email & Portal modes.
)

echo.
echo ============================================================
echo [SUCCESS] Setup Complete! 
echo Double-click 'run.bat' anytime to launch BD Job Finder.
echo ============================================================
pause
