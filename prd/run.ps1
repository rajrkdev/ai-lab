# InsureChat v3.0 Run Script (PowerShell)
# Run: .\run.ps1

param(
    [string]$VenvPath = "C:\Users\dearr\Documents\.venv"
)

Write-Host "=== InsureChat v3.0 - Starting Services ===" -ForegroundColor Cyan

# Activate venv
$activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Host "ERROR: Venv not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Start FastAPI backend
Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "web.fastapi_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -NoNewWindow

Start-Sleep -Seconds 2

# Start Microsite Chatbot
Write-Host "Starting Microsite Chatbot on port 8501..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "streamlit", "run", "web/streamlit_microsite.py", "--server.port", "8501" -NoNewWindow

Start-Sleep -Seconds 1

# Start Support Chatbot
Write-Host "Starting Support Chatbot on port 8502..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "streamlit", "run", "web/streamlit_support.py", "--server.port", "8502" -NoNewWindow

Write-Host ""
Write-Host "=== All Services Started ===" -ForegroundColor Green
Write-Host "  FastAPI Backend:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Microsite Chatbot:  http://localhost:8501" -ForegroundColor Cyan
Write-Host "  Support Chatbot:    http://localhost:8502" -ForegroundColor Cyan
