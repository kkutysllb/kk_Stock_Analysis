#!/usr/bin/env python3
"""
测试优化后的连板龙头策略API
"""

import sys
import asyncio
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

from routers.strategy import limit_up_leader_screening
from cloud_db_handler import CloudDBHandler

class MockUser:
    """模拟用户对象"""
    def __init__(self):
        self.user_id = "test_user"
        self.username = "test"

async def test_limit_up_api():
    """测试连板龙头策略API"""
    print("🚀 测试优化后的连板龙头策略API...")
    print("=" * 60)
    
    try:
        # 模拟用户
        mock_user = MockUser()
        
        # 测试API调用
        print("📊 调用连板龙头策略API...")
        result = await limit_up_leader_screening(
            market_cap="all",
            stock_pool="all",
            limit=15,
            min_limit_times=2,
            max_limit_times=10,
            max_open_times=3,
            min_turnover=5.0,
            max_turnover=30.0,
            current_user=mock_user
        )
        
        print(f"✅ API调用成功!")
        print(f"策略名称: {result.strategy_name}")
        print(f"策略类型: {result.strategy_type}")
        print(f"筛选时间: {result.screening_time}")
        print(f"筛选结果: {result.total_count} 只股票")
        print("-" * 60)
        
        if result.results:
            for i, stock in enumerate(result.results, 1):
                special = stock.special or {}
                print(f"{i:2d}. {stock.ts_code} - {stock.name}")
                print(f"    行业: {stock.industry}")
                print(f"    连板次数: {special.get('limit_times')}连板")
                print(f"    开板次数: {special.get('open_times')}次")
                print(f"    涨跌幅: {stock.pct_chg:.2f}%")
                print(f"    成交额: {(special.get('amount') or 0) / 10000:.2f}万元")
                print(f"    总市值: {(stock.total_mv or 0) / 10000:.2f}万元")
                print(f"    换手率: {special.get('turnover_rate', 0):.2f}%")
                print(f"    板块涨停数: {special.get('sector_up_nums')}只")
                print(f"    龙头评分: {stock.score:.2f}分")
                print(f"    龙头信号: {'🔥 强龙头' if special.get('leader_signal') else '⚠️ 观察'}")
                print("-" * 40)
        else:
            print("❌ 没有找到符合条件的连板龙头股票")
        
        # 测试不同参数组合
        print(f"\n🔍 测试严格筛选参数...")
        strict_result = await limit_up_leader_screening(
            market_cap="large",           # 大盘股
            stock_pool="all",
            limit=10,
            min_limit_times=3,           # 最少3连板
            max_limit_times=6,           # 最多6连板
            max_open_times=1,            # 最多开板1次
            min_turnover=8.0,            # 最小换手率8%
            max_turnover=25.0,           # 最大换手率25%
            current_user=mock_user
        )
        
        print(f"严格筛选结果: {strict_result.total_count} 只股票")
        
        if strict_result.results:
            for i, stock in enumerate(strict_result.results, 1):
                print(f"{i}. {stock.ts_code} - {stock.name} ({stock.limit_times}连板, 评分:{stock.score:.1f})")
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_limit_up_api())