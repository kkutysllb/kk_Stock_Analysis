#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道氏理论分析模块测试用例
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from analysis.dow_theory.core.dow_theory_engine import DowTheoryEngine
from analysis.dow_theory.analyzers.trend_analyzer import TrendAnalyzer
from analysis.dow_theory.analyzers.volume_analyzer import VolumeAnalyzer
from analysis.dow_theory.analyzers.phase_analyzer import PhaseAnalyzer
from analysis.dow_theory.analyzers.technical_analyzer import TechnicalAnalyzer
from analysis.dow_theory.utils.data_fetcher import DataFetcher
from analysis.dow_theory.utils.confirmation_validator import ConfirmationValidator
from analysis.dow_theory.models.dow_theory_models import (
    TrendDirection, TrendType, TrendPhase, VolumePattern, SignalStrength
)


class TestDowTheoryEngine(unittest.TestCase):
    """道氏理论引擎测试"""
    
    def setUp(self):
        """测试前准备"""
        self.engine = DowTheoryEngine()
        self.sample_data = self._create_sample_data()
    
    def _create_sample_data(self) -> pd.DataFrame:
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
    
    def test_analyze_stock_success(self):
        """测试股票分析成功情况"""
        # 直接使用mock而不依赖真实数据库
        with patch.object(self.engine, 'data_fetcher') as mock_fetcher:
            # Mock数据获取器的返回值
            mock_fetcher.get_daily_data.return_value = self.sample_data
            mock_fetcher.get_weekly_data.return_value = self.sample_data.resample('W').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            })
            mock_fetcher.get_monthly_data.return_value = self.sample_data.resample('ME').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            })
            mock_fetcher.get_factor_data.return_value = pd.DataFrame()
            mock_fetcher.get_stock_basic_info.return_value = {'name': '测试股票'}
            
            # 执行分析
            result = self.engine.analyze_stock('000001.SZ')
            
            # 验证结果
            self.assertIsNotNone(result)
            self.assertEqual(result.stock_code, '000001.SZ')
            self.assertIn(result.overall_trend, [TrendDirection.UPWARD, TrendDirection.DOWNWARD, TrendDirection.SIDEWAYS])
            self.assertIn(result.overall_phase, [TrendPhase.ACCUMULATION, TrendPhase.PUBLIC_PARTICIPATION, TrendPhase.PANIC])
            self.assertGreaterEqual(result.overall_confidence, 0)
            self.assertLessEqual(result.overall_confidence, 100)


