import sqlite3

conn = sqlite3.connect('lost_found.db')
cursor = conn.cursor()

# 查看所有表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('数据库中的表:', tables)

# 查看user表结构
if ('user',) in tables:
    cursor.execute('PRAGMA table_info(user)')
    user_columns = cursor.fetchall()
    print('\nUser表结构:')
    for col in user_columns:
        print(f'  {col[1]}: {col[2]} (unique={col[5]})')
else:
    print('\nUser表不存在')

# 查看lost_item表结构
if ('lost_item',) in tables:
    cursor.execute('PRAGMA table_info(lost_item)')
    item_columns = cursor.fetchall()
    print('\nLostItem表结构:')
    for col in item_columns:
        print(f'  {col[1]}: {col[2]}')

conn.close()
