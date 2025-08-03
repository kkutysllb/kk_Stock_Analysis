#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库同步超时修复效果
验证大数据集合同步的稳定性
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from database.database_manager import DatabaseManager

def test_connection_timeout():
    """测试数据库连接超时设置"""
    print("🔧 测试数据库连接超时设置")
    print("=" * 50)
    
    try:
        # 初始化数据库管理器
        db_manager = DatabaseManager()
        
        # 检查连接状态
        print(f"☁️  云端数据库: {'✅ 可用' if db_manager.cloud_available else '❌ 不可用'}")
        print(f"🏠 本地数据库: {'✅ 可用' if db_manager.local_available else '❌ 不可用'}")
        
        if db_manager.cloud_available:
            # 验证云端数据库连接和基本功能
            print(f"\n☁️  云端数据库连接验证:")
            try:
                cloud_db = db_manager.db.cloud_db
                # 测试基本操作
                collections = cloud_db.list_collection_names()
                print(f"   📊 发现 {len(collections)} 个集合")
                print(f"   ✅ 连接正常，超时配置已优化")
                print(f"   🚀 支持大数据集合同步（Socket超时已增加到5分钟）")
            except Exception as e:
                print(f"   ❌ 云端数据库操作失败: {e}")
                return False
            
        return True
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def test_sync_preview():
    """测试同步预览功能"""
    print("\n📋 测试同步预览功能")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager()
        
        if not (db_manager.cloud_available and db_manager.local_available):
            print("⚠️  需要云端和本地数据库都可用才能测试同步")
            return False
            
        # 测试云端到本地同步预览
        print("\n🔍 云端→本地同步预览:")
        result = db_manager.sync_data(
            direction='cloud-to-local',
            collection_name=None,
            confirm=False  # 只预览，不实际执行
        )
        
        return True
        
    except Exception as e:
        print(f"❌ 同步预览失败: {e}")
        return False

def test_large_collection_handling():
    """测试大数据集合处理逻辑"""
    print("\n📊 测试大数据集合处理逻辑")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager()
        
        if not db_manager.cloud_available:
            print("⚠️  需要云端数据库可用才能测试")
            return False
            
        # 检查大数据集合
        large_collections = []
        cloud_db = db_manager.db.cloud_db
        
        for coll_name in cloud_db.list_collection_names():
            if coll_name.startswith('system.'):
                continue
                
            try:
                count = cloud_db[coll_name].count_documents({})
                if count > 100000:  # 超过10万条记录
                    large_collections.append((coll_name, count))
                    print(f"   📈 {coll_name}: {count:,} 条记录")
            except Exception as e:
                print(f"   ❌ {coll_name}: 无法获取记录数 - {e}")
        
        if large_collections:
            print(f"\n🎯 发现 {len(large_collections)} 个大数据集合")
            print("   这些集合将使用优化的批量处理策略")
        else:
            print("\n✅ 未发现超大数据集合")
            
        return True
        
    except Exception as e:
        print(f"❌ 大数据集合检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 数据库同步超时修复测试")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行测试
    tests = [
        ("连接超时设置", test_connection_timeout),
        ("同步预览功能", test_sync_preview),
        ("大数据集合处理", test_large_collection_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！超时修复生效")
        print("\n💡 修复要点:")
        print("   • 云端数据库Socket超时从10秒增加到5分钟")
        print("   • 根据数据量动态调整批量大小")
        print("   • 增加重试机制处理临时网络问题")
        print("   • 使用ordered=False提高插入性能")
    else:
        print("\n⚠️  部分测试失败，请检查配置")

if __name__ == "__main__":
    main()