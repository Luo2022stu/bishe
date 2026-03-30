import sqlite3
import os
import sys
import io

# 修复Windows控制台编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db_path = os.path.join(os.path.dirname(__file__), 'lost_found.db')
print(f"数据库路径: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 修改 longitude 字段允许为空
    print("修改 longitude 字段允许为 NULL...")
    cursor.execute("ALTER TABLE lost_item RENAME TO lost_item_old")
    cursor.execute("""
        CREATE TABLE lost_item (
            id INTEGER PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(50) NOT NULL,
            location VARCHAR(100),
            latitude FLOAT,
            longitude FLOAT,
            contact VARCHAR(50) NOT NULL,
            type VARCHAR(20) DEFAULT 'found',
            status VARCHAR(20),
            user_id INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    """)
    cursor.execute("""
        INSERT INTO lost_item
        SELECT id, title, description, category, location, latitude,
               IFNULL(longitude, NULL), contact, type, status, user_id,
               created_at, updated_at
        FROM lost_item_old
    """)
    cursor.execute("DROP TABLE lost_item_old")
    conn.commit()
    print("数据库表结构已修复！")
    print("longitude 字段现在允许为 NULL")

    # 验证修改
    cursor.execute("PRAGMA table_info(lost_item)")
    columns = cursor.fetchall()
    print("\nlost_item 表结构:")
    for col in columns:
        print(f"  {col[1]}: {col[2]} (notnull: {col[3]})")

except Exception as e:
    print(f"错误: {e}")
    conn.rollback()
    print("\n如果修复失败，请运行重置数据库:")
    print("  python d:\\BiShe\\app\\reset_db.py")
finally:
    conn.close()
