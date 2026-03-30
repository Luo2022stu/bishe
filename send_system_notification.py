#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送系统推送通知
"""

import sys
import os

# 添加 app 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import app, db, SystemNotification, User

def send_system_notification():
    """发送系统推送通知"""
    with app.app_context():
        print('=== 系统推送通知发送工具 ===\n')

        # 获取输入
        title = input('请输入通知标题: ').strip()
        if not title:
            print('错误: 标题不能为空')
            return

        content = input('请输入通知内容: ').strip()
        if not content:
            print('错误: 内容不能为空')
            return

        tag = input('请输入标签（默认为"公告"）: ').strip() or '公告'

        print(f'\n即将发送推送通知:')
        print(f'标题: {title}')
        print(f'内容: {content}')
        print(f'标签: {tag}')

        confirm = input('\n确认发送吗？(y/n): ').strip().lower()
        if confirm != 'y':
            print('已取消')
            return

        try:
            # 创建系统通知
            notification = SystemNotification(
                title=title,
                content=content,
                tag=tag,
                is_active=True
            )

            db.session.add(notification)
            db.session.commit()

            print(f'\n✓ 成功创建系统推送通知')
            print(f'通知ID: {notification.id}')
            print(f'创建时间: {notification.created_at}')

            # 获取所有用户数量
            user_count = User.query.count()
            print(f'该通知将推送给 {user_count} 个用户')

        except Exception as e:
            print(f'\n✗ 发送失败: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    try:
        send_system_notification()
    except KeyboardInterrupt:
        print('\n\n操作已取消')
