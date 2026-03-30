from app.app import app, db, LostItem, Post

with app.app_context():
    print("=" * 60)
    print("测试搜索功能")
    print("=" * 60)

    # 测试1: 搜索空字符串
    print("\n测试1: 搜索空字符串")
    print("-" * 60)
    try:
        items = LostItem.query.filter_by(audit_status='approved').all()
        print(f"[OK] 不带关键词搜索成功, 找到 {len(items)} 条物品")
    except Exception as e:
        print(f"[ERROR] 搜索失败: {e}")

    # 测试2: 搜索"钱包"
    print("\n测试2: 搜索'钱包'")
    print("-" * 60)
    try:
        items = LostItem.query.filter(
            LostItem.title.contains('钱包') |
            LostItem.description.contains('钱包') |
            LostItem.location.contains('钱包')
        ).filter_by(audit_status='approved').all()
        print(f"[OK] 搜索'钱包'成功, 找到 {len(items)} 条物品")
        for item in items:
            print(f"  - {item.title}")
    except Exception as e:
        print(f"[ERROR] 搜索失败: {e}")

    # 测试3: 搜索"水卡"
    print("\n测试3: 搜索'水卡'")
    print("-" * 60)
    try:
        items = LostItem.query.filter(
            LostItem.title.contains('水卡') |
            LostItem.description.contains('水卡') |
            LostItem.location.contains('水卡')
        ).filter_by(audit_status='approved').all()
        print(f"[OK] 搜索'水卡'成功, 找到 {len(items)} 条物品")
        if len(items) > 0:
            for item in items:
                print(f"  - {item.title}")
        else:
            print("  提示: 数据库中没有包含'水卡'的物品")
    except Exception as e:
        print(f"[ERROR] 搜索失败: {e}")

    # 测试4: 搜索帖子
    print("\n测试4: 搜索帖子'钱包'")
    print("-" * 60)
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        posts = Post.query.filter_by(audit_status='approved').filter(
            (Post.is_hidden == False) | (Post.hidden_until < now)
        ).filter(
            (Post.title.contains('钱包')) |
            (Post.content.contains('钱包'))
        ).all()

        print(f"[OK] 搜索帖子'钱包'成功, 找到 {len(posts)} 条帖子")
        for post in posts:
            print(f"  - {post.title}")
    except Exception as e:
        print(f"[ERROR] 搜索失败: {e}")

    # 测试5: 添加测试数据
    print("\n测试5: 添加'水卡'测试数据")
    print("-" * 60)

    # 检查是否已有"水卡"数据
    existing = LostItem.query.filter(
        LostItem.title.contains('水卡')
    ).filter_by(audit_status='approved').all()

    if len(existing) > 0:
        print(f"[INFO] 已存在 {len(existing)} 条'水卡'数据")
    else:
        # 获取admin用户
        from app.app import User
        admin = User.query.filter_by(username='admin').first()
        if admin:
            test_water_card = LostItem(
                user_id=admin.id,
                title='蓝色水卡',
                description='在食堂一楼丢失一张蓝色水卡,余额100元',
                category='水卡',
                location='食堂一楼',
                type='lost',
                status='pending',
                audit_status='approved',
                view_count=0,
                like_count=0
            )
            db.session.add(test_water_card)
            db.session.commit()
            print(f"[OK] 已添加'水卡'测试数据")

            # 验证添加成功
            items = LostItem.query.filter(
                LostItem.title.contains('水卡')
            ).filter_by(audit_status='approved').all()
            print(f"[OK] 验证成功, 现在有 {len(items)} 条'水卡'数据")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
