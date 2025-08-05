#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多趋势共振策略-BOLL+WR精确版回测脚本
专为A股高波动市场设计的精确买卖点系统
买入条件：WR>90(极度超卖) + 触碰布林带下轨
卖出条件：WR<20(极度超买) + 触碰布林带上轨
风控：止损5%优先级最高，止盈25%
"""

import sys
import os
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.backtest_engine import run_strategy_backtest
from multi_trend_strategy_adapter import MultiTrendResonanceStrategyAdapter
from config import Config


def setup_logging():
    """简化日志配置"""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


def create_backtest_config() -> Config:
    """创建回测配置"""
    config = Config()
    
    # 回测基本配置
    config.backtest.initial_cash = 1000000.0  # 100万初始资金
    config.backtest.start_date = "2025-01-01"  # 回测开始日期
    config.backtest.end_date = "2025-08-04"    # 回测结束日期
    config.backtest.commission_rate = 0.0001   # 万一手续费
    config.backtest.stamp_tax_rate = 0.001     # 千一印花税
    config.backtest.slippage_rate = 0.001      # 千一滑点
    
    # 太上老君1号策略配置 - 价值动量策略
    config.strategy.max_positions = 5           # 最多5只股票（等于选股池）
    config.strategy.max_single_position = 0.20  # 20%单股仓位（5只平均分配）
    config.strategy.stop_loss_pct = -0.03       # 3%止损，快速止损
    config.strategy.take_profit_pct = 0.15      # 15%止盈，保持盈亏比5:1
    config.strategy.max_drawdown_limit = -0.15  # 15%最大回撤限制
    
    # 选股参数 - PE_TTM + 20日收益率 + 波动率调整权重
    config.strategy.selection_pool_size = 5     # 选股池大小5只
    config.strategy.rebalance_selection_freq = 5 # 每5个交易日重新选股
    config.strategy.pe_weight = 0.5             # PE权重50%
    config.strategy.momentum_weight = 0.5       # 动量权重50%
    config.strategy.volatility_adjustment = True # 启用波动率调整权重
    config.strategy.base_volatility = 0.5       # 基础波动率参数
    config.strategy.min_weight = 0.05           # 最小权重5%
    config.strategy.max_weight = 0.30           # 最大权重30%
    
    # BOLL+WR技术指标参数 - 简化信号逻辑
    config.strategy.enable_technical_signals = True  # 启用技术信号
    config.strategy.require_boll_signal = True       # 需要布林带信号
    config.strategy.require_wr_signal = True         # 需要威廉指标信号
    config.strategy.wr_oversold = 90            # WR>90极度超卖
    config.strategy.wr_overbought = 20          # WR<20极度超买
    config.strategy.boll_lower_threshold = 0.1  # 下轨触碰阈值10%
    config.strategy.boll_upper_threshold = 0.9  # 上轨触碰阈值90%
    
    # 输出配置
    config.backtest.output_dir = "./results"
    config.backtest.save_trades = True
    config.backtest.save_positions = True
    config.backtest.save_performance = True
    
    return config


def print_backtest_summary(result: dict):
    """打印核心回测结果"""
    print("\n" + "="*60)
    print("🎯 太上老君1号策略回测结果")
    print("="*60)
    
    # 基本配置
    config_info = result['backtest_config']
    strategy_info = result['strategy_info']
    performance = result['performance_report']['basic_metrics']
    portfolio = result['portfolio_summary']
    
    print(f"📋 配置: {config_info['initial_cash']:,.0f}元 | "
          f"{config_info['start_date']} 至 {config_info['end_date']} | "
          f"{config_info['trading_days']}天")
    
    print(f"🎯 策略: BOLL+WR技术信号 | "
          f"信号{strategy_info['buy_signals_count']}买/{strategy_info['sell_signals_count']}卖")
    
    print(f"📊 收益: {performance.get('total_return', 0):.2%}总收益 | "
          f"{performance.get('annual_return', 0):.2%}年化 | "
          f"{performance.get('max_drawdown', 0):.2%}最大回撤")
    
    print(f"🔢 风险: {performance.get('sharpe_ratio', 0):.2f}夏普 | "
          f"{performance.get('volatility', 0):.2%}波动率")
    
    print(f"💰 组合: {portfolio['total_value']:,.0f}元总价值 | "
          f"{portfolio['cash_ratio']:.1%}现金 | "
          f"{portfolio['win_rate']:.1%}胜率")
    
    print("="*60)
    
    # 添加太上老君1号策略特色信息
    print(f"🔍 买入: WR>90超卖 + 触碰下轨 | 止损5%(优先级最高)")
    print(f"🔍 卖出: WR<20超买 + 触碰上轨 | 止盈25%")
    print("="*60)


def analyze_performance(result: dict):
    """快速性能评估"""
    performance = result['performance_report']['basic_metrics']
    portfolio = result['portfolio_summary']
    
    total_return = performance.get('total_return', 0)
    max_drawdown = abs(performance.get('max_drawdown', 0))
    sharpe_ratio = performance.get('sharpe_ratio', 0)
    win_rate = portfolio.get('win_rate', 0)
    
    print(f"🔍 评估: ", end="")
    
    if total_return > 0.08 and max_drawdown < 0.15 and sharpe_ratio > 1.0:
        print("✅ 策略表现良好")
    elif total_return > 0 and max_drawdown < 0.25:
        print("⚠️ 策略表现一般")
    else:
        print("❌ 策略需要优化")


def main():
    """主函数"""
    print("🚀 太上老君1号策略回测启动...")
    
    try:
        setup_logging()
        os.makedirs("./results", exist_ok=True)
        
        # 创建配置和策略
        config = create_backtest_config()
        strategy = MultiTrendResonanceStrategyAdapter()
        
        # 运行回测
        print("🔄 运行回测中...")
        result = run_strategy_backtest(
            strategy=strategy,
            config=config,
            stock_codes=None,
            max_stocks=500  # 从中证A500全量选择，不限制数量
        )
        
        # 输出结果
        print_backtest_summary(result)
        analyze_performance(result)
        
        print(f"\n🎉 回测完成! {datetime.now().strftime('%H:%M:%S')}")
        return result
        
    except Exception as e:
        print(f"❌ 回测失败: {e}")
        return None


if __name__ == "__main__":
    result = main()
    
    if result:
        print("📁 详细结果已保存到 ./results 目录")
    else:
        print("❌ 请检查错误日志")