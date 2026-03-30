@echo off
chcp 65001 >nul
echo ========================================
echo 校园失物招领系统 - 后端服务
echo ========================================
echo.

cd /d "%~dp0app"
echo 当前目录: %CD%
echo.
echo 正在启动后端服务...
echo 服务地址: http://localhost:5000
echo.

python app.py

pause
