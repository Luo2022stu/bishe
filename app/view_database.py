"""
可视化查看 SQLite 数据库表结构
"""
import sqlite3
import os

def view_tables():
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'lost_found.db')
    
    print("=" * 80)
    print("SQLite 数据库表结构可视化")
    print("=" * 80)
    print(f"数据库路径: {db_path}")
    print()
    
    if not os.path.exists(db_path):
        print("错误: 数据库文件不存在！")
        return
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        if not tables:
            print("数据库中暂无表")
            return
        
        # 遍历每个表
        for table in tables:
            table_name = table[0]
            print("=" * 80)
            print(f"表名: {table_name}")
            print("=" * 80)
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("\n字段信息:")
            print(f"{'字段名':<20} {'类型':<15} {'非空':<8} {'默认值':<15} {'主键':<8}")
            print("-" * 80)
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = col[3] == 1
                default_val = col[4] if col[4] else 'NULL'
                is_pk = col[5] == 1
                
                print(f"{col_name:<20} {col_type:<15} {'YES' if not_null else 'NO':<8} {str(default_val):<15} {'YES' if is_pk else 'NO':<8}")
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print("-" * 80)
            print(f"总记录数: {count}")
            
            # 显示前5条数据
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
            rows = cursor.fetchall()
            
            if rows:
                print("\n数据预览 (前5条):")
                # 获取列名
                cursor.execute(f"PRAGMA table_info({table_name});")
                col_names = [col[1] for col in cursor.fetchall()]
                
                # 显示表头
                col_widths = [15] * len(col_names)
                print("-" * 80)
                header_parts = []
                for i, name in enumerate(col_names):
                    header_parts.append(f"{name[:15]:<15}")
                print(" | ".join(header_parts))
                print("-" * 80)

                # 显示数据
                for row in rows:
                    row_str = []
                    for i, value in enumerate(row):
                        str_val = str(value) if value is not None else 'NULL'
                        row_str.append(f"{str_val[:15]:<15}")
                    print(" | ".join(row_str))
                print()
            else:
                print("\n暂无数据")
                print()
    
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    finally:
        conn.close()
    
    print("=" * 80)
    print("查询完成")
    print("=" * 80)

if __name__ == '__main__':
    view_tables()
