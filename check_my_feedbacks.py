import sqlite3
import os

def check_my_feedbacks():
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查询所有用户
        print("=" * 100)
        print("所有用户：")
        print("=" * 100)
        cursor.execute("SELECT id, username, email FROM user")
        users = cursor.fetchall()

        for user_id, username, email in users:
            print(f"ID: {user_id}, 用户名: {username}, 邮箱: {email}")

        # 查询所有反馈
        print("\n" + "=" * 100)
        print("所有反馈记录：")
        print("=" * 100)
        cursor.execute("""
            SELECT f.id, f.user_id, u.username, f.content, f.reply, f.status, f.created_at
            FROM feedback f
            LEFT JOIN user u ON f.user_id = u.id
            ORDER BY f.id DESC
        """)
        feedbacks = cursor.fetchall()

        if feedbacks:
            for fb_id, user_id, username, content, reply, status, created_at in feedbacks:
                print(f"\n反馈ID: {fb_id}")
                print(f"用户: {username} (ID: {user_id})")
                print(f"内容: {content}")
                print(f"回复: {reply or '暂无回复'}")
                print(f"状态: {status}")
                print(f"创建时间: {created_at}")
                print("-" * 100)
        else:
            print("没有找到任何反馈记录")

        conn.close()
        print("\n检查完成！")

    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        import traceback
        traceback.print_exc()
        conn.close()

if __name__ == '__main__':
    check_my_feedbacks()
