#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强多趋势共振策略回测脚本
Enhanced Multi-Trend Resonance Strategy Backtest

2025年最新优化版本，基于：
1. 多因子选股：价值+动量+质量+情绪四维度综合评分
2. 多时间周期技术信号：MACD+RSI+BOLL+KDJ综合共振  
3. 智能资金管理：凯利公式+风险平价动态权重
4. 增强风控系统：止损+止盈+移动止损+技术止损
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
from strategy_adapters.enhanced_multi_trend_strategy_adapter import EnhancedMultiTrendStrategyAdapter
from config import Config


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


def create_enhanced_backtest_config() -> Config:
    """创建增强回测配置"""
    config = Config()
    
    # 回测基本配置
    config.backtest.initial_cash = 1000000.0  # 100万初始资金
    config.backtest.start_date = "2023-01-01"  # 更长的回测期间以验证策略稳定性
    config.backtest.end_date = "2023-12-31"    # 回测结束日期
    config.backtest.commission_rate = 0.0001   # 万一手续费
    config.backtest.stamp_tax_rate = 0.001     # 千一印花税
    config.backtest.slippage_rate = 0.0005     # 千分之五滑点（更保守）
    
    # 增强策略配置
    config.strategy.max_positions = 8           # 最多8只股票
    config.strategy.max_single_position = 0.20  # 20%单股最大仓位
    config.strategy.stop_loss_pct = -0.05       # 5%止损
    config.strategy.take_profit_pct = 0.20      # 20%止盈
    config.strategy.trailing_stop_pct = 0.08    # 8%移动止损
    config.strategy.max_drawdown_limit = -0.12  # 12%最大回撤限制
    
    # 选股参数
    config.strategy.selection_pool_size = 8     # 选股池大小8只
    config.strategy.rebalance_selection_freq = 3 # 每3个交易日重新选股
    
    # 多因子权重配置
    config.strategy.value_weight = 0.30         # 价值因子30%
    config.strategy.momentum_weight = 0.25      # 动量因子25%
    config.strategy.quality_weight = 0.25       # 质量因子25%
    config.strategy.sentiment_weight = 0.20     # 情绪因子20%
    
    # 技术信号权重配置
    config.strategy.macd_weight = 0.30          # MACD信号30%
    config.strategy.rsi_weight = 0.25           # RSI信号25%
    config.strategy.boll_weight = 0.25          # BOLL信号25%
    config.strategy.kdj_weight = 0.20           # KDJ信号20%
    
    # 输出配置
    config.backtest.output_dir = "./results"
    config.backtest.save_trades = True
    config.backtest.save_positions = True
    config.backtest.save_performance = True
    
    return config


def print_enhanced_backtest_summary(result: dict):
    """打印增强回测结果摘要"""
    print("\n" + "="*70)
    print("🎯 太上老君1号Plus - 增强多因子动量策略回测结果")
    print("="*70)
    
    # 基本配置信息
    config_info = result['backtest_config']
    strategy_info = result['strategy_info']
    performance = result['performance_report']['basic_metrics']
    portfolio = result['portfolio_summary']
    
    print(f"📋 配置: {config_info['initial_cash']:,.0f}元 | "
          f"{config_info['start_date']} 至 {config_info['end_date']} | "
          f"{config_info['trading_days']}天")
    
    print(f"🎯 策略: 增强多因子 | 选股池{strategy_info.get('max_positions', 8)}只 | "
          f"买信号{strategy_info['buy_signals_count']} | 卖信号{strategy_info['sell_signals_count']}")
    
    print(f"📊 收益: {performance.get('total_return', 0):.2%}总收益 | "
          f"{performance.get('annual_return', 0):.2%}年化收益 | "
          f"{performance.get('max_drawdown', 0):.2%}最大回撤")
    
    print(f"🔢 风险: {performance.get('sharpe_ratio', 0):.2f}夏普比率 | "
          f"{performance.get('volatility', 0):.2%}年化波动率 | "
          f"{performance.get('calmar_ratio', 0):.2f}卡玛比率")
    
    print(f"💰 组合: {portfolio['total_value']:,.0f}元总价值 | "
          f"{portfolio['cash_ratio']:.1%}现金比例 | "
          f"{portfolio['win_rate']:.1%}交易胜率")
    
    print("="*70)
    
    # 显示策略特色信息
    factor_weights = strategy_info.get('factor_weights', {})
    signal_weights = strategy_info.get('signal_weights', {})
    
    print(f"🔍 多因子权重: 价值{factor_weights.get('value', 0.3):.0%} + "
          f"动量{factor_weights.get('momentum', 0.25):.0%} + "
          f"质量{factor_weights.get('quality', 0.25):.0%} + "
          f"情绪{factor_weights.get('sentiment', 0.2):.0%}")
    
    print(f"🔍 技术信号权重: MACD{signal_weights.get('macd', 0.3):.0%} + "
          f"RSI{signal_weights.get('rsi', 0.25):.0%} + "
          f"BOLL{signal_weights.get('boll', 0.25):.0%} + "
          f"KDJ{signal_weights.get('kdj', 0.2):.0%}")
    
    print(f"🔍 风控: 止损5% + 止盈20% + 移动止损8% + 技术止损")
    print("="*70)


