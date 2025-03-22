#!/usr/bin/env pwsh
# AI Interviewer Agent - Simplified Startup Script
# This script starts both the frontend and backend servers efficiently

# Define parameters for the script
param (
    [switch]$Clean = $false,        # Force clean reinstall of all dependencies
    [switch]$SkipBackend = $false,  # Skip starting the backend
    [switch]$SkipFrontend = $false, # Skip starting the frontend
    [switch]$Help = $false          # Show help message
)

# Show help if requested
if ($Help) {
    Write-Host "AI Interviewer Agent Startup Script" -ForegroundColor Cyan
    Write-Host "Usage: ./start_opt.ps1 [options]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Clean         Force clean reinstall of all dependencies"
    Write-Host "  -SkipBackend   Don't start the backend server"
    Write-Host "  -SkipFrontend  Don't start the frontend server"
    Write-Host "  -Help          Display this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./start_opt.ps1                # Efficient startup, reuse existing environments"
    Write-Host "  ./start_opt.ps1 -Clean         # Force clean reinstall of all dependencies"
    Write-Host "  ./start_opt.ps1 -SkipFrontend  # Start only the backend server"
    exit 0
}

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "   AI INTERVIEWER AGENT STARTUP    " -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

if ($Clean) {
    Write-Host "Running in CLEAN mode - Will reinstall all dependencies" -ForegroundColor Yellow
}

# Explicitly use Python 3.10
$pythonCommand = "C:\Users\Ranjit\AppData\Local\Programs\Python\Python310\python.exe"

# Check if Python is installed and verify version
try {
    $pythonVersion = & $pythonCommand --version
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
    
    # Check if it's Python 3.10.x
    if (-not ($pythonVersion -match "Python 3\.10\.")) {
        Write-Host "Warning: This application works best with Python 3.10.x. You are using $pythonVersion" -ForegroundColor Yellow
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

# Simple check if virtual environment exists
$venvExists = (Test-DirectoryExists -Path ".\backend\.venv") -and (Test-Path -Path ".\backend\.venv\Scripts\activate.bat")

# Should we install or reinstall dependencies?
$needsDependencyInstall = $Clean

# Only perform backend setup if we're going to start the backend
if (-not $SkipBackend) {
    if ($Clean -or (-not $venvExists)) {
        # Need to create or recreate virtual environment
        Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow
        if (Test-DirectoryExists -Path ".\backend\.venv") {
            Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
            Remove-Item -Path ".\backend\.venv" -Recurse -Force
        }

        Set-Location -Path ".\backend"
        & $pythonCommand -m venv .venv
        Set-Location -Path ".."
        Write-Host "✓ Virtual environment created fresh." -ForegroundColor Green
        $needsDependencyInstall = $true
    } else {
        Write-Host "✓ Using existing Python virtual environment." -ForegroundColor Green
        
        # Simple check for a core dependency
        if (-not $Clean) {
            $activateScript = "$PWD\backend\.venv\Scripts\activate.bat"
            $testScript = "$PWD\backend\temp\test_deps.py"
            
            # Create a simple test script to check for core dependencies
            $testContent = @"
try:
    import fastapi
    import uvicorn
    import numpy
    import scipy
    print('DEPS_OK')
except ImportError as e:
    print(f'Missing: {e}')
"@
            Set-Content -Path $testScript -Value $testContent
            
            # Execute the test script in a batch file to maintain context
            $testBatch = "$PWD\backend\temp\test_deps.bat"
            $batchContent = @"
@echo off
call "$activateScript"
python "$testScript"
"@
            Set-Content -Path $testBatch -Value $batchContent
            
            # Run the batch file
            $testOutput = & $testBatch
            
            # Clean up temp files
            Remove-Item -Path $testScript -Force
            Remove-Item -Path $testBatch -Force
            
            if ($testOutput -contains "DEPS_OK") {
                Write-Host "✓ Core dependencies verified." -ForegroundColor Green
            } else {
                Write-Host "Some core dependencies are missing. Will reinstall." -ForegroundColor Yellow
                $needsDependencyInstall = $true
            }
        }
    }
}

# Function to start the backend server
function Start-BackendServer {
    Write-Host "Starting backend server..." -ForegroundColor Cyan
    
    # Create a batch file to run the backend commands in sequence
    $backendBatch = "$PWD\backend\temp\run_backend.bat"
    if ($needsDependencyInstall) {
        # With dependencies installation
        $batchContent = @"
@echo off
cd "$PWD\backend"
call .\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install setuptools wheel
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"@
    } else {
        # Without reinstalling dependencies
        $batchContent = @"
@echo off
cd "$PWD\backend"
call .\.venv\Scripts\activate.bat
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"@
    }
    
    Set-Content -Path $backendBatch -Value $batchContent
    
    # Execute the batch file
    & $backendBatch
    
    # Clean up temp file
    Remove-Item -Path $backendBatch -Force -ErrorAction SilentlyContinue
}

# Function to start the frontend server
function Start-FrontendServer {
    Write-Host "Starting frontend server..." -ForegroundColor Cyan
    
    Set-Location -Path ".\frontend"
    
    # Check if node_modules exists
    $needsNpmInstall = $Clean -or (-not (Test-DirectoryExists -Path ".\node_modules"))
    
    # Clean .next if needed
    if ($Clean -and (Test-DirectoryExists -Path ".\.next")) {
        Write-Host "Removing previous Next.js build artifacts..." -ForegroundColor Yellow
        Remove-Item -Path ".\.next" -Recurse -Force
    }
    
    # Install dependencies if needed
    if ($needsNpmInstall) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        npm install
    } else {
        Write-Host "✓ Using existing frontend dependencies." -ForegroundColor Green
    }
    
    # Start Next.js dev server
    Write-Host "Starting Next.js development server..." -ForegroundColor Green
    npm run dev
}

# Start services based on parameters
if (-not $SkipBackend -and -not $SkipFrontend) {
    # Start both services
    Write-Host "Starting frontend in a new window and backend in current window..." -ForegroundColor Yellow
    
    # Create a batch file for the frontend
    $frontendBatch = "$PWD\frontend\run_frontend.bat"
    $frontendContent = @"
@echo off
cd "$PWD\frontend"
"@
    
    # Add frontend setup operations
    if ($Clean -and (Test-DirectoryExists -Path "$PWD\frontend\.next")) {
        $frontendContent += @"

echo Cleaning Next.js artifacts...
rmdir /s /q .next
"@
    }
    
    if ($Clean -or (-not (Test-DirectoryExists -Path "$PWD\frontend\node_modules"))) {
        $frontendContent += @"

echo Installing frontend dependencies...
call npm install
"@
    }
    
    $frontendContent += @"

echo Starting Next.js server...
call npm run dev
"@
    
    Set-Content -Path $frontendBatch -Value $frontendContent
    
    # Start frontend in new window
    Start-Process "cmd" -ArgumentList "/c $frontendBatch"
    
    # Start backend in current window
    Start-BackendServer
} 
elseif (-not $SkipFrontend) {
    # Start only frontend
    Start-FrontendServer
}
elseif (-not $SkipBackend) {
    # Start only backend
    Start-BackendServer
}
else {
    Write-Host "Both frontend and backend are skipped. Nothing to do." -ForegroundColor Yellow
} 