@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动角色 AIGC 工作台...
echo 地址: http://127.0.0.1:8000
"C:\Users\26046\Desktop\inerview\runtime\.venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000
echo.
echo 服务已退出（如报错请截图上面的信息）
pause