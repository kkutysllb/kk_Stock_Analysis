#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道氏理论分析模块使用示例
展示如何使用道氏理论分析模块进行股票分析
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from analysis.dow_theory.core.dow_theory_engine import DowTheoryEngine
from analysis.dow_theory.models.dow_theory_models import TrendDirection, TrendPhase


def basic_analysis_example():
    """基础分析示例"""
    print("=== 道氏理论基础分析示例 ===\n")
    
    # 创建分析引擎
    engine = DowTheoryEngine()
    
    try:
        # 分析指定股票
        stock_code = "000001.SZ"  # 平安银行
        print(f"正在分析股票: {stock_code}")
        
        result = engine.analyze_stock(stock_code)
        
        # 输出基本信息
        print(f"\n股票信息:")
        print(f"  代码: {result.stock_code}")
        print(f"  名称: {result.stock_name}")
        print(f"  当前价格: {result.current_price:.2f}")
        print(f"  分析日期: {result.analysis_date.strftime('%Y-%m-%d')}")
        
        # 输出综合评价
        print(f"\n综合评价:")
        print(f"  整体趋势: {result.overall_trend.value}")
        print(f"  趋势阶段: {result.overall_phase.value}")
        print(f"  信心指数: {result.overall_confidence:.1f}%")
        print(f"  操作建议: {result.action_recommendation}")
        
        # 输出多时间周期分析
        print(f"\n多时间周期分析:")
        timeframes = [
            ("月线", result.monthly_analysis),
            ("周线", result.weekly_analysis),
            ("日线", result.daily_analysis)
        ]
        
        for name, analysis in timeframes:
            print(f"  {name}:")
            print(f"    趋势方向: {analysis.direction.value}")
            print(f"    趋势阶段: {analysis.phase.value}")
            print(f"    信心指数: {analysis.confidence_score:.1f}%")
            
            # 输出支撑阻力位
            if analysis.support_resistance:
                sr_info = []
                for sr in analysis.support_resistance[:3]:  # 显示前3个
                    sr_info.append(f"{sr.level:.2f}({sr.level_type})")
                print(f"    关键位置: {', '.join(sr_info)}")
        
        # 输出多重确认
        print(f"\n多重确认:")
        conf = result.multi_timeframe_confirmation
        print(f"  主要-次要趋势一致: {'是' if conf.primary_secondary_alignment else '否'}")
        print(f"  次要-短期趋势一致: {'是' if conf.secondary_minor_alignment else '否'}")
        print(f"  整体趋势一致: {'是' if conf.overall_alignment else '否'}")
        print(f"  确认强度: {conf.confirmation_strength.value}")
        
        if conf.conflicting_signals:
            print(f"  冲突信号: {', '.join(conf.conflicting_signals)}")
        
        # 输出风险评估
        print(f"\n风险评估:")
        risk = result.risk_assessment
        print(f"  风险等级: {risk.risk_level}")
        print(f"  止损价位: {risk.stop_loss_price:.2f}")
        print(f"  目标价位: {risk.target_price:.2f}")
        print(f"  建议仓位: {risk.position_suggestion:.1f}%")
        
        if risk.key_risk_factors:
            print(f"  关键风险: {', '.join(risk.key_risk_factors)}")
        
        # 输出分析摘要
        print(f"\n分析摘要:")
        print(f"  {result.analysis_summary}")
        
    except Exception as e:
        print(f"分析失败: {e}")