def analyze_enhanced_performance(result: dict):
    """增强策略性能评估"""
    performance = result['performance_report']['basic_metrics']
    portfolio = result['portfolio_summary']
    
    total_return = performance.get('total_return', 0)
    annual_return = performance.get('annual_return', 0)
    max_drawdown = abs(performance.get('max_drawdown', 0))
    sharpe_ratio = performance.get('sharpe_ratio', 0)
    calmar_ratio = performance.get('calmar_ratio', 0)
    win_rate = portfolio.get('win_rate', 0)
    
    print(f"📈 策略评估: ", end="")
    
    # 多维度评估标准
    score = 0
    criteria = []
    
    # 收益评估
    if annual_return > 0.15:
        score += 2
        criteria.append("年化收益优秀")
    elif annual_return > 0.08:
        score += 1
        criteria.append("年化收益良好")
    
    # 回撤评估
    if max_drawdown < 0.08:
        score += 2
        criteria.append("回撤控制优秀")
    elif max_drawdown < 0.15:
        score += 1
        criteria.append("回撤控制良好")
    
    # 夏普比率评估
    if sharpe_ratio > 1.5:
        score += 2
        criteria.append("风险调整收益优秀")
    elif sharpe_ratio > 1.0:
        score += 1
        criteria.append("风险调整收益良好")
    
    # 胜率评估
    if win_rate > 0.6:
        score += 1
        criteria.append("胜率较高")
    
    # 综合评估
    if score >= 6:
        print("🌟 策略表现优秀")
    elif score >= 4:
        print("✅ 策略表现良好")
    elif score >= 2:
        print("⚠️ 策略表现一般")
    else:
        print("❌ 策略需要进一步优化")
    
    if criteria:
        print(f"   优势: {', '.join(criteria)}")


def main():
    """主函数"""
    print("🚀 太上老君1号Plus - 增强多因子动量策略回测启动...")
    print("📊 基于2025年最新量化投资实践优化")
    
    try:
        setup_logging()
        os.makedirs("./results", exist_ok=True)
        
        # 创建增强配置和策略
        config = create_enhanced_backtest_config()
        strategy = EnhancedMultiTrendStrategyAdapter()
        
        print("🔄 开始增强策略回测...")
        print(f"   📅 回测期间: {config.backtest.start_date} → {config.backtest.end_date}")
        print(f"   💰 初始资金: {config.backtest.initial_cash:,.0f}元")
        print(f"   🎯 选股池: {config.strategy.selection_pool_size}只股票")
        print(f"   ⚖️  多因子: 价值+动量+质量+情绪四维度评分")
        print(f"   📈 技术信号: MACD+RSI+BOLL+KDJ多时间周期共振")
        
        # 运行回测
        result = run_strategy_backtest(
            strategy=strategy,
            config=config,
            stock_codes=None,  # 使用策略内部选股
            max_stocks=800     # 从更大的股票池中选择
        )
        
        # 输出结果
        print_enhanced_backtest_summary(result)
        analyze_enhanced_performance(result)
        
        print(f"\n🎉 增强策略回测完成! {datetime.now().strftime('%H:%M:%S')}")
        return result
        
    except Exception as e:
        print(f"❌ 增强策略回测失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = main()
    
    if result:
        print("📁 详细回测结果已保存到 ./results 目录")
        print("💡 建议对比原策略和增强策略的性能表现")
    else:
        print("❌ 请检查错误日志并重新运行")