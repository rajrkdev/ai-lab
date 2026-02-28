# InsureChat v3.0 Setup Script (PowerShell)
# Run: .\setup.ps1

param(
    [string]$VenvPath = "C:\Users\dearr\Documents\.venv"
)

Write-Host "=== InsureChat v3.0 Setup ===" -ForegroundColor Cyan

# Create venv if it doesn't exist
if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment at $VenvPath..." -ForegroundColor Yellow
    python -m venv $VenvPath
}

# Activate venv
$activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & $activateScript
} else {
    Write-Host "ERROR: Cannot find activation script at $activateScript" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Download spaCy model
Write-Host "Downloading spaCy language model..." -ForegroundColor Yellow
python -m spacy download en_core_web_lg

# Create data directories
Write-Host "Creating data directories..." -ForegroundColor Yellow
$directories = @(
    "data\insurance",
    "data\support",
    "data\chroma_db"
)
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Copy .env template if .env doesn't exist
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example - edit with your API keys!" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env with your ANTHROPIC_API_KEY and GOOGLE_API_KEY"
Write-Host "  2. Run: .\run.ps1"
