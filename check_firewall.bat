@echo off
echo 正在检查防火墙规则...
echo.
netsh advfirewall firewall show rule name="Python Flask Server 5000" | findstr "已启用"
echo.
echo 正在检查端口5000是否被监听...
echo.
netstat -ano | findstr :5000
echo.
if %errorlevel% equ 0 (
    echo [√] 端口5000正在被监听
) else (
    echo [×] 端口5000未被监听，请确保服务器已启动
)
echo.
echo 正在检查网络接口...
echo.
ipconfig | findstr /i "IPv4"
echo.
echo ================================
echo 如果防火墙规则未启用，请运行 add_firewall_rule.bat
echo 如果端口未监听，请运行 start.bat 启动服务器
echo ================================
pause
