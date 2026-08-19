@echo off
cd /d "%~dp0"
echo ============================================
echo   Starting Ailin Godot demo ...
echo ============================================
echo.
start "" "C:\Users\26046\Documents\lovegaming\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64.exe" --path "%cd%"
echo Game window opened. Close the game to exit.
echo Controls: WASD/Arrows move, SPACE attack, H hurt, 1-4 expressions
echo.
pause >nul