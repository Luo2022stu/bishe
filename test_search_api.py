"""测试搜索API"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import app, LostItem

def test_search():
    """测试搜索功能"""
    with app.app_context():
        try:
            # 测试基本搜索
            print("[测试] 开始测试搜索API...")
            print("[测试] 数据库中的物品数量:", LostItem.query.count())

            # 查询已审核的物品
            approved_items = LostItem.query.filter_by(audit_status='approved').all()
            print(f"[测试] 已审核的物品数量: {len(approved_items)}")

            # 测试多关键词搜索
            from sqlalchemy import or_
            from datetime import datetime, timezone

            keyword = "证件 身份卡"
            keywords = [k.strip() for k in keyword.split() if k.strip()]
            print(f"[测试] 测试关键词: {keywords}")

            now = datetime.now(timezone.utc)
            query = LostItem.query.filter(
                (LostItem.is_hidden == False) | (LostItem.hidden_until < now)
            )

            if keywords:
                conditions = []
                for kw in keywords:
                    conditions.append(LostItem.title.contains(kw))
                    conditions.append(LostItem.description.contains(kw))
                    conditions.append(LostItem.location.contains(kw))
                    conditions.append(LostItem.category.contains(kw))

                if conditions:
                    query = query.filter(or_(*conditions))

            items = query.filter_by(audit_status='approved').all()
            print(f"[测试] 找到 {len(items)} 条结果")

            for item in items[:3]:
                print(f"  - {item.title} ({item.category})")

            print("[✓] 搜索API测试成功！")
            return True

        except Exception as e:
            print(f"[✗] 搜索API测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    test_search()
