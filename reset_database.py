"""
重置数据库脚本
删除现有数据库并重新创建
"""
import os
from app import app, db

# 删除现有数据库
if os.path.exists('lost_found.db'):
    os.remove('lost_found.db')
    print('✓ 已删除旧数据库')

# 创建新数据库
with app.app_context():
    db.create_all()
    print('✓ 已创建新数据库')

    # 创建默认管理员账户
    from app import User
    admin = User(username='admin', email='admin@school.edu', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('✓ 已创建默认管理员账户: admin / admin123')

print('\n数据库重置完成！')
