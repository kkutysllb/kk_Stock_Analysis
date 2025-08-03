#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库同步功能测试脚本 - 增强版
测试修复后的增量同步、全量同步、并发安全等功能

运行方式：
python test_sync_enhanced.py [test_type]

test_type可选值：
- all: 运行所有测试
- incremental: 只测试增量同步
- full: 只测试全量同步
- concurrent: 只测试并发安全
- performance: 只测试性能
"""

import os
import sys
import time
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from database_manager import DatabaseManager
from data_collector_new.db_handler import DBHandler

class SyncTester:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_handler = DBHandler()
        self.test_collection = 'test_sync_collection'
        self.test_results = []
        
    def setup_test_data(self, count=1000):
        """设置测试数据"""
        print(f"🔧 设置测试数据 ({count:,} 条记录)...")
        
        # 清理测试集合
        self._cleanup_test_collections()
        
        # 生成测试数据
        test_data = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(count):
            doc = {
                'ts_code': f'00000{i % 100:02d}.SZ',
                'trade_date': (base_date + timedelta(days=i % 365)).strftime('%Y%m%d'),
                'open': round(random.uniform(10, 100), 2),
                'high': round(random.uniform(10, 100), 2),
                'low': round(random.uniform(10, 100), 2),
                'close': round(random.uniform(10, 100), 2),
                'vol': random.randint(1000, 1000000),
                'amount': round(random.uniform(1000000, 100000000), 2),
                'created_at': datetime.utcnow(),
                'seq_id': i
            }
            test_data.append(doc)
        
        # 插入到云端数据库
        if self.db_manager.cloud_available:
            cloud_collection = self.db_handler.get_cloud_collection(self.test_collection)
            cloud_collection.insert_many(test_data)
            print(f"   ☁️  云端插入完成: {count:,} 条")
        
        # 插入部分数据到本地数据库（模拟不同步状态）
        if self.db_manager.local_available:
            local_collection = self.db_handler.get_local_collection(self.test_collection)
            partial_data = test_data[:count//2]  # 只插入一半数据
            local_collection.insert_many(partial_data)
            print(f"   🏠 本地插入完成: {len(partial_data):,} 条")
        
        return True
    
    def test_incremental_sync(self):
        """测试增量同步功能"""
        print("\n📈 测试增量同步功能...")
        
        try:
            # 执行增量同步
            start_time = time.time()
            result = self.db_manager.sync_data_incremental(
                direction='cloud-to-local',
                collection_name=self.test_collection,
                confirm=True
            )
            end_time = time.time()
            
            success = result and self._verify_sync_result()
            
            self.test_results.append({
                'test': 'incremental_sync',
                'success': success,
                'duration': end_time - start_time,
                'details': f"增量同步{'成功' if success else '失败'}"
            })
            
            print(f"   {'✅' if success else '❌'} 增量同步测试: {'通过' if success else '失败'}")
            print(f"   ⏱️  耗时: {end_time - start_time:.2f} 秒")
            
            return success
            
        except Exception as e:
            print(f"   ❌ 增量同步测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_full_sync(self):
        """测试全量同步功能"""
        print("\n🔄 测试全量同步功能...")
        
        try:
            # 清空本地集合
            if self.db_manager.local_available:
                local_collection = self.db_handler.get_local_collection(self.test_collection)
                local_collection.drop()
            
            # 执行全量同步
            start_time = time.time()
            result = self.db_manager.sync_data(
                direction='cloud-to-local',
                collection_name=self.test_collection,
                confirm=True
            )
            end_time = time.time()
            
            success = result and self._verify_sync_result()
            
            self.test_results.append({
                'test': 'full_sync',
                'success': success,
                'duration': end_time - start_time,
                'details': f"全量同步{'成功' if success else '失败'}"
            })
            
            print(f"   {'✅' if success else '❌'} 全量同步测试: {'通过' if success else '失败'}")
            print(f"   ⏱️  耗时: {end_time - start_time:.2f} 秒")
            
            return success
            
        except Exception as e:
            print(f"   ❌ 全量同步测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_concurrent_sync(self):
        """测试并发同步安全性"""
        print("\n⚡ 测试并发同步安全性...")
        
        try:
            # 创建多个测试集合
            test_collections = [f'{self.test_collection}_{i}' for i in range(3)]
            
            # 为每个集合准备测试数据
            for coll_name in test_collections:
                self._prepare_collection_data(coll_name, 500)
            
            # 并发执行同步
            start_time = time.time()
            success_count = 0
            
            def sync_collection(coll_name):
                try:
                    return self.db_manager.sync_data_incremental(
                        direction='cloud-to-local',
                        collection_name=coll_name,
                        confirm=True
                    )
                except Exception as e:
                    print(f"   ⚠️  并发同步失败 {coll_name}: {e}")
                    return False
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(sync_collection, coll) for coll in test_collections]
                results = [future.result() for future in futures]
                success_count = sum(results)
            
            end_time = time.time()
            
            success = success_count == len(test_collections)
            
            self.test_results.append({
                'test': 'concurrent_sync',
                'success': success,
                'duration': end_time - start_time,
                'details': f"并发同步 {success_count}/{len(test_collections)} 成功"
            })
            
            print(f"   {'✅' if success else '❌'} 并发同步测试: {'通过' if success else '失败'}")
            print(f"   📊 成功率: {success_count}/{len(test_collections)}")
            print(f"   ⏱️  耗时: {end_time - start_time:.2f} 秒")
            
            # 清理测试集合
            for coll_name in test_collections:
                self._cleanup_collection(coll_name)
            
            return success
            
        except Exception as e:
            print(f"   ❌ 并发同步测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_performance(self):
        """测试同步性能"""
        print("\n🚀 测试同步性能...")
        
        try:
            # 测试不同数据量的同步性能
            test_sizes = [100, 1000, 5000]
            performance_results = []
            
            for size in test_sizes:
                print(f"   📊 测试数据量: {size:,} 条")
                
                # 设置测试数据
                self.setup_test_data(size)
                
                # 测试增量同步性能
                start_time = time.time()
                result = self.db_manager.sync_data_incremental(
                    direction='cloud-to-local',
                    collection_name=self.test_collection,
                    confirm=True
                )
                end_time = time.time()
                
                duration = end_time - start_time
                throughput = size / duration if duration > 0 else 0
                
                performance_results.append({
                    'size': size,
                    'duration': duration,
                    'throughput': throughput,
                    'success': result
                })
                
                print(f"      ⏱️  耗时: {duration:.2f} 秒")
                print(f"      📈 吞吐量: {throughput:.0f} 条/秒")
            
            # 计算平均性能
            avg_throughput = sum(r['throughput'] for r in performance_results) / len(performance_results)
            success = all(r['success'] for r in performance_results)
            
            self.test_results.append({
                'test': 'performance',
                'success': success,
                'duration': sum(r['duration'] for r in performance_results),
                'details': f"平均吞吐量: {avg_throughput:.0f} 条/秒"
            })
            
            print(f"   {'✅' if success else '❌'} 性能测试: {'通过' if success else '失败'}")
            print(f"   📈 平均吞吐量: {avg_throughput:.0f} 条/秒")
            
            return success
            
        except Exception as e:
            print(f"   ❌ 性能测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_error_recovery(self):
        """测试错误恢复机制"""
        print("\n🛡️ 测试错误恢复机制...")
        
        try:
            # 模拟网络中断等错误情况
            original_method = self.db_handler.get_local_collection
            
            def failing_method(name):
                if name == self.test_collection and random.random() < 0.3:
                    raise Exception("模拟网络错误")
                return original_method(name)
            
            # 临时替换方法
            self.db_handler.get_local_collection = failing_method
            
            start_time = time.time()
            try:
                result = self.db_manager.sync_data_incremental(
                    direction='cloud-to-local',
                    collection_name=self.test_collection,
                    confirm=True
                )
            finally:
                # 恢复原方法
                self.db_handler.get_local_collection = original_method
            
            end_time = time.time()
            
            # 验证错误恢复后的数据一致性
            success = self._verify_sync_result()
            
            self.test_results.append({
                'test': 'error_recovery',
                'success': success,
                'duration': end_time - start_time,
                'details': f"错误恢复测试{'成功' if success else '失败'}"
            })
            
            print(f"   {'✅' if success else '❌'} 错误恢复测试: {'通过' if success else '失败'}")
            print(f"   ⏱️  耗时: {end_time - start_time:.2f} 秒")
            
            return success
            
        except Exception as e:
            print(f"   ❌ 错误恢复测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _verify_sync_result(self):
        """验证同步结果"""
        try:
            if not (self.db_manager.cloud_available and self.db_manager.local_available):
                print("   ⚠️  双数据库不可用，跳过验证")
                return True
            
            cloud_collection = self.db_handler.get_cloud_collection(self.test_collection)
            local_collection = self.db_handler.get_local_collection(self.test_collection)
            
            cloud_count = cloud_collection.count_documents({})
            local_count = local_collection.count_documents({})
            
            print(f"   📊 数据量对比: 云端 {cloud_count:,} vs 本地 {local_count:,}")
            
            # 验证数据量是否一致
            if cloud_count != local_count:
                print(f"   ❌ 数据量不一致")
                return False
            
            # 抽样验证数据内容
            sample_size = min(10, cloud_count)
            if sample_size > 0:
                cloud_samples = list(cloud_collection.find().limit(sample_size))
                for sample in cloud_samples:
                    query = {'ts_code': sample['ts_code'], 'trade_date': sample['trade_date']}
                    local_doc = local_collection.find_one(query)
                    if not local_doc:
                        print(f"   ❌ 本地缺失记录: {query}")
                        return False
            
            print(f"   ✅ 数据验证通过")
            return True
            
        except Exception as e:
            print(f"   ❌ 验证失败: {e}")
            return False
    
    def _prepare_collection_data(self, collection_name, count):
        """为指定集合准备测试数据"""
        test_data = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(count):
            doc = {
                'ts_code': f'{collection_name}_{i % 10:02d}',
                'trade_date': (base_date + timedelta(days=i % 30)).strftime('%Y%m%d'),
                'value': random.uniform(1, 100),
                'created_at': datetime.utcnow()
            }
            test_data.append(doc)
        
        # 插入到云端
        if self.db_manager.cloud_available:
            cloud_collection = self.db_handler.get_cloud_collection(collection_name)
            cloud_collection.insert_many(test_data)
    
    def _cleanup_collection(self, collection_name):
        """清理指定集合"""
        try:
            if self.db_manager.cloud_available:
                self.db_handler.get_cloud_collection(collection_name).drop()
            if self.db_manager.local_available:
                self.db_handler.get_local_collection(collection_name).drop()
        except Exception:
            pass
    
    def _cleanup_test_collections(self):
        """清理所有测试集合"""
        test_collections = [self.test_collection]
        
        for collection_name in test_collections:
            self._cleanup_collection(collection_name)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始数据库同步功能测试")
        print("=" * 60)
        
        # 检查数据库可用性
        if not (self.db_manager.cloud_available and self.db_manager.local_available):
            print("❌ 需要云端和本地数据库都可用才能进行测试")
            return False
        
        # 设置初始测试数据
        self.setup_test_data(1000)
        
        # 运行各项测试
        tests = [
            ('增量同步', self.test_incremental_sync),
            ('全量同步', self.test_full_sync),
            ('并发安全', self.test_concurrent_sync),
            ('性能测试', self.test_performance),
            ('错误恢复', self.test_error_recovery)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔬 开始测试: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name} 测试通过")
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
        
        # 清理测试数据
        self._cleanup_test_collections()
        
        # 显示测试总结
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        
        for result in self.test_results:
            status = "✅ 通过" if result['success'] else "❌ 失败"
            print(f"{result['test']:<20} {status:<10} {result['duration']:.2f}s  {result['details']}")
        
        print(f"\n📈 总体结果: {passed_tests}/{total_tests} 项测试通过")
        success_rate = (passed_tests / total_tests) * 100
        print(f"📊 成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 测试结果良好，同步功能基本正常！")
        elif success_rate >= 60:
            print("⚠️  测试结果一般，建议检查失败的测试项")
        else:
            print("❌ 测试结果较差，需要重点修复同步功能")
        
        return success_rate >= 80

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库同步功能测试")
    parser.add_argument('test_type', nargs='?', default='all',
                       choices=['all', 'incremental', 'full', 'concurrent', 'performance', 'error'],
                       help="测试类型")
    
    args = parser.parse_args()
    
    tester = SyncTester()
    
    if args.test_type == 'all':
        success = tester.run_all_tests()
    elif args.test_type == 'incremental':
        tester.setup_test_data(1000)
        success = tester.test_incremental_sync()
        tester._cleanup_test_collections()
    elif args.test_type == 'full':
        tester.setup_test_data(1000)
        success = tester.test_full_sync()
        tester._cleanup_test_collections()
    elif args.test_type == 'concurrent':
        success = tester.test_concurrent_sync()
    elif args.test_type == 'performance':
        success = tester.test_performance()
        tester._cleanup_test_collections()
    elif args.test_type == 'error':
        tester.setup_test_data(1000)
        success = tester.test_error_recovery()
        tester._cleanup_test_collections()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 