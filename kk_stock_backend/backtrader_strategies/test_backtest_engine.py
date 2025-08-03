#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎测试脚本
验证回测引擎的各个组件是否正常工作
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.backtest_engine import BacktestEngine, StrategyInterface, run_strategy_backtest
from backtest.trading_simulator import OrderType
from config import Config


class SimpleTestStrategy(StrategyInterface):
    """
    简单测试策略
    用于验证回测引擎功能
    """
    
    def __init__(self):
        self.name = "简单测试策略"
        self.buy_signals_count = 0
        self.sell_signals_count = 0
        self.positions = {}
    
    def initialize(self, context: Dict[str, Any]):
        """策略初始化"""
        self.context = context
        print(f"🚀 {self.name} 初始化完成")
        print(f"   初始资金: {context['initial_cash']:,.0f}元")
        print(f"   回测期间: {context['start_date']} 到 {context['end_date']}")
    
    def generate_signals(self, 
                        current_date: str, 
                        market_data: Dict[str, Dict],
                        portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成交易信号
        
        简单策略逻辑：
        1. 如果持仓少于5只，随机买入一只股票
        2. 如果某只股票盈利超过10%，卖出
        3. 如果某只股票亏损超过5%，止损
        """
        signals = []
        
        try:
            # 获取可交易的股票
            available_stocks = list(market_data.keys())
            current_positions = portfolio_info.get('total_positions', 0)
            cash_ratio = portfolio_info.get('cash_ratio', 1.0)
            
            # 买入逻辑：持仓少于5只且有足够现金
            if current_positions < 5 and cash_ratio > 0.2:
                # 简单选择：选择第一只没有持仓的股票
                for stock_code in available_stocks[:10]:  # 只检查前10只
                    if stock_code not in self.positions:
                        stock_data = market_data[stock_code]
                        
                        # 简单的买入条件：价格大于0
                        if stock_data['close'] > 0 and stock_data['volume'] > 0:
                            signals.append({
                                'action': 'buy',
                                'stock_code': stock_code,
                                'price': stock_data['close'],
                                'weight': 0.15  # 15%仓位
                            })
                            
                            self.positions[stock_code] = {
                                'entry_date': current_date,
                                'entry_price': stock_data['close']
                            }
                            
                            self.buy_signals_count += 1
                            break  # 一次只买一只
            
            # 卖出逻辑：检查持仓股票
            positions_to_sell = []
            for stock_code in list(self.positions.keys()):
                if stock_code in market_data:
                    stock_data = market_data[stock_code]
                    entry_price = self.positions[stock_code]['entry_price']
                    current_price = stock_data['close']
                    
                    if entry_price > 0:
                        pnl_pct = (current_price - entry_price) / entry_price
                        
                        # 止盈：盈利10%
                        if pnl_pct >= 0.10:
                            signals.append({
                                'action': 'sell',
                                'stock_code': stock_code,
                                'price': current_price,
                                'reason': f'止盈卖出: {pnl_pct:.2%}'
                            })
                            positions_to_sell.append(stock_code)
                            self.sell_signals_count += 1
                        
                        # 止损：亏损5%
                        elif pnl_pct <= -0.05:
                            signals.append({
                                'action': 'sell',
                                'stock_code': stock_code,
                                'price': current_price,
                                'reason': f'止损卖出: {pnl_pct:.2%}'
                            })
                            positions_to_sell.append(stock_code)
                            self.sell_signals_count += 1
            
            # 移除已卖出的持仓记录
            for stock_code in positions_to_sell:
                del self.positions[stock_code]
            
            # 调试输出（每10天输出一次）
            if current_date.endswith(('10', '20', '30')):
                print(f"📊 {current_date}: 持仓{current_positions}只, 现金比例{cash_ratio:.1%}, "
                      f"信号{len(signals)}个 (买{self.buy_signals_count}/卖{self.sell_signals_count})")
            
        except Exception as e:
            print(f"❌ 生成信号失败 {current_date}: {e}")
        
        return signals
    
    def on_trade_executed(self, trade_info: Dict[str, Any]):
        """交易执行后回调"""
        action = trade_info['order_type']
        stock_code = trade_info['stock_code']
        price = trade_info['price']
        quantity = trade_info['quantity']
        
        print(f"✅ 交易执行: {action} {stock_code} {quantity}股 @{price:.2f}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            'strategy_name': self.name,
            'strategy_type': '测试策略',
            'buy_signals_count': self.buy_signals_count,
            'sell_signals_count': self.sell_signals_count,
            'current_positions': len(self.positions),
            'description': '简单的买入持有策略，用于测试回测引擎功能'
        }


def test_backtest_components():
    """测试回测引擎各个组件"""
    print("🔧 测试回测引擎组件...")
    
    try:
        # 1. 测试配置
        config = Config()
        config.backtest.start_date = "2024-01-01"
        config.backtest.end_date = "2024-03-31"
        config.backtest.initial_cash = 1000000.0
        print(f"✅ 配置测试通过")
        
        # 2. 测试数据管理器
        from backtest.data_manager import DataManager
        data_manager = DataManager(config.database)
        
        # 测试股票池加载
        stock_universe = data_manager.load_stock_universe()
        print(f"✅ 股票池加载: {len(stock_universe)}只股票")
        
        # 测试单只股票数据加载
        if stock_universe:
            test_stock = stock_universe[0]
            df = data_manager.load_stock_data(
                stock_code=test_stock,
                start_date="2024-01-01",
                end_date="2024-01-31",
                include_indicators=True
            )
            print(f"✅ 单股数据加载: {test_stock} - {len(df)}条记录")
        
        # 3. 测试交易模拟器
        from backtest.trading_simulator import TradingSimulator
        trading_simulator = TradingSimulator()
        trading_info = trading_simulator.get_trading_info()
        print(f"✅ 交易模拟器: 手续费{trading_info['commission_rate']:.4f}")
        
        # 4. 测试订单管理器
        from backtest.order_manager import OrderManager
        order_manager = OrderManager(trading_simulator)
        
        # 5. 测试组合管理器
        from backtest.portfolio_manager import PortfolioManager
        portfolio_manager = PortfolioManager(config.backtest.initial_cash)
        summary = portfolio_manager.get_portfolio_summary()
        print(f"✅ 组合管理器: 初始资金{summary['total_value']:,.0f}元")
        
        # 6. 测试性能分析器
        from backtest.performance_analyzer import PerformanceAnalyzer
        performance_analyzer = PerformanceAnalyzer()
        print(f"✅ 性能分析器初始化完成")
        
        print("🎉 所有组件测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_strategy_backtest():
    """测试简单策略回测"""
    print("\n🚀 开始简单策略回测测试...")
    
    try:
        # 创建配置
        config = Config()
        config.backtest.start_date = "2024-01-01"
        config.backtest.end_date = "2024-02-29"  # 缩短测试期间
        config.backtest.initial_cash = 1000000.0
        config.strategy.max_positions = 5
        config.strategy.max_single_position = 0.2
        
        # 创建测试策略
        strategy = SimpleTestStrategy()
        
        # 运行回测
        result = run_strategy_backtest(
            strategy=strategy,
            config=config,
            stock_codes=None,  # 使用默认股票池
            max_stocks=20  # 限制股票数量以加快测试
        )
        
        # 输出结果
        print("\n📊 回测结果摘要:")
        performance = result['performance_report']['basic_metrics']
        portfolio = result['portfolio_summary']
        trading = result['trading_summary']
        
        print(f"   总收益率: {performance.get('total_return', 0):.2%}")
        print(f"   年化收益率: {performance.get('annual_return', 0):.2%}")
        print(f"   最大回撤: {performance.get('max_drawdown', 0):.2%}")
        print(f"   夏普比率: {performance.get('sharpe_ratio', 0):.2f}")
        
        print(f"   最终价值: {portfolio['total_value']:,.0f}元")
        print(f"   现金比例: {portfolio['cash_ratio']:.1%}")
        print(f"   总交易次数: {trading['trades']['total']}")
        print(f"   胜率: {portfolio['win_rate']:.1%}")
        
        strategy_info = result['strategy_info']
        print(f"   买入信号: {strategy_info['buy_signals_count']}")
        print(f"   卖出信号: {strategy_info['sell_signals_count']}")
        
        print("🎉 简单策略回测测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 简单策略回测失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🧪 回测引擎测试开始...")
    
    # 设置日志级别
    logging.basicConfig(level=logging.WARNING)  # 减少日志输出
    
    # 1. 测试组件
    components_ok = test_backtest_components()
    
    if components_ok:
        # 2. 测试简单策略回测
        strategy_ok = test_simple_strategy_backtest()
        
        if strategy_ok:
            print("\n🎉 所有测试通过! 回测引擎可以正常工作")
        else:
            print("\n❌ 策略回测测试失败")
    else:
        print("\n❌ 组件测试失败")


if __name__ == "__main__":
    main()