import sqlite3
import os

def check_mike_notifications():
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查询Mike用户的信息
        print("=" * 100)
        print("Mike用户信息：")
        print("=" * 100)
        cursor.execute("SELECT id, username, phone, email FROM user WHERE username = 'Mike'")
        mike = cursor.fetchone()

        if mike:
            user_id, username, phone, email = mike
            print(f"ID: {user_id}, 用户名: {username}, 手机号: {phone}, 邮箱: {email}")
        else:
            print("未找到Mike用户")
            conn.close()
            return

        # 查询Mike的所有通知
        print("\n" + "=" * 100)
        print(f"Mike的所有通知：")
        print("=" * 100)
        cursor.execute("""
            SELECT un.id, un.user_id, un.type, un.title, un.content, un.is_read, un.created_at
            FROM user_notification un
            WHERE un.user_id = ?
            ORDER BY un.id DESC
        """, (user_id,))
        notifications = cursor.fetchall()

        if notifications:
            for notif_id, user_id, notif_type, title, content, is_read, created_at in notifications:
                status = "已读" if is_read else "未读"
                print(f"\n通知ID: {notif_id}")
                print(f"类型: {notif_type}")
                print(f"状态: {status}")
                print(f"标题: {title}")
                print(f"内容: {content}")
                print(f"时间: {created_at}")
                print("-" * 100)
        else:
            print("Mike没有收到任何通知")

        # 查询所有智能柜物品，看看Mike是否是接收人
        print("\n" + "=" * 100)
        print("所有智能柜物品（检查Mike是否为接收人）：")
        print("=" * 100)
        cursor.execute("""
            SELECT li.id, li.item_name, li.pickup_code, li.recipient_phone, li.status,
                   u.username as sender_name
            FROM locker_item li
            LEFT JOIN user u ON li.sender_id = u.id
            ORDER BY li.id DESC
        """)
        items = cursor.fetchall()

        for item_id, item_name, pickup_code, recipient_phone, status, sender_name in items:
            is_for_mike = "是" if recipient_phone == phone else "否"
            print(f"物品ID: {item_id}, 名称: {item_name}, 取件码: {pickup_code}")
            print(f"接收人手机: {recipient_phone}, Mike的接收人: {is_for_mike}")
            print(f"存入者: {sender_name}, 状态: {status}")
            print("-" * 100)

        conn.close()
        print("\n检查完成！")

    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        import traceback
        traceback.print_exc()
        conn.close()

if __name__ == '__main__':
    check_mike_notifications()
