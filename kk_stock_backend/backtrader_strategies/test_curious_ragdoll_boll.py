#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
好奇布偶猫BOLL策略调试测试脚本
检查策略信号生成问题
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curious_ragdoll_boll_strategy_adapter import CuriousRagdollBollStrategyAdapter
from backtest.data_manager import DataManager
from config import Config


def test_data_availability():
    """测试数据可用性"""
    print("🔍 测试数据可用性...")
    
    config = Config()
    data_manager = DataManager(config.database)
    
    # 加载一只股票的数据进行检查
    test_stock = "000001.SZ"
    
    try:
        # 直接查询数据库
        collection = data_manager.client[config.database.database_name]['stock_factor_pro']
        
        # 查询一条记录
        sample = collection.find_one(
            {"code": test_stock},
            sort=[("trade_date", -1)]
        )
        
        if sample:
            print(f"✅ 找到 {test_stock} 的数据")
            
            # 检查布林带字段
            boll_fields = ['boll_upper_bfq', 'boll_mid_bfq', 'boll_lower_bfq']
            available_fields = []
            missing_fields = []
            
            for field in boll_fields:
                if field in sample and sample[field] is not None:
                    available_fields.append(field)
                    print(f"  ✅ {field}: {sample[field]}")
                else:
                    missing_fields.append(field)
                    print(f"  ❌ {field}: 缺失")
            
            # 检查其他关键字段
            key_fields = ['close', 'pre_close', 'volume', 'amount', 'circ_mv']
            for field in key_fields:
                if field in sample and sample[field] is not None:
                    print(f"  ✅ {field}: {sample[field]}")
                else:
                    print(f"  ❌ {field}: 缺失")
                    
            return len(available_fields) == 3
        else:
            print(f"❌ 未找到 {test_stock} 的数据")
            return False
            
    except Exception as e:
        print(f"❌ 数据查询失败: {e}")
        return False


def test_strategy_signals():
    """测试策略信号生成"""
    print("\n🎯 测试策略信号生成...")
    
    strategy = CuriousRagdollBollStrategyAdapter()
    
    # 初始化策略
    context = {
        'initial_cash': 1000000,
        'start_date': '2020-01-01',
        'end_date': '2025-07-18'
    }
    strategy.initialize(context)
    
    # 构造测试数据 - 使用正确的布林带字段名
    mock_market_data = {
        '000001.SZ': {
            'close': 10.50,
            'pre_close': 9.80,          # 前收盘价跌破下轨
            'volume': 2000000,
            'amount': 21000000,
            'circ_mv': 1500,            # 万元，对应150亿市值
            'boll_upper_bfq': 11.0,     # 布林带上轨
            'boll_mid_bfq': 10.5,       # 布林带中轨
            'boll_lower_bfq': 10.0,     # 布林带下轨
        }
    }
    
    portfolio_info = {
        'total_value': 1000000,
        'cash_ratio': 0.8,
        'total_positions': 0
    }
    
    # 测试信号生成
    test_date = "2024-12-31"
    signals = strategy.generate_signals(test_date, mock_market_data, portfolio_info)
    
    print(f"\n📊 {test_date} 测试结果:")
    print(f"总信号数: {len(signals)}")
    
    buy_signals = [s for s in signals if s['action'] == 'buy']
    sell_signals = [s for s in signals if s['action'] == 'sell']
    
    print(f"买入信号: {len(buy_signals)} 个")
    for signal in buy_signals:
        print(f"  🟢 {signal['stock_code']}: 价格{signal['price']:.2f}元, 得分={signal.get('boll_score', 0):.1f}")
    
    print(f"卖出信号: {len(sell_signals)} 个")
    for signal in sell_signals:
        print(f"  🔴 {signal['stock_code']}: {signal.get('reason', '未知原因')}")
    
    # 测试买入条件检查
    print(f"\n🔍 详细买入条件分析:")
    stock_code = '000001.SZ'
    stock_data = mock_market_data[stock_code]
    
    # 检查股票质量过滤
    is_qualified = strategy._is_stock_qualified(stock_code, stock_data)
    print(f"股票质量过滤: {'✅ 通过' if is_qualified else '❌ 不通过'}")
    
    # 检查买入信号
    should_buy = strategy._check_buy_signal(stock_code, stock_data)
    print(f"买入信号检查: {'✅ 应该买入' if should_buy else '❌ 不应买入'}")
    
    # 详细条件分析
    current_price = stock_data.get('close', 0)
    prev_price = stock_data.get('pre_close', 0)
    boll_lower = stock_data.get('boll_lower_bfq', 0)
    
    print(f"\n买入条件详细分析:")
    print(f"  当前价格: {current_price}")
    print(f"  前收盘价: {prev_price}")
    print(f"  布林下轨: {boll_lower}")
    
    condition1 = prev_price < boll_lower
    condition2 = current_price > prev_price
    condition3 = True  # 简化处理
    condition4 = len(strategy.positions_info) < strategy.params['max_positions']
    
    print(f"  条件1 (前价跌破下轨): {'✅' if condition1 else '❌'} ({prev_price} < {boll_lower})")
    print(f"  条件2 (当前价反弹): {'✅' if condition2 else '❌'} ({current_price} > {prev_price})")
    print(f"  条件3 (高于前期低点): {'✅' if condition3 else '❌'} (简化为True)")
    print(f"  条件4 (仓位控制): {'✅' if condition4 else '❌'} (持仓{len(strategy.positions_info)} < {strategy.params['max_positions']})")
    
    all_conditions = all([condition1, condition2, condition3, condition4])
    print(f"  所有条件: {'✅ 满足' if all_conditions else '❌ 不满足'}")
    
    return len(signals) > 0