def batch_analysis_example():
    """批量分析示例"""
    print("\n\n=== 批量分析示例 ===\n")
    
    engine = DowTheoryEngine()
    
    # 要分析的股票列表
    stock_codes = [
        "000001.SZ",  # 平安银行
        "000002.SZ",  # 万科A
        "600000.SH",  # 浦发银行
        "600036.SH",  # 招商银行
    ]
    
    results = []
    
    print("正在进行批量分析...")
    for code in stock_codes:
        try:
            print(f"  分析 {code}...")
            result = engine.analyze_stock(code)
            results.append(result)
        except Exception as e:
            print(f"  {code} 分析失败: {e}")
    
    # 汇总结果
    print(f"\n批量分析结果汇总:")
    print(f"{'股票代码':<12} {'股票名称':<8} {'当前价格':<8} {'趋势方向':<8} {'趋势阶段':<12} {'信心指数':<8} {'操作建议':<8}")
    print("-" * 80)
    
    for result in results:
        print(f"{result.stock_code:<12} {result.stock_name:<8} {result.current_price:<8.2f} "
              f"{result.overall_trend.value:<8} {result.overall_phase.value:<12} "
              f"{result.overall_confidence:<8.1f} {result.action_recommendation:<8}")
    
    # 统计分析
    if results:
        trend_stats = {}
        phase_stats = {}
        action_stats = {}
        
        for result in results:
            trend = result.overall_trend.value
            phase = result.overall_phase.value
            action = result.action_recommendation
            
            trend_stats[trend] = trend_stats.get(trend, 0) + 1
            phase_stats[phase] = phase_stats.get(phase, 0) + 1
            action_stats[action] = action_stats.get(action, 0) + 1
        
        print(f"\n统计分析:")
        print(f"  趋势分布: {trend_stats}")
        print(f"  阶段分布: {phase_stats}")
        print(f"  操作建议分布: {action_stats}")


def technical_indicators_example():
    """技术指标分析示例"""
    print("\n\n=== 技术指标分析示例 ===\n")
    
    engine = DowTheoryEngine()
    
    try:
        stock_code = "000001.SZ"
        result = engine.analyze_stock(stock_code)
        
        print(f"股票 {result.stock_code} ({result.stock_name}) 技术指标分析:")
        
        # 展示各时间周期的技术指标
        timeframes = [
            ("月线", result.monthly_analysis),
            ("周线", result.weekly_analysis),
            ("日线", result.daily_analysis)
        ]
        
        for name, analysis in timeframes:
            tech = analysis.technical_indicators
            print(f"\n{name}技术指标:")
            print(f"  当前价格: {tech.current_price:.2f}")
            print(f"  MA20: {tech.ma_20:.2f}")
            print(f"  MA60: {tech.ma_60:.2f}")
            print(f"  MA250: {tech.ma_250:.2f}")
            print(f"  MACD DIF: {tech.macd_dif:.4f}")
            print(f"  MACD DEA: {tech.macd_dea:.4f}")
            print(f"  MACD 柱状线: {tech.macd_histogram:.4f}")
            print(f"  RSI: {tech.rsi:.2f}")
            
            # 移动平均线排列分析
            if tech.current_price > tech.ma_20 > tech.ma_60:
                ma_signal = "多头排列"
            elif tech.current_price < tech.ma_20 < tech.ma_60:
                ma_signal = "空头排列"
            else:
                ma_signal = "混乱排列"
            print(f"  均线排列: {ma_signal}")
            
            # MACD信号
            if tech.macd_dif > tech.macd_dea:
                macd_signal = "金叉(看多)"
            else:
                macd_signal = "死叉(看空)"
            print(f"  MACD信号: {macd_signal}")
            
            # RSI信号
            if tech.rsi > 80:
                rsi_signal = "超买"
            elif tech.rsi < 20:
                rsi_signal = "超卖"
            elif tech.rsi > 70:
                rsi_signal = "偏强"
            elif tech.rsi < 30:
                rsi_signal = "偏弱"
            else:
                rsi_signal = "正常"
            print(f"  RSI状态: {rsi_signal}")
        
    except Exception as e:
        print(f"技术指标分析失败: {e}")


