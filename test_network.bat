@echo off
echo ================================
echo 网络连接测试工具
echo ================================
echo.

echo [1] 检查本地网络配置...
ipconfig | findstr /i "IPv4"
echo.

echo [2] 检查防火墙规则...
netsh advfirewall firewall show rule name="Python Flask Server 5000" 2>nul
if %errorlevel% equ 0 (
    echo [√] 防火墙规则已配置
) else (
    echo [×] 防火墙规则不存在，请运行 add_firewall_rule.bat
)
echo.

echo [3] 检查端口5000监听状态...
netstat -ano | findstr :5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] 端口5000正在被监听
    netstat -ano | findstr :5000
) else (
    echo [×] 端口5000未被监听
)
echo.

echo [4] 测试本地服务器访问...
echo 访问: http://127.0.0.1:5000
echo 如果可以访问，说明服务器运行正常
echo.

echo [5] 测试局域网访问...
echo 请确保手机连接到同一WiFi网络后访问: http://192.168.43.55:5000
echo.

echo ================================
echo 故障排查建议:
echo ================================
echo 1. 如果防火墙规则不存在: 运行 add_firewall_rule.bat
echo 2. 如果端口未监听: 运行 start.bat 启动服务器
echo 3. 如果手机无法访问:
echo    - 确保手机连接到同一WiFi (192.168.43.x)
echo    - 在手机浏览器中直接输入 http://192.168.43.55:5000
echo    - 尝试使用Chrome或系统自带浏览器，避免使用UC浏览器
echo    - 检查手机是否开启了VPN或代理
echo ================================
pause
