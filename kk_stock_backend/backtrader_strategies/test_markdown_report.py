#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Markdown报告生成功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.performance_analyzer import PerformanceAnalyzer
from datetime import datetime

def test_markdown_report():
    """测试Markdown报告生成"""
    print("🧪 测试Markdown报告生成功能...")
    
    # 创建模拟回测结果
    mock_result = {
        'backtest_config': {
            'initial_cash': 1000000,
            'start_date': '2020-01-01',
            'end_date': '2025-07-18',
            'trading_days': 1400,
            'total_stocks': 50,
            'commission_rate': 0.0003,
            'stamp_tax_rate': 0.001,
            'slippage_rate': 0.001
        },
        'strategy_info': {
            'strategy_name': '多趋势共振策略测试',
            'strategy_version': '1.0.0',
            'max_positions': 8,
            'max_single_weight': 0.12,
            'min_resonance_score': 7,
            'buy_signals_count': 150,
            'sell_signals_count': 145
        },
        'performance_report': {
            'basic_metrics': {
                'total_return': 1.63,
                'annual_return': 0.15,
                'volatility': 0.25,
                'sharpe_ratio': 1.2,
                'max_drawdown': -0.08,
                'calmar_ratio': 1.875
            },
            'advanced_metrics': {
                'sortino_ratio': 1.5,
                'var_5': -0.03,
                'cvar_5': -0.045,
                'max_consecutive_losses': 5,
                'winning_days_ratio': 0.58,
                'avg_win_loss_ratio': 1.8
            },
            'trade_metrics': {
                'monthly_trade_frequency': 5.2,
                'avg_holding_period_days': 15.5
            }
        },
        'portfolio_summary': {
            'total_value': 2630000,
            'cash': 350000,
            'positions_value': 2280000,
            'cash_ratio': 0.133,
            'total_positions': 6,
            'cumulative_return': 1.63,
            'win_rate': 0.62,
            'winning_trades': 90,
            'losing_trades': 55
        },
        'trading_summary': {
            'trades': {
                'total': 295,
                'buy_trades': 150,
                'sell_trades': 145
            },
            'fees': {
                'total_commission': 8500,
                'total_stamp_tax': 12000,
                'total_fees': 20500
            }
        },
        'chart_files': [
            'MultiTrendResonanceStrategyAdapter_portfolio_value.png',
            'MultiTrendResonanceStrategyAdapter_returns_distribution.png',
            'MultiTrendResonanceStrategyAdapter_drawdown.png',
            'MultiTrendResonanceStrategyAdapter_trades_analysis.png'
        ]
    }
    
    # 创建性能分析器
    analyzer = PerformanceAnalyzer()
    
    # 生成Markdown报告
    output_dir = "./results/test"
    os.makedirs(output_dir, exist_ok=True)
    
    markdown_filename = f"{output_dir}/test_comprehensive_analysis_report.md"
    
    try:
        analyzer.export_comprehensive_markdown_report(mock_result, markdown_filename)
        print(f"✅ Markdown报告生成成功: {markdown_filename}")
        
        # 读取并显示报告前几行
        with open(markdown_filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print("\n📋 报告预览（前20行）：")
            print("=" * 60)
            for i, line in enumerate(lines[:20]):
                print(f"{i+1:2}: {line.rstrip()}")
            print("=" * 60)
            print(f"📄 完整报告共 {len(lines)} 行")
        
        return True
        
    except Exception as e:
        print(f"❌ Markdown报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_markdown_report()
    if success:
        print("\n🎉 测试完成！Markdown报告功能正常工作")
    else:
        print("\n❌ 测试失败！请检查错误信息")