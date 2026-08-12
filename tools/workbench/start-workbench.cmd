@echo off
chcp 65001 >nul
echo 启动角色 AIGC 工作台...
cd /d "%~dp0..\..\..\.."
start "" /b "C:\Users\26046\Desktop\inerview\runtime\.venv\Scripts\python.exe" -m uvicorn app:app --app-dir "tools\workbench" --host 127.0.0.1 --port 8000
echo 工作台: http://127.0.0.1:8000  （浏览器打开；Ctrl+C 停止）
pause
