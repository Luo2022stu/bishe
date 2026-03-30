#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查帖子图片数据"""

import sqlite3
import os

# 数据库文件路径
db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

def check_post_images():
    """检查帖子的图片数据"""

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询有图片的帖子
        cursor.execute("SELECT id, title, image FROM post WHERE image IS NOT NULL AND image != '' LIMIT 5")
        posts = cursor.fetchall()

        print('帖子图片数据检查:')
        print('=' * 80)

        for post in posts:
            post_id, title, image = post
            print(f'\n帖子ID: {post_id}')
            print(f'标题: {title}')
            print(f'图片数据长度: {len(image) if image else 0} 字符')

            if image:
                # 检查是否是base64格式
                if image.startswith('data:image'):
                    print('✓ 格式: base64 data URL')
                else:
                    print('✗ 格式: 纯base64（可能需要添加前缀）')

                # 显示前50个字符
                print(f'前50字符: {image[:50]}...')

    except sqlite3.Error as e:
        print(f'[×] 数据库错误: {e}')
    except Exception as e:
        print(f'[×] 检查失败: {e}')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_post_images()