def test_candidate_stocks():
    """测试候选股票筛选"""
    print("\n📋 测试候选股票筛选...")
    
    strategy = CuriousRagdollBollStrategyAdapter()
    
    # 构造多只股票数据
    mock_market_data = {
        '000001.SZ': {  # 符合条件的股票
            'close': 10.50,
            'pre_close': 9.80,
            'volume': 2000000,
            'amount': 21000000,
            'circ_mv': 1500,  # 150亿市值
            'boll_lower_bfq': 10.0
        },
        '000002.SZ': {  # 价格太低
            'close': 2.50,
            'pre_close': 2.40,
            'volume': 1500000,
            'amount': 3750000,
            'circ_mv': 800,   # 80亿市值
            'boll_lower_bfq': 2.60
        },
        '000003.SZ': {  # 成交量太小
            'close': 15.50,
            'pre_close': 15.20,
            'volume': 500000,    # 成交量不足
            'amount': 7750000,
            'circ_mv': 2000,     # 200亿市值
            'boll_lower_bfq': 15.80
        },
        '000004.SZ': {  # 市值太大
            'close': 25.50,
            'pre_close': 25.20,
            'volume': 3000000,
            'amount': 76500000,
            'circ_mv': 8000,     # 800亿市值，超过500亿限制
            'boll_lower_bfq': 26.0
        }
    }
    
    # 测试候选股票获取
    candidate_stocks = strategy._get_candidate_stocks(mock_market_data)
    print(f"候选股票数量: {len(candidate_stocks)}")
    for stock in candidate_stocks:
        market_cap = mock_market_data[stock]['circ_mv'] * 1e4
        print(f"  ✅ {stock}: 市值{market_cap/1e8:.0f}亿元")
    
    # 测试每只股票的过滤结果
    print(f"\n详细过滤分析:")
    for stock_code, stock_data in mock_market_data.items():
        is_qualified = strategy._is_stock_qualified(stock_code, stock_data)
        price = stock_data['close']
        volume = stock_data['volume']
        amount = stock_data['amount']
        market_cap = stock_data['circ_mv'] / 100  # 万元转换为亿元 (1500万元 = 15亿元)
        
        print(f"  {stock_code}: {'✅' if is_qualified else '❌'}")
        print(f"    价格: {price:.2f} (≥3.0: {'✅' if price >= 3.0 else '❌'})")
        print(f"    成交量: {volume:,} (≥1,000,000: {'✅' if volume >= 1000000 else '❌'})")
        print(f"    成交额: {amount:,} (≥5,000,000: {'✅' if amount >= 5000000 else '❌'})")
        print(f"    市值: {market_cap:.0f}亿 (10-500亿: {'✅' if 10 <= market_cap <= 500 else '❌'})")
    
    return len(candidate_stocks) > 0


def main():
    """主函数"""
    print("🚀 好奇布偶猫BOLL策略调试测试")
    print("=" * 60)
    
    try:
        # 1. 测试数据可用性
        data_ok = test_data_availability()
        
        # 2. 测试候选股票筛选
        stocks_ok = test_candidate_stocks()
        
        # 3. 测试策略信号生成
        signals_ok = test_strategy_signals()
        
        # 总结
        print("\n" + "=" * 60)
        print("🔧 问题诊断总结:")
        print(f"  数据可用性: {'✅ 正常' if data_ok else '❌ 异常'}")
        print(f"  股票筛选: {'✅ 正常' if stocks_ok else '❌ 异常'}")
        print(f"  信号生成: {'✅ 正常' if signals_ok else '❌ 异常'}")
        
        if not data_ok:
            print("\n💡 数据问题修复建议:")
            print("  1. 检查数据库中是否有布林带指标数据")
            print("  2. 确认字段映射配置是否正确")
            print("  3. 验证股票数据的完整性")
        
        if not stocks_ok:
            print("\n💡 股票筛选问题修复建议:")
            print("  1. 放宽市值限制范围")
            print("  2. 降低成交量要求")
            print("  3. 调整价格筛选条件")
        
        if not signals_ok:
            print("\n💡 信号生成问题修复建议:")
            print("  1. 放宽布林带买入条件")
            print("  2. 检查前收盘价数据")
            print("  3. 优化技术指标计算")
        
    except Exception as e:
        print(f"❌ 测试过程发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()