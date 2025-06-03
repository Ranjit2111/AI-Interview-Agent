@echo off
setlocal

echo ===================================================
echo     AI INTERVIEWER AGENT - VIRTUAL ENV STARTER
echo               (WITHOUT STAGEWISE TOOL)
echo ===================================================
echo.

:: Get the current directory (project root)
set "PROJECT_ROOT=%CD%"
echo Project root: %PROJECT_ROOT%

:: Setup virtual environment if it doesn't exist
if not exist backend\venv (
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    cd ..
)

echo.
echo Installing essential backend dependencies...
cd backend
call venv\Scripts\activate
call pip install -r requirements.txt
:: Deactivate virtual environment
call deactivate
cd ..

echo.
echo Starting backend server...
start cmd /k "cd backend && call venv\Scripts\activate && set PYTHONPATH=%PROJECT_ROOT% && python -m uvicorn main:app --reload --port 8000"

echo.
echo Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo Starting frontend server (without stagewise)...
start cmd /k "cd frontend && npm run dev:no-stagewise"

echo.
echo Services are starting in separate windows.
echo.
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:8080
echo.
echo NOTE: Stagewise toolbar is DISABLED in this session
echo If you encounter errors, check the console windows for details.

pause 