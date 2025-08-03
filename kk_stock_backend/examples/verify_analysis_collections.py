#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证分析结果数据库集合创建脚本
"""

import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from api.cloud_db_handler import CloudDBHandler

def verify_analysis_collections():
    """验证分析结果相关的数据库集合"""
    try:
        # 初始化数据库处理器
        db_handler = CloudDBHandler()
        
        print("🔍 检查分析结果相关数据库集合...")
        
        # 获取数据库连接信息
        connection_info = db_handler.get_connection_info()
        print(f"📡 数据库连接状态: {connection_info}")
        
        # 检查现有集合
        db = db_handler.get_api_db()
        existing_collections = db.list_collection_names()
        
        print(f"\n📋 现有集合列表 ({len(existing_collections)}个):")
        for collection in sorted(existing_collections):
            count = db[collection].count_documents({})
            print(f"  - {collection}: {count:,} 条记录")
        
        # 检查分析结果相关集合
        analysis_collections = [
            "user_analysis_results",
            "user_analysis_operations"
        ]
        
        print(f"\n🎯 分析结果相关集合状态:")
        for collection_name in analysis_collections:
            if collection_name in existing_collections:
                count = db[collection_name].count_documents({})
                print(f"  ✅ {collection_name}: 已存在，{count:,} 条记录")
                
                # 显示最近的几条记录
                if count > 0:
                    recent_docs = list(db[collection_name].find().sort("_id", -1).limit(3))
                    print(f"    📝 最近记录预览:")
                    for i, doc in enumerate(recent_docs, 1):
                        if collection_name == "user_analysis_results":
                            stock_info = f"{doc.get('stock_name', 'N/A')} ({doc.get('stock_code', 'N/A')})"
                            analysis_type = doc.get('analysis_type', 'N/A')
                            create_time = doc.get('create_time', 'N/A')
                            print(f"      {i}. {stock_info} - {analysis_type} - {create_time}")
                        else:
                            operation_type = doc.get('operation_type', 'N/A')
                            description = doc.get('description', 'N/A')
                            operation_time = doc.get('operation_time', 'N/A')
                            print(f"      {i}. {operation_type}: {description} - {operation_time}")
            else:
                print(f"  ⏳ {collection_name}: 尚未创建（首次插入数据时将自动创建）")
        
        # 检查用户相关集合
        user_collections = [coll for coll in existing_collections if 'user' in coll.lower()]
        if user_collections:
            print(f"\n👥 用户相关集合:")
            for collection_name in sorted(user_collections):
                count = db[collection_name].count_documents({})
                print(f"  - {collection_name}: {count:,} 条记录")
        
        print(f"\n📊 数据库集合总结:")
        print(f"  - 总集合数: {len(existing_collections)}")
        print(f"  - 用户相关集合: {len(user_collections)}")
        print(f"  - 分析结果集合: {len([c for c in analysis_collections if c in existing_collections])}/2")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False

def test_collection_auto_creation():
    """测试集合自动创建功能"""
    try:
        print(f"\n🧪 测试集合自动创建功能...")
        
        db_handler = CloudDBHandler()
        db = db_handler.get_api_db()
        
        # 检查测试集合是否存在
        test_collection_name = "test_auto_creation"
        existing_collections = db.list_collection_names()
        
        if test_collection_name in existing_collections:
            print(f"  📝 删除已存在的测试集合: {test_collection_name}")
            db.drop_collection(test_collection_name)
        
        # 插入测试数据
        test_doc = {
            "test_field": "test_value",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        print(f"  📝 向不存在的集合插入测试数据...")
        collection = db[test_collection_name]
        result = collection.insert_one(test_doc)
        
        print(f"  ✅ 插入成功，文档ID: {result.inserted_id}")
        
        # 验证集合已创建
        updated_collections = db.list_collection_names()
        if test_collection_name in updated_collections:
            count = db[test_collection_name].count_documents({})
            print(f"  ✅ 集合自动创建成功: {test_collection_name}, 记录数: {count}")
        else:
            print(f"  ❌ 集合创建失败")
            return False
        
        # 清理测试数据
        print(f"  🧹 清理测试数据...")
        db.drop_collection(test_collection_name)
        print(f"  ✅ 测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        return False

if __name__ == "__main__":
    print("🚀 分析结果数据库集合验证工具")
    print("=" * 50)
    
    # 验证现有集合
    verify_success = verify_analysis_collections()
    
    # 测试自动创建功能
    test_success = test_collection_auto_creation()
    
    print("\n" + "=" * 50)
    if verify_success and test_success:
        print("✅ 所有验证通过！")
        print("📢 总结:")
        print("  - MongoDB会在首次插入数据时自动创建集合")
        print("  - 不需要手动初始化数据库集合")
        print("  - 前端分析完成后会自动保存到数据库")
    else:
        print("❌ 验证过程中出现问题")
        
    print("\n📝 使用说明:")
    print("  1. 前端完成分析后，数据会自动保存到数据库")
    print("  2. 如果集合不存在，MongoDB会自动创建")
    print("  3. 可以通过API接口查询历史分析结果")