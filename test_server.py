#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Flask 服务器是否可以从外部访问
"""

import socket
import sys

def test_port(ip, port):
    """测试端口是否可访问"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"错误: {e}")
        return False

def get_local_ip():
    """获取本机 IP 地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    print("=" * 50)
    print("Flask 服务器连接测试")
    print("=" * 50)
    print()

    local_ip = get_local_ip()
    print(f"本机 IP 地址: {local_ip}")
    print()

    # 测试 localhost
    print("测试 1: localhost:5000")
    if test_port('127.0.0.1', 5000):
        print("  [OK] 成功")
    else:
        print("  [FAIL] 失败")

    # 测试本机 IP
    print(f"测试 2: {local_ip}:5000")
    if test_port(local_ip, 5000):
        print("  [OK] 成功")
    else:
        print("  [FAIL] 失败 - 需要配置防火墙")

    print()
    print("请在手机浏览器中访问:")
    print(f"  http://{local_ip}:5000")
    print()
    print("=" * 50)

    input("按回车键退出...")
