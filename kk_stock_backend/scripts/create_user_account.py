#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建用户账号的脚本
"""

import sys
import os
import uuid
import bcrypt
from datetime import datetime

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from api.cloud_db_handler import CloudDBHandler

def create_user_account():
    """创建用户账号"""
    try:
        # 使用API专用的数据库处理器
        db_handler = CloudDBHandler()
        users_col = db_handler.get_collection('users')
        
        # 检查用户是否已存在
        existing_user = users_col.find_one({'phone': '+8618092401097'})
        if existing_user:
            print(f"用户已存在: {existing_user['_id']}")
            return existing_user
        
        # 创建新用户
        user_data = {
            'user_id': str(uuid.uuid4()),
            'phone': '+8618092401097',
            'email': '3842627@qq.com',
            'nickname': '拉萨之狐',
            'password': bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),  # 默认密码
            'password_hash': bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'roles': ['user'],
            'status': 1,
            'create_time': datetime.now().isoformat(),
            'last_login': None,
            'login_count': 0,
            'is_online': False,
            'permissions': {
                'user_management': False,
                'system_management': False,
                'data_management': False,
                'all_access': False
            }
        }
        
        # 插入用户
        result = users_col.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        
        print(f"✅ 用户创建成功: {user_data['nickname']} (ID: {result.inserted_id})")
        print(f"📱 手机号: {user_data['phone']}")
        print(f"📧 邮箱: {user_data['email']}")
        print(f"🔐 默认密码: 123456")
        
        return user_data
        
    except Exception as e:
        print(f"创建用户失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_user_account()