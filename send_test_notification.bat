@echo off
cd /d d:\BiShe
python -c "from send_system_notification import send_system_notification; send_system_notification('校园失物招领系统测试通知', '欢迎使用校园失物招领系统，如有任何问题请随时联系管理员。', '公告')"
pause
