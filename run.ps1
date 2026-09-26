# PowerShell Activator for BD Job Finder
Set-Location -Path $PSScriptRoot

Write-Host "============================================================" -ForegroundColor Green
Write-Host "         BD Job Finder - Bangladesh Employment Hub" -ForegroundColor Cyan
Write-Host "                 Activating Environment..." -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green

# Verify dependencies
try {
    python -c "import streamlit, google.genai, bs4, pypdf" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[INFO] Installing required libraries from requirements.txt..." -ForegroundColor Yellow
        python -m pip install -r requirements.txt
    }
} catch {
    Write-Host "[NOTICE] Proceeding with standard launch..." -ForegroundColor Gray
}

# Free occupied port 8502 if any previous instance is running
try {
    $connections = Get-NetTCPConnection -LocalPort 8502 -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            if ($conn.OwningProcess -gt 0) {
                Write-Host "[INFO] Freeing occupied port 8502 (PID $($conn.OwningProcess))..." -ForegroundColor Yellow
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Seconds 1
    }
} catch {}

Write-Host "[OK] Launching BD Job Finder on http://localhost:8503 ..." -ForegroundColor Green
python -m streamlit run app.py --server.port 8503
