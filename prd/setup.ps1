# =============================================================================
# InsureChat v3.0 — Setup Script (PowerShell)
# =============================================================================
# One-time setup that prepares the development environment:
#   1. Creates a Python virtual environment (if it doesn’t exist)
#   2. Installs all pip dependencies from requirements.txt
#   3. Downloads the spaCy NLP model (en_core_web_lg) for Presidio PII detection
#   4. Creates the required data directories for documents and vector DB
#   5. Copies .env.example → .env so the user can fill in their API keys
#
# Usage:  .\setup.ps1
#         .\setup.ps1 -VenvPath "D:\my_venv"   # override venv location
# =============================================================================

# --- Parameter: path where the virtual environment will be created ---
param(
    [string]$VenvPath = "C:\Users\dearr\Documents\.venv"
)

Write-Host "=== InsureChat v3.0 Setup ===" -ForegroundColor Cyan

# --- Step 1: Create Python venv if it doesn’t already exist ---
if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment at $VenvPath..." -ForegroundColor Yellow
    python -m venv $VenvPath
}

# --- Step 2: Activate the virtual environment ---
$activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & $activateScript
} else {
    Write-Host "ERROR: Cannot find activation script at $activateScript" -ForegroundColor Red
    exit 1
}

# --- Step 3: Install all Python dependencies listed in requirements.txt ---
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# --- Step 4: Download the large spaCy English model ---
# Presidio (PII detection engine) requires a spaCy model for tokenization.
# en_core_web_lg is the large model (~560 MB) providing best accuracy.
Write-Host "Downloading spaCy language model..." -ForegroundColor Yellow
python -m spacy download en_core_web_lg

# --- Step 5: Create required data directories for document storage ---
# These folders hold uploaded documents and the ChromaDB vector database.
Write-Host "Creating data directories..." -ForegroundColor Yellow
$directories = @(
    "data\insurance",      # Uploaded insurance policy documents (PDFs, DOCX, etc.)
    "data\support",        # Uploaded API error / integration documents
    "data\chroma_db"       # ChromaDB persistent vector store (auto-populated)
)
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# --- Step 6: Create .env from template if it doesn’t exist ---
# The .env file holds secret API keys; never commit it to version control.
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example - edit with your API keys!" -ForegroundColor Yellow
    }
}

# --- Done — tell the user what to do next ---
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env with your ANTHROPIC_API_KEY and GOOGLE_API_KEY"
Write-Host "  2. Run: .\run.ps1"
