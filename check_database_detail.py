from app.app import app, db

with app.app_context():
    print("=" * 70)
    print("数据库表详细统计 - 校园失物招领系统")
    print("=" * 70)

    tables = db.metadata.tables.keys()

    # 按功能分类
    table_categories = {
        "用户相关": ["user", "user_settings", "browse_history"],
        "物品管理": ["lost_item", "item_like"],
        "帖子管理": ["post", "post_like", "comment", "comment_like"],
        "通知系统": ["system_notification", "user_notification"],
        "好友和聊天": ["friendship", "chat_message"],
        "反馈和举报": ["feedback", "report"],
        "智能存储柜": ["smart_locker", "locker_item"]
    }

    total_tables = 0

    for category, table_list in table_categories.items():
        print(f"\n【{category}】")
        print("-" * 70)
        for table_name in table_list:
            if table_name in tables:
                total_tables += 1
                table = db.metadata.tables[table_name]
                columns = list(table.columns.keys())
                print(f"  {table_name}")
                print(f"    └─ 字段数: {len(columns)}")
            else:
                print(f"  {table_name} (不存在)")

    # 检查是否有未分类的表
    categorized_tables = set()
    for table_list in table_categories.values():
        categorized_tables.update(table_list)

    uncategorized = [t for t in tables if t not in categorized_tables]

    if uncategorized:
        print(f"\n【未分类表】")
        print("-" * 70)
        for table_name in uncategorized:
            total_tables += 1
            table = db.metadata.tables[table_name]
            columns = list(table.columns.keys())
            print(f"  {table_name}")
            print(f"    └─ 字段数: {len(columns)}")

    print("\n" + "=" * 70)
    print(f"总计: {total_tables} 个表")
    print("=" * 70)
    print("\n表功能说明:")
    print("=" * 70)

    descriptions = {
        "user": "用户信息表 - 存储用户账号、个人信息、角色等",
        "user_settings": "用户设置表 - 存储用户偏好设置(通知、主题等)",
        "browse_history": "浏览历史表 - 记录用户浏览过的物品和帖子",
        "lost_item": "失物物品表 - 存储失物招领和寻物信息",
        "item_like": "物品点赞表 - 记录用户对物品的点赞",
        "post": "帖子表 - 存储社区交流帖子",
        "post_like": "帖子点赞表 - 记录用户对帖子的点赞",
        "comment": "评论表 - 存储帖子评论",
        "comment_like": "评论点赞表 - 记录用户对评论的点赞",
        "system_notification": "系统通知表 - 存储系统公告和通知",
        "user_notification": "用户通知表 - 存储用户的个人通知消息",
        "friendship": "好友关系表 - 存储用户间的好友关系",
        "chat_message": "聊天消息表 - 存储用户间的聊天记录",
        "feedback": "反馈表 - 存储用户反馈意见",
        "report": "举报表 - 存储用户举报信息",
        "smart_locker": "智能存储柜表 - 存储存储柜信息",
        "locker_item": "存储柜物品表 - 存储存储柜中存储的物品"
    }

    for table_name, desc in sorted(descriptions.items()):
        if table_name in tables:
            print(f"  * {table_name:20s} - {desc}")

    print("=" * 70)
