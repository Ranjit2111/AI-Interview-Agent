@echo off
echo Running AI Interviewer Agent dependency fixer...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher and try again.
    echo.
    pause
    exit /b 1
)

REM Run the dependency fixer script
python fix_dependencies.py

echo.
if errorlevel 1 (
    echo There was an error running the script.
    echo Please check the output above for more details.
) else (
    echo Dependencies fixed successfully!
)

pause 