#!/usr/bin/env python3
"""
测试新的用户认证系统
包括注册、登录、密码重置等功能
"""

import requests
import json
import time
import random

# API基础URL
BASE_URL = "http://localhost:9000"

def test_user_register():
    """测试用户注册"""
    print("\n=== 测试用户注册 ===")
    
    # 生成测试数据
    test_phone = f"1388888{random.randint(1000, 9999)}"
    test_email = f"test{random.randint(1000, 9999)}@example.com"
    
    register_data = {
        "phone": test_phone,
        "password": "123456",
        "email": test_email,
        "nickname": "测试用户"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user/register", json=register_data)
        print(f"注册响应状态码: {response.status_code}")
        print(f"注册响应内容: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            return result.get("access_token"), test_phone, test_email
        else:
            print(f"注册失败: {response.text}")
            return None, test_phone, test_email
            
    except Exception as e:
        print(f"注册请求异常: {e}")
        return None, test_phone, test_email

def test_user_login(phone, password="123456"):
    """测试用户登录"""
    print("\n=== 测试用户登录 ===")
    
    login_data = {
        "phone": phone,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user/login", json=login_data)
        print(f"登录响应状态码: {response.status_code}")
        print(f"登录响应内容: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            return result.get("access_token")
        else:
            print(f"登录失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"登录请求异常: {e}")
        return None

def test_get_user_info(token):
    """测试获取用户信息"""
    print("\n=== 测试获取用户信息 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/user/user-info", headers=headers)
        print(f"获取用户信息响应状态码: {response.status_code}")
        print(f"获取用户信息响应内容: {response.json()}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"获取用户信息请求异常: {e}")
        return False

def test_password_reset_request(email):
    """测试密码重置请求"""
    print("\n=== 测试密码重置请求 ===")
    
    reset_data = {
        "email": email
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user/password/reset", json=reset_data)
        print(f"密码重置请求响应状态码: {response.status_code}")
        print(f"密码重置请求响应内容: {response.json()}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"密码重置请求异常: {e}")
        return False

def test_change_password(token):
    """测试修改密码"""
    print("\n=== 测试修改密码 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    change_data = {
        "old_password": "123456",
        "new_password": "654321"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user/password/change", json=change_data, headers=headers)
        print(f"修改密码响应状态码: {response.status_code}")
        print(f"修改密码响应内容: {response.json()}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"修改密码请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试新的用户认证系统...")
    
    # 导入random模块
    import random
    
    # 1. 测试用户注册
    token, phone, email = test_user_register()
    
    if not token:
        print("注册失败，无法继续测试")
        return
    
    print(f"\n注册成功，获得token: {token[:20]}...")
    
    # 2. 测试获取用户信息
    if test_get_user_info(token):
        print("获取用户信息成功")
    else:
        print("获取用户信息失败")
    
    # 3. 测试密码重置请求
    if test_password_reset_request(email):
        print("密码重置请求成功")
    else:
        print("密码重置请求失败")
    
    # 4. 测试修改密码
    if test_change_password(token):
        print("修改密码成功")
        
        # 5. 用新密码登录
        new_token = test_user_login(phone, "654321")
        if new_token:
            print("新密码登录成功")
        else:
            print("新密码登录失败")
    else:
        print("修改密码失败")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()