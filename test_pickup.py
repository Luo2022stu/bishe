#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import sys

def test_pickup_api():
    """测试拾取API"""

    # 登录获取token
    login_url = 'http://127.0.0.1:5000/api/auth/login'
    login_data = {
        'username': 'testuser',  # 替换为实际用户名
        'password': '123456'    # 替换为实际密码
    }

    try:
        print('1. 登录...')
        login_response = requests.post(login_url, json=login_data)
        print(f'   状态码: {login_response.status_code}')

        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('token')
            print(f'   Token: {token}')
        else:
            print(f'   登录失败: {login_response.text}')
            return

        # 测试拾取API
        item_id = 10  # 测试的物品ID
        pickup_url = f'http://127.0.0.1:5000/api/items/{item_id}/pickup'

        print(f'\n2. 测试拾取物品 {item_id}...')
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        pickup_response = requests.post(pickup_url, headers=headers)
        print(f'   状态码: {pickup_response.status_code}')
        print(f'   响应: {pickup_response.text}')

        if pickup_response.status_code == 200:
            print('\n✓ 拾取成功!')
        else:
            print('\n✗ 拾取失败')

    except requests.exceptions.ConnectionError:
        print('错误: 无法连接到服务器，请确保应用正在运行')
    except Exception as e:
        print(f'错误: {e}')

if __name__ == '__main__':
    test_pickup_api()
