#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库表结构"""

import sqlite3
import os

# 数据库文件路径
db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

def check_table_structure():
    """检查所有表的结构"""

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print('数据库表结构:')
        print('=' * 60)

        for table in tables:
            table_name = table[0]
            print(f'\n表名: {table_name}')
            print('-' * 60)

            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            print('{:<20} {:<15} {:<10} {:<10}'.format(
                '列名', '类型', '非空', '默认值'))
            print('-' * 60)

            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = '是' if col[3] else '否'
                default = str(col[4]) if col[4] is not None else ''

                print('{:<20} {:<15} {:<10} {:<10}'.format(
                    col_name, col_type, not_null, default))

    except sqlite3.Error as e:
        print(f'[×] 数据库错误: {e}')
    except Exception as e:
        print(f'[×] 检查失败: {e}')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_table_structure()
