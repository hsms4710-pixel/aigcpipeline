@echo off
cd /d "%~dp0"
set "PY=C:\Users\26046\Desktop\inerview\runtime\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] python not found: %PY%
  echo Install runtime venv first.
  pause
  exit /b 1
)
echo Starting workbench at http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
"%PY%" -m uvicorn app:app --host 127.0.0.1 --port 8000
echo.
echo Server stopped.
pause