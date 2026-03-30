import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, LostItem, User, Post, Comment, PostLike

with app.app_context():
    # 删除所有表
    print("删除旧表...")
    db.drop_all()

    # 重新创建表
    print("创建新表...")
    db.create_all()

    # 创建默认管理员
    print("\n创建默认管理员账户...")
    admin = User(
        username='admin',
        email='admin@school.edu',
        role='admin'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()

    print("\n数据库重置完成！")
    print("默认管理员: admin / admin123")
