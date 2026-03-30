import sqlite3
import os

def check_users_and_notifications():
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查询所有用户及其手机号
        print("=" * 100)
        print("所有用户信息：")
        print("=" * 100)
        cursor.execute("SELECT id, username, phone, email FROM user")
        users = cursor.fetchall()

        for user_id, username, phone, email in users:
            print(f"ID: {user_id}, 用户名: {username}, 手机号: {phone}, 邮箱: {email}")

        # 查询所有智能柜物品
        print("\n" + "=" * 100)
        print("智能柜物品记录：")
        print("=" * 100)
        cursor.execute("""
            SELECT li.id, li.item_name, li.pickup_code, li.recipient_phone, li.sender_id
            FROM locker_item li
            ORDER BY li.id DESC LIMIT 5
        """)
        items = cursor.fetchall()

        for item_id, item_name, pickup_code, recipient_phone, sender_id in items:
            print(f"物品ID: {item_id}, 名称: {item_name}, 取件码: {pickup_code}, 接收人手机: {recipient_phone}, 存入者ID: {sender_id}")

        # 查询所有通知
        print("\n" + "=" * 100)
        print("所有通知记录：")
        print("=" * 100)
        cursor.execute("""
            SELECT un.id, un.user_id, u.username, un.type, un.title, un.content, un.is_read, un.created_at
            FROM user_notification un
            LEFT JOIN user u ON un.user_id = u.id
            ORDER BY un.id DESC LIMIT 10
        """)
        notifications = cursor.fetchall()

        if notifications:
            for notif_id, user_id, username, notif_type, title, content, is_read, created_at in notifications:
                status = "已读" if is_read else "未读"
                print(f"通知ID: {notif_id}, 用户: {username}(ID:{user_id}), 类型: {notif_type}, 状态: {status}")
                print(f"  标题: {title}")
                print(f"  内容: {content}")
                print(f"  时间: {created_at}")
                print("-" * 100)
        else:
            print("没有找到任何通知记录")

        conn.close()
        print("\n检查完成！")

    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        import traceback
        traceback.print_exc()
        conn.close()

if __name__ == '__main__':
    check_users_and_notifications()
