#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沪深300专属策略测试脚本
专门针对沪深300成分股的量化策略测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from strategies.qlib_integrated_strategy import QlibIntegratedStrategy, QlibIntegratedConfig
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_csi300_strategy_single_year(year: str):
    """测试沪深300策略单年表现"""
    print(f"\n{'='*60}")
    print(f"🎯 测试沪深300策略 - {year}年")
    print(f"{'='*60}")
    
    # 沪深300专属配置
    config = QlibIntegratedConfig(
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        instruments="csi300",  # 沪深300
        topk=25,              # 选股25只
        n_drop=4,             # 换手4只
        benchmark="SH000300", # 沪深300基准
        max_weight=0.08,      # 单股最大权重8%
        stop_loss=0.06,       # 止损6%
        take_profit=0.12,     # 止盈12%
        rebalance_freq=7      # 调仓频率7天
    )
    
    try:
        # 创建策略实例
        strategy = QlibIntegratedStrategy(config)
        
        # 运行回测
        results = strategy.run_backtest()
        
        # 输出结果
        print("\n📊 回测结果:")
        print(f"年度收益率: {results.get('annual_return', 0):.2%}")
        print(f"最大回撤: {results.get('max_drawdown', 0):.2%}")
        print(f"夏普比率: {results.get('sharpe_ratio', 0):.2f}")
        print(f"胜率: {results.get('win_rate', 0):.2%}")
        print(f"总交易次数: {results.get('total_trades', 0)}")
        print(f"初始资金: {results.get('initial_capital', 0):,.0f}")
        print(f"最终资金: {results.get('final_capital', 0):,.0f}")
        
        return results
        
    except Exception as e:
        logger.error(f"测试{year}年失败: {e}")
        return None


def test_csi300_strategy_multi_year():
    """测试沪深300策略多年表现"""
    print(f"\n{'='*80}")
    print(f"🚀 沪深300专属策略 - 多年回测分析")
    print(f"{'='*80}")
    
    # 测试年份
    test_years = ["2020", "2021", "2022", "2023", "2024"]
    
    all_results = {}
    
    for year in test_years:
        result = test_csi300_strategy_single_year(year)
        if result:
            all_results[year] = result
    
    # 汇总分析
    print(f"\n{'='*80}")
    print(f"📈 沪深300策略多年汇总分析")
    print(f"{'='*80}")
    
    if all_results:
        print(f"{'年份':<8} {'收益率':<12} {'最大回撤':<12} {'夏普比率':<12} {'胜率':<12}")
        print("-" * 60)
        
        total_return = 1.0
        for year, result in all_results.items():
            annual_return = result.get('annual_return', 0)
            max_drawdown = result.get('max_drawdown', 0)
            sharpe_ratio = result.get('sharpe_ratio', 0)
            win_rate = result.get('win_rate', 0)
            
            total_return *= (1 + annual_return)
            
            print(f"{year:<8} {annual_return:<12.2%} {max_drawdown:<12.2%} {sharpe_ratio:<12.2f} {win_rate:<12.2%}")
        
        print("-" * 60)
        print(f"累计收益率: {total_return - 1:.2%}")
        print(f"年化收益率: {(total_return ** (1/len(all_results))) - 1:.2%}")
    
    return all_results


def test_csi300_vs_other_indices():
    """测试沪深300与其他指数的对比"""
    print(f"\n{'='*80}")
    print(f"🏆 沪深300 vs 其他指数对比测试")
    print(f"{'='*80}")
    
    # 测试配置
    indices_configs = [
        ("CSI300", "沪深300", "SH000300"),
        ("CSI500", "中证500", "SH000905"),
        ("CSI1000", "中证1000", "SH000852"),
        ("SSE50", "上证50", "SH000016")
    ]
    
    test_period = ("2023-01-01", "2023-12-31")
    results = {}
    
    for index_code, index_name, benchmark in indices_configs:
        print(f"\n🔍 测试{index_name}...")
        
        config = QlibIntegratedConfig(
            start_date=test_period[0],
            end_date=test_period[1],
            instruments=index_code.lower(),
            benchmark=benchmark,
            # 根据指数特点调整参数
            topk=30 if index_code == "CSI300" else 50,
            n_drop=5 if index_code == "CSI300" else 8,
            max_weight=0.08 if index_code == "CSI300" else 0.1,
            rebalance_freq=7 if index_code == "CSI300" else 5
        )
        
        try:
            strategy = QlibIntegratedStrategy(config)
            result = strategy.run_backtest()
            results[index_name] = result
            
            print(f"  收益率: {result.get('annual_return', 0):.2%}")
            print(f"  最大回撤: {result.get('max_drawdown', 0):.2%}")
            print(f"  夏普比率: {result.get('sharpe_ratio', 0):.2f}")
            
        except Exception as e:
            logger.error(f"测试{index_name}失败: {e}")
            results[index_name] = None
    
    # 对比分析
    print(f"\n{'='*80}")
    print(f"📊 指数对比分析结果")
    print(f"{'='*80}")
    
    print(f"{'指数':<12} {'收益率':<12} {'最大回撤':<12} {'夏普比率':<12} {'评级':<12}")
    print("-" * 72)
    
    for index_name, result in results.items():
        if result:
            annual_return = result.get('annual_return', 0)
            max_drawdown = result.get('max_drawdown', 0)
            sharpe_ratio = result.get('sharpe_ratio', 0)
            
            # 简单评级
            if sharpe_ratio > 1.5:
                rating = "优秀"
            elif sharpe_ratio > 1.0:
                rating = "良好"
            elif sharpe_ratio > 0.5:
                rating = "一般"
            else:
                rating = "需改进"
            
            print(f"{index_name:<12} {annual_return:<12.2%} {max_drawdown:<12.2%} {sharpe_ratio:<12.2f} {rating:<12}")
    
    return results


if __name__ == "__main__":
    print("🎯 沪深300专属策略测试系统")
    print("="*80)
    
    # 1. 单年测试
    print("\n1️⃣ 单年测试 (2023年)")
    test_csi300_strategy_single_year("2023")
    
    # 2. 多年测试
    print("\n2️⃣ 多年测试 (2020-2024)")
    test_csi300_strategy_multi_year()
    
    # 3. 指数对比测试
    print("\n3️⃣ 指数对比测试")
    test_csi300_vs_other_indices()
    
    print("\n✅ 沪深300专属策略测试完成！")