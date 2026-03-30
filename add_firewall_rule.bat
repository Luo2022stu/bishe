@echo off
echo 正在添加防火墙规则...
netsh advfirewall firewall add rule name="Python Flask Server 5000" dir=in action=allow protocol=TCP localport=5000
echo 防火墙规则已添加！
echo.
echo 请在手机浏览器中访问：http://192.168.43.55:5000
echo.
pause
