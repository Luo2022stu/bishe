from app.app import app, db

with app.app_context():
    print("=" * 60)
    print("数据库表统计")
    print("=" * 60)

    # 获取所有表
    tables = db.metadata.tables.keys()
    table_count = len(tables)

    print(f"\n总共有 {table_count} 个表\n")

    print("=" * 60)
    print("表列表:")
    print("=" * 60)

    for i, table_name in enumerate(sorted(tables), 1):
        print(f"{i:2d}. {table_name}")

        # 获取表的基本信息
        table = db.metadata.tables[table_name]
        columns = [c.name for c in table.columns]
        print(f"    - 字段数量: {len(columns)}")
        print(f"    - 字段: {', '.join(columns)}")
        print()

    print("=" * 60)
    print(f"统计完成: 共 {table_count} 个表")
    print("=" * 60)
