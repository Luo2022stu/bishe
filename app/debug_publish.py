import requests
import json

# 测试发布物品功能
API_BASE = 'http://localhost:5000/api'

# 首先测试登录
print("1. 测试登录...")
login_data = {
    'username': 'admin',
    'password': 'admin123'
}

try:
    response = requests.post(f'{API_BASE}/auth/login', json=login_data)
    print(f"   登录响应状态码: {response.status_code}")
    print(f"   登录响应: {response.text}")
    
    if response.ok:
        user_data = response.json()
        token = user_data.get('token')
        print(f"   获取到token: {token[:20]}...")
        
        # 测试发布物品
        print("\n2. 测试发布物品...")
        item_data = {
            'type': 'found',
            'title': '测试物品',
            'category': '其他',
            'location': '测试地点',
            'contact': '13800138000',
            'description': '这是一个测试物品',
            'latitude': None,
            'longitude': None
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.post(f'{API_BASE}/items', json=item_data, headers=headers)
        print(f"   发布响应状态码: {response.status_code}")
        print(f"   发布响应: {response.text}")
        
        if response.ok:
            print("   ✓ 发布成功!")
        else:
            print("   ✗ 发布失败")
            try:
                error_data = response.json()
                print(f"   错误信息: {error_data.get('error', '未知错误')}")
            except:
                pass
    else:
        print("   ✗ 登录失败")
        
except requests.exceptions.ConnectionError:
    print("   ✗ 无法连接到后端服务器，请确保后端服务已启动")
except Exception as e:
    print(f"   ✗ 发生错误: {str(e)}")

print("\n3. 检查数据库连接...")
try:
    from app import app, db, LostItem
    with app.app_context():
        items_count = LostItem.query.count()
        print(f"   当前数据库中有 {items_count} 条物品记录")
except Exception as e:
    print(f"   ✗ 数据库连接失败: {str(e)}")
