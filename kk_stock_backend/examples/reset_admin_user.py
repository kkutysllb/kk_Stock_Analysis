#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置超级管理员用户
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def reset_admin_user():
    """重置超级管理员用户"""
    # 数据库连接
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@127.0.0.1:27017/?authSource=admin")
    DB_NAME = os.getenv("DB_NAME", "quant_analysis")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        users_col = db["users"]
        
        print("🔄 开始重置超级管理员用户...")
        
        # 查找现有的超级管理员
        admin_users = list(users_col.find({
            "$or": [
                {"user_id": "super_admin_001"},
                {"roles": {"$in": ["super_admin"]}},
                {"phone": "+8613800000001"}
            ]
        }))
        
        print(f"📋 找到 {len(admin_users)} 个管理员用户:")
        for user in admin_users:
            print(f"  - {user.get('user_id', 'N/A')}: {user.get('phone', 'N/A')} ({user.get('nickname', 'N/A')})")
        
        if admin_users:
            confirm = input("\n❓ 确认删除这些管理员用户吗？(y/N): ")
            if confirm.lower() == 'y':
                # 删除现有管理员
                result = users_col.delete_many({
                    "$or": [
                        {"user_id": "super_admin_001"},
                        {"roles": {"$in": ["super_admin"]}},
                        {"phone": "+8613800000001"}
                    ]
                })
                print(f"✅ 已删除 {result.deleted_count} 个管理员用户")
            else:
                print("❌ 取消删除操作")
        else:
            print("✅ 没有找到管理员用户")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 重置失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_admin_user() 