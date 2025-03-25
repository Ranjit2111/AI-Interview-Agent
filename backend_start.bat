@echo off 
setlocal EnableDelayedExpansion 
 
echo >>> Trying method 1: Setting PYTHONPATH to parent directory... 
set "PYTHONPATH=.." 
echo PYTHONPATH set to: %PYTHONPATH% 
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload 
if %ERRORLEVEL% EQU 0 goto :eof 
echo Method 1 failed with error code: %ERRORLEVEL% 
 
echo >>> Trying method 2: Running from project root... 
cd .. 
echo Current directory: %CD% 
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload 
if %ERRORLEVEL% EQU 0 goto :eof 
echo Method 2 failed with error code: %ERRORLEVEL% 
 
echo >>> Trying method 3: Running main.py directly with sys.path modification... 
cd .. 
echo Current directory: %CD% 
python -c "import sys; sys.path.insert(0, '.'); from backend.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)" 
if %ERRORLEVEL% EQU 0 goto :eof 
echo Method 3 failed with error code: %ERRORLEVEL% 
 
echo >>> Trying method 4: Setting PYTHONPATH to current directory from root... 
set "PYTHONPATH=." 
echo PYTHONPATH set to: %PYTHONPATH% 
python -m backend.main 
if %ERRORLEVEL% EQU 0 goto :eof 
echo Method 4 failed with error code: %ERRORLEVEL% 
 
echo All methods failed. Please check the error messages above. 
echo. 
echo Common solutions: 
echo 1. Run the backend manually with: cd backend && set PYTHONPATH=.. && python -m uvicorn main:app --reload 
echo 2. Run from project root with: python -m backend.main 
echo 3. Check if all dependencies are installed 
echo. 
pause 
