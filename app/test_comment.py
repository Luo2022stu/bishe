"""
测试评论功能
"""
import requests
import json

API_BASE = 'http://127.0.0.1:5000/api'

def test_comment():
    # 1. 先登录获取 token
    print('[1] 登录...')
    login_response = requests.post(f'{API_BASE}/auth/login', json={
        'email': 'test@test.com',
        'password': '123456'
    })
    print(f'登录响应: {login_response.status_code}')
    if login_response.status_code != 200:
        print(f'登录失败: {login_response.text}')
        return
    
    token = login_response.json().get('token')
    print(f'Token: {token}')
    
    # 2. 获取帖子列表
    print('\n[2] 获取帖子列表...')
    posts_response = requests.get(f'{API_BASE}/posts')
    print(f'响应状态: {posts_response.status_code}')
    if posts_response.status_code == 200:
        posts = posts_response.json()
        print(f'帖子数量: {len(posts)}')
        if posts:
            post_id = posts[0]['id']
            print(f'帖子ID: {post_id}')
            
            # 3. 添加评论
            print(f'\n[3] 为帖子 {post_id} 添加评论...')
            comment_response = requests.post(
                f'{API_BASE}/posts/{post_id}/comments',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                json={'content': '测试评论'}
            )
            print(f'评论响应状态: {comment_response.status_code}')
            print(f'评论响应内容: {comment_response.text}')
            
            if comment_response.status_code == 201:
                print('[√] 评论成功！')
            else:
                print('[!] 评论失败')
        else:
            print('[!] 没有帖子')
    else:
        print(f'获取帖子失败: {posts_response.text}')

if __name__ == '__main__':
    try:
        test_comment()
    except Exception as e:
        print(f'测试出错: {e}')
