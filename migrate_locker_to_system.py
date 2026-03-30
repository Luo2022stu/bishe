import sqlite3
import os

def migrate_locker_to_system():
    """将所有locker类型的通知改为system类型"""
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查询所有locker类型的通知
        print("正在查询所有locker类型的通知...")
        cursor.execute("SELECT id, user_id, title FROM user_notification WHERE type = 'locker'")
        locker_notifications = cursor.fetchall()

        if not locker_notifications:
            print("没有找到locker类型的通知")
            conn.close()
            return

        print(f"找到 {len(locker_notifications)} 条locker类型的通知:")
        for notif_id, user_id, title in locker_notifications:
            print(f"  - 通知ID: {notif_id}, 用户ID: {user_id}, 标题: {title}")

        # 更新通知类型
        print("\n正在更新通知类型...")
        cursor.execute("UPDATE user_notification SET type = 'system' WHERE type = 'locker'")
        updated_count = cursor.rowcount

        conn.commit()

        print(f"\n成功！已将 {updated_count} 条通知从 'locker' 类型更新为 'system' 类型")

        # 验证更新
        cursor.execute("SELECT COUNT(*) FROM user_notification WHERE type = 'locker'")
        remaining = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user_notification WHERE type = 'system'")
        system_count = cursor.fetchone()[0]

        print(f"剩余locker类型通知: {remaining}")
        print(f"当前system类型通知: {system_count}")

        conn.close()
        print("\n迁移完成！")

    except Exception as e:
        print(f"[ERROR] 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()

if __name__ == '__main__':
    migrate_locker_to_system()
