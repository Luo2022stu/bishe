"""
直接修改数据库的示例脚本
"""
from app import app, db, User, LostItem

def example_operations():
    """示例操作"""
    with app.app_context():
        # 示例1: 查询所有用户
        print('\n=== 查询所有用户 ===')
        users = User.query.all()
        for user in users:
            print(f'ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}')

        # 示例2: 查询特定用户
        print('\n=== 查询特定用户 ===')
        user = User.query.filter_by(username='admin').first()
        if user:
            print(f'找到管理员: {user.username}, 邮箱: {user.email}')

        # 示例3: 更新用户信息
        print('\n=== 更新用户信息 ===')
        user = User.query.filter_by(username='admin').first()
        if user:
            user.email = 'new_admin@school.edu'
            db.session.commit()
            print(f'已更新管理员邮箱为: {user.email}')

        # 示例4: 创建新用户
        print('\n=== 创建新用户 ===')
        new_user = User(username='testuser', email='test@example.com', phone='13800138000')
        new_user.set_password('password123')
        db.session.add(new_user)
        db.session.commit()
        print(f'已创建新用户: {new_user.username}')

        # 示例5: 删除用户
        print('\n=== 删除用户 ===')
        user_to_delete = User.query.filter_by(username='testuser').first()
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            print(f'已删除用户: {user_to_delete.username}')

        # 示例6: 查询所有失物
        print('\n=== 查询所有失物 ===')
        items = LostItem.query.all()
        for item in items:
            print(f'ID: {item.id}, 标题: {item.title}, 状态: {item.status}')

        # 示例7: 更新失物状态
        print('\n=== 更新失物状态 ===')
        item = LostItem.query.first()
        if item:
            item.status = 'returned'
            db.session.commit()
            print(f'已更新失物状态: {item.title} -> {item.status}')

        # 示例8: 删除失物
        print('\n=== 删除失物 ===')
        item_to_delete = LostItem.query.first()
        if item_to_delete:
            db.session.delete(item_to_delete)
            db.session.commit()
            print(f'已删除失物: {item_to_delete.title}')

if __name__ == '__main__':
    example_operations()
