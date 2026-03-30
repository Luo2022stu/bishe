@echo off
echo ================================================
echo 重启Flask服务器
echo ================================================
echo.

echo [1/3] 停止现有服务器...
taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo 已停止现有服务器
) else (
    echo 没有运行中的服务器
)

echo.
echo [2/3] 等待2秒...
timeout /t 2 /nobreak >nul

echo.
echo [3/3] 启动新服务器...
echo 服务器将在新窗口中启动
echo 按 Ctrl+C 可以停止服务器
echo.
start python app/app.py

echo.
echo ================================================
echo 服务器启动完成!
echo 请访问: http://localhost:5000
echo ================================================
echo.
pause
