@echo off
title BD Job Finder - All-Bangladesh Recruitment Assistant
cd /d "%~dp0"

echo ============================================================
echo         BD Job Finder - Bangladesh Employment Hub
echo                 Launching Local Server...
echo ============================================================
echo.

:: Test Python availability
python -c "import streamlit" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing required dependencies...
    python -m pip install -r requirements.txt
)

:: Automatically check and release occupied port 8502 from previous instances
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8502 ^| findstr LISTENING') do (
    echo [INFO] Releasing occupied port 8502 [PID %%a]
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 1 /nobreak >nul 2>&1
)

echo [OK] Launching application on http://localhost:8502 ...
echo [INFO] Your default browser will open automatically.
echo.
echo Press Ctrl+C anytime in this window to stop the server.
echo ============================================================
echo.

python -m streamlit run app.py --server.port 8502

if %ERRORLEVEL% neq 0 (
    echo.
    echo [Notice] Trying alternate launcher command...
    streamlit run app.py --server.port 8502
)

pause
