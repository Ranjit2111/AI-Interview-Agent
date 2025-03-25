@echo off
setlocal

echo ===================================================
echo     AI INTERVIEWER AGENT - MINIMAL STARTER
echo ===================================================
echo.

set "PYTHON_PATH=C:\Users\Ranjit\AppData\Local\Programs\Python\Python310\python.exe"
echo Using Python 3.10: %PYTHON_PATH%

:: Get the current directory (project root)
set "PROJECT_ROOT=%CD%"
echo Project root: %PROJECT_ROOT%

echo.
echo Installing essential backend dependencies...
cd backend
"%PYTHON_PATH%" -m pip install "uvicorn[standard]" "fastapi" "sqlalchemy" "python-dotenv" "pydantic<2.0.0" "python-multipart"
"%PYTHON_PATH%" -m pip install "langchain-core" "langchain-community" "langchain-google-genai"
"%PYTHON_PATH%" -m pip install "numpy==1.23.5" "scipy==1.10.0" "PyMuPDF==1.21.1" "python-docx==0.8.11"
cd ..

:: Create or copy environment file if needed
if not exist backend\.env (
    if exist backend\.env.example (
        echo Creating backend .env file from example...
        copy backend\.env.example backend\.env
    )
)

echo.
echo Starting backend server...
start cmd /k "cd backend && set PYTHONPATH=%PROJECT_ROOT% && "%PYTHON_PATH%" -m uvicorn main:app --reload --port 8000"

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