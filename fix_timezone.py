#!/usr/bin/env python
"""
修复数据库中hidden_until字段的时区问题
将所有naive datetime转换为aware datetime
"""

from datetime import datetime, timezone
import sys
import os

# 添加app目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import app, db, Post, LostItem, FoundItem

def fix_hidden_until_timezone():
    """修复hidden_until字段的时区"""
    with app.app_context():
        print("开始修复hidden_until字段的时区...")

        # 修复Post表
        posts = Post.query.filter(Post.hidden_until.isnot(None)).all()
        for post in posts:
            if post.hidden_until.tzinfo is None:
                print(f"修复Post {post.id}: {post.hidden_until} -> ", end='')
                post.hidden_until = post.hidden_until.replace(tzinfo=timezone.utc)
                print(f"{post.hidden_until}")
            else:
                print(f"Post {post.id}: 已有时区信息，跳过")

        # 修复LostItem表
        lost_items = LostItem.query.filter(LostItem.hidden_until.isnot(None)).all()
        for item in lost_items:
            if item.hidden_until.tzinfo is None:
                print(f"修复LostItem {item.id}: {item.hidden_until} -> ", end='')
                item.hidden_until = item.hidden_until.replace(tzinfo=timezone.utc)
                print(f"{item.hidden_until}")
            else:
                print(f"LostItem {item.id}: 已有时区信息，跳过")

        # 修复FoundItem表
        found_items = FoundItem.query.filter(FoundItem.hidden_until.isnot(None)).all()
        for item in found_items:
            if item.hidden_until.tzinfo is None:
                print(f"修复FoundItem {item.id}: {item.hidden_until} -> ", end='')
                item.hidden_until = item.hidden_until.replace(tzinfo=timezone.utc)
                print(f"{item.hidden_until}")
            else:
                print(f"FoundItem {item.id}: 已有时区信息，跳过")

        try:
            db.session.commit()
            print("\n✓ 数据库修复完成！")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ 数据库修复失败: {e}")
            raise

if __name__ == '__main__':
    fix_hidden_until_timezone()