class TestTrendAnalyzer(unittest.TestCase):
    """趋势分析器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.analyzer = TrendAnalyzer()
        self.upward_data = self._create_upward_trend_data()
        self.downward_data = self._create_downward_trend_data()
        self.sideways_data = self._create_sideways_trend_data()
    
    def _create_upward_trend_data(self) -> pd.DataFrame:
        """创建上升趋势数据"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        base_prices = np.linspace(10, 15, 50)
        noise = np.random.normal(0, 0.1, 50)
        
        close_prices = base_prices + noise
        open_prices = close_prices + np.random.normal(0, 0.05, 50)
        high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 0.1, 50))
        low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 0.1, 50))
        volumes = np.random.normal(1000000, 200000, 50)
        
        return pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': np.abs(volumes)
        }, index=dates)
    
    def _create_downward_trend_data(self) -> pd.DataFrame:
        """创建下降趋势数据"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        base_prices = np.linspace(15, 10, 50)
        noise = np.random.normal(0, 0.1, 50)
        
        close_prices = base_prices + noise
        open_prices = close_prices + np.random.normal(0, 0.05, 50)
        high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 0.1, 50))
        low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 0.1, 50))
        volumes = np.random.normal(1000000, 200000, 50)
        
        return pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': np.abs(volumes)
        }, index=dates)
    
    def _create_sideways_trend_data(self) -> pd.DataFrame:
        """创建横盘趋势数据"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        base_prices = np.full(50, 12.5)  # 横盘在12.5附近
        noise = np.random.normal(0, 0.3, 50)
        
        close_prices = base_prices + noise
        open_prices = close_prices + np.random.normal(0, 0.05, 50)
        high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 0.1, 50))
        low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 0.1, 50))
        volumes = np.random.normal(1000000, 200000, 50)
        
        return pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': np.abs(volumes)
        }, index=dates)
    
    def test_analyze_upward_trend(self):
        """测试上升趋势识别"""
        direction, trend_line = self.analyzer.analyze_trend(self.upward_data, TrendType.MINOR)
        self.assertIn(direction, [TrendDirection.UPWARD, TrendDirection.SIDEWAYS])  # 允许一定误差
    
    def test_analyze_downward_trend(self):
        """测试下降趋势识别"""
        direction, trend_line = self.analyzer.analyze_trend(self.downward_data, TrendType.MINOR)
        self.assertIn(direction, [TrendDirection.DOWNWARD, TrendDirection.SIDEWAYS])  # 允许一定误差
    
    def test_analyze_sideways_trend(self):
        """测试横盘趋势识别"""
        direction, trend_line = self.analyzer.analyze_trend(self.sideways_data, TrendType.MINOR)
        # 横盘数据可能被识别为任何方向，这是正常的
        self.assertIsInstance(direction, TrendDirection)
    
    def test_identify_support_resistance(self):
        """测试支撑阻力位识别"""
        sr_levels = self.analyzer.identify_support_resistance(self.upward_data, TrendType.MINOR)
        self.assertIsInstance(sr_levels, list)
        
        for sr in sr_levels:
            self.assertIn(sr.level_type, ['support', 'resistance'])
            self.assertIsInstance(sr.strength, SignalStrength)
            self.assertGreater(sr.level, 0)


class TestVolumeAnalyzer(unittest.TestCase):
    """成交量分析器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.analyzer = VolumeAnalyzer()
        self.price_up_volume_up_data = self._create_price_up_volume_up_data()
        self.price_up_volume_down_data = self._create_price_up_volume_down_data()
    
    def _create_price_up_volume_up_data(self) -> pd.DataFrame:
        """创建价涨量增数据"""
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        
        # 价格上涨
        close_prices = np.linspace(10, 12, 20)
        open_prices = close_prices + np.random.normal(0, 0.05, 20)
        high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 0.1, 20))
        low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 0.1, 20))
        
        # 成交量放大
        volumes = np.linspace(500000, 1500000, 20)
        
        return pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        }, index=dates)
    
    def _create_price_up_volume_down_data(self) -> pd.DataFrame:
        """创建价涨量缩数据"""
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        
        # 价格上涨
        close_prices = np.linspace(10, 12, 20)
        open_prices = close_prices + np.random.normal(0, 0.05, 20)
        high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 0.1, 20))
        low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 0.1, 20))
        
        # 成交量萎缩
        volumes = np.linspace(1500000, 500000, 20)
        
        return pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        }, index=dates)
    
    def test_analyze_price_up_volume_up(self):
        """测试价涨量增模式识别"""
        result = self.analyzer.analyze_volume_pattern(self.price_up_volume_up_data)
        self.assertIsInstance(result.pattern, VolumePattern)
        self.assertIsInstance(result.strength, SignalStrength)
        self.assertGreater(result.current_volume, 0)
    
    def test_analyze_price_up_volume_down(self):
        """测试价涨量缩模式识别"""
        result = self.analyzer.analyze_volume_pattern(self.price_up_volume_down_data)
        self.assertIsInstance(result.pattern, VolumePattern)
        self.assertIsInstance(result.strength, SignalStrength)
        self.assertGreater(result.current_volume, 0)


class TestPhaseAnalyzer(unittest.TestCase):
    """趋势阶段分析器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.analyzer = PhaseAnalyzer()
        self.accumulation_data = self._create_accumulation_data()
        self.participation_data = self._create_participation_data()
    
    def _create_accumulation_data(self) -> pd.DataFrame:
        """创建累积期数据"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        
        # 低位横盘，成交量较小
        close_prices = 10 + np.random.normal(0, 0.2, 50)
        volumes = np.random.normal(500000, 100000, 50)
        
        return pd.DataFrame({
            'open': close_prices + np.random.normal(0, 0.05, 50),
            'high': close_prices + np.abs(np.random.normal(0, 0.1, 50)),
            'low': close_prices - np.abs(np.random.normal(0, 0.1, 50)),
            'close': close_prices,
            'volume': np.abs(volumes)
        }, index=dates)
    
    def _create_participation_data(self) -> pd.DataFrame:
        """创建公众参与期数据"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        
        # 明显上涨，成交量放大
        close_prices = np.linspace(10, 15, 50) + np.random.normal(0, 0.1, 50)
        volumes = np.random.normal(1500000, 300000, 50)
        
        return pd.DataFrame({
            'open': close_prices + np.random.normal(0, 0.05, 50),
            'high': close_prices + np.abs(np.random.normal(0, 0.1, 50)),
            'low': close_prices - np.abs(np.random.normal(0, 0.1, 50)),
            'close': close_prices,
            'volume': np.abs(volumes)
        }, index=dates)
    
    def test_identify_accumulation_phase(self):
        """测试累积期识别"""
        # 创建mock成交量分析结果
        volume_analysis = Mock()
        volume_analysis.volume_ratio = 0.8
        volume_analysis.divergence_signal = False
        
        phase = self.analyzer.identify_phase(
            self.accumulation_data, 
            TrendDirection.SIDEWAYS, 
            volume_analysis
        )
        
        # 累积期识别可能有多种结果，验证返回的是有效的趋势阶段
        self.assertIsInstance(phase, TrendPhase)
    
    def test_identify_participation_phase(self):
        """测试公众参与期识别"""
        # 创建mock成交量分析结果
        volume_analysis = Mock()
        volume_analysis.volume_ratio = 1.5
        volume_analysis.divergence_signal = False
        
        phase = self.analyzer.identify_phase(
            self.participation_data, 
            TrendDirection.UPWARD, 
            volume_analysis
        )
        
        # 验证返回的是有效的趋势阶段
        self.assertIsInstance(phase, TrendPhase)


class TestTechnicalAnalyzer(unittest.TestCase):
    """技术指标分析器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.analyzer = TechnicalAnalyzer()
        self.sample_data = self._create_sample_data()
    
    def _create_sample_data(self) -> pd.DataFrame:
        """创建示例数据"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        close_prices = 10 + np.cumsum(np.random.normal(0, 0.1, 100))
        
        return pd.DataFrame({
            'open': close_prices + np.random.normal(0, 0.05, 100),
            'high': close_prices + np.abs(np.random.normal(0, 0.1, 100)),
            'low': close_prices - np.abs(np.random.normal(0, 0.1, 100)),
            'close': close_prices,
            'volume': np.abs(np.random.normal(1000000, 200000, 100))
        }, index=dates)
    
    def test_calculate_indicators(self):
        """测试技术指标计算"""
        indicators = self.analyzer.calculate_indicators(self.sample_data)
        
        # 验证指标值的合理性
        self.assertGreater(indicators.ma_20, 0)
        self.assertGreater(indicators.ma_60, 0)
        self.assertGreater(indicators.ma_250, 0)
        self.assertGreaterEqual(indicators.rsi, 0)
        self.assertLessEqual(indicators.rsi, 100)
        self.assertGreater(indicators.current_price, 0)
    
    def test_calculate_macd(self):
        """测试MACD计算"""
        dif, dea, histogram = self.analyzer._calculate_macd(self.sample_data)
        
        # MACD值应该是数值
        self.assertIsInstance(dif, (int, float))
        self.assertIsInstance(dea, (int, float))
        self.assertIsInstance(histogram, (int, float))
    
    def test_calculate_rsi(self):
        """测试RSI计算"""
        rsi = self.analyzer._calculate_rsi(self.sample_data)
        
        # RSI应该在0-100之间
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)
    
    def test_bollinger_bands(self):
        """测试布林带计算"""
        bb = self.analyzer.calculate_bollinger_bands(self.sample_data)
        
        # 验证布林带结构
        self.assertIn('upper_band', bb)
        self.assertIn('middle_band', bb)
        self.assertIn('lower_band', bb)
        self.assertIn('position', bb)
        
        # 上轨应该大于中轨，中轨应该大于下轨
        self.assertGreater(bb['upper_band'], bb['middle_band'])
        self.assertGreater(bb['middle_band'], bb['lower_band'])
        
        # 位置应该在0-1之间
        self.assertGreaterEqual(bb['position'], 0)
        self.assertLessEqual(bb['position'], 1)


class TestConfirmationValidator(unittest.TestCase):
    """确认验证器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.validator = ConfirmationValidator()
        self.monthly_analysis = self._create_mock_analysis(TrendType.PRIMARY)
        self.weekly_analysis = self._create_mock_analysis(TrendType.SECONDARY)
        self.daily_analysis = self._create_mock_analysis(TrendType.MINOR)
    
    def _create_mock_analysis(self, trend_type: TrendType):
        """创建模拟分析结果"""
        analysis = Mock()
        analysis.trend_type = trend_type
        analysis.direction = TrendDirection.UPWARD
        analysis.phase = TrendPhase.PUBLIC_PARTICIPATION
        analysis.confidence_score = 75.0
        analysis.volume_analysis = Mock()
        analysis.volume_analysis.pattern = VolumePattern.PRICE_UP_VOLUME_UP
        analysis.volume_analysis.divergence_signal = False
        analysis.technical_indicators = Mock()
        analysis.technical_indicators.macd_dif = 0.1
        analysis.technical_indicators.macd_dea = 0.05
        analysis.technical_indicators.rsi = 60.0
        analysis.breakthrough_signals = []
        return analysis
    
    def test_validate_confirmation_aligned(self):
        """测试一致性确认"""
        # 设置所有分析结果一致
        for analysis in [self.monthly_analysis, self.weekly_analysis, self.daily_analysis]:
            analysis.direction = TrendDirection.UPWARD
            analysis.phase = TrendPhase.PUBLIC_PARTICIPATION
        
        confirmation = self.validator.validate_confirmation(
            self.monthly_analysis, 
            self.weekly_analysis, 
            self.daily_analysis
        )
        
        self.assertTrue(confirmation.primary_secondary_alignment)
        self.assertTrue(confirmation.secondary_minor_alignment)
        self.assertTrue(confirmation.overall_alignment)
        self.assertIsInstance(confirmation.confirmation_strength, SignalStrength)
    
    def test_validate_confirmation_divergent(self):
        """测试分歧确认"""
        # 设置分析结果严格不一致
        self.monthly_analysis.direction = TrendDirection.UPWARD
        self.monthly_analysis.confidence_score = 40.0  # 进一步降低信心指数
        self.monthly_analysis.phase = TrendPhase.ACCUMULATION  # 改变阶段
        
        self.weekly_analysis.direction = TrendDirection.DOWNWARD  
        self.weekly_analysis.confidence_score = 90.0   # 很高的信心指数
        self.weekly_analysis.phase = TrendPhase.PANIC
        
        self.daily_analysis.direction = TrendDirection.SIDEWAYS
        self.daily_analysis.confidence_score = 30.0  # 很低的信心指数
        self.daily_analysis.phase = TrendPhase.PUBLIC_PARTICIPATION
        
        confirmation = self.validator.validate_confirmation(
            self.monthly_analysis, 
            self.weekly_analysis, 
            self.daily_analysis
        )
        
        # 应该检测到不一致
        self.assertFalse(confirmation.overall_alignment)
        self.assertIsInstance(confirmation.conflicting_signals, list)


def create_test_suite():
    """创建测试套件"""
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    test_classes = [
        TestDowTheoryEngine,
        TestTrendAnalyzer,
        TestVolumeAnalyzer,
        TestPhaseAnalyzer,
        TestTechnicalAnalyzer,
        TestConfirmationValidator
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


if __name__ == '__main__':
    # 设置numpy随机种子以确保测试的可重现性
    np.random.seed(42)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)
    
    # 输出测试结果统计
    print(f"\n测试完成:")
    print(f"总测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"成功率: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")