from app.app import app, db, User, ChatMessage, Friendship

with app.app_context():
    # 获取两个用户
    user1 = User.query.filter_by(username='admin').first()
    user2 = User.query.filter_by(username='user').first()

    if not user1 or not user2:
        print('❌ 用户不存在，请先创建用户')
        exit(1)

    print(f'✅ 找到用户: {user1.username}(ID:{user1.id}) 和 {user2.username}(ID:{user2.id})')

    # 确保他们是好友
    friendship = Friendship.query.filter(
        ((Friendship.user_id == user1.id) & (Friendship.friend_id == user2.id)) |
        ((Friendship.user_id == user2.id) & (Friendship.friend_id == user1.id))
    ).first()

    if not friendship:
        # 创建好友关系
        friendship = Friendship(
            user_id=user1.id,
            friend_id=user2.id,
            status='accepted'
        )
        db.session.add(friendship)
        db.session.commit()
        print(f'✅ 已创建好友关系')
    else:
        friendship.status = 'accepted'
        db.session.commit()
        print(f'✅ 好友关系已存在')

    # 发送几条测试消息
    test_messages = [
        {'sender': user1, 'receiver': user2, 'content': '你好！这是一条测试消息'},
        {'sender': user1, 'receiver': user2, 'content': '收到消息了吗？'},
        {'sender': user1, 'receiver': user2, 'content': '这是第三条消息'},
    ]

    for msg in test_messages:
        chat_msg = ChatMessage(
            sender_id=msg['sender'].id,
            receiver_id=msg['receiver'].id,
            content=msg['content'],
            is_read=False
        )
        db.session.add(chat_msg)

    db.session.commit()

    print(f'✅ 已发送 {len(test_messages)} 条测试消息')
    print(f'📤 发送者: {user1.username}(ID:{user1.id})')
    print(f'📥 接收者: {user2.username}(ID:{user2.id})')

    # 检查未读消息数
    unread_count = ChatMessage.query.filter(
        ChatMessage.receiver_id == user2.id,
        ChatMessage.is_read == False
    ).count()

    print(f'📊 用户 {user2.username} 的未读消息数: {unread_count}')

    # 显示每个发送者的未读数
    from sqlalchemy import func
    unread_by_sender = db.session.query(
        ChatMessage.sender_id,
        func.count(ChatMessage.id)
    ).filter(
        ChatMessage.receiver_id == user2.id,
        ChatMessage.is_read == False
    ).group_by(ChatMessage.sender_id).all()

    print('📋 按发送者统计的未读消息:')
    for sender_id, count in unread_by_sender:
        sender = User.query.get(sender_id)
        print(f'  - {sender.username}(ID:{sender_id}): {count}条未读')
