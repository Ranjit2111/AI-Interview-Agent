#!/usr/bin/env pwsh
# AI Interviewer Agent - Local Startup Script
# This script starts both the frontend and backend servers

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "   AI INTERVIEWER AGENT STARTUP    " -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Explicitly use Python 3.10
$pythonCommand = "C:\Users\Ranjit\AppData\Local\Programs\Python\Python310\python.exe"

# Check if Python is installed and verify version
try {
    $pythonVersion = & $pythonCommand --version
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
    
    # Check if it's Python 3.10.x
    if (-not ($pythonVersion -match "Python 3\.10\.")) {
        Write-Host "Warning: This application works best with Python 3.10.x. You are using $pythonVersion" -ForegroundColor Yellow
        Write-Host "Options:" -ForegroundColor Yellow
        Write-Host "1. Install Python 3.10 and set it as your default" -ForegroundColor Yellow
        Write-Host "2. Edit this script and set pythonCommand to point to Python 3.10" -ForegroundColor Yellow
        Write-Host "   Example: `$pythonCommand = `"C:\Path\To\Python310\python.exe`"" -ForegroundColor Yellow
        $proceed = Read-Host "Do you want to proceed with $pythonVersion anyway? (y/n)"
        if ($proceed -ne "y") {
            Write-Host "Installation aborted. Please set up Python 3.10.x" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✓ Python 3.10.x detected, perfect for this application" -ForegroundColor Green
    }
} 
catch {
    Write-Host "✗ Python not found. Please install Python 3.10.x" -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js detected: $nodeVersion" -ForegroundColor Green
} 
catch {
    Write-Host "✗ Node.js not found. Please install Node.js 14 or later." -ForegroundColor Red
    exit 1
}

# Function to check if a directory exists
function Test-DirectoryExists {
    param (
        [string]$Path
    )
    return (Test-Path -Path $Path -PathType Container)
}

# Detect Windows - more reliable than using $IsWindows which is PowerShell Core only
$IsWindowsOS = $env:OS -eq "Windows_NT"

# Verify backend directory
if (-not (Test-DirectoryExists -Path ".\backend")) {
    Write-Host "✗ Backend directory not found." -ForegroundColor Red
    exit 1
}

# Verify frontend directory
if (-not (Test-DirectoryExists -Path ".\frontend")) {
    Write-Host "✗ Frontend directory not found." -ForegroundColor Red
    exit 1
}

# Verify backend .env file
if (-not (Test-Path -Path ".\backend\.env")) {
    Write-Host "! Backend .env file not found. Copying from example..." -ForegroundColor Yellow
    Copy-Item ".\backend\.env.example" ".\backend\.env" -ErrorAction SilentlyContinue
    if (-not (Test-Path -Path ".\backend\.env")) {
        Write-Host "✗ Failed to create .env file. Please create it manually." -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Created backend .env file. Please edit it to add your API key." -ForegroundColor Green
}

# Verify frontend .env.local file
if (-not (Test-Path -Path ".\frontend\.env.local")) {
    Write-Host "! Frontend .env.local file not found. Creating..." -ForegroundColor Yellow
    Set-Content -Path ".\frontend\.env.local" -Value "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000"
    if (-not (Test-Path -Path ".\frontend\.env.local")) {
        Write-Host "✗ Failed to create .env.local file. Please create it manually." -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Created frontend .env.local file." -ForegroundColor Green
}

# Create a temporary directory for backend if it doesn't exist
if (-not (Test-DirectoryExists -Path ".\backend\temp")) {
    Write-Host "Creating temp directory for backend..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path ".\backend\temp" | Out-Null
    Write-Host "✓ Created temp directory." -ForegroundColor Green
}

# Clean up and recreate Python virtual environment
Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow
if (Test-DirectoryExists -Path ".\backend\.venv") {
    Write-Host "Removing existing virtual environment to avoid dependency conflicts..." -ForegroundColor Yellow
    Remove-Item -Path ".\backend\.venv" -Recurse -Force
}

Set-Location -Path ".\backend"
& $pythonCommand -m venv .venv
Set-Location -Path ".."
Write-Host "✓ Virtual environment created fresh with $pythonCommand." -ForegroundColor Green

# Function to start the backend server
function Start-BackendServer {
    Write-Host "Starting backend server..." -ForegroundColor Cyan
    Set-Location -Path ".\backend"
    
    # Activate virtual environment based on OS
    if ($IsWindowsOS) {
        Write-Host "Activating Windows virtual environment..." -ForegroundColor Yellow
        # Use cmd.exe to run everything in one context with the activated environment
        cmd /c ".\.venv\Scripts\activate.bat && python -m pip install --upgrade pip && python -m pip install setuptools wheel && python -m pip install -r requirements.txt && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    } 
    else {
        # Unix style activation and execution
        Write-Host "Activating Unix virtual environment..." -ForegroundColor Yellow
        bash -c "source ./.venv/bin/activate && python -m pip install --upgrade pip && python -m pip install setuptools wheel && python -m pip install -r requirements.txt && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    }
}

# Function to start the frontend server
function Start-FrontendServer {
    Write-Host "Starting frontend server..." -ForegroundColor Cyan
    Set-Location -Path ".\frontend"
    
    # Clear .next directory to ensure clean build
    if (Test-DirectoryExists -Path ".\.next") {
        Write-Host "Removing previous Next.js build artifacts..." -ForegroundColor Yellow
        Remove-Item -Path ".\.next" -Recurse -Force
    }
    
    # Install dependencies if needed
    Write-Host "Installing/updating frontend dependencies..." -ForegroundColor Yellow
    npm install
    
    # Skip build during start - we'll run dev mode directly
    Write-Host "Starting Next.js development server..." -ForegroundColor Green
    npm run dev
}

# Start the frontend in a new window and the backend in the current window
if ($IsWindowsOS) {
    Write-Host "Starting frontend in a new window..." -ForegroundColor Yellow
    Start-Process -FilePath "powershell" -ArgumentList "-Command", "Set-Location '$PWD'; cd frontend; npm install; npm run dev"
    Start-BackendServer
} 
else {
    # For non-Windows systems
    Write-Host "Starting services in separate terminals..." -ForegroundColor Yellow
    Start-Process -FilePath "bash" -ArgumentList "-c", "cd '$PWD/frontend' && npm install && npm run dev"
    Start-BackendServer
}

# Parameter handling for if script is called with arguments
if ($args.Count -gt 0) {
    if ($args[0] -eq "frontend") {
        Start-FrontendServer
    } 
    elseif ($args[0] -eq "backend") {
        Start-BackendServer
    }
} 

