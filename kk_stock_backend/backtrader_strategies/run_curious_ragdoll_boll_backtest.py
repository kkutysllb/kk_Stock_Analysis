#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
好奇布偶猫BOLL择时策略完整回测脚本
使用新的回测引擎运行好奇布偶猫BOLL择时策略
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
from curious_ragdoll_boll_strategy_adapter import CuriousRagdollBollStrategyAdapter
from config import Config


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'./results/curious_ragdoll_boll_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
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
    
    # 策略配置 - 按文档要求
    config.strategy.max_positions = 10          # 最多10只股票
    config.strategy.max_single_position = 0.20  # 单股最大20%仓位
    config.strategy.stop_loss_pct = -0.10       # 10%止损
    config.strategy.take_profit_pct = 0.15      # 15%止盈
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
    print("🎯 好奇布偶猫BOLL择时策略回测结果摘要")
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
    print(f"   策略类型: {strategy_info['strategy_type']}")
    print(f"   最大持仓: {strategy_info['max_positions']}只")
    print(f"   单股仓位: {strategy_info['max_single_weight']:.0%}")
    print(f"   单股限额: {strategy_info['max_position_value']:,}元")
    print(f"   布林带参数: {strategy_info['boll_period']}日, {strategy_info['boll_std']}倍标准差")
    print(f"   股票池大小: {strategy_info['stock_pool_size']}只（中证500小市值）")
    print(f"   买入信号: {strategy_info['buy_signals_count']}次")
    print(f"   卖出信号: {strategy_info['sell_signals_count']}次")
    print(f"   总信号数: {strategy_info['total_signals']}次")
    
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
    print("\n🔍 好奇布偶猫BOLL策略性能分析:")
    
    performance = result['performance_report']['basic_metrics']
    portfolio = result['portfolio_summary']
    strategy_info = result['strategy_info']
    
    # 策略特色分析
    print(f"\n🎨 策略特色:")
    print(f"   ✅ 专注中证500小市值股票择时")
    print(f"   ✅ 基于布林带技术指标捕捉超跌反弹")
    print(f"   ✅ 严格风险控制（10%止损，15%止盈）")
    print(f"   ✅ 最大10只持仓分散风险")
    
    # 收益分析
    total_return = performance.get('total_return', 0)
    annual_return = performance.get('annual_return', 0)
    
    if total_return > 0.20:
        print("✅ 策略收益表现优秀（>20%）")
    elif total_return > 0.12:
        print("✅ 策略收益表现良好（12%-20%）")
    elif total_return > 0:
        print("⚠️  策略收益一般（0%-12%）")
    else:
        print("❌ 策略出现亏损，需要优化")
    
    # 风险分析
    max_drawdown = performance.get('max_drawdown', 0)
    volatility = performance.get('volatility', 0)
    
    if abs(max_drawdown) < 0.08:
        print("✅ 回撤控制优秀（<8%）")
    elif abs(max_drawdown) < 0.15:
        print("✅ 回撤控制良好（8%-15%）")
    elif abs(max_drawdown) < 0.25:
        print("⚠️  回撤适中（15%-25%）")
    else:
        print("❌ 回撤较大（>25%），需要优化风控")
    
    # 夏普比率分析
    sharpe_ratio = performance.get('sharpe_ratio', 0)
    
    if sharpe_ratio > 1.5:
        print("✅ 风险调整收益优秀（夏普比率>1.5）")
    elif sharpe_ratio > 1.0:
        print("✅ 风险调整收益良好（夏普比率>1.0）")
    elif sharpe_ratio > 0.5:
        print("⚠️  风险调整收益一般（夏普比率0.5-1.0）")
    else:
        print("❌ 风险调整收益较差（夏普比率<0.5）")
    
    # 胜率分析
    win_rate = portfolio.get('win_rate', 0)
    
    if win_rate > 0.65:
        print("✅ 交易胜率优秀（>65%）")
    elif win_rate > 0.55:
        print("✅ 交易胜率良好（55%-65%）")
    elif win_rate > 0.45:
        print("⚠️  交易胜率一般（45%-55%）")
    else:
        print("❌ 交易胜率较低（<45%），需要优化信号质量")
    
    # 交易频率分析
    total_signals = strategy_info.get('total_signals', 0)
    trading_days = result['backtest_config']['trading_days']
    
    signal_frequency = total_signals / trading_days if trading_days > 0 else 0
    
    if signal_frequency < 0.1:
        print("✅ 交易频率适中，有利于降低成本")
    elif signal_frequency < 0.2:
        print("⚠️  交易频率较高，注意控制成本")
    else:
        print("❌ 交易频率过高，可能过度交易")
    
    # BOLL策略特定分析
    print(f"\n📊 布林带策略特色表现:")
    boll_period = strategy_info.get('boll_period', 20)
    boll_std = strategy_info.get('boll_std', 2.0)
    print(f"   布林带参数: {boll_period}日均线, {boll_std}倍标准差")
    print(f"   小市值专注: 优先选择中证500中市值较小的股票")
    print(f"   择时精度: 捕捉跌破下轨后的反弹机会")


