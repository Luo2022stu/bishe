"""
数据库迁移脚本：为 LostItem 表添加 view_count 和 like_count 字段
"""
import sys
import os

# 添加app目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import app, db, LostItem

def migrate():
    """执行数据库迁移"""
    with app.app_context():
        try:
            # 创建新字段（如果不存在）
            db.engine.execute(db.text("ALTER TABLE lost_item ADD COLUMN view_count INTEGER DEFAULT 0"))
            print("[√] 已添加 view_count 字段")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("[!] view_count 字段已存在，跳过")
            else:
                print(f"[×] 添加 view_count 字段失败: {e}")

        try:
            db.engine.execute(db.text("ALTER TABLE lost_item ADD COLUMN like_count INTEGER DEFAULT 0"))
            print("[√] 已添加 like_count 字段")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("[!] like_count 字段已存在，跳过")
            else:
                print(f"[×] 添加 like_count 字段失败: {e}")

        try:
            # 创建 ItemLike 表（如果不存在）
            db.create_all()
            print("[√] 数据库表结构已更新")

            # 检查 ItemLike 表是否创建成功
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'item_like' in tables:
                print("[√] item_like 表已创建")
            else:
                print("[!] item_like 表未找到")

            # 检查 lost_item 表是否有新字段
            lost_item_columns = [col['name'] for col in inspector.get_columns('lost_item')]
            if 'view_count' in lost_item_columns:
                print("[√] view_count 字段存在于 lost_item 表中")
            else:
                print("[!] view_count 字段不存在于 lost_item 表中")

            if 'like_count' in lost_item_columns:
                print("[√] like_count 字段存在于 lost_item 表中")
            else:
                print("[!] like_count 字段不存在于 lost_item 表中")

        except Exception as e:
            print(f"[×] 数据库迁移失败: {e}")

        print("\n[✓] 数据库迁移完成！")

if __name__ == '__main__':
    migrate()
