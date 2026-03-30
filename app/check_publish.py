"""
检查发布功能
"""
import sys
import os

# 添加app目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, LostItem, User

with app.app_context():
    print("=== 数据库状态检查 ===\n")

    # 检查用户数量
    user_count = User.query.count()
    print(f"用户数量: {user_count}")
    if user_count > 0:
        users = User.query.all()
        print("用户列表:")
        for user in users:
            print(f"  - ID: {user.id}, 用户名: {user.username}, 角色: {user.role}")
    else:
        print("  ⚠️ 没有用户！请先注册或使用默认管理员账户 (admin/admin123)")

    print("\n" + "="*50 + "\n")

    # 检查物品数量
    item_count = LostItem.query.count()
    print(f"物品数量: {item_count}")
    if item_count > 0:
        print("最近的物品:")
        items = LostItem.query.order_by(LostItem.created_at.desc()).limit(5).all()
        for item in items:
            print(f"  - ID: {item.id}, 类型: {item.type}, 标题: {item.title}, 用户ID: {item.user_id}")
    else:
        print("  没有发布任何物品")

    print("\n" + "="*50)
    print("\n测试数据格式:")
    test_data = {
        'type': 'found',
        'title': '测试物品',
        'description': '这是一个测试',
        'category': '其他',
        'location': '测试地点',
        'contact': '13800138000',
        'latitude': None,
        'longitude': None
    }
    print(f"  预期的数据格式: {test_data}")

print("\n提示: 如果数据库为空，请先访问登录页面创建账户或使用默认管理员账户")