def volume_analysis_example():
    """成交量分析示例"""
    print("\n\n=== 成交量分析示例 ===\n")
    
    engine = DowTheoryEngine()
    
    try:
        stock_code = "000001.SZ"
        result = engine.analyze_stock(stock_code)
        
        print(f"股票 {result.stock_code} ({result.stock_name}) 成交量分析:")
        
        timeframes = [
            ("月线", result.monthly_analysis),
            ("周线", result.weekly_analysis),
            ("日线", result.daily_analysis)
        ]
        
        for name, analysis in timeframes:
            vol = analysis.volume_analysis
            print(f"\n{name}成交量分析:")
            print(f"  当前成交量: {vol.current_volume:,.0f}")
            print(f"  20日均量: {vol.avg_volume_20d:,.0f}")
            print(f"  量比: {vol.volume_ratio:.2f}")
            print(f"  量价模式: {vol.pattern.value}")
            print(f"  背离信号: {'是' if vol.divergence_signal else '否'}")
            print(f"  信号强度: {vol.strength.value}")
            
            # 成交量状态解读
            if vol.volume_ratio > 2.0:
                vol_status = "异常放量"
            elif vol.volume_ratio > 1.5:
                vol_status = "明显放量"
            elif vol.volume_ratio > 1.2:
                vol_status = "温和放量"
            elif vol.volume_ratio < 0.5:
                vol_status = "严重萎缩"
            elif vol.volume_ratio < 0.8:
                vol_status = "成交萎缩"
            else:
                vol_status = "正常水平"
            print(f"  量能状态: {vol_status}")
        
    except Exception as e:
        print(f"成交量分析失败: {e}")


def phase_transition_example():
    """趋势阶段转换分析示例"""
    print("\n\n=== 趋势阶段转换分析示例 ===\n")
    
    from analysis.dow_theory.analyzers.phase_analyzer import PhaseAnalyzer
    from analysis.dow_theory.utils.data_fetcher import DataFetcher
    
    try:
        # 获取数据
        data_fetcher = DataFetcher()
        stock_code = "000001.SZ"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 6个月数据
        
        daily_data = data_fetcher.get_daily_data(stock_code, start_date, end_date)
        
        if not daily_data.empty:
            phase_analyzer = PhaseAnalyzer()
            
            # 假设当前阶段为公众参与期
            current_phase = TrendPhase.PUBLIC_PARTICIPATION
            
            # 分析阶段转换可能性
            transition_analysis = phase_analyzer.analyze_phase_transition(daily_data, current_phase)
            
            print(f"股票 {stock_code} 阶段转换分析:")
            print(f"  当前阶段: {current_phase.value}")
            print(f"  转换概率: {transition_analysis['transition_probability']:.1%}")
            print(f"  可能的下一阶段: {transition_analysis['next_phase'].value}")
            print(f"  当前阶段强度: {transition_analysis['current_phase_strength']:.2f}")
            
            if transition_analysis['signals']:
                print(f"  转换信号:")
                for signal in transition_analysis['signals']:
                    print(f"    - {signal}")
            
            # 获取阶段特征描述
            characteristics = phase_analyzer.get_phase_characteristics(current_phase)
            print(f"\n当前阶段特征:")
            print(f"  描述: {characteristics.get('description', 'N/A')}")
            print(f"  价格行为: {characteristics.get('price_behavior', 'N/A')}")
            print(f"  成交量行为: {characteristics.get('volume_behavior', 'N/A')}")
            print(f"  投资策略: {characteristics.get('investment_strategy', 'N/A')}")
            print(f"  风险等级: {characteristics.get('risk_level', 'N/A')}")
        
        else:
            print("无法获取数据进行阶段转换分析")
    
    except Exception as e:
        print(f"阶段转换分析失败: {e}")


def main():
    """主函数"""
    print("道氏理论分析模块使用示例")
    print("=" * 50)
    
    try:
        # 运行各种示例
        basic_analysis_example()
        batch_analysis_example()
        technical_indicators_example()
        volume_analysis_example()
        phase_transition_example()
        
        print("\n\n=== 示例运行完成 ===")
        print("更多功能请参考模块文档和API接口")
        
    except KeyboardInterrupt:
        print("\n用户中断执行")
    except Exception as e:
        print(f"\n示例运行出错: {e}")


if __name__ == "__main__":
    main()