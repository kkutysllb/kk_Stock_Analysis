#!/usr/bin/env python3
"""
增强策略诊断脚本
分析为什么策略无法选出股票
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy_adapters.enhanced_multi_trend_strategy_adapter import EnhancedMultiTrendStrategyAdapter
from backtest.data_manager import DataManager

def debug_strategy_selection():
    """诊断策略选股问题"""
    print("🔍 开始诊断增强策略选股问题...")
    
    # 1. 创建策略实例
    strategy = EnhancedMultiTrendStrategyAdapter()
    dm = DataManager()
    
    print(f"📊 策略参数:")
    print(f"  选股池大小: {strategy.params['selection_pool_size']}")
    print(f"  最小成交额: {strategy.params['min_amount']:,}")
    print(f"  最小成交量: {strategy.params['min_volume']:,}")
    
    # 2. 加载股票池和测试数据
    try:
        print("\n📅 加载股票池...")
        stock_codes = dm.load_stock_universe()
        if not stock_codes:
            # 使用默认股票池进行测试
            stock_codes = ['000001', '000002', '000858', '002415', '600000', '600036', '600519', '000858']
            print(f"使用默认测试股票池: {stock_codes}")
        else:
            stock_codes = stock_codes[:20]  # 只测试前20只
            print(f"✅ 加载股票池: {len(stock_codes)} 只股票")
            
        print("\n📅 加载市场数据...")
        # 尝试多个日期
        test_dates = ['2023-12-29', '2023-12-28', '2023-12-27']
        market_data = None
        
        for test_date in test_dates:
            try:
                end_date = test_date  # 同一天
                market_data = dm.load_market_data(stock_codes, test_date, end_date)
                if market_data:
                    print(f"✅ 使用日期: {test_date}")
                    break
            except Exception as e:
                print(f"❌ 日期 {test_date} 失败: {e}")
                continue
        
        if not market_data:
            print("❌ 无法加载市场数据")
            return
            
        print(f"✅ 加载了 {len(market_data)} 只股票的数据")
        
        # 3. 转换数据格式用于测试
        print("\n🔍 转换数据格式...")
        # 使用实际加载成功的日期
        test_date = test_dates[0] if market_data else '2023-12-29'
        daily_market_data = {}
        
        for stock_code, df in market_data.items():
            if test_date in df.index:
                row_data = df.loc[test_date].to_dict()
                daily_market_data[stock_code] = row_data
                
        print(f"✅ 转换了 {len(daily_market_data)} 只股票的数据")
        
        if not daily_market_data:
            print("❌ 无有效数据进行测试")
            return
        
        # 4. 测试股票筛选
        print("\n🔍 测试股票筛选...")
        qualified_count = 0
        
        for stock_code, stock_data in daily_market_data.items():
            is_qualified = strategy._is_enhanced_stock_qualified(stock_code, stock_data)
            
            print(f"  {stock_code}: {'✅' if is_qualified else '❌'} ", end="")
            
            # 显示关键指标
            close = stock_data.get('close', 0)
            volume = stock_data.get('volume', 0) 
            amount = stock_data.get('amount', 0)
            turnover = stock_data.get('turnover_rate', 0)
            
            print(f"价格:{close:.2f}, 量:{volume:,.0f}, 额:{amount:,.0f}, 换手:{turnover:.2f}%")
            
            if is_qualified:
                qualified_count += 1
                
                # 测试多因子得分
                factor_score, factor_details = strategy._calculate_multi_factor_score(stock_code, stock_data)
                signal_score, signal_details = strategy._calculate_multi_timeframe_signals(stock_data)
                composite_score = factor_score * 0.7 + signal_score * 0.3
                
                print(f"    📈 因子得分: {factor_score:.3f}, 信号得分: {signal_score:.3f}, 综合: {composite_score:.3f}")
        
        print(f"\n📊 筛选结果: {qualified_count}/{len(daily_market_data)} 只股票通过筛选")
        
        if qualified_count == 0:
            print("⚠️  无股票通过筛选，需要降低门槛！")
            return
        
        # 5. 测试完整选股流程
        print("\n🎯 测试完整选股流程...")
        selected_stocks = strategy._update_enhanced_stock_selection(test_date, daily_market_data)
        
        print(f"✅ 最终选中 {len(selected_stocks)} 只股票: {selected_stocks}")
        
    except Exception as e:
        print(f"❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_strategy_selection()