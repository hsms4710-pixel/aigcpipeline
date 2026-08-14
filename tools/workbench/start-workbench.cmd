@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "PY=C:\Users\26046\Desktop\inerview\runtime\.venv\Scripts\python.exe"
echo ============================================
echo  ?? AIGC ????????
echo ============================================
rem ???? 8000
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/api/health > %temp%\wbcheck.txt 2>nul
set /p wbcode=<%temp%\wbcheck.txt
if "%wbcode%"=="200" (
  echo [OK] ?????? (8000)
) else (
  echo [..] ???? (8000) ...
  start "pipeline-backend" /min "%PY%" -m uvicorn app:app --host 127.0.0.1 --port 8000
  timeout /t 4 /nobreak >nul
)
start "" http://127.0.0.1:8000/
echo.
echo ?????? http://127.0.0.1:8000/
echo ?????/???? StretchyStudio ??(5173/5174)?
echo   ?? env\runtime\tools\stretchy-studio\start-stretchy.cmd
echo.
endlocal
