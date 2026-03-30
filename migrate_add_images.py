import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查images列是否已存在
        cursor.execute("PRAGMA table_info(lost_item)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'images' not in columns:
            cursor.execute('''
                ALTER TABLE lost_item
                ADD COLUMN images TEXT
            ''')
            print('[OK] 成功添加images列到lost_item表')
        else:
            print('[OK] images列已存在，跳过')

        conn.commit()
        print('[OK] 迁移完成')

    except Exception as e:
        print(f'[ERROR] 迁移失败: {e}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
