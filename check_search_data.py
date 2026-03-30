from app.app import app, db, LostItem, Post, User

with app.app_context():
    # 获取admin用户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print('X 没有找到admin用户')
        exit(1)

    print(f'[OK] 找到用户: {admin.username} (ID: {admin.id})')

    # 检查物品数量
    items = LostItem.query.filter_by(audit_status='approved').all()
    print(f'\n[物品] 当前已审核物品数量: {len(items)}')

    # 检查帖子数量
    posts = Post.query.filter_by(audit_status='approved').all()
    print(f'[帖子] 当前已审核帖子数量: {len(posts)}')

    # 如果没有物品,创建一些测试物品
    if len(items) == 0:
        print('\n[警告] 没有已审核的物品,创建测试数据...')
        test_items = [
            {
                'title': '黑色钱包',
                'description': '在图书馆二楼丢失一个黑色钱包,内有学生证、银行卡和少量现金',
                'category': '钱包',
                'location': '图书馆二楼',
                'type': 'lost'
            },
            {
                'title': '红色雨伞',
                'description': '在食堂门口捡到一把红色雨伞,请失主前来认领',
                'category': '雨伞',
                'location': '食堂门口',
                'type': 'found'
            },
            {
                'title': '蓝色书包',
                'description': '在操场丢失一个蓝色书包,内有课本和笔记本',
                'category': '书包',
                'location': '操场',
                'type': 'lost'
            },
            {
                'title': '黑色眼镜',
                'description': '在教学楼301教室捡到一副黑色眼镜',
                'category': '眼镜',
                'location': '教学楼301教室',
                'type': 'found'
            },
            {
                'title': '白色耳机',
                'description': '在宿舍楼下丢失一副白色耳机,品牌是小米',
                'category': '耳机',
                'location': '宿舍楼下',
                'type': 'lost'
            }
        ]

        for item_data in test_items:
            item = LostItem(
                user_id=admin.id,
                title=item_data['title'],
                description=item_data['description'],
                category=item_data['category'],
                location=item_data['location'],
                type=item_data['type'],
                status='pending',
                audit_status='approved',
                view_count=0,
                like_count=0
            )
            db.session.add(item)

        db.session.commit()
        print(f'[OK] 已创建 {len(test_items)} 条测试物品')

    # 如果没有帖子,创建一些测试帖子
    if len(posts) == 0:
        print('\n[警告] 没有已审核的帖子,创建测试数据...')
        test_posts = [
            {
                'title': '请问有人捡到我的钱包吗？',
                'content': '我今天在图书馆二楼丢失了一个黑色钱包,里面有学生证和银行卡,如果有人捡到请联系我,必有重谢！',
                'category': '寻物启事'
            },
            {
                'title': '分享失物招领的经验',
                'content': '大家丢失物品后要及时发布信息,我之前丢了手机就是通过这个平台找回来的。建议大家多关注这个系统。',
                'category': '经验分享'
            },
            {
                'title': '食堂门口捡到雨伞',
                'content': '今天中午在食堂门口捡到一把红色雨伞,已经发布在失物招领里了,希望失主能看到',
                'category': '物品归还'
            },
            {
                'title': '建议增加更多分类',
                'content': '希望系统能增加更多的物品分类,这样查找起来会更方便',
                'category': '建议反馈'
            },
            {
                'title': '感谢好心人',
                'content': '之前我丢了钱包,后来有好心人联系我归还了,非常感谢！这个平台真的很有用',
                'category': '感谢信'
            }
        ]

        for post_data in test_posts:
            post = Post(
                user_id=admin.id,
                title=post_data['title'],
                content=post_data['content'],
                category=post_data['category'],
                audit_status='approved',
                is_hidden=False,
                view_count=0,
                like_count=0,
                comment_count=0
            )
            db.session.add(post)

        db.session.commit()
        print(f'[OK] 已创建 {len(test_posts)} 条测试帖子')

    # 重新检查
    items = LostItem.query.filter_by(audit_status='approved').all()
    posts = Post.query.filter_by(audit_status='approved').all()

    print(f'\n[统计] 最终统计:')
    print(f'   物品总数: {len(items)}')
    print(f'   帖子总数: {len(posts)}')

    # 测试搜索功能
    print(f'\n[搜索] 测试搜索功能:')
    
    # 搜索"钱包"
    items_with_wallet = LostItem.query.filter(
        LostItem.title.contains('钱包')
    ).filter_by(audit_status='approved').all()
    print(f'   搜索"钱包" - 物品: {len(items_with_wallet)}条')

    posts_with_wallet = Post.query.filter(
        Post.title.contains('钱包') | Post.content.contains('钱包')
    ).filter_by(audit_status='approved').all()
    print(f'   搜索"钱包" - 帖子: {len(posts_with_wallet)}条')

    # 搜索"图书馆"
    items_with_library = LostItem.query.filter(
        LostItem.location.contains('图书馆') | LostItem.description.contains('图书馆')
    ).filter_by(audit_status='approved').all()
    print(f'   搜索"图书馆" - 物品: {len(items_with_library)}条')

    print(f'\n[完成] 数据检查完成!')

