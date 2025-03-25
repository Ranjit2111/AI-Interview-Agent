@echo off 
setlocal 
 
echo Trying method 1: Setting PYTHONPATH... 
set "PYTHONPATH=.." 
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload 
if not ERRORLEVEL 1 goto :success 
echo Method 1 failed. 
 
echo Trying method 2: Running from project root... 
cd .. 
python -m backend.main  
if not ERRORLEVEL 1 goto :success 
echo Method 2 failed. 
cd backend 
 
echo Trying method 3: Direct approach... 
cd .. 
set "PYTHONPATH=." 
python backend\main.py 
if not ERRORLEVEL 1 goto :success 
echo Method 3 failed. 
 
echo All methods failed. Please see errors above. 
echo. 
echo Try running manually: 
echo cd backend && set PYTHONPATH=.. && python -m uvicorn main:app --reload 
echo OR 
echo cd [project_root] && python -m backend.main 
goto :end 
 
:success 
echo Backend started successfully 
goto :end 
 
:end 
pause 
