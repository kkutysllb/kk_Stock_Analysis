#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户登录功能修复
验证手机号格式和密码验证是否正常工作
"""

import requests
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API基础URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:9000")

def test_phone_validation():
    """测试手机号格式验证"""
    print("🔍 测试手机号格式验证...")
    
    test_cases = [
        # 正确格式
        ("+8613800000001", True, "正确格式：+86开头11位手机号"),
        ("+8613900000002", True, "正确格式：+86开头11位手机号"),
        
        # 错误格式
        ("13800000001", False, "错误格式：缺少+86前缀"),
        ("+86138000000011", False, "错误格式：手机号过长"),
        ("+8613800000", False, "错误格式：手机号过短"),
        ("+8612800000001", False, "错误格式：第二位不是3-9"),
        ("86138000000001", False, "错误格式：缺少+号"),
        ("+8613800000001 ", True, "包含空格但会被清理"),
    ]
    
    for phone, should_pass, description in test_cases:
        # 测试登录接口的手机号验证
        login_data = {
            "phone": phone,
            "password": "test123456"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/user/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if should_pass:
                # 应该通过手机号验证（可能因为用户不存在而失败，但不应该是格式错误）
                if response.status_code == 400 and "手机号格式不正确" in response.text:
                    print(f"❌ {description}: 手机号格式验证失败")
                else:
                    print(f"✅ {description}: 手机号格式验证通过")
            else:
                # 应该因为手机号格式错误而失败
                if response.status_code == 400 and "手机号格式不正确" in response.text:
                    print(f"✅ {description}: 正确拒绝了错误格式")
                else:
                    print(f"❌ {description}: 应该拒绝但没有拒绝")
                    
        except requests.exceptions.RequestException as e:
            print(f"⚠️ {description}: 网络请求失败 - {e}")
    
    print("-" * 60)

def test_user_login():
    """测试用户登录功能"""
    print("🔐 测试用户登录功能...")
    
    # 测试用例
    test_users = [
        {
            "phone": "+8613609247807",
            "password": "Imscfg_2252",
            "description": "超级管理员登录",
            "should_succeed": True
        },
        {
            "phone": "+8613900000002", 
            "password": "test123456",
            "description": "测试用户登录",
            "should_succeed": True
        },
        {
            "phone": "+8613609247807",
            "password": "wrongpassword",
            "description": "错误密码",
            "should_succeed": False
        },
        {
            "phone": "+8613999999999",
            "password": "test123456",
            "description": "不存在的用户",
            "should_succeed": False
        }
    ]
    
    for test_case in test_users:
        login_data = {
            "phone": test_case["phone"],
            "password": test_case["password"]
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/user/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if test_case["should_succeed"]:
                if response.status_code == 200:
                    result = response.json()
                    if "access_token" in result:
                        print(f"✅ {test_case['description']}: 登录成功")
                        print(f"   Token: {result['access_token'][:20]}...")
                        if "user_info" in result:
                            user_info = result["user_info"]
                            print(f"   用户: {user_info.get('nickname', 'N/A')}")
                            print(f"   角色: {user_info.get('roles', [])}")
                    else:
                        print(f"❌ {test_case['description']}: 响应格式错误")
                else:
                    print(f"❌ {test_case['description']}: 登录失败 - {response.status_code}")
                    print(f"   错误: {response.text}")
            else:
                if response.status_code != 200:
                    print(f"✅ {test_case['description']}: 正确拒绝登录")
                else:
                    print(f"❌ {test_case['description']}: 应该失败但成功了")
                    
        except requests.exceptions.RequestException as e:
            print(f"⚠️ {test_case['description']}: 网络请求失败 - {e}")
        
        print("-" * 40)

def test_user_registration():
    """测试用户注册功能"""
    print("📝 测试用户注册功能...")
    
    # 生成随机测试用户
    import random
    random_num = random.randint(100000000, 999999999)  # 生成9位数字
    
    register_data = {
        "phone": f"+8613{random_num}",
        "email": f"test{random_num}@example.com",
        "password": "test123456",
        "nickname": f"测试用户{random_num}"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/user/register",
            json=register_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "access_token" in result:
                print(f"✅ 用户注册成功")
                print(f"   手机号: {register_data['phone']}")
                print(f"   邮箱: {register_data['email']}")
                print(f"   昵称: {register_data['nickname']}")
                print(f"   Token: {result['access_token'][:20]}...")
            else:
                print(f"❌ 注册响应格式错误")
        else:
            print(f"❌ 用户注册失败 - {response.status_code}")
            print(f"   错误: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 用户注册测试失败 - {e}")
    
    print("-" * 60)

def main():
    """主测试函数"""
    print("🧪 开始测试用户登录功能修复")
    print("=" * 60)
    
    # 检查API服务是否运行
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ API服务运行正常: {API_BASE_URL}")
        else:
            print(f"⚠️ API服务响应异常: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到API服务: {e}")
        print(f"请确保API服务正在运行在 {API_BASE_URL}")
        return
    
    print("-" * 60)
    
    # 运行测试
    test_phone_validation()
    test_user_login()
    test_user_registration()
    
    print("🎉 测试完成！")
    print("\n💡 如果测试失败，请检查：")
    print("1. API服务是否正常运行")
    print("2. 数据库连接是否正常")
    print("3. 是否已创建测试用户（运行 create_super_admin.py）")

if __name__ == "__main__":
    main() 