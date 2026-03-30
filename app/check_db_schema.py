import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'lost_found.db')
print(f"数据库路径: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看 lost_item 表结构
print("=== lost_item 表结构 ===")
cursor.execute("PRAGMA table_info(lost_item)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]}: {col[2]} (notnull: {col[3]}, default: {col[4]}, pk: {col[5]})")

print("\n=== user 表结构 ===")
cursor.execute("PRAGMA table_info(user)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]}: {col[2]} (notnull: {col[3]}, default: {col[4]}, pk: {col[5]})")

conn.close()
