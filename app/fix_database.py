import sqlite3
import os

# 备份旧数据库
if os.path.exists('lost_found.db'):
    os.rename('lost_found.db', 'lost_found.db.backup')
    print('已备份旧数据库为 lost_found.db.backup')

# 创建新数据库
from app import app, db

with app.app_context():
    db.create_all()
    print('新数据库创建成功')

# 迁移旧数据
old_conn = sqlite3.connect('lost_found.db.backup')
new_conn = sqlite3.connect('lost_found.db')

old_cursor = old_conn.cursor()
new_cursor = new_conn.cursor()

# 迁移user表数据
old_cursor.execute('SELECT * FROM user')
users = old_cursor.fetchall()

for user in users:
    # user表结构: id, username, password, email, role, created_at
    # 新表结构: id, username, password, email, phone, role, created_at
    new_cursor.execute('''
        INSERT INTO user (id, username, password, email, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user[0], user[1], user[2], user[3], user[4], user[5]))

# 迁移lost_item表数据
old_cursor.execute('SELECT * FROM lost_item')
items = old_cursor.fetchall()

for item in items:
    new_cursor.execute('''
        INSERT INTO lost_item (id, title, description, category, location, contact, status, user_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', item)

new_conn.commit()
old_conn.close()
new_conn.close()

print('数据迁移完成！')
print('旧数据库备份文件: lost_found.db.backup')
