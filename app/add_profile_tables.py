"""
数据库迁移脚本：添加浏览历史和用户设置表
"""

from app import app, db, BrowseHistory, UserSettings

def migrate():
    with app.app_context():
        # 创建新表
        print("正在创建浏览历史表...")
        db.create_all()

        # 检查表是否创建成功
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()

        if 'browse_history' in tables:
            print("✓ 浏览历史表创建成功")
        else:
            print("✗ 浏览历史表创建失败")

        if 'user_settings' in tables:
            print("✓ 用户设置表创建成功")
        else:
            print("✗ 用户设置表创建失败")

        print("\n迁移完成！")

if __name__ == '__main__':
    migrate()
