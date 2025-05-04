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
if not exist backend\.venv (
    echo Creating virtual environment...
    cd backend
    python -m venv .venv
    cd ..
)

echo.
echo Installing essential backend dependencies...
cd backend
call .venv\Scripts\activate

:: Deactivate virtual environment
call deactivate
cd ..

:: Create or copy environment file if needed
if not exist backend\.env (
    if exist backend\.env.example (
        echo Creating backend .env file from example...
        copy backend\.env.example backend\.env
    ) else if exist sample_env.txt (
        echo Creating backend .env file from sample...
        copy sample_env.txt backend\.env
    )
)

echo.
echo Starting Kokoro TTS service...
start cmd /k "cd /d D:\\Kokoro\\Kokoro-FastAPI\\docker\\gpu && docker compose up"
echo Kokoro TTS service starting in a separate window. Check that window for status.
cd /d "%PROJECT_ROOT%"

echo.
echo Starting backend server...
start cmd /k "cd backend && call .venv\Scripts\activate && set PYTHONPATH=%PROJECT_ROOT% && python -m uvicorn main:app --reload --port 8000"

echo.
echo Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo Starting frontend server...
start cmd /k "cd frontend && npm run dev"

echo.
echo Services are starting in separate windows.
echo.
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:8080
echo.
echo If you encounter errors, check the console windows for details.

pause 