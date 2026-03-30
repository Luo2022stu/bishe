from app import app, db, User
import hashlib

with app.app_context():
    # 检查管理员是否已存在
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print('管理员账户已存在')
        print(f'用户名: {admin.username}')
        print(f'角色: {admin.role}')
    else:
        # 创建管理员账户
        admin = User(
            username='admin',
            email='admin@example.com',
            phone='',
            role='admin'
        )
        # 设置密码为: admin123
        admin.password = hashlib.sha256('admin123'.encode()).hexdigest()
        
        db.session.add(admin)
        db.session.commit()
        
        print('✓ 管理员账户创建成功')
        print('用户名: admin')
        print('密码: admin123')
        print('角色: admin')
        print('\n请在登录后立即修改密码！')
