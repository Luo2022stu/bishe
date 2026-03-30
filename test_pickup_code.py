import requests
import json

def test_verify_pickup_code():
    url = 'http://localhost:5000/api/lockers/verify'
    pickup_code = '845418'  # 使用数据库中存在的取件码

    try:
        response = requests.post(url, json={'pickup_code': pickup_code})
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == '__main__':
    test_verify_pickup_code()
