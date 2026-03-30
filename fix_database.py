"""修复数据库表结构问题"""
import sys
import os
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import app, db

def fix_database():
    """修复数据库表结构"""
    print("[修复] 开始修复数据库...")

    # 备份数据库
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')
    backup_path = db_path + '.backup'

    if os.path.exists(db_path):
        print(f"[修复] 备份数据库到: {backup_path}")
        shutil.copy2(db_path, backup_path)
        print("[修复] 数据库备份完成")

    # 删除旧数据库
    if os.path.exists(db_path):
        print(f"[修复] 删除旧数据库: {db_path}")
        os.remove(db_path)

    # 重新创建数据库
    print("[修复] 重新创建数据库...")
    with app.app_context():
        db.create_all()

        # 创建默认管理员账户
        from app import User
        admin = User(username='admin', email='admin@school.edu', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("[修复] 默认管理员账户已创建: admin / admin123")

    print("[OK] 数据库修复完成！")
    print("[提示] 请运行 start.bat 重启服务器")

if __name__ == '__main__':
    fix_database()
