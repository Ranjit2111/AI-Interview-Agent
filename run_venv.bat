@echo off
setlocal

echo ===================================================
echo     AI INTERVIEWER AGENT - VIRTUAL ENV STARTER
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
echo Starting frontend server with environment variables...
start cmd /k "cd frontend && set VITE_API_BASE_URL=http://localhost:8000 && set VITE_WS_BASE_URL=ws://localhost:8000 && npm run dev"

echo.
echo Services are starting in separate windows.
echo.
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:8080
echo.
echo Environment Variables Set:
echo - VITE_API_BASE_URL=http://localhost:8000
echo - VITE_WS_BASE_URL=ws://localhost:8000
echo.
echo If you encounter errors, check the console windows for details.

pause 