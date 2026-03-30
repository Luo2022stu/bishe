"""
查看 SQLite 数据库中的所有用户
"""
import sqlite3
import os

def view_users():
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'lost_found.db')
    
    print("=" * 60)
    print("SQLite 数据库用户查询")
    print("=" * 60)
    print(f"数据库路径: {db_path}")
    print()
    
    if not os.path.exists(db_path):
        print("错误: 数据库文件不存在！")
        return
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 查询所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("数据库中的表:")
        for table in tables:
            print(f"  - {table[0]}")
        print()
        
        # 查询用户表结构
        if ('user',) in tables:
            cursor.execute("PRAGMA table_info(user);")
            columns = cursor.fetchall()
            print("user 表结构:")
            for col in columns:
                print(f"  {col[1]}: {col[2]}")
            print()
        
        # 查询所有用户
        cursor.execute("SELECT * FROM user;")
        users = cursor.fetchall()
        
        if not users:
            print("暂无用户数据")
        else:
            print(f"共有 {len(users)} 个用户:")
            print()
            
            # 显示表头
            headers = ["ID", "用户名", "邮箱", "手机号", "角色", "创建时间"]
            print("-" * 100)
            print(f"{'ID':<5} {'用户名':<20} {'邮箱':<25} {'手机号':<15} {'角色':<10} {'创建时间':<20}")
            print("-" * 100)
            
            # 显示每个用户
            for user in users:
                print(f"{user[0]:<5} {user[1]:<20} {user[3]:<25} {user[4] if user[4] else 'N/A':<15} {user[5]:<10} {user[6]:<20}")
            
            print("-" * 100)
            
        # 统计用户角色
        cursor.execute("SELECT role, COUNT(*) as count FROM user GROUP BY role;")
        role_stats = cursor.fetchall()
        print()
        print("用户角色统计:")
        for role, count in role_stats:
            role_name = "管理员" if role == "admin" else "普通用户"
            print(f"  {role_name}: {count} 人")
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    finally:
        conn.close()
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    view_users()