def compare_with_benchmark(result: dict):
    """与基准对比分析"""
    print(f"\n📈 基准对比分析:")
    
    performance = result['performance_report']['basic_metrics']
    annual_return = performance.get('annual_return', 0)
    max_drawdown = performance.get('max_drawdown', 0)
    sharpe_ratio = performance.get('sharpe_ratio', 0)
    
    # 假设基准数据（中证500指数年化收益率约8-12%）
    benchmark_return = 0.10  # 10%基准收益
    benchmark_drawdown = -0.25  # 25%基准回撤
    benchmark_sharpe = 0.6  # 基准夏普比率
    
    print(f"   策略年化收益: {annual_return:.2%} vs 中证500基准: {benchmark_return:.2%}")
    if annual_return > benchmark_return:
        print("   ✅ 收益率超越基准")
    else:
        print("   ⚠️  收益率未达到基准水平")
    
    print(f"   策略最大回撤: {max_drawdown:.2%} vs 基准回撤: {benchmark_drawdown:.2%}")
    if max_drawdown > benchmark_drawdown:
        print("   ✅ 回撤控制优于基准")
    else:
        print("   ⚠️  回撤控制有待提升")
    
    print(f"   策略夏普比率: {sharpe_ratio:.3f} vs 基准夏普: {benchmark_sharpe:.3f}")
    if sharpe_ratio > benchmark_sharpe:
        print("   ✅ 风险调整收益优于基准")
    else:
        print("   ⚠️  风险调整收益有待提升")


def provide_optimization_suggestions(result: dict):
    """提供优化建议"""
    print(f"\n💡 策略优化建议:")
    
    performance = result['performance_report']['basic_metrics']
    portfolio = result['portfolio_summary']
    strategy_info = result['strategy_info']
    
    # 收益优化建议
    total_return = performance.get('total_return', 0)
    if total_return < 0.15:
        print("📈 收益优化建议:")
        print("   1. 考虑调整布林带参数（如18日/2.2倍标准差）")
        print("   2. 优化小市值股票筛选条件")
        print("   3. 增加成交量放大确认信号")
        print("   4. 考虑结合RSI等超买超卖指标")
    
    # 风险控制建议
    max_drawdown = performance.get('max_drawdown', 0)
    if abs(max_drawdown) > 0.20:
        print("🛡️  风险控制建议:")
        print("   1. 降低单股最大仓位（如调整至15%）")
        print("   2. 加强止损执行（如调整至8%止损）")
        print("   3. 增加市场环境判断，熊市减仓")
        print("   4. 考虑增加最大持仓天数限制")
    
    # 胜率提升建议
    win_rate = portfolio.get('win_rate', 0)
    if win_rate < 0.55:
        print("🎯 胜率提升建议:")
        print("   1. 提高买入信号的筛选标准")
        print("   2. 增加基本面筛选条件")
        print("   3. 优化卖出时机（如趋势反转确认）")
        print("   4. 考虑增加市场情绪指标过滤")
    
    # 交易效率建议
    total_signals = strategy_info.get('total_signals', 0)
    if total_signals < 50:
        print("⚡ 交易效率建议:")
        print("   1. 适当放宽买入条件增加交易机会")
        print("   2. 考虑扩大股票池范围")
        print("   3. 优化调仓频率（如每3天检查一次）")
    elif total_signals > 200:
        print("⚡ 交易效率建议:")
        print("   1. 提高买入门槛减少频繁交易")
        print("   2. 增加持仓时间降低交易成本")
        print("   3. 优化信号过滤避免噪音交易")


def main():
    """主函数"""
    print("🚀 好奇布偶猫BOLL择时策略回测开始...")
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
        strategy = CuriousRagdollBollStrategyAdapter()
        print(f"🎯 好奇布偶猫BOLL择时策略创建完成")
        
        # 4. 运行回测
        print(f"🔄 开始运行回测...")
        result = run_strategy_backtest(
            strategy=strategy,
            config=config,
            stock_codes=None,  # 使用中证500成分股
            max_stocks=50      # 限制股票数量以加快回测速度
        )
        
        # 5. 输出结果
        print_backtest_summary(result)
        
        # 6. 性能分析
        analyze_strategy_performance(result)
        
        # 7. 基准对比
        compare_with_benchmark(result)
        
        # 8. 优化建议
        provide_optimization_suggestions(result)
        
        print(f"\n🎉 回测完成! 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 回测过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 运行好奇布偶猫BOLL择时策略回测
    result = main()
    
    if result:
        print("\n💡 回测结果解读:")
        print("1. 查看生成的图表文件了解策略表现趋势")
        print("2. 分析交易记录CSV文件优化买卖时机")
        print("3. 对比中证500指数评估策略有效性")
        print("4. 关注小市值股票在不同市场环境下的表现")
        print("5. 考虑结合多因子模型进一步优化选股")
        
        print("\n🔧 策略特色:")
        print("✨ 专注中证500小市值股票，挖掘超跌反弹机会")
        print("✨ 布林带技术择时，捕捉趋势转折点")
        print("✨ 严格风险控制，保护资金安全")
        print("✨ 适合中长期持有，降低频繁交易成本")
    else:
        print("\n❌ 回测失败，请检查错误信息并重试")
        print("💡 常见问题排查:")
        print("1. 检查数据库连接是否正常")
        print("2. 确认中证500成分股数据是否完整")
        print("3. 验证布林带技术指标计算是否正确")
        print("4. 检查策略参数配置是否合理")