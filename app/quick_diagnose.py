"""
快速诊断发布问题
"""
import requests
import json
import sys
import io

# 修复Windows控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=== 发布功能诊断 ===\n")

# 检查后端服务
print("1. 检查后端服务...")
try:
    response = requests.get('http://localhost:5000/api/items', timeout=5)
    print(f"   ✓ 后端服务正常 (状态码: {response.status_code})")
except requests.exceptions.ConnectionError:
    print("   ✗ 无法连接到后端服务!")
    print("   解决方法: 请先启动后端服务")
    print("   命令: python d:\\BiShe\\app\\app.py")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ 连接错误: {e}")
    sys.exit(1)

# 测试登录
print("\n2. 测试登录...")
login_data = {
    'username': 'admin',
    'password': 'admin123'
}

try:
    response = requests.post('http://localhost:5000/api/auth/login', json=login_data, timeout=5)
    print(f"   登录响应状态: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        user = data.get('user')
        print(f"   ✓ 登录成功")
        print(f"   Token: {token[:30]}...")
        print(f"   用户: {user['username']} (ID: {user['id']})")

        # 测试发布
        print("\n3. 测试发布物品...")
        item_data = {
            'type': 'found',
            'title': '诊断测试物品',
            'category': '其他',
            'location': '诊断测试地点',
            'contact': '13800138000',
            'description': '这是自动诊断测试物品',
            'latitude': None,
            'longitude': None
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.post('http://localhost:5000/api/items', json=item_data, headers=headers, timeout=5)
        print(f"   发布响应状态: {response.status_code}")

        if response.status_code == 201:
            item = response.json()
            print(f"   ✓ 发布成功!")
            print(f"   物品ID: {item['id']}")
            print(f"   物品标题: {item['title']}")
            print(f"   物品类型: {item['type']}")
            print(f"   用户ID: {item['user_id']}")
        else:
            print(f"   ✗ 发布失败")
            try:
                error = response.json()
                print(f"   错误信息: {error}")
            except:
                print(f"   响应内容: {response.text}")
    else:
        print(f"   ✗ 登录失败")
        try:
            error = response.json()
            print(f"   错误信息: {error.get('error', '未知错误')}")
        except:
            print(f"   响应内容: {response.text}")

except requests.exceptions.Timeout:
    print("   ✗ 请求超时")
    print("   解决方法: 检查网络连接或增加超时时间")
except Exception as e:
    print(f"   ✗ 请求错误: {e}")

print("\n" + "="*50)
print("\n如果以上测试都通过，问题可能出在前端:")
print("1. 清除浏览器缓存和Cookies")
print("2. 检查浏览器控制台 (F12) 的错误信息")
print("3. 确保已登录 (页面右上角应显示用户名)")
print("4. 尝试访问 http://localhost:5000/test_publish.html 进行测试")
