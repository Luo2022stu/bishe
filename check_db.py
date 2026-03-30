import sqlite3

def check_db():
    conn = sqlite3.connect('app/lost_found.db')
    cursor = conn.cursor()

    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"数据库表: {[t[0] for t in tables]}")

    # 检查user表结构
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    print("\nuser表列:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # 检查lost_item表
    cursor.execute("SELECT COUNT(*) FROM lost_item")
    count = cursor.fetchone()[0]
    print(f"\nlost_item表记录数: {count}")

    conn.close()
    print("\n[OK] 数据库检查完成")

if __name__ == '__main__':
    check_db()
