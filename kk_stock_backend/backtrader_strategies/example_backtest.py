#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多趋势共振策略完整回测脚本
使用新的回测引擎运行多趋势共振策略
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
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'./results/backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def create_backtest_config() -> Config:
    """创建回测配置"""
    config = Config()
    
    # 回测基本配置
    config.backtest.initial_cash = 1000000.0  # 100万初始资金
    config.backtest.start_date = "2020-01-01"  # 回测开始日期
    config.backtest.end_date = "2025-07-18"    # 回测结束日期
    config.backtest.commission_rate = 0.0001   # 万一手续费
    config.backtest.stamp_tax_rate = 0.001     # 千一印花税
    config.backtest.slippage_rate = 0.001      # 千一滑点
    
    # 策略配置
    config.strategy.max_positions = 8           # 最多8只股票
    config.strategy.max_single_position = 0.12  # 单股最大12%仓位
    config.strategy.stop_loss_pct = -0.06       # 6%止损
    config.strategy.take_profit_pct = 0.12      # 12%止盈
    config.strategy.max_drawdown_limit = -0.20  # 20%最大回撤限制
    
    # 输出配置
    config.backtest.output_dir = "./results"
    config.backtest.save_trades = True
    config.backtest.save_positions = True
    config.backtest.save_performance = True
    
    return config


def print_backtest_summary(result: dict):
    """打印回测结果摘要"""
    print("\n" + "="*80)
    print("🎯 多趋势共振策略回测结果摘要")
    print("="*80)
    
    # 基本信息
    config_info = result['backtest_config']
    print(f"\n📋 回测配置:")
    print(f"   初始资金: {config_info['initial_cash']:,.0f}元")
    print(f"   回测期间: {config_info['start_date']} 至 {config_info['end_date']}")
    print(f"   交易日数: {config_info['trading_days']}天")
    print(f"   股票池: {config_info['total_stocks']}只股票")
    
    # 策略信息
    strategy_info = result['strategy_info']
    print(f"\n🎯 策略信息:")
    print(f"   策略名称: {strategy_info['strategy_name']}")
    print(f"   策略版本: {strategy_info['strategy_version']}")
    print(f"   最大持仓: {strategy_info['max_positions']}只")
    print(f"   单股仓位: {strategy_info['max_single_weight']:.0%}")
    print(f"   最小共振得分: {strategy_info['min_resonance_score']}")
    print(f"   买入信号: {strategy_info['buy_signals_count']}次")
    print(f"   卖出信号: {strategy_info['sell_signals_count']}次")
    
    # 绩效指标
    performance = result['performance_report']['basic_metrics']
    print(f"\n📊 基础绩效指标:")
    print(f"   总收益率: {performance.get('total_return', 0):.2%}")
    print(f"   年化收益率: {performance.get('annual_return', 0):.2%}")
    print(f"   年化波动率: {performance.get('volatility', 0):.2%}")
    print(f"   夏普比率: {performance.get('sharpe_ratio', 0):.3f}")
    print(f"   最大回撤: {performance.get('max_drawdown', 0):.2%}")
    print(f"   卡玛比率: {performance.get('calmar_ratio', 0):.3f}")
    
    # 高级指标
    if 'advanced_metrics' in result['performance_report']:
        advanced = result['performance_report']['advanced_metrics']
        print(f"\n📈 高级绩效指标:")
        print(f"   索蒂诺比率: {advanced.get('sortino_ratio', 0):.3f}")
        print(f"   VaR(5%): {advanced.get('var_5', 0):.2%}")
        print(f"   盈利日占比: {advanced.get('winning_days_ratio', 0):.1%}")
        print(f"   最大连续亏损: {advanced.get('max_consecutive_losses', 0)}天")
        print(f"   盈亏比: {advanced.get('avg_win_loss_ratio', 0):.2f}")
    
    # 组合摘要
    portfolio = result['portfolio_summary']
    print(f"\n💰 组合摘要:")
    print(f"   最终价值: {portfolio['total_value']:,.0f}元")
    print(f"   现金余额: {portfolio['cash']:,.0f}元")
    print(f"   持仓市值: {portfolio['positions_value']:,.0f}元")
    print(f"   现金比例: {portfolio['cash_ratio']:.1%}")
    print(f"   累计收益率: {portfolio['cumulative_return']:.2%}")
    print(f"   最大回撤: {portfolio['max_drawdown']:.2%}")
    
    # 交易统计
    trading = result['trading_summary']
    print(f"\n🔄 交易统计:")
    print(f"   总交易次数: {trading['trades']['total']}")
    print(f"   买入交易: {trading['trades']['buy_trades']}")
    print(f"   卖出交易: {trading['trades']['sell_trades']}")
    print(f"   盈利交易: {portfolio['winning_trades']}")
    print(f"   亏损交易: {portfolio['losing_trades']}")
    print(f"   胜率: {portfolio['win_rate']:.1%}")
    print(f"   总手续费: {trading['fees']['total_commission']:,.2f}元")
    print(f"   总印花税: {trading['fees']['total_stamp_tax']:,.2f}元")
    print(f"   总费用: {trading['fees']['total_fees']:,.2f}元")
    
    # 生成的文件
    if result['chart_files']:
        print(f"\n📊 生成的图表文件:")
        for chart_file in result['chart_files']:
            print(f"   {os.path.basename(chart_file)}")
    
    print(f"\n📁 详细结果保存在: {config_info.get('output_dir', './results')} 目录")
    print("="*80)


