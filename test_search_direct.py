"""直接测试搜索SQL查询"""
import sqlite3
import urllib.parse

db_path = 'app/lost_found.db'

def test_search_sql(keyword):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 解析关键词（按空格分割）
        keywords = [k.strip() for k in keyword.split() if k.strip()]
        print(f"[测试] 关键词: {keywords}")

        # 构建SQL查询
        conditions = []
        params = []

        for kw in keywords:
            conditions.append("title LIKE ?")
            conditions.append("description LIKE ?")
            conditions.append("location LIKE ?")
            conditions.append("category LIKE ?")
            params.extend([f'%{kw}%'] * 4)

        where_clause = " AND ".join(conditions)
        sql = f"""
            SELECT * FROM lost_item
            WHERE audit_status = 'approved'
            AND (is_hidden = 0 OR hidden_until IS NULL OR datetime(hidden_until) < datetime('now'))
            AND ({where_clause})
            ORDER BY created_at DESC
        """

        print(f"[测试] SQL: {sql}")
        print(f"[测试] 参数: {params}")

        cursor.execute(sql, params)
        results = cursor.fetchall()

        print(f"\n[测试] 找到 {len(results)} 条结果:")
        for row in results:
            print(f"  - {row['title']} ({row['category']})")

        return results

    except Exception as e:
        print(f"[错误] 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()

if __name__ == '__main__':
    # 测试搜索
    keyword = urllib.parse.unquote("%E6%9C%AA%E5%88%86%E7%B1%BB%20%E6%97%A0%E6%B3%95%E8%AF%86%E5%88%AB%E5%85%B7%E4%BD%93%E7%89%A9%E5%93%81")
    print(f"[测试] 原始URL关键词: {keyword}")
    test_search_sql(keyword)
