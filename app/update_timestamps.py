import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, LostItem, Post, Comment
from datetime import datetime, timezone, timedelta

with app.app_context():
    print("=== 更新时间戳 ===\n")

    # 更新 LostItem
    print("更新 lost_item 表...")
    items = LostItem.query.all()
    print(f"  找到 {len(items)} 条记录")

    now = datetime.now(timezone.utc)
    for i, item in enumerate(items, 1):
        # 按创建顺序设置时间（从最早开始）
        hours_ago = len(items) - i
        item.created_at = now - timedelta(hours=hours_ago)
        item.updated_at = item.created_at
        if i % 10 == 0:
            print(f"  已更新 {i} 条...")

    db.session.commit()
    print("  完成!\n")

    # 更新 Post
    print("更新 post 表...")
    posts = Post.query.all()
    print(f"  找到 {len(posts)} 条记录")

    for i, post in enumerate(posts, 1):
        hours_ago = len(posts) - i
        post.created_at = now - timedelta(hours=hours_ago)
        post.updated_at = post.created_at
        if i % 10 == 0:
            print(f"  已更新 {i} 条...")

    db.session.commit()
    print("  完成!\n")

    # 更新 Comment
    print("更新 comment 表...")
    comments = Comment.query.all()
    print(f"  找到 {len(comments)} 条记录")

    for i, comment in enumerate(comments, 1):
        hours_ago = len(comments) - i
        comment.created_at = now - timedelta(hours=hours_ago)
        if i % 10 == 0:
            print(f"  已更新 {i} 条...")

    db.session.commit()
    print("  完成!\n")

    print("所有时间戳已更新!")
    print("发布时间现在从发布时开始计算")
