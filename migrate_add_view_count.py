"""
迁移脚本：为 lost_item 表添加缺失的列
"""
import os
import sqlite3
from datetime import datetime

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

    if not os.path.exists(db_path):
        print('[!] 数据库文件不存在')
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 获取 lost_item 表的列信息
        cursor.execute("PRAGMA table_info(lost_item)")
        columns = [row[1] for row in cursor.fetchall()]

        # 检查并添加 view_count 列
        if 'view_count' not in columns:
            cursor.execute("ALTER TABLE lost_item ADD COLUMN view_count INTEGER DEFAULT 0")
            print('[√] 添加 view_count 列')
        else:
            print('[i] view_count 列已存在')

        # 检查并添加 like_count 列
        if 'like_count' not in columns:
            cursor.execute("ALTER TABLE lost_item ADD COLUMN like_count INTEGER DEFAULT 0")
            print('[√] 添加 like_count 列')
        else:
            print('[i] like_count 列已存在')

        conn.commit()
        print('[√] 迁移完成')

    except Exception as e:
        conn.rollback()
        print(f'[!] 迁移失败: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
