"""
数据库迁移脚本
添加 type, latitude, longitude 字段到 lost_item 表
"""
import sqlite3
import os

def migrate_sqlite():
    """迁移 SQLite 数据库"""
    db_path = 'lost_found.db'

    if not os.path.exists(db_path):
        print('数据库文件不存在，无需迁移')
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lost_item'")
        if not cursor.fetchone():
            print('lost_item 表不存在，无需迁移')
            return

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(lost_item)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'type' in columns and 'latitude' in columns and 'longitude' in columns:
            print('字段已存在，无需迁移')
            return

        # 备份数据
        print('正在备份数据...')
        cursor.execute('SELECT * FROM lost_item')
        old_data = cursor.fetchall()

        # 获取旧表结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='lost_item'")
        old_table_sql = cursor.fetchone()[0]

        # 创建新表
        print('正在创建新表...')
        new_table_sql = old_table_sql.replace(
            'CREATE TABLE lost_item',
            'CREATE TABLE lost_item_new'
        )

        # 在新表SQL中添加新字段
        new_table_sql = new_table_sql.replace(
            'status VARCHAR(20)',
            'type VARCHAR(20) DEFAULT \'found\', status VARCHAR(20)'
        )
        new_table_sql = new_table_sql.replace(
            'location VARCHAR(100)',
            'location VARCHAR(100), latitude FLOAT, longitude FLOAT'
        )

        cursor.execute(new_table_sql)

        # 迁移数据
        print('正在迁移数据...')
        for row in old_data:
            # 旧表没有新字段，使用默认值
            new_row = list(row)
            # 在适当位置插入新字段
            # 假设旧表结构：id, title, description, category, location, contact, status, user_id, created_at, updated_at
            # 新表结构：id, type, title, description, category, location, latitude, longitude, contact, status, user_id, created_at, updated_at
            new_row.insert(1, 'found')  # type
            new_row.insert(6, None)  # latitude
            new_row.insert(7, None)  # longitude

            placeholders = ', '.join(['?' for _ in range(len(new_row))])
            cursor.execute(f'INSERT INTO lost_item_new VALUES ({placeholders})', new_row)

        # 删除旧表
        print('正在删除旧表...')
        cursor.execute('DROP TABLE lost_item')

        # 重命名新表
        print('正在重命名新表...')
        cursor.execute('ALTER TABLE lost_item_new RENAME TO lost_item')

        conn.commit()
        print('✓ 数据库迁移成功！')

    except Exception as e:
        print(f'✗ 迁移失败: {e}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print('开始数据库迁移...\n')
    migrate_sqlite()
    print('\n迁移完成！')
