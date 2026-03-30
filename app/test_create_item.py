"""
测试创建物品，捕获详细错误信息
"""
import sys
sys.path.insert(0, 'd:\\BiShe\\app')

from app import app, db, LostItem, User

print("=== 测试创建物品 ===\n")

with app.app_context():
    try:
        # 获取一个用户
        user = User.query.first()
        if not user:
            print("错误: 数据库中没有用户")
            print("请先创建用户（注册或使用默认管理员）")
            sys.exit(1)

        print(f"使用用户: {user.username} (ID: {user.id})")

        # 尝试创建物品
        print("\n尝试创建物品...")
        new_item = LostItem(
            type='found',
            title='测试物品',
            description='这是一个测试',
            category='其他',
            location='测试地点',
            contact='13800138000',
            user_id=user.id
        )

        print(f"物品对象创建成功: {new_item.title}")

        db.session.add(new_item)
        print("已添加到session")

        db.session.commit()
        print("数据库提交成功!")
        print(f"物品ID: {new_item.id}")

    except Exception as e:
        db.session.rollback()
        print(f"\n错误: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print(f"\n详细错误:")
        import traceback
        traceback.print_exc()

print("\n" + "="*50)
print("\n如果测试成功，说明数据库和模型都正常，问题可能在API路由。")
