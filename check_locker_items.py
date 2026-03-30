import sqlite3
import os

def check_locker_items():
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查询所有智能柜物品
        cursor.execute("SELECT id, item_name, pickup_code, status, expires_at FROM locker_item ORDER BY id DESC LIMIT 10")
        items = cursor.fetchall()

        print("智能柜物品检查：")
        print("=" * 100)
        for item_id, item_name, pickup_code, status, expires_at in items:
            print(f"\nID: {item_id}")
            print(f"物品名称: {item_name}")
            print(f"取件码: {pickup_code}")
            print(f"状态: {status}")
            print(f"过期时间: {expires_at}")
            print("-" * 100)

        conn.close()
        print("\n检查完成！")

    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        conn.close()

if __name__ == '__main__':
    check_locker_items()
