from app import app, db, User, LostItem
import os

def check_database():
    with app.app_context():
        print("=" * 60)
        print("数据库检查报告")
        print("=" * 60)
        
        # 检查数据库文件是否存在
        db_type = os.getenv('DATABASE_TYPE', 'sqlite')
        print(f"\n数据库类型: {db_type}")
        
        if db_type == 'sqlite':
            db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lost_found.db')
            print(f"数据库路径: {db_path}")
            if os.path.exists(db_path):
                print(f"✓ 数据库文件存在")
                print(f"  文件大小: {os.path.getsize(db_path)} 字节")
            else:
                print(f"✗ 数据库文件不存在！")
                print("\n建议：运行以下命令创建数据库")
                print("  with app.app_context():")
                print("      db.create_all()")
                return
        
        # 检查表结构
        print("\n" + "-" * 60)
        print("表结构检查")
        print("-" * 60)
        
        tables = db.metadata.tables.keys()
        print(f"已创建的表: {list(tables)}")
        
        # 检查用户表
        print("\n" + "-" * 60)
        print("用户表 (user) 数据")
        print("-" * 60)
        users = User.query.all()
        print(f"用户总数: {len(users)}")
        
        if users:
            print("\n用户列表:")
            for user in users:
                print(f"  ID: {user.id}")
                print(f"  用户名: {user.username}")
                print(f"  邮箱: {user.email}")
                print(f"  手机号: {user.phone}")
                print(f"  角色: {user.role}")
                print(f"  创建时间: {user.created_at}")
                print()
        else:
            print("  暂无用户数据")
        
        # 检查物品表
        print("-" * 60)
        print("物品表 (lost_item) 数据")
        print("-" * 60)
        items = LostItem.query.all()
        print(f"物品总数: {len(items)}")
        
        if items:
            print("\n物品列表:")
            for item in items:
                print(f"  ID: {item.id}")
                print(f"  类型: {item.type}")
                print(f"  标题: {item.title}")
                print(f"  类别: {item.category}")
                print(f"  状态: {item.status}")
                print()
        else:
            print("  暂无物品数据")
        
        print("=" * 60)
        print("检查完成")
        print("=" * 60)

if __name__ == '__main__':
    check_database()
