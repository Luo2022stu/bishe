@echo off
chcp 65001 >nul
echo ========================================
echo 初始化智能存储柜数据
echo ========================================
echo.

python init_lockers.py

echo.
echo ========================================
echo 按任意键退出...
pause >nul
