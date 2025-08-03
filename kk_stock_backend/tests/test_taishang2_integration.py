#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试太上老君2号策略集成
验证真实的好奇布偶猫BOLL策略是否正确集成到模拟交易系统
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.simulation.strategy_adapter import StrategyRunner

async def test_taishang_2_integration():
    """测试太上老君2号策略集成"""
    print("🚀 开始测试太上老君2号策略集成...")
    
    try:
        # 创建策略运行器
        strategy_runner = StrategyRunner()
        
        # 模拟用户ID
        user_id = "test_user_123"
        
        # 模拟策略配置
        strategy_config = {
            'strategy_name': 'taishang_2',
            'allocated_cash': 400000,
            'custom_params': {}
        }
        
        print(f"📊 测试策略配置:")
        print(f"   策略名称: {strategy_config['strategy_name']}")
        print(f"   分配资金: {strategy_config['allocated_cash']:,.0f}元")
        
        # 调用策略生成信号
        print("\n🔍 开始调用BOLL策略逻辑...")
        signals = await strategy_runner.run_strategy_realtime(user_id, strategy_config)
        
        print(f"\n📈 BOLL策略执行结果:")
        print(f"   生成信号数量: {len(signals)}")
        
        if signals:
            print(f"\n🟢 买入信号详情:")
            for i, signal in enumerate(signals, 1):
                print(f"   {i}. {signal.get('stock_code')} ({signal.get('stock_name')})")
                print(f"      价格: ¥{signal.get('price', 0):.2f}")
                print(f"      数量: {signal.get('quantity', 0):,}股")
                print(f"      原因: {signal.get('reason', '未知')}")
                print(f"      金额: ¥{signal.get('price', 0) * signal.get('quantity', 0):,.2f}")
                print()
        else:
            print("   ❌ 当前市场条件下未生成买入信号")
            print("   这可能是因为:")
            print("   - 当前没有股票符合BOLL策略的买入条件")
            print("   - 布林带数据不完整") 
            print("   - 市场数据获取异常")
        
        # 验证策略逻辑是否正确加载
        print(f"\n✅ 太上老君2号策略集成测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_boll_market_data():
    """测试BOLL市场数据构建"""
    print("\n🔍 测试BOLL市场数据构建...")
    
    try:
        strategy_runner = StrategyRunner()
        
        # 测试BOLL市场数据构建
        market_data = await strategy_runner._build_boll_market_data()
        
        print(f"📊 BOLL市场数据统计:")
        print(f"   获取股票数量: {len(market_data)}")
        
        if market_data:
            # 随机选取几只股票查看数据质量
            sample_stocks = list(market_data.keys())[:3]
            print(f"\n📈 样本股票数据质量检查:")
            
            for stock_code in sample_stocks:
                data = market_data[stock_code]
                print(f"\n   📍 {stock_code}:")
                print(f"      收盘价: ¥{data.get('close', 0):.2f}")
                print(f"      前收盘: ¥{data.get('pre_close', 0):.2f}")
                print(f"      成交量: {data.get('volume', 0):,.0f}股")
                print(f"      布林上轨: ¥{data.get('boll_upper', 0):.2f}")
                print(f"      布林中轨: ¥{data.get('boll_mid', 0):.2f}")
                print(f"      布林下轨: ¥{data.get('boll_lower', 0):.2f}")
                print(f"      流通市值: {data.get('circ_mv', 0):.0f}万元")
                
                # 检查数据完整性
                required_fields = ['close', 'pre_close', 'volume', 'boll_upper', 'boll_lower']
                missing_fields = [field for field in required_fields if not data.get(field, 0)]
                
                if missing_fields:
                    print(f"      ⚠️ 缺少字段: {missing_fields}")
                else:
                    print(f"      ✅ 数据完整")
        else:
            print("   ❌ 未获取到BOLL市场数据")
            
    except Exception as e:
        print(f"❌ BOLL市场数据测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("太上老君2号策略集成测试")
    print("=" * 60)
    
    # 运行测试
    asyncio.run(test_boll_market_data())
    asyncio.run(test_taishang_2_integration())