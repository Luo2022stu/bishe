#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试系统公告功能
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

# 测试用的管理员token（需要先登录获取管理员账号的token）
ADMIN_TOKEN = None

def test_login_admin():
    """登录管理员账号"""
    global ADMIN_TOKEN
    print('\n=== 测试登录管理员 ===')

    # 假设有一个测试管理员账号
    login_data = {
        'email': 'admin@test.com',
        'password': 'admin123'
    }

    try:
        response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
        if response.status_code == 200:
            data = response.json()
            ADMIN_TOKEN = data.get('token')
            print(f'✓ 管理员登录成功，token: {ADMIN_TOKEN[:20]}...')
            return True
        else:
            print(f'✗ 登录失败: {response.text}')
            return False
    except Exception as e:
        print(f'✗ 登录异常: {e}')
        return False

def test_create_announcement():
    """测试创建系统公告"""
    print('\n=== 测试创建系统公告 ===')

    if not ADMIN_TOKEN:
        print('✗ 请先登录管理员账号')
        return False

    announcement_data = {
        'title': '测试公告标题',
        'content': '这是一条测试系统公告的内容，用于验证管理员发送公告的功能。',
        'tag': '公告'
    }

    try:
        response = requests.post(
            f'{BASE_URL}/api/admin/system-notifications',
            json=announcement_data,
            headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
        )

        if response.status_code == 201:
            data = response.json()
            print(f'✓ 公告创建成功: {json.dumps(data, indent=2, ensure_ascii=False)}')
            return data
        else:
            print(f'✗ 创建公告失败: {response.text}')
            return None
    except Exception as e:
        print(f'✗ 创建公告异常: {e}')
        return None

def test_get_announcements():
    """测试获取公告列表"""
    print('\n=== 测试获取公告列表 ===')

    if not ADMIN_TOKEN:
        print('✗ 请先登录管理员账号')
        return False

    try:
        response = requests.get(
            f'{BASE_URL}/api/admin/system-notifications',
            headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
        )

        if response.status_code == 200:
            data = response.json()
            print(f'✓ 获取到 {len(data)} 条公告')
            for announcement in data:
                print(f'  - ID: {announcement["id"]}, 标题: {announcement["title"]}, 状态: {"启用" if announcement["is_active"] else "停用"}')
            return data
        else:
            print(f'✗ 获取公告失败: {response.text}')
            return None
    except Exception as e:
        print(f'✗ 获取公告异常: {e}')
        return None

def test_get_public_announcements():
    """测试获取公开公告（首页用）"""
    print('\n=== 测试获取公开公告（首页） ===')

    try:
        response = requests.get(f'{BASE_URL}/api/system-notifications')

        if response.status_code == 200:
            data = response.json()
            print(f'✓ 获取到 {len(data)} 条公开公告')
            for announcement in data:
                print(f'  - ID: {announcement["id"]}, 标题: {announcement["title"]}')
            return data
        else:
            print(f'✗ 获取公开公告失败: {response.text}')
            return None
    except Exception as e:
        print(f'✗ 获取公开公告异常: {e}')
        return None

def test_toggle_announcement(notif_id):
    """测试切换公告状态"""
    print(f'\n=== 测试切换公告状态 (ID: {notif_id}) ===')

    if not ADMIN_TOKEN:
        print('✗ 请先登录管理员账号')
        return False

    try:
        response = requests.put(
            f'{BASE_URL}/api/admin/system-notifications/{notif_id}/toggle',
            headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
        )

        if response.status_code == 200:
            data = response.json()
            print(f'✓ 公告状态切换成功: {"启用" if data["is_active"] else "停用"}')
            return True
        else:
            print(f'✗ 切换状态失败: {response.text}')
            return False
    except Exception as e:
        print(f'✗ 切换状态异常: {e}')
        return False

def main():
    """主测试函数"""
    print('=' * 60)
    print('系统公告功能测试')
    print('=' * 60)

    # 如果需要测试，取消下面的注释
    # test_login_admin()
    # announcement = test_create_announcement()
    # if announcement:
    #     test_get_announcements()
    #     test_get_public_announcements()
    #     test_toggle_announcement(announcement['id'])
    print('\n提示：取消代码中的注释即可运行测试')
    print('请先确保有一个管理员账号（role = "admin"）')

if __name__ == '__main__':
    main()
