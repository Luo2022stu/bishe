from app.app import app, db, User, UserNotification, SystemNotification

with app.app_context():
    # 创建系统推送通知（用于首页重要推送版块）
    notification = SystemNotification(
        title='校园失物招领系统测试通知',
        content='欢迎使用校园失物招领系统，如有任何问题请随时联系管理员。',
        tag='公告',
        is_active=True
    )

    db.session.add(notification)
    db.session.flush()

    # 给所有用户发送个人通知
    all_users = User.query.all()
    for user in all_users:
        user_notification = UserNotification(
            user_id=user.id,
            type='system',
            title='校园失物招领系统测试通知',
            content='欢迎使用校园失物招领系统，如有任何问题请随时联系管理员。',
            is_read=False,
            related_id=notification.id,
            related_type='system_notification'
        )
        db.session.add(user_notification)

    db.session.commit()

    print(f'✅ 系统通知创建成功！')
    print(f'📢 标题: 校园失物招领系统测试通知')
    print(f'👥 已发送给 {len(all_users)} 个用户')
    print(f'🆔 通知ID: {notification.id}')
