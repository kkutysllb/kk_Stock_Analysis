#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置管理员用户脚本
删除测试用户和超级管理员用户，重建新的超级管理员用户
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient
from passlib.context import CryptContext
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 密码加密上下文 - 与API接口相同的加密方式
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    return pwd_context.hash(password)

def main():
    # 数据库连接配置
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@127.0.0.1:27017/authSource=admin")
    DB_NAME = os.getenv("DB_NAME", "quant_analysis")
    
    try:
        # 连接数据库
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        users_col = db["users"]
        
        print("🔗 已连接到数据库")
        
        # 查看当前用户数量
        current_count = users_col.count_documents({})
        print(f"📊 当前用户总数: {current_count}")
        
        # 删除所有现有用户（包括测试用户和超级管理员）
        delete_result = users_col.delete_many({})
        print(f"🗑️ 已删除 {delete_result.deleted_count} 个用户")
        
        # 创建新的超级管理员用户
        admin_phone = "+8613609247807"
        admin_email = "31468130@qq.com"
        admin_password = "Imscfg_2252"
        
        # 生成用户ID
        import time
        import random
        user_id = f"admin_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # 创建管理员用户文档
        now = datetime.utcnow()
        admin_doc = {
            "user_id": user_id,
            "phone": admin_phone,
            "email": admin_email,
            "password_hash": hash_password(admin_password),  # 使用bcrypt加密
            "nickname": "超级管理员",
            "roles": ["admin", "analyst", "operator", "user"],  # 拥有所有权限
            "status": 1,  # 激活状态
            "create_time": now,
            "last_login": None,
            "login_count": 0,
            "module_call_count": 0,
            "module_call_detail": {},
            "recharge_amount": 9999999999,  # 无限额度
            "recharge_order_id": "UNLIMITED"
        }
        
        # 插入管理员用户
        result = users_col.insert_one(admin_doc)
        
        print("✅ 超级管理员用户创建成功！")
        print(f"📱 手机号: {admin_phone}")
        print(f"📧 邮箱: {admin_email}")
        print(f"🆔 用户ID: {user_id}")
        print(f"🔑 密码: {admin_password} (已使用bcrypt加密存储)")
        print(f"👑 角色: {admin_doc['roles']}")
        print(f"💰 充值额度: {admin_doc['recharge_amount']}")
        
        # 验证创建结果
        final_count = users_col.count_documents({})
        print(f"📊 操作后用户总数: {final_count}")
        
        # 验证密码加密
        stored_user = users_col.find_one({"user_id": user_id})
        if stored_user:
            print(f"🔐 密码哈希值: {stored_user['password_hash'][:50]}...")
            # 验证密码是否正确
            is_valid = pwd_context.verify(admin_password, stored_user['password_hash'])
            print(f"✅ 密码验证: {'通过' if is_valid else '失败'}")
        
        client.close()
        print("🎉 操作完成！")
        
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 开始重置管理员用户...")
    main()