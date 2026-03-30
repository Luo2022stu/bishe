@echo off
echo ================================
echo 校园失物招领系统 - USB调试模式配置
echo ================================
echo.
echo 正在获取网络配置信息...
echo.

ipconfig | findstr /i "IPv4"

echo.
echo ================================
echo 手机端配置步骤（华为 nova 8SE）:
echo ================================
echo 1. 进入「设置」→「关于手机」
echo 2. 连续点击「EMUI版本」或「HarmonyOS版本」7次
echo 3. 返回「设置」→「系统和更新」→「开发人员选项」
echo 4. 开启「USB调试」和「USB安装」
echo 5. 用USB数据线连接手机和电脑
echo 6. 手机弹出提示时，勾选「始终允许」并点击「确定」
echo.
echo ================================
echo 电脑端配置步骤:
echo ================================
echo 1. 确保USB数据线连接正常
echo 2. 手机已授权USB调试
echo 3. 运行此脚本后会显示电脑IP地址
echo 4. 在手机浏览器中访问: http://192.168.43.55:5000
echo.
echo ================================
echo 注意事项:
echo ================================
echo - 确保电脑和手机在同一网络
echo - 如遇连接问题，请检查防火墙设置
echo - 运行 add_firewall_rule.bat 添加防火墙规则
echo.
echo 按任意键启动服务器...
pause > nul

cd /d "%~dp0app"
python app.py