def analyze_strategy_performance(result: dict):
    """分析策略性能"""
    print("\n🔍 策略性能分析:")
    
    performance = result['performance_report']['basic_metrics']
    portfolio = result['portfolio_summary']
    
    # 收益分析
    total_return = performance.get('total_return', 0)
    annual_return = performance.get('annual_return', 0)
    
    if total_return > 0.15:
        print("✅ 策略收益表现优秀（>15%）")
    elif total_return > 0.08:
        print("✅ 策略收益表现良好（8%-15%）")
    else:
        print("⚠️  策略收益有待提高（<8%）")
    
    # 风险分析
    max_drawdown = performance.get('max_drawdown', 0)
    volatility = performance.get('volatility', 0)
    
    if abs(max_drawdown) < 0.10:
        print("✅ 回撤控制良好（<10%）")
    elif abs(max_drawdown) < 0.20:
        print("⚠️  回撤适中（10%-20%）")
    else:
        print("❌ 回撤较大（>20%），需要优化风控")
    
    # 夏普比率分析
    sharpe_ratio = performance.get('sharpe_ratio', 0)
    
    if sharpe_ratio > 1.5:
        print("✅ 风险调整收益优秀（夏普比率>1.5）")
    elif sharpe_ratio > 1.0:
        print("✅ 风险调整收益良好（夏普比率>1.0）")
    else:
        print("⚠️  风险调整收益有待提高（夏普比率<1.0）")
    
    # 胜率分析
    win_rate = portfolio.get('win_rate', 0)
    
    if win_rate > 0.6:
        print("✅ 交易胜率优秀（>60%）")
    elif win_rate > 0.5:
        print("✅ 交易胜率良好（50%-60%）")
    else:
        print("⚠️  交易胜率有待提高（<50%）")


def main():
    """主函数"""
    print("🚀 多趋势共振策略回测开始...")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 设置环境
        setup_logging()
        
        # 确保结果目录存在
        os.makedirs("./results", exist_ok=True)
        
        # 2. 创建配置
        config = create_backtest_config()
        print(f"📋 回测配置创建完成")
        
        # 3. 创建策略
        strategy = MultiTrendResonanceStrategyAdapter()
        print(f"🎯 多趋势共振策略创建完成")
        
        # 4. 运行回测
        print(f"🔄 开始运行回测...")
        result = run_strategy_backtest(
            strategy=strategy,
            config=config,
            stock_codes=None,  # 使用中证A500成分股
            max_stocks=50      # 限制股票数量以加快回测速度
        )
        
        # 5. 输出结果
        print_backtest_summary(result)
        
        # 6. 性能分析
        analyze_strategy_performance(result)
        
        print(f"\n🎉 回测完成! 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 回测过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 运行多趋势共振策略回测
    result = main()
    
    if result:
        print("\n💡 回测建议:")
        print("1. 查看生成的图表文件了解详细表现")
        print("2. 分析交易记录CSV文件优化策略参数")
        print("3. 对比基准指数评估策略有效性")
        print("4. 考虑不同市场环境下的策略稳定性")
    else:
        print("\n❌ 回测失败，请检查错误信息")