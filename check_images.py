import sqlite3
import os

def check_images():
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'lost_found.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查询所有物品的images字段
        cursor.execute("SELECT id, title, images FROM lost_item ORDER BY id DESC LIMIT 10")
        items = cursor.fetchall()

        print("数据库中的图片数据检查：")
        print("=" * 80)
        for item_id, title, images in items:
            print(f"\nID: {item_id}")
            print(f"标题: {title}")
            if images:
                # 检查是否以逗号分隔
                image_list = images.split(',') if isinstance(images, str) else []
                print(f"图片数量: {len(image_list)}")
                print(f"第一个图片长度: {len(image_list[0]) if image_list else 0} 字符")
                print(f"第一个图片前50字符: {image_list[0][:50] if image_list else '无'}")
            else:
                print("图片: 无")
            print("-" * 80)

        conn.close()
        print("\n检查完成！")

    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        conn.close()

if __name__ == '__main__':
    check_images()
