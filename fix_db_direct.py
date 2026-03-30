"""直接修复数据库表结构 - 不需要删除文件"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

def fix_database():
    print("[修复] 开始修复数据库表结构...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查user表是否有credit_score字段
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"[修复] 当前user表字段: {column_names}")

        if 'credit_score' not in column_names:
            print("[修复] 添加 credit_score 字段...")
            cursor.execute("ALTER TABLE user ADD COLUMN credit_score INTEGER DEFAULT 100")
            print("[修复] credit_score 字段已添加")

        if 'name' not in column_names:
            print("[修复] 添加 name 字段...")
            cursor.execute("ALTER TABLE user ADD COLUMN name VARCHAR(50)")
            print("[修复] name 字段已添加")

        if 'is_muted' not in column_names:
            print("[修复] 添加 is_muted 字段...")
            cursor.execute("ALTER TABLE user ADD COLUMN is_muted BOOLEAN DEFAULT 0")
            print("[修复] is_muted 字段已添加")

        if 'muted_until' not in column_names:
            print("[修复] 添加 muted_until 字段...")
            cursor.execute("ALTER TABLE user ADD COLUMN muted_until DATETIME")
            print("[修复] muted_until 字段已添加")

        # 检查lost_item表是否有必要的字段
        cursor.execute("PRAGMA table_info(lost_item)")
        lost_item_columns = cursor.fetchall()
        lost_item_column_names = [col[1] for col in lost_item_columns]

        print(f"[修复] 当前lost_item表字段: {lost_item_column_names}")

        if 'view_count' not in lost_item_column_names:
            print("[修复] 添加 view_count 字段...")
            cursor.execute("ALTER TABLE lost_item ADD COLUMN view_count INTEGER DEFAULT 0")
            print("[修复] view_count 字段已添加")

        if 'like_count' not in lost_item_column_names:
            print("[修复] 添加 like_count 字段...")
            cursor.execute("ALTER TABLE lost_item ADD COLUMN like_count INTEGER DEFAULT 0")
            print("[修复] like_count 字段已添加")

        if 'images' not in lost_item_column_names:
            print("[修复] 添加 images 字段...")
            cursor.execute("ALTER TABLE lost_item ADD COLUMN images TEXT")
            print("[修复] images 字段已添加")

        if 'is_hidden' not in lost_item_column_names:
            print("[修复] 添加 is_hidden 字段...")
            cursor.execute("ALTER TABLE lost_item ADD COLUMN is_hidden BOOLEAN DEFAULT 0")
            print("[修复] is_hidden 字段已添加")

        if 'hidden_until' not in lost_item_column_names:
            print("[修复] 添加 hidden_until 字段...")
            cursor.execute("ALTER TABLE lost_item ADD COLUMN hidden_until DATETIME")
            print("[修复] hidden_until 字段已添加")

        if 'latitude' not in lost_item_column_names:
            print("[修复] 添加 latitude 字段...")
            cursor.execute("ALTER TABLE lost_item ADD COLUMN latitude FLOAT")
            print("[修复] latitude 字段已添加")

        if 'longitude' not in lost_item_column_names:
            print("[修复] 添加 longitude 字段...")
            cursor.execute("ALTER TABLE lost_item ADD COLUMN longitude FLOAT")
            print("[修复] longitude 字段已添加")

        conn.commit()
        print("\n[OK] 数据库修复完成！")
        print("[提示] 请运行 start.bat 重启服务器")

    except Exception as e:
        print(f"[错误] 修复失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_database()
