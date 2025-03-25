# AI Interviewer Agent - Virtual Environment Starter
# PowerShell Script

# Display header
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    AI INTERVIEWER AGENT - VIRTUAL ENV STARTER" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$ProjectRoot = Get-Location
Write-Host "Project root: $ProjectRoot"

# Function to handle errors
function Handle-Error {
    param (
        [string]$ErrorMessage
    )
    Write-Host "ERROR: $ErrorMessage" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "backend\.venv")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    try {
        Push-Location backend
        python -m venv .venv
        if (-not $?) { throw "Failed to create virtual environment" }
        Pop-Location
    }
    catch {
        Handle-Error "Failed to create virtual environment: $_"
    }
}

# Install backend dependencies
Write-Host "`nInstalling essential backend dependencies..." -ForegroundColor Yellow
try {
    Push-Location backend
    & .\.venv\Scripts\Activate.ps1
    
    Write-Host "Installing core packages..." -ForegroundColor Yellow
    python -m pip install "uvicorn[standard]" "fastapi" "sqlalchemy" "python-dotenv" "pydantic<2.0.0" "python-multipart"
    if (-not $?) { throw "Failed to install core packages" }
    
    Write-Host "Installing langchain packages..." -ForegroundColor Yellow
    python -m pip install "langchain-core" "langchain-community" "langchain-google-genai"
    if (-not $?) { throw "Failed to install langchain packages" }
    
    Write-Host "Installing data processing packages..." -ForegroundColor Yellow
    python -m pip install "numpy==1.23.5" "scipy==1.10.0" "PyMuPDF==1.21.1" "python-docx==0.8.11"
    if (-not $?) { throw "Failed to install data processing packages" }
    
    deactivate
    Pop-Location
}
catch {
    deactivate
    Pop-Location
    Handle-Error "Failed to install dependencies: $_"
}

# Create or copy environment file if needed
if (-not (Test-Path "backend\.env")) {
    if (Test-Path "backend\.env.example") {
        Write-Host "Creating backend .env file from example..." -ForegroundColor Yellow
        Copy-Item "backend\.env.example" "backend\.env"
    }
    elseif (Test-Path "sample_env.txt") {
        Write-Host "Creating backend .env file from sample..." -ForegroundColor Yellow
        Copy-Item "sample_env.txt" "backend\.env"
    }
}

# Start backend server
Write-Host "`nStarting backend server..." -ForegroundColor Green
try {
    $backendCmd = "cd '$ProjectRoot\backend'; & .\.venv\Scripts\Activate.ps1; `$env:PYTHONPATH='$ProjectRoot'; python -m uvicorn main:app --reload --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
}
catch {
    Handle-Error "Failed to start backend server: $_"
}

# Start frontend server
Write-Host "`nStarting frontend server..." -ForegroundColor Green
try {
    $frontendCmd = "cd '$ProjectRoot\frontend'; npm run dev"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
}
catch {
    Handle-Error "Failed to start frontend server: $_"
}

# Final instructions
Write-Host "`nServices are starting in separate windows." -ForegroundColor Green
Write-Host ""
Write-Host "- Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "- Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "If you encounter errors, check the console windows for details." -ForegroundColor Yellow

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 