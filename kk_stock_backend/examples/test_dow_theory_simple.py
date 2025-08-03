#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道氏理论分析模块简单测试
验证模块是否正常工作
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from analysis.dow_theory.core.dow_theory_engine import DowTheoryEngine
from analysis.dow_theory.analyzers.trend_analyzer import TrendAnalyzer
from analysis.dow_theory.analyzers.volume_analyzer import VolumeAnalyzer
from analysis.dow_theory.analyzers.technical_analyzer import TechnicalAnalyzer
from analysis.dow_theory.models.dow_theory_models import TrendType


def create_sample_data():
    """创建示例数据"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # 创建上升趋势的价格数据
    base_price = 10.0
    trend = np.linspace(0, 2, 100)  # 上升趋势
    noise = np.random.normal(0, 0.1, 100)  # 噪声
    
    close_prices = base_price + trend + noise
    open_prices = close_prices + np.random.normal(0, 0.05, 100)
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 0.1, 100))
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 0.1, 100))
    volumes = np.random.normal(1000000, 200000, 100)
    
    return pd.DataFrame({
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': np.abs(volumes)
    }, index=dates)


def test_trend_analyzer():
    """测试趋势分析器"""
    print("=== 测试趋势分析器 ===")
    
    analyzer = TrendAnalyzer()
    data = create_sample_data()
    
    try:
        # 分析趋势
        direction, trend_line = analyzer.analyze_trend(data, TrendType.MINOR)
        print(f"趋势方向: {direction.value}")
        
        if trend_line:
            print(f"趋势线有效: {trend_line.is_valid}")
            print(f"趋势线斜率: {trend_line.slope:.4f}")
            print(f"拟合度: {trend_line.r_squared:.4f}")
        
        # 识别支撑阻力位
        sr_levels = analyzer.identify_support_resistance(data, TrendType.MINOR)
        print(f"发现 {len(sr_levels)} 个支撑阻力位")
        
        for i, sr in enumerate(sr_levels[:3]):
            print(f"  {i+1}. {sr.level_type}: {sr.level:.2f} (强度: {sr.strength.value})")
        
        print("✅ 趋势分析器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 趋势分析器测试失败: {e}")
        return False


def test_volume_analyzer():
    """测试成交量分析器"""
    print("\n=== 测试成交量分析器 ===")
    
    analyzer = VolumeAnalyzer()
    data = create_sample_data()
    
    try:
        # 分析成交量模式
        volume_analysis = analyzer.analyze_volume_pattern(data)
        
        print(f"当前成交量: {volume_analysis.current_volume:,.0f}")
        print(f"20日均量: {volume_analysis.avg_volume_20d:,.0f}")
        print(f"量比: {volume_analysis.volume_ratio:.2f}")
        print(f"量价模式: {volume_analysis.pattern.value}")
        print(f"背离信号: {'是' if volume_analysis.divergence_signal else '否'}")
        print(f"信号强度: {volume_analysis.strength.value}")
        
        print("✅ 成交量分析器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 成交量分析器测试失败: {e}")
        return False


def test_technical_analyzer():
    """测试技术指标分析器"""
    print("\n=== 测试技术指标分析器 ===")
    
    analyzer = TechnicalAnalyzer()
    data = create_sample_data()
    
    try:
        # 计算技术指标
        indicators = analyzer.calculate_indicators(data)
        
        print(f"当前价格: {indicators.current_price:.2f}")
        print(f"MA20: {indicators.ma_20:.2f}")
        print(f"MA60: {indicators.ma_60:.2f}")
        print(f"MACD DIF: {indicators.macd_dif:.4f}")
        print(f"MACD DEA: {indicators.macd_dea:.4f}")
        print(f"RSI: {indicators.rsi:.2f}")
        
        # 测试布林带
        bb = analyzer.calculate_bollinger_bands(data)
        print(f"布林带上轨: {bb['upper_band']:.2f}")
        print(f"布林带中轨: {bb['middle_band']:.2f}")
        print(f"布林带下轨: {bb['lower_band']:.2f}")
        print(f"价格位置: {bb['position']:.2f}")
        
        print("✅ 技术指标分析器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 技术指标分析器测试失败: {e}")
        return False


def test_integration():
    """测试集成功能"""
    print("\n=== 测试集成功能 ===")
    
    try:
        # 注意：这个测试需要数据库连接，如果没有数据可能会失败
        # 我们创建一个简化的测试
        
        from analysis.dow_theory.utils.data_fetcher import DataFetcher
        from analysis.dow_theory.utils.confirmation_validator import ConfirmationValidator
        
        # 测试数据获取器初始化
        data_fetcher = DataFetcher()
        print("✅ 数据获取器初始化成功")
        
        # 测试确认验证器
        validator = ConfirmationValidator()
        print("✅ 确认验证器初始化成功")
        
        print("✅ 集成功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 集成功能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("道氏理论分析模块简单测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各个测试
    test_results.append(test_trend_analyzer())
    test_results.append(test_volume_analyzer())
    test_results.append(test_technical_analyzer())
    test_results.append(test_integration())
    
    # 汇总结果
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n" + "=" * 50)
    print(f"测试完成: {passed}/{total} 通过")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有测试都通过了！道氏理论分析模块运行正常。")
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)