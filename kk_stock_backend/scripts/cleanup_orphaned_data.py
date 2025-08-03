#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理孤立数据脚本
删除所有非管理员的用户相关数据，包括已删除用户的孤立数据
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from api.cloud_db_handler import CloudDBHandler


def cleanup_orphaned_data():
    """清理孤立数据"""
    
    # 管理员用户ID
    admin_user_id = "946c1533-e852-45ca-abe2-54b9864b63b8"
    
    # 需要清理的集合
    collections_to_clean = [
        "user_stock_pools",
        "user_pool_operations",
        "strategy_screening_results", 
        "user_analysis_operations",
        "user_analysis_results",
        "test_user_watchlist"
    ]
    
    db_handler = CloudDBHandler()
    
    print("🧹 清理所有非管理员用户的孤立数据...")
    print(f"📋 保留管理员ID: {admin_user_id}")
    print("-" * 60)
    
    total_deleted = 0
    
    for collection_name in collections_to_clean:
        try:
            collection = db_handler.get_collection(collection_name)
            
            # 先检查当前记录数
            total_count = collection.count_documents({})
            non_admin_count = collection.count_documents({
                "user_id": {"$ne": admin_user_id}
            })
            
            print(f"📊 {collection_name}:")
            print(f"   总记录: {total_count}, 非管理员记录: {non_admin_count}")
            
            if non_admin_count > 0:
                # 删除所有非管理员的数据
                result = collection.delete_many({
                    "user_id": {"$ne": admin_user_id}
                })
                
                print(f"   ✅ 删除: {result.deleted_count} 条记录")
                total_deleted += result.deleted_count
            else:
                print(f"   ✅ 无需清理")
            
        except Exception as e:
            print(f"   ❌ 清理失败: {str(e)}")
    
    print("-" * 60)
    print(f"📊 清理完成，总计删除: {total_deleted} 条记录")
    
    # 验证清理结果
    print("\n🔍 验证清理结果:")
    for collection_name in collections_to_clean:
        try:
            collection = db_handler.get_collection(collection_name)
            remaining_non_admin = collection.count_documents({
                "user_id": {"$ne": admin_user_id}
            })
            
            if remaining_non_admin == 0:
                print(f"   ✅ {collection_name}: 清理完成")
            else:
                print(f"   ⚠️  {collection_name}: 仍有 {remaining_non_admin} 条非管理员数据")
                
        except Exception as e:
            print(f"   ❌ {collection_name}: 检查失败 - {str(e)}")


if __name__ == "__main__":
    cleanup_orphaned_data()