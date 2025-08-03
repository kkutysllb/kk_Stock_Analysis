#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的用户信息
"""

import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# 数据库连接
MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@127.0.0.1:27017/authSource=admin")
DB_NAME = os.getenv("DB_NAME", "quant_analysis")

def check_users():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        users_col = db["users"]
        
        # 获取所有用户
        users = list(users_col.find({}, {"password_hash": 0}))  # 不显示密码
        
        print(f"数据库中共有 {len(users)} 个用户:")
        for i, user in enumerate(users, 1):
            print(f"\n{i}. 用户ID: {user.get('user_id')}")
            print(f"   手机号: {user.get('phone')}")
            print(f"   邮箱: {user.get('email')}")
            print(f"   昵称: {user.get('nickname')}")
            print(f"   角色: {user.get('roles')}")
            print(f"   状态: {user.get('status')}")
            
        # 如果没有用户，创建一个测试用户
        if len(users) == 0:
            print("\n没有找到用户，建议创建一个测试用户...")
            
        client.close()
        
    except Exception as e:
        print(f"❌ 检查用户失败: {e}")

if __name__ == "__main__":
    check_users()