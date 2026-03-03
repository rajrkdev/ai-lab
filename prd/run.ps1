# =============================================================================
# InsureChat v3.0 — Run Script (PowerShell)
# =============================================================================
# Starts all four services that make up the running application:
#   1. FastAPI backend   (port 8000) — REST API / RAG pipeline / reports
#   2. Admin Dashboard   (port 8500) — Streamlit UI for ingestion & management
#   3. Microsite Chatbot (port 8501) — Streamlit UI for insurance customers
#   4. Support Chatbot   (port 8502) — Streamlit UI for API developers
#
# Prerequisites:
#   - Virtual environment created by setup.ps1
#   - .env file populated with ANTHROPIC_API_KEY and GEMINI_API_KEY
#
# Usage:  .\run.ps1
#         .\run.ps1 -VenvPath "D:\my_venv"   # override venv location
# =============================================================================

# --- Parameter: path to the Python virtual environment ---
param(
    [string]$VenvPath = "C:\Users\dearr\Documents\.venv"
)

Write-Host "=== InsureChat v3.0 - Starting Services ===" -ForegroundColor Cyan

# --- Activate the virtual environment so all python/pip calls use it ---
$activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Host "ERROR: Venv not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# --- Service 1: FastAPI backend (uvicorn with hot-reload) ---
# Serves all REST endpoints: /chat, /ingest, /analytics, /reports, /health
Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "web.fastapi_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -NoNewWindow

# Brief pause to let the backend bind its port before starting frontends
Start-Sleep -Seconds 2

# --- Service 2: Admin Dashboard (Streamlit — ingestion & management UI) ---
Write-Host "Starting Admin Dashboard on port 8500..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "streamlit", "run", "web/admin.py", "--server.port", "8500" -NoNewWindow

Start-Sleep -Seconds 1

# --- Service 3: Microsite Chatbot (Streamlit — insurance customer UI) ---
Write-Host "Starting Microsite Chatbot on port 8501..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "streamlit", "run", "web/microsite.py", "--server.port", "8501" -NoNewWindow

Start-Sleep -Seconds 1

# --- Service 4: Support Chatbot (Streamlit — developer support UI) ---
Write-Host "Starting Support Chatbot on port 8502..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "streamlit", "run", "web/support.py", "--server.port", "8502" -NoNewWindow

# --- Print the access URLs for all services ---
Write-Host ""
Write-Host "=== All Services Started ===" -ForegroundColor Green
Write-Host "  FastAPI Backend:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Admin Dashboard:    http://localhost:8500" -ForegroundColor Cyan
Write-Host "  Microsite Chatbot:  http://localhost:8501" -ForegroundColor Cyan
Write-Host "  Support Chatbot:    http://localhost:8502" -ForegroundColor Cyan
