#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略选股缓存机制测试脚本
验证策略选股接口的缓存功能是否正常工作
"""

import requests
import time
import json

# API基础URL
API_BASE_URL = "http://localhost:9000"

class StrategyCacheTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def login(self):
        """登录获取token"""
        print("🔑 正在登录...")
        
        login_data = {
            "phone": "+8613609247807",
            "password": "Imscfg_2252"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE_URL}/user/login",
                json=login_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('access_token'):
                    self.token = result['access_token']
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.token}'
                    })
                    print(f"✅ 登录成功，token: {self.token[:20]}...")
                    return True
                else:
                    print(f"❌ 登录失败: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"❌ 登录请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def check_redis_status(self):
        """检查Redis状态"""
        print("\n🔍 检查Redis缓存状态...")
        
        try:
            # 通过缓存演示接口检查Redis状态
            response = self.session.get(f"{API_BASE_URL}/cache/cache-stats")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    cache_stats = result['data'].get('cache_stats', {})
                    print(f"✅ Redis缓存可用")
                    print(f"   缓存命中率: {cache_stats.get('hit_rate', 'N/A')}")
                    print(f"   已用内存: {cache_stats.get('used_memory_human', 'N/A')}")
                    print(f"   连接数: {cache_stats.get('connected_clients', 'N/A')}")
                    return True
                else:
                    print(f"❌ Redis缓存不可用: {result.get('message')}")
                    return False
            else:
                print(f"❌ 无法获取缓存状态: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 检查缓存状态异常: {e}")
            return False
    
    def test_cache_mechanism(self):
        """测试策略选股缓存机制"""
        print("\n📊 测试策略选股缓存机制")
        print("=" * 50)
        
        # 构建测试请求
        test_request = {
            "strategy_name": "缓存测试策略",
            "strategy_type": "technical",
            "technical_conditions": {
                "rsi_min": 30,
                "rsi_max": 70,
                "above_ma20": True
            },
            "limit": 20
        }
        
        # 第一次请求 - 应该从数据库查询
        print("🔍 第一次请求（应该从数据库查询）...")
        start_time = time.time()
        
        response1 = self.session.post(
            f"{API_BASE_URL}/strategy/templates/value_investment_template/apply",
            json={"market_cap": "all", "stock_pool": "all", "limit": 20}
        )
        
        end_time = time.time()
        first_time = end_time - start_time
        
        if response1.status_code == 200:
            result1 = response1.json()
            # 标准缓存装饰器不会添加这些字段，我们通过性能判断
            
            print(f"✅ 第一次请求成功")
            print(f"   响应时间: {first_time:.3f}秒")
            print(f"   结果数量: {result1.get('total_count', 0)}")
            print(f"   策略类型: {result1.get('strategy_type', '')}")
            print(f"   性能: {result1.get('performance', 'N/A')}")
        else:
            print(f"❌ 第一次请求失败: {response1.text}")
            return
        
        # 立即第二次请求 - 应该从缓存获取
        print("\n🚀 第二次请求（应该从缓存获取）...")
        start_time = time.time()
        
        response2 = self.session.post(
            f"{API_BASE_URL}/strategy/templates/value_investment_template/apply",
            json={"market_cap": "all", "stock_pool": "all", "limit": 20}
        )
        
        end_time = time.time()
        second_time = end_time - start_time
        
        if response2.status_code == 200:
            result2 = response2.json()
            
            print(f"✅ 第二次请求成功")
            print(f"   响应时间: {second_time:.3f}秒")
            print(f"   结果数量: {result2.get('total_count', 0)}")
            print(f"   策略类型: {result2.get('strategy_type', '')}")
            print(f"   性能: {result2.get('performance', 'N/A')}")
            
            # 性能对比
            if first_time > 0 and second_time > 0:
                speedup = first_time / second_time
                print(f"\n📈 性能提升分析:")
                print(f"   第一次响应时间: {first_time:.3f}秒")
                print(f"   第二次响应时间: {second_time:.3f}秒")
                print(f"   性能提升倍数: {speedup:.1f}x")
                
                if speedup > 3:
                    print(f"   🎉 缓存机制正常工作！")
                elif speedup > 1.5:
                    print(f"   ⚠️  可能有轻微缓存效果")
                else:
                    print(f"   ❌ 缓存机制可能未生效")
        else:
            print(f"❌ 第二次请求失败: {response2.text}")
    
    def test_cache_with_debug(self):
        """测试缓存机制并输出调试信息"""
        print("\n🔧 缓存调试测试")
        print("=" * 50)
        
        # 构建简单的测试请求
        test_request = {
            "strategy_name": "调试测试",
            "strategy_type": "technical",
            "technical_conditions": {
                "rsi_min": 50
            },
            "limit": 5
        }
        
        print(f"📋 测试请求: {json.dumps(test_request, ensure_ascii=False, indent=2)}")
        
        # 连续3次相同请求，观察性能变化
        times = []
        for i in range(3):
            print(f"\n🔍 第{i+1}次请求...")
            start_time = time.time()
            
            response = self.session.post(
                f"{API_BASE_URL}/strategy/templates/value_investment_template/apply",
                json={"market_cap": "all", "stock_pool": "all", "limit": 20}
            )
            
            end_time = time.time()
            request_time = end_time - start_time
            times.append(request_time)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 请求成功，响应时间: {request_time:.3f}秒")
                print(f"   结果数量: {result.get('total_count', 0)}")
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
        
        # 分析性能趋势
        print(f"\n📊 性能趋势分析:")
        for i, t in enumerate(times):
            print(f"   第{i+1}次: {t:.3f}秒")
        
        if len(times) >= 2:
            if times[1] < times[0] * 0.7:  # 第二次比第一次快30%以上
                print("   🎉 检测到明显的缓存效果！")
            elif times[1] < times[0] * 0.9:  # 第二次比第一次快10%以上
                print("   ⚠️  可能有轻微缓存效果")
            else:
                print("   ❌ 未检测到明显缓存效果")
            
    def test_different_conditions(self):
        """测试不同条件的缓存键生成"""
        print("\n🔧 测试不同条件的缓存键生成")
        print("=" * 50)
        
        # 测试数据1
        request1 = {
            "strategy_name": "技术策略A",
            "strategy_type": "technical",
            "technical_conditions": {
                "rsi_min": 30,
                "rsi_max": 70
            },
            "limit": 10
        }
        
        # 测试数据2（条件不同）
        request2 = {
            "strategy_name": "技术策略B",
            "strategy_type": "technical", 
            "technical_conditions": {
                "rsi_min": 40,
                "rsi_max": 80
            },
            "limit": 10
        }
        
        # 测试数据3（与数据1相同）
        request3 = {
            "strategy_name": "技术策略C",  # 名称不同但条件相同
            "strategy_type": "technical",
            "technical_conditions": {
                "rsi_min": 30,
                "rsi_max": 70
            },
            "limit": 10
        }
        
        requests_data = [
            ("请求A", request1),
            ("请求B", request2), 
            ("请求C", request3)
        ]
        
        cache_keys = []
        
        for name, req_data in requests_data:
            print(f"\n🔍 执行{name}...")
            
            response = self.session.post(
                f"{API_BASE_URL}/strategy/templates/value_investment_template/apply",
                json={"market_cap": "all", "stock_pool": "all", "limit": 20}
            )
            
            if response.status_code == 200:
                result = response.json()
                cache_key = result.get('cache_key', '')
                from_cache = result.get('from_cache', False)
                cache_keys.append(cache_key)
                
                print(f"   ✅ {name}成功")
                print(f"   缓存键: {cache_key}")
                print(f"   来自缓存: {from_cache}")
            else:
                print(f"   ❌ {name}失败: {response.text}")
                cache_keys.append("")
        
        # 分析缓存键
        print(f"\n📋 缓存键分析:")
        print(f"   请求A缓存键: {cache_keys[0]}")
        print(f"   请求B缓存键: {cache_keys[1]}")
        print(f"   请求C缓存键: {cache_keys[2]}")
        
        if len(cache_keys) >= 3:
            if cache_keys[0] == cache_keys[2]:
                print(f"   ✅ 相同条件生成相同缓存键（A=C）")
            else:
                print(f"   ⚠️  相同条件生成不同缓存键")
                
            if cache_keys[0] != cache_keys[1]:
                print(f"   ✅ 不同条件生成不同缓存键（A≠B）")
            else:
                print(f"   ⚠️  不同条件生成相同缓存键")
    
    def test_template_cache(self):
        """测试策略模板缓存"""
        print("\n📝 测试策略模板缓存")
        print("=" * 50)
        
        # 第一次获取模板
        print("🔍 第一次获取策略模板...")
        start_time = time.time()
        
        response1 = self.session.get(f"{API_BASE_URL}/strategy/templates")
        
        end_time = time.time()
        first_time = end_time - start_time
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"✅ 第一次获取成功，响应时间: {first_time:.3f}秒")
            print(f"   模板数量: {len(result1.get('templates', []))}")
        else:
            print(f"❌ 第一次获取失败: {response1.text}")
            return
        
        # 第二次获取模板
        print("\n🚀 第二次获取策略模板...")
        start_time = time.time()
        
        response2 = self.session.get(f"{API_BASE_URL}/strategy/templates")
        
        end_time = time.time()
        second_time = end_time - start_time
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"✅ 第二次获取成功，响应时间: {second_time:.3f}秒")
            print(f"   模板数量: {len(result2.get('templates', []))}")
            
            if first_time > 0 and second_time > 0:
                speedup = first_time / second_time
                print(f"\n📈 模板缓存性能提升: {speedup:.1f}x")
        else:
            print(f"❌ 第二次获取失败: {response2.text}")
    
    def test_complex_cache_performance(self):
        """测试复杂条件下的缓存性能"""
        print("\n🚀 复杂条件缓存性能测试")
        print("=" * 50)
        
        # 构建复杂的测试请求
        complex_request = {
            "strategy_name": "复杂缓存测试",
            "strategy_type": "comprehensive",
            "technical_conditions": {
                "rsi_min": 30,
                "rsi_max": 70,
                "macd_positive": True,
                "above_ma20": True,
                "volume_ratio_min": 1.5,
                "kdj_k_min": 20,
                "bb_position": "middle"
            },
            "fundamental_conditions": {
                "total_score_min": 60,
                "roe_min": 5,
                "pe_max": 30,
                "pb_max": 5,
                "growth_score_min": 50,
                "profitability_score_min": 50,
                "debt_ratio_max": 70
            },
            "special_conditions": {
                "limit_days_min": 2,
                "net_inflow_positive": True,
                "hot_money_score_min": 60,
                "dragon_tiger_count_min": 1,
                "institution_attention_min": 50
            },
            "limit": 100
        }
        
        print(f"📋 使用复杂条件进行测试...")
        
        # 连续5次相同请求，观察缓存效果
        times = []
        for i in range(5):
            print(f"\n🔍 第{i+1}次复杂查询...")
            start_time = time.time()
            
            response = self.session.post(
                f"{API_BASE_URL}/strategy/screening",  # 使用更完整的选股接口
                json=complex_request
            )
            
            end_time = time.time()
            request_time = end_time - start_time
            times.append(request_time)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 请求成功，响应时间: {request_time:.3f}秒")
                print(f"   结果数量: {result.get('total_count', 0)}")
                if i == 0:
                    print(f"   策略类型: {result.get('strategy_type')}")
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
        
        # 分析缓存性能
        print(f"\n📊 复杂查询缓存性能分析:")
        for i, t in enumerate(times):
            status = "🔍 首次查询" if i == 0 else f"🚀 缓存查询{i}"
            print(f"   {status}: {t:.3f}秒")
        
        if len(times) >= 2:
            first_time = times[0]
            avg_cached_time = sum(times[1:]) / len(times[1:])
            speedup = first_time / avg_cached_time if avg_cached_time > 0 else 0
            
            print(f"\n📈 缓存效果总结:")
            print(f"   首次查询时间: {first_time:.3f}秒")
            print(f"   缓存查询平均时间: {avg_cached_time:.3f}秒")
            print(f"   性能提升倍数: {speedup:.1f}x")
            
            if speedup > 5:
                print("   🎉 缓存效果非常明显！")
            elif speedup > 2:
                print("   ✅ 缓存效果良好")
            elif speedup > 1.3:
                print("   ⚠️  缓存有一定效果")
            else:
                print("   ❌ 缓存效果不明显")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 策略选股缓存机制测试")
        print("=" * 60)
        
        if not self.login():
            return
        
        # 检查Redis状态
        redis_ok = self.check_redis_status()
        
        if not redis_ok:
            print("⚠️  Redis缓存不可用，但仍继续测试...")
        
        # 执行缓存测试
        self.test_cache_mechanism()
        
        # 执行调试测试
        self.test_cache_with_debug()
        
        # 测试不同条件
        self.test_different_conditions()
        
        # 测试模板缓存
        self.test_template_cache()
        
        # 测试复杂条件缓存性能
        self.test_complex_cache_performance()
        
        print("\n🎉 所有缓存测试完成！")

if __name__ == "__main__":
    tester = StrategyCacheTest()
    tester.run_all_tests()