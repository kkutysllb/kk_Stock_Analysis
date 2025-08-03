#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
太上老君3号策略回测运行器 - 小市值动量版本
基于3因子增强的小市值动量策略
"""

import sys
import os
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from taishang_3_factor_strategy_adapter import TaiShang3FactorStrategyAdapter
from backtest.backtest_engine import run_strategy_backtest
from config import Config


def create_backtest_config():
    """创建回测配置"""
    config = Config()
    
    # 回测基本配置
    config.backtest.initial_cash = 1000000.0
    config.backtest.start_date = "2020-01-01"
    config.backtest.end_date = "2025-07-18"
    config.backtest.commission_rate = 0.0001
    config.backtest.stamp_tax_rate = 0.001
    config.backtest.slippage_rate = 0.001
    
    # 策略配置
    config.strategy.max_positions = 25
    config.strategy.max_single_position = 0.08
    config.strategy.stop_loss_pct = -0.06
    config.strategy.take_profit_pct = 0.15
    config.strategy.rebalance_frequency = 5
    
    # 数据配置
    config.backtest.data_frequency = "daily"
    config.backtest.benchmark = "000852.SH"
    config.strategy.min_market_cap = 10e9  # 10亿
    config.strategy.max_market_cap = 100e9  # 1000亿
    
    return config


def print_backtest_summary(result):
    """打印回测结果摘要"""
    print(f"\n{'='*80}")
    print(f"🎯 太上老君3号策略回测结果摘要")
    print(f"{'='*80}")
    
    # 基本信息
    config_info = result.get('backtest_config', {})
    strategy_info = result.get('strategy_info', {})
    
    print(f"\n📋 回测配置:")
    print(f"   初始资金: {config_info.get('initial_cash', 0):,}元")
    print(f"   回测期间: {config_info.get('start_date', 'N/A')} 至 {config_info.get('end_date', 'N/A')}")
    print(f"   交易日数: {config_info.get('trading_days', 0)}天")
    print(f"   股票池: {config_info.get('total_stocks', 0)}只股票")
    
    print(f"\n🎯 策略信息:")
    print(f"   策略名称: {strategy_info.get('strategy_name', 'N/A')}")
    print(f"   策略版本: {strategy_info.get('strategy_version', 'N/A')}")
    print(f"   策略类型: {strategy_info.get('strategy_type', 'N/A')}")
    print(f"   最大持仓: {strategy_info.get('max_positions', 'N/A')}只")
    print(f"   单股仓位: {strategy_info.get('max_single_weight', 0):.0%}")
    print(f"   RSI参数: {strategy_info.get('rsi_period', 'N/A')}周, 上限{strategy_info.get('rsi_upper', 'N/A')}, 下限{strategy_info.get('rsi_lower', 'N/A')}")
    print(f"   调仓周期: {strategy_info.get('rebalance_period', 'N/A')}天")
    print(f"   股票池大小: {strategy_info.get('stock_pool_size', 'N/A')}只（中证1000成分股）")
    print(f"   买入信号: {strategy_info.get('buy_signals_count', 0)}次")
    print(f"   卖出信号: {strategy_info.get('sell_signals_count', 0)}次")
    print(f"   总信号数: {strategy_info.get('total_signals', 0)}次")
    
    # 绩效指标
    performance = result.get('performance_report', {}).get('basic_metrics', {})
    advanced_metrics = result.get('performance_report', {}).get('advanced_metrics', {})
    
    print(f"\n📊 基础绩效指标:")
    print(f"   总收益率: {performance.get('total_return', 0):.2%}")
    print(f"   年化收益率: {performance.get('annual_return', 0):.2%}")
    print(f"   年化波动率: {performance.get('annual_volatility', 0):.2%}")
    print(f"   夏普比率: {performance.get('sharpe_ratio', 0):.3f}")
    print(f"   最大回撤: {performance.get('max_drawdown', 0):.2%}")
    print(f"   卡玛比率: {advanced_metrics.get('calmar_ratio', 0):.3f}")
    
    print(f"\n📈 高级绩效指标:")
    print(f"   索蒂诺比率: {advanced_metrics.get('sortino_ratio', 0):.3f}")
    print(f"   VaR(5%): {advanced_metrics.get('var_5', 0):.2%}")
    print(f"   盈利日占比: {advanced_metrics.get('profit_days_ratio', 0):.1%}")
    print(f"   最大连续亏损: {advanced_metrics.get('max_consecutive_losses', 0)}天")
    print(f"   盈亏比: {advanced_metrics.get('profit_loss_ratio', 0):.2f}")
    
    # 组合情况
    portfolio = result.get('portfolio_summary', {})
    print(f"\n💰 组合摘要:")
    print(f"   最终价值: {portfolio.get('final_value', 0):,}元")
    print(f"   现金余额: {portfolio.get('cash', 0):,}元")
    print(f"   持仓市值: {portfolio.get('positions_value', 0):,}元")
    print(f"   现金比例: {portfolio.get('cash_ratio', 0):.1%}")
    print(f"   累计收益率: {portfolio.get('total_return', 0):.2%}")
    print(f"   最大回撤: {portfolio.get('max_drawdown', 0):.2%}")
    
    # 交易统计
    trading = result.get('trading_summary', {})
    print(f"\n🔄 交易统计:")
    print(f"   总交易次数: {trading.get('total_trades', 0)}")
    print(f"   买入交易: {trading.get('buy_trades', 0)}")
    print(f"   卖出交易: {trading.get('sell_trades', 0)}")
    print(f"   盈利交易: {trading.get('profit_trades', 0)}")
    print(f"   亏损交易: {trading.get('loss_trades', 0)}")
    print(f"   胜率: {trading.get('win_rate', 0):.1%}")
    print(f"   总手续费: {trading.get('total_commission', 0):.2f}元")
    print(f"   总印花税: {trading.get('total_stamp_tax', 0):.2f}元")
    print(f"   总费用: {trading.get('total_costs', 0):.2f}元")
    
    # 生成的文件
    charts = result.get('charts', {})
    print(f"\n📊 生成的图表文件:")
    for chart_name, chart_path in charts.items():
        if chart_path:
            filename = os.path.basename(chart_path)
            print(f"   {filename}")
    
    results_dir = result.get('results_directory', './results')
    print(f"\n📁 详细结果保存在: {results_dir} 目录")
    print(f"{'='*80}")


def analyze_strategy_performance(result):
    """分析策略表现"""
    print(f"\n🔍 太上老君3号策略性能分析:")
    
    performance = result.get('performance_report', {}).get('basic_metrics', {})
    advanced_metrics = result.get('performance_report', {}).get('advanced_metrics', {})
    
    annual_return = performance.get('annual_return', 0)
    max_drawdown = performance.get('max_drawdown', 0)
    sharpe_ratio = performance.get('sharpe_ratio', 0)
    win_rate = result.get('trading_summary', {}).get('win_rate', 0)
    
    print(f"\n🎨 策略特色:")
    print(f"   ✅ 专注中证1000指数增强策略")
    print(f"   ✅ 基于3因子量化选股模型")
    print(f"   ✅ RSI择时优化入市时机")
    print(f"   ✅ 组合优化控制风险敞口")
    
    # 收益分析
    if annual_return > 0.15:
        print(f"✅ 年化收益优秀（>{annual_return:.1%}）")
    elif annual_return > 0.08:
        print(f"⚠️  年化收益良好（{annual_return:.1%}）")
    else:
        print(f"❌ 策略出现亏损，需要优化")
    
    # 风控分析
    if abs(max_drawdown) < 0.15:
        print(f"✅ 回撤控制优秀（{max_drawdown:.1%}）")
    elif abs(max_drawdown) < 0.25:
        print(f"⚠️  回撤控制良好（{max_drawdown:.1%}）")
    else:
        print(f"❌ 回撤过大，需要加强风控")
    
    # 风险调整收益
    if sharpe_ratio > 1.0:
        print(f"✅ 风险调整收益优秀（夏普比率{sharpe_ratio:.2f}）")
    elif sharpe_ratio > 0.5:
        print(f"⚠️  风险调整收益良好（夏普比率{sharpe_ratio:.2f}）")
    else:
        print(f"❌ 风险调整收益较差（夏普比率{sharpe_ratio:.2f}），需要优化信号质量")
    
    # 胜率分析
    if win_rate > 0.55:
        print(f"✅ 交易胜率优秀（{win_rate:.1%}）")
    elif win_rate > 0.45:
        print(f"⚠️  交易胜率适中（{win_rate:.1%}）")
    else:
        print(f"❌ 交易胜率较低（{win_rate:.1%}），需要优化信号质量")
    
    print(f"\n📊 3因子策略特色表现:")
    strategy_info = result.get('strategy_info', {})
    print(f"   RSI择时: {strategy_info.get('rsi_period', 'N/A')}周期, 上限{strategy_info.get('rsi_upper', 'N/A')}, 下限{strategy_info.get('rsi_lower', 'N/A')}")
    print(f"   因子选股: VOV(风险模糊度) + EPS + 预期EPS")
    print(f"   调仓频率: 每{strategy_info.get('rebalance_period', 'N/A')}天调仓一次")


def compare_with_benchmark(result):
    """与基准对比分析"""
    print(f"\n📈 基准对比分析:")
    
    performance = result.get('performance_report', {}).get('basic_metrics', {})
    annual_return = performance.get('annual_return', 0)
    max_drawdown = performance.get('max_drawdown', 0)
    sharpe_ratio = performance.get('sharpe_ratio', 0)
    
    # 假设基准数据（中证1000指数历史表现）
    benchmark_return = 0.08  # 假设中证1000年化8%
    benchmark_drawdown = -0.30  # 假设最大回撤30%
    benchmark_sharpe = 0.4   # 假设夏普比率0.4
    
    print(f"   策略年化收益: {annual_return:.2%} vs 中证1000基准: {benchmark_return:.2%}")
    if annual_return > benchmark_return:
        print(f"   ✅ 收益率跑赢基准 {(annual_return - benchmark_return):.2%}")
    else:
        print(f"   ⚠️  收益率未达到基准水平")
    
    print(f"   策略最大回撤: {max_drawdown:.2%} vs 基准回撤: {benchmark_drawdown:.2%}")
    if max_drawdown > benchmark_drawdown:
        print(f"   ✅ 回撤控制优于基准")
    else:
        print(f"   ⚠️  回撤控制需要改进")
    
    print(f"   策略夏普比率: {sharpe_ratio:.3f} vs 基准夏普: {benchmark_sharpe:.3f}")
    if sharpe_ratio > benchmark_sharpe:
        print(f"   ✅ 风险调整收益优于基准")
    else:
        print(f"   ⚠️  风险调整收益有待提升")


def provide_optimization_suggestions(result):
    """提供优化建议"""
    print(f"\n💡 策略优化建议:")
    
    performance = result.get('performance_report', {}).get('basic_metrics', {})
    trading = result.get('trading_summary', {})
    
    annual_return = performance.get('annual_return', 0)
    win_rate = trading.get('win_rate', 0)
    total_trades = trading.get('total_trades', 0)
    
    print(f"📈 收益优化建议:")
    if annual_return < 0.10:
        print(f"   1. 优化3因子权重配置")
        print(f"   2. 调整RSI择时参数")
        print(f"   3. 增加动量因子或质量因子")
        print(f"   4. 考虑行业轮动策略")
    
    print(f"🎯 胜率提升建议:")
    if win_rate < 0.50:
        print(f"   1. 提高因子选股的筛选标准")
        print(f"   2. 增加基本面过滤条件")
        print(f"   3. 优化择时信号的确认机制")
        print(f"   4. 考虑加入止盈止损优化")
    
    print(f"⚡ 交易效率建议:")
    if total_trades < 100:
        print(f"   1. 适当提高调仓频率")
        print(f"   2. 降低RSI择时阈值")
        print(f"   3. 增加股票池规模")
    elif total_trades > 2000:
        print(f"   1. 降低调仓频率减少成本")
        print(f"   2. 提高择时信号阈值")
        print(f"   3. 增加持仓周期")


def main():
    """主函数"""
    print("🚀 太上老君3号小市值动量策略回测开始...")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 创建配置
        config = create_backtest_config()
        print(f"📋 回测配置创建完成")
        
        # 2. 创建策略
        strategy = TaiShang3FactorStrategyAdapter()
        print(f"🎯 太上老君3号策略创建完成")
        
        # 3. 运行回测
        print(f"🔄 开始运行回测...")
        result = run_strategy_backtest(
            strategy=strategy,
            config=config,
            stock_codes=None,  # 使用中证1000成分股
            max_stocks=100     # 限制股票数量
        )
        
        # 4. 输出结果
        print_backtest_summary(result)
        
        # 5. 性能分析
        analyze_strategy_performance(result)
        
        # 6. 基准对比
        compare_with_benchmark(result)
        
        # 7. 优化建议
        provide_optimization_suggestions(result)
        
        print(f"\n🎉 回测完成! 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 8. 结果解读
        print(f"\n💡 回测结果解读:")
        print(f"1. 查看生成的图表文件了解策略表现趋势")
        print(f"2. 分析交易记录CSV文件优化因子权重")
        print(f"3. 对比中证1000指数评估策略有效性")
        print(f"4. 关注3因子在不同市场环境下的表现")
        print(f"5. 考虑结合机器学习模型进一步优化")
        
        print(f"\n🔧 策略特色:")
        print(f"✨ 专注中证1000指数增强，挖掘小盘成长机会")
        print(f"✨ 3因子量化选股，科学化投资决策")
        print(f"✨ RSI择时策略，优化入市时机")
        print(f"✨ 组合优化管理，有效控制风险敞口")
        
        # 9. 故障排查提示
        print(f"\n⚠️  如遇问题，请检查:")
        print(f"1. 确认中证1000成分股数据是否完整")
        print(f"2. 检查因子计算是否正确")
        print(f"3. 验证RSI择时信号是否有效")
        print(f"4. 确保组合优化约束合理")
        
    except Exception as e:
        print(f"❌ 回测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()