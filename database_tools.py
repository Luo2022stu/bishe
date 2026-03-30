"""
数据库管理工具
提供常用的数据库操作功能
"""
import sqlite3
from app import app, db, User, LostItem

def view_all_users():
    """查看所有用户"""
    conn = sqlite3.connect('lost_found.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, phone, role, created_at FROM user')
    users = cursor.fetchall()
    
    print('\n=== 所有用户 ===')
    print(f'{"ID":<5} {"用户名":<15} {"邮箱":<25} {"手机号":<15} {"角色":<10} {"创建时间"}')
    print('-' * 90)
    for user in users:
        print(f'{user[0]:<5} {user[1]:<15} {user[2]:<25} {user[3] or "N/A":<15} {user[4]:<10} {user[5]}')
    conn.close()

def view_all_items():
    """查看所有失物"""
    conn = sqlite3.connect('lost_found.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, category, location, status, user_id FROM lost_item')
    items = cursor.fetchall()
    
    print('\n=== 所有失物 ===')
    print(f'{"ID":<5} {"标题":<20} {"类别":<10} {"地点":<20} {"状态":<10} {"用户ID"}')
    print('-' * 80)
    for item in items:
        print(f'{item[0]:<5} {item[1]:<20} {item[2]:<10} {item[3]:<20} {item[4]:<10} {item[5] or "N/A"}')
    conn.close()

def delete_user(user_id):
    """删除指定用户"""
    conn = sqlite3.connect('lost_found.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user WHERE id = ?', (user_id,))
    conn.commit()
    print(f'✓ 已删除用户 ID: {user_id}')
    conn.close()

def delete_item(item_id):
    """删除指定失物"""
    conn = sqlite3.connect('lost_found.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lost_item WHERE id = ?', (item_id,))
    conn.commit()
    print(f'✓ 已删除失物 ID: {item_id}')
    conn.close()

def update_user_role(user_id, new_role):
    """更新用户角色"""
    conn = sqlite3.connect('lost_found.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE user SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    print(f'✓ 已更新用户 {user_id} 的角色为: {new_role}')
    conn.close()

def add_column(table_name, column_name, column_type):
    """添加新列（SQLite限制：不能添加UNIQUE列）"""
    conn = sqlite3.connect('lost_found.db')
    cursor = conn.cursor()
    try:
        cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
        conn.commit()
        print(f'✓ 已添加列: {table_name}.{column_name} ({column_type})')
    except Exception as e:
        print(f'✗ 添加列失败: {e}')
    conn.close()

def interactive_menu():
    """交互式菜单"""
    while True:
        print('\n' + '='*50)
        print('数据库管理工具')
        print('='*50)
        print('1. 查看所有用户')
        print('2. 查看所有失物')
        print('3. 删除用户')
        print('4. 删除失物')
        print('5. 更新用户角色')
        print('6. 添加新列')
        print('0. 退出')
        
        choice = input('\n请选择操作 (0-6): ').strip()
        
        if choice == '1':
            view_all_users()
        elif choice == '2':
            view_all_items()
        elif choice == '3':
            user_id = input('请输入要删除的用户ID: ').strip()
            if user_id.isdigit():
                delete_user(int(user_id))
            else:
                print('✗ 无效的用户ID')
        elif choice == '4':
            item_id = input('请输入要删除的失物ID: ').strip()
            if item_id.isdigit():
                delete_item(int(item_id))
            else:
                print('✗ 无效的失物ID')
        elif choice == '5':
            user_id = input('请输入用户ID: ').strip()
            new_role = input('请输入新角色 (user/admin): ').strip()
            if user_id.isdigit() and new_role in ['user', 'admin']:
                update_user_role(int(user_id), new_role)
            else:
                print('✗ 无效的输入')
        elif choice == '6':
            table_name = input('请输入表名 (user/lost_item): ').strip()
            column_name = input('请输入列名: ').strip()
            column_type = input('请输入列类型 (VARCHAR(50)/INTEGER/TEXT): ').strip()
            add_column(table_name, column_name, column_type)
        elif choice == '0':
            print('再见！')
            break
        else:
            print('✗ 无效的选择')

if __name__ == '__main__':
    interactive_menu()
