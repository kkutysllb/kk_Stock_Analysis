#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存功能测试脚本
用于验证API缓存系统是否正常工作
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any

# API基础URL
API_BASE_URL = "http://localhost:9000"

class CacheTestRunner:
    """缓存测试运行器"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_endpoint(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """测试单个端点的缓存性能"""
        url = f"{self.base_url}{endpoint}"
        
        print(f"\n🧪 测试端点: {endpoint}")
        print(f"📍 URL: {url}")
        if params:
            print(f"📋 参数: {params}")
        
        # 第一次请求（无缓存）
        start_time = time.time()
        try:
            response1 = await self.client.get(url, params=params)
            first_request_time = time.time() - start_time
            
            if response1.status_code != 200:
                print(f"❌ 请求失败: {response1.status_code} - {response1.text}")
                return {"success": False, "error": f"HTTP {response1.status_code}"}
            
            print(f"⏱️  第一次请求时间: {first_request_time:.3f}秒")
            
        except Exception as e:
            print(f"❌ 第一次请求异常: {str(e)}")
            return {"success": False, "error": str(e)}
        
        # 等待一小段时间
        await asyncio.sleep(0.1)
        
        # 第二次请求（应该命中缓存）
        start_time = time.time()
        try:
            response2 = await self.client.get(url, params=params)
            second_request_time = time.time() - start_time
            
            if response2.status_code != 200:
                print(f"❌ 第二次请求失败: {response2.status_code}")
                return {"success": False, "error": f"HTTP {response2.status_code}"}
            
            print(f"⏱️  第二次请求时间: {second_request_time:.3f}秒")
            
            # 计算性能提升
            if second_request_time > 0:
                speedup = first_request_time / second_request_time
                print(f"🚀 性能提升: {speedup:.2f}倍")
            
            # 检查响应是否一致
            if response1.text == response2.text:
                print("✅ 缓存数据一致性验证通过")
            else:
                print("⚠️  缓存数据可能不一致")
            
            return {
                "success": True,
                "first_request_time": first_request_time,
                "second_request_time": second_request_time,
                "speedup": speedup if second_request_time > 0 else 0,
                "data_consistent": response1.text == response2.text
            }
            
        except Exception as e:
            print(f"❌ 第二次请求异常: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_cache_stats(self) -> Dict[str, Any]:
        """测试缓存统计信息"""
        print("\n📊 获取缓存统计信息...")
        try:
            response = await self.client.get(f"{self.base_url}/cache/cache-stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ 缓存统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
                return stats
            else:
                print(f"❌ 获取缓存统计失败: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ 缓存统计异常: {str(e)}")
            return {}
    
    async def test_system_metrics(self) -> Dict[str, Any]:
        """测试系统指标（包含缓存状态）"""
        print("\n📈 获取系统指标...")
        try:
            response = await self.client.get(f"{self.base_url}/metrics")
            if response.status_code == 200:
                metrics = response.json()
                cache_info = metrics.get('data', {}).get('cache', {})
                print(f"✅ 缓存状态: {json.dumps(cache_info, indent=2, ensure_ascii=False)}")
                return metrics
            else:
                print(f"❌ 获取系统指标失败: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ 系统指标异常: {str(e)}")
            return {}
    
    async def run_comprehensive_test(self):
        """运行综合缓存测试"""
        print("🎯 开始Redis缓存功能综合测试")
        print("=" * 50)
        
        # 测试端点列表
        test_cases = [
            {
                "name": "股票搜索",
                "endpoint": "/stock/basic/search",
                "params": {"keyword": "平安", "limit": 10}
            },
            {
                "name": "股票列表",
                "endpoint": "/stock/basic/list",
                "params": {"market": "主板", "limit": 20}
            },
            {
                "name": "股票详情",
                "endpoint": "/stock/basic/detail/000001.SZ",
                "params": None
            },
            {
                "name": "K线数据",
                "endpoint": "/stock/kline/000001.SZ",
                "params": {"period": "daily", "limit": 30}
            },
            {
                "name": "市场指数",
                "endpoint": "/market/indices",
                "params": {"period": "daily", "limit": 10}
            },
            {
                "name": "龙虎榜",
                "endpoint": "/market/dragon-tiger",
                "params": {"limit": 10}
            },
            {
                "name": "缓存演示",
                "endpoint": "/cache/cached-stock-list",
                "params": {"market": "主板", "limit": 10}
            }
        ]
        
        results = []
        
        # 获取初始缓存统计
        initial_stats = await self.test_cache_stats()
        
        # 测试各个端点
        for test_case in test_cases:
            result = await self.test_endpoint(
                test_case["endpoint"], 
                test_case["params"]
            )
            result["test_name"] = test_case["name"]
            results.append(result)
            
            # 短暂等待
            await asyncio.sleep(0.5)
        
        # 获取最终缓存统计
        final_stats = await self.test_cache_stats()
        
        # 获取系统指标
        system_metrics = await self.test_system_metrics()
        
        # 生成测试报告
        await self.generate_test_report(results, initial_stats, final_stats)
        
        await self.client.aclose()
    
    async def generate_test_report(self, results, initial_stats, final_stats):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📋 测试报告")
        print("=" * 50)
        
        successful_tests = [r for r in results if r.get("success", False)]
        failed_tests = [r for r in results if not r.get("success", False)]
        
        print(f"✅ 成功测试: {len(successful_tests)}/{len(results)}")
        print(f"❌ 失败测试: {len(failed_tests)}/{len(results)}")
        
        if successful_tests:
            avg_speedup = sum(r.get("speedup", 0) for r in successful_tests) / len(successful_tests)
            print(f"🚀 平均性能提升: {avg_speedup:.2f}倍")
            
            avg_first_time = sum(r.get("first_request_time", 0) for r in successful_tests) / len(successful_tests)
            avg_second_time = sum(r.get("second_request_time", 0) for r in successful_tests) / len(successful_tests)
            print(f"⏱️  平均首次请求时间: {avg_first_time:.3f}秒")
            print(f"⏱️  平均缓存请求时间: {avg_second_time:.3f}秒")
        
        if failed_tests:
            print("\n❌ 失败的测试:")
            for test in failed_tests:
                print(f"  - {test.get('test_name', 'Unknown')}: {test.get('error', 'Unknown error')}")
        
        # 缓存统计对比
        if initial_stats and final_stats:
            print("\n📊 缓存统计变化:")
            initial_hits = initial_stats.get('data', {}).get('cache_hits', 0)
            final_hits = final_stats.get('data', {}).get('cache_hits', 0)
            print(f"  缓存命中增加: {final_hits - initial_hits}")
            
            initial_misses = initial_stats.get('data', {}).get('cache_misses', 0)
            final_misses = final_stats.get('data', {}).get('cache_misses', 0)
            print(f"  缓存未命中增加: {final_misses - initial_misses}")
        
        print("\n🎉 测试完成!")
        
        # 提供使用建议
        print("\n💡 使用建议:")
        print("1. 如果看到明显的性能提升，说明缓存工作正常")
        print("2. 如果性能提升不明显，可能需要调整缓存配置")
        print("3. 可以通过 /cache/cache-stats 监控缓存状态")
        print("4. 可以通过 /metrics 查看系统整体状态")

async def main():
    """主函数"""
    tester = CacheTestRunner()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    print("🚀 启动Redis缓存测试...")
    print("请确保API服务已启动 (python api/main.py)")
    print("请确保Redis服务已启动")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试异常: {str(e)}")