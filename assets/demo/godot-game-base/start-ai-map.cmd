@echo off
rem 启动 AI 瓦片地图（HD-2D 横板，艾琳主角）
setlocal
cd /d "%~dp0"
set GODOT=C:\Users\26046\Documents\lovegaming\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64.exe
"%GODOT%" --path . -- --map res://assets/maps/ai_forest.map.json