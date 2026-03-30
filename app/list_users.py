from app import app, db, User

with app.app_context():
    users = User.query.all()
    print('用户列表:')
    for u in users:
        print(f'  ID: {u.id}, 用户名: {u.username}, 邮箱: {u.email}, 角色: {u.role}')
