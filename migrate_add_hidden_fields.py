"""
数据库迁移脚本：添加is_hidden和hidden_until字段到LostItem和Post模型
运行此脚本以更新现有数据库结构
"""
import os
import sys
from datetime import datetime, timezone

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import app, db, LostItem, Post

def migrate():
    with app.app_context():
        print("开始数据库迁移...")
        print("添加 is_hidden 和 hidden_until 字段到 LostItem 和 Post 表")

        try:
            # 使用SQLAlchemy执行原始SQL来添加字段
            # 这适用于SQLite、MySQL、PostgreSQL和SQL Server

            # 为LostItem表添加字段
            print("\n正在为 LostItem 表添加字段...")
            try:
                # 检查字段是否已存在
                inspector = db.inspect(db.engine)
                lostitem_columns = [col['name'] for col in inspector.get_columns('lost_item')]

                if 'is_hidden' not in lostitem_columns:
                    db.session.execute(db.text("ALTER TABLE lost_item ADD COLUMN is_hidden BOOLEAN DEFAULT 0"))
                    print("  [OK] 添加 is_hidden 字段")
                else:
                    print("  [-] is_hidden 字段已存在，跳过")

                if 'hidden_until' not in lostitem_columns:
                    db.session.execute(db.text("ALTER TABLE lost_item ADD COLUMN hidden_until DATETIME"))
                    print("  [OK] 添加 hidden_until 字段")
                else:
                    print("  [-] hidden_until 字段已存在，跳过")

            except Exception as e:
                print(f"  [WARN] 为 LostItem 表添加字段时出错: {e}")

            # 为Post表添加字段
            print("\n正在为 Post 表添加字段...")
            try:
                # 检查字段是否已存在
                inspector = db.inspect(db.engine)
                post_columns = [col['name'] for col in inspector.get_columns('post')]

                if 'is_hidden' not in post_columns:
                    db.session.execute(db.text("ALTER TABLE post ADD COLUMN is_hidden BOOLEAN DEFAULT 0"))
                    print("  [OK] 添加 is_hidden 字段")
                else:
                    print("  [-] is_hidden 字段已存在，跳过")

                if 'hidden_until' not in post_columns:
                    db.session.execute(db.text("ALTER TABLE post ADD COLUMN hidden_until DATETIME"))
                    print("  [OK] 添加 hidden_until 字段")
                else:
                    print("  [-] hidden_until 字段已存在，跳过")

            except Exception as e:
                print(f"  [WARN] 为 Post 表添加字段时出错: {e}")

            db.session.commit()
            print("\n数据库迁移完成！")
            print("\n说明：")
            print("- 被举报的内容现在会被隐藏3天而不是直接删除")
            print("- 被隐藏的内容在3天后会自动恢复显示")
            print("- 用户会收到隐藏通知而不是删除通知")

        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
