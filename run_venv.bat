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

::echo Installing core packages...
::python -m pip install "uvicorn[standard]" "fastapi" "sqlalchemy" "python-dotenv" "pydantic<2.0.0" "python-multipart"

::echo Installing langchain packages...
::python -m pip install "langchain-core" "langchain-community" "langchain-google-genai"

::echo Installing data processing packages...
::python -m pip install "numpy==1.23.5" "scipy==1.10.0" "PyMuPDF==1.21.1" "python-docx==0.8.11"

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
echo Starting frontend server...
start cmd /k "cd frontend && npm run dev"

echo.
echo Services are starting in separate windows.
echo.
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo.
echo If you encounter errors, check the console windows for details.

pause 