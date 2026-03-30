#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""添加 credit_score 列到 user 表的迁移脚本"""

import sqlite3
import os

# 数据库文件路径
db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

def migrate_add_credit_score():
    """添加 credit_score 列到 user 表"""

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'credit_score' in columns:
            print('[√] credit_score 列已存在，跳过迁移')
            return

        # 添加 credit_score 列，默认值为 80
        cursor.execute("ALTER TABLE user ADD COLUMN credit_score INTEGER DEFAULT 80")
        conn.commit()

        # 验证列是否添加成功
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'credit_score' in columns:
            print('[√] 成功添加 credit_score 列到 user 表')
        else:
            print('[×] 添加 credit_score 列失败')

        # 更新现有用户的 credit_score
        cursor.execute("UPDATE user SET credit_score = 80 WHERE credit_score IS NULL")
        conn.commit()

        print(f'[√] 已更新 {cursor.rowcount} 个用户的 credit_score')

    except sqlite3.Error as e:
        print(f'[×] 数据库错误: {e}')
    except Exception as e:
        print(f'[×] 迁移失败: {e}')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrate_add_credit_score()
