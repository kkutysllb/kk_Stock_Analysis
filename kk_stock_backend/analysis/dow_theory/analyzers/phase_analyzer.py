#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势阶段识别器
实现道氏理论中的三个趋势阶段识别：累积期、公众参与期、恐慌期
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
import logging

import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from analysis.dow_theory.models.dow_theory_models import (
    TrendPhase, TrendDirection, VolumeAnalysis, SignalStrength
)


class PhaseAnalyzer:
    """趋势阶段识别器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def identify_phase(self, data: pd.DataFrame, trend_direction: TrendDirection, 
                      volume_analysis: VolumeAnalysis) -> TrendPhase:
        """
        识别当前趋势阶段
        
        Args:
            data: 价格和成交量数据
            trend_direction: 趋势方向
            volume_analysis: 成交量分析结果
            
        Returns:
            趋势阶段
        """
        if data.empty or len(data) < 30:
            return TrendPhase.ACCUMULATION
        
        # 基于趋势方向选择不同的阶段识别策略
        if trend_direction == TrendDirection.UPWARD:
            return self._identify_uptrend_phase(data, volume_analysis)
        elif trend_direction == TrendDirection.DOWNWARD:
            return self._identify_downtrend_phase(data, volume_analysis)
        else:
            return self._identify_sideways_phase(data, volume_analysis)
    
    def _identify_uptrend_phase(self, data: pd.DataFrame, volume_analysis: VolumeAnalysis) -> TrendPhase:
        """识别上升趋势的阶段"""
        # 计算关键指标
        phase_indicators = self._calculate_phase_indicators(data)
        
        # 累积期特征判断
        if self._is_accumulation_phase(data, phase_indicators, volume_analysis):
            return TrendPhase.ACCUMULATION
        
        # 恐慌期特征判断（上升趋势中的恐慌期表现为过度乐观）
        if self._is_panic_phase_uptrend(data, phase_indicators, volume_analysis):
            return TrendPhase.PANIC
        
        # 默认为公众参与期
        return TrendPhase.PUBLIC_PARTICIPATION
    
    def _identify_downtrend_phase(self, data: pd.DataFrame, volume_analysis: VolumeAnalysis) -> TrendPhase:
        """识别下降趋势的阶段"""
        # 计算关键指标
        phase_indicators = self._calculate_phase_indicators(data)
        
        # 恐慌期特征判断（下降趋势中的恐慌期表现为恐慌抛售）
        if self._is_panic_phase_downtrend(data, phase_indicators, volume_analysis):
            return TrendPhase.PANIC
        
        # 累积期特征判断（下降趋势后期的筑底阶段）
        if self._is_accumulation_phase_downtrend(data, phase_indicators, volume_analysis):
            return TrendPhase.ACCUMULATION
        
        # 默认为公众参与期
        return TrendPhase.PUBLIC_PARTICIPATION
    
    def _identify_sideways_phase(self, data: pd.DataFrame, volume_analysis: VolumeAnalysis) -> TrendPhase:
        """识别横盘震荡的阶段"""
        # 横盘期间通常是累积期或分化期
        phase_indicators = self._calculate_phase_indicators(data)
        
        # 检查是否为低位横盘（累积期）
        current_price = data.iloc[-1]['close']
        price_range = data['high'].max() - data['low'].min()
        price_position = (current_price - data['low'].min()) / price_range if price_range > 0 else 0.5
        
        # 如果在低位区间且成交量较小，可能是累积期
        if price_position < 0.3 and volume_analysis.volume_ratio < 1.2:
            return TrendPhase.ACCUMULATION
        
        # 如果在高位区间且成交量放大，可能是分发期（恐慌期前期）
        if price_position > 0.7 and volume_analysis.volume_ratio > 1.5:
            return TrendPhase.PANIC
        
        return TrendPhase.PUBLIC_PARTICIPATION
    
    def _calculate_phase_indicators(self, data: pd.DataFrame) -> Dict:
        """计算阶段识别所需的指标"""
        indicators = {}
        
        # 价格波动性
        returns = data['close'].pct_change().fillna(0)
        indicators['volatility'] = returns.std() * np.sqrt(252)  # 年化波动率
        indicators['recent_volatility'] = returns.tail(10).std() * np.sqrt(252)
        
        # 价格位置
        recent_period = min(60, len(data))
        recent_data = data.tail(recent_period)
        price_high = recent_data['high'].max()
        price_low = recent_data['low'].min()
        current_price = data.iloc[-1]['close']
        indicators['price_position'] = (current_price - price_low) / (price_high - price_low) if price_high > price_low else 0.5
        
        # 趋势强度
        ma_20 = data['close'].rolling(20).mean()
        ma_60 = data['close'].rolling(60).mean()
        indicators['trend_strength'] = abs(ma_20.iloc[-1] - ma_60.iloc[-1]) / ma_60.iloc[-1] if len(data) >= 60 and ma_60.iloc[-1] > 0 else 0
        
        # 价格动量
        momentum_10 = (data['close'].iloc[-1] - data['close'].iloc[-11]) / data['close'].iloc[-11] if len(data) >= 11 else 0
        momentum_20 = (data['close'].iloc[-1] - data['close'].iloc[-21]) / data['close'].iloc[-21] if len(data) >= 21 else 0
        indicators['momentum_10'] = momentum_10
        indicators['momentum_20'] = momentum_20
        
        # 成交量相对水平
        volume_recent = data['volume'].tail(10).mean()
        volume_baseline = data['volume'].tail(50).mean() if len(data) >= 50 else data['volume'].mean()
        indicators['volume_relative'] = volume_recent / volume_baseline if volume_baseline > 0 else 1.0
        
        # 价格区间突破情况
        indicators['breakout_strength'] = self._calculate_breakout_strength(data)
        
        return indicators
    
    def _calculate_breakout_strength(self, data: pd.DataFrame) -> float:
        """计算突破强度"""
        if len(data) < 20:
            return 0.0
        
        # 计算最近20日的价格区间
        recent_data = data.tail(20)
        price_range = recent_data['high'].max() - recent_data['low'].min()
        
        if price_range == 0:
            return 0.0
        
        # 当前价格相对于区间的位置
        current_price = data.iloc[-1]['close']
        range_low = recent_data['low'].min()
        range_high = recent_data['high'].max()
        
        if current_price > range_high:
            # 向上突破
            return (current_price - range_high) / price_range
        elif current_price < range_low:
            # 向下突破
            return (range_low - current_price) / price_range
        else:
            return 0.0
    
    def _is_accumulation_phase(self, data: pd.DataFrame, indicators: Dict, volume_analysis: VolumeAnalysis) -> bool:
        """判断是否为累积期"""
        conditions = []
        
        # 1. 价格在相对低位（低于60%）
        conditions.append(indicators['price_position'] < 0.6)
        
        # 2. 波动性相对较低
        conditions.append(indicators['recent_volatility'] < indicators['volatility'] * 1.2)
        
        # 3. 成交量相对较小
        conditions.append(volume_analysis.volume_ratio < 1.3)
        
        # 4. 趋势强度不大（处于整理状态）
        conditions.append(indicators['trend_strength'] < 0.05)
        
        # 5. 动量较弱
        conditions.append(abs(indicators['momentum_10']) < 0.03)
        
        # 6. 没有明显突破
        conditions.append(indicators['breakout_strength'] < 0.02)
        
        # 至少满足4个条件
        return sum(conditions) >= 4
    
    def _is_accumulation_phase_downtrend(self, data: pd.DataFrame, indicators: Dict, volume_analysis: VolumeAnalysis) -> bool:
        """判断下降趋势中是否为累积期（筑底阶段）"""
        conditions = []
        
        # 1. 价格在低位
        conditions.append(indicators['price_position'] < 0.4)
        
        # 2. 下跌动量减弱
        conditions.append(indicators['momentum_10'] > -0.02)  # 不再大幅下跌
        
        # 3. 成交量萎缩
        conditions.append(volume_analysis.volume_ratio < 0.8)
        
        # 4. 波动性下降
        conditions.append(indicators['recent_volatility'] < indicators['volatility'])
        
        # 5. 出现背离信号
        conditions.append(volume_analysis.divergence_signal)
        
        # 至少满足3个条件
        return sum(conditions) >= 3
    
    def _is_panic_phase_uptrend(self, data: pd.DataFrame, indicators: Dict, volume_analysis: VolumeAnalysis) -> bool:
        """判断上升趋势中是否为恐慌期（过度乐观）"""
        conditions = []
        
        # 1. 价格在高位
        conditions.append(indicators['price_position'] > 0.8)
        
        # 2. 成交量异常放大
        conditions.append(volume_analysis.volume_ratio > 2.0)
        
        # 3. 短期动量过大
        conditions.append(indicators['momentum_10'] > 0.05)
        
        # 4. 波动性明显增加
        conditions.append(indicators['recent_volatility'] > indicators['volatility'] * 1.5)
        
        # 5. 出现向上突破但可能失败
        conditions.append(indicators['breakout_strength'] > 0.03)
        
        # 6. 量价背离信号
        conditions.append(volume_analysis.divergence_signal)
        
        # 至少满足4个条件
        return sum(conditions) >= 4
    
    def _is_panic_phase_downtrend(self, data: pd.DataFrame, indicators: Dict, volume_analysis: VolumeAnalysis) -> bool:
        """判断下降趋势中是否为恐慌期（恐慌抛售）"""
        conditions = []
        
        # 1. 急速下跌
        conditions.append(indicators['momentum_10'] < -0.05)
        
        # 2. 成交量爆发
        conditions.append(volume_analysis.volume_ratio > 2.0)
        
        # 3. 波动性急剧上升
        conditions.append(indicators['recent_volatility'] > indicators['volatility'] * 2.0)
        
        # 4. 向下突破重要支撑
        conditions.append(indicators['breakout_strength'] > 0.03)
        
        # 5. 价格可能已经在相对低位但仍在下跌
        conditions.append(indicators['price_position'] < 0.5 and indicators['momentum_10'] < 0)
        
        # 至少满足3个条件
        return sum(conditions) >= 3
    
    def analyze_phase_transition(self, historical_data: pd.DataFrame, current_phase: TrendPhase) -> Dict:
        """分析阶段转换的可能性"""
        if len(historical_data) < 60:
            return {'transition_probability': 0.0, 'next_phase': current_phase, 'signals': []}
        
        signals = []
        transition_probability = 0.0
        next_phase = current_phase
        
        # 计算最近的趋势变化
        recent_indicators = self._calculate_phase_indicators(historical_data.tail(30))
        older_indicators = self._calculate_phase_indicators(historical_data.tail(60).head(30))
        
        # 分析各种转换信号
        if current_phase == TrendPhase.ACCUMULATION:
            # 累积期向公众参与期转换的信号
            if (recent_indicators['volume_relative'] > older_indicators['volume_relative'] * 1.3 and
                recent_indicators['breakout_strength'] > 0.02):
                signals.append("成交量开始放大，可能突破")
                transition_probability += 0.3
            
            if recent_indicators['momentum_10'] > 0.02:
                signals.append("价格动量转正")
                transition_probability += 0.3
                next_phase = TrendPhase.PUBLIC_PARTICIPATION
        
        elif current_phase == TrendPhase.PUBLIC_PARTICIPATION:
            # 公众参与期向恐慌期转换的信号
            if (recent_indicators['volatility'] > older_indicators['volatility'] * 1.5 and
                recent_indicators['volume_relative'] > 2.0):
                signals.append("波动性和成交量急剧上升")
                transition_probability += 0.4
                next_phase = TrendPhase.PANIC
            
            # 公众参与期向累积期转换的信号（趋势衰竭）
            if (recent_indicators['momentum_10'] < older_indicators['momentum_10'] * 0.5 and
                recent_indicators['volume_relative'] < 0.8):
                signals.append("动量衰减，成交量萎缩")
                transition_probability += 0.3
                next_phase = TrendPhase.ACCUMULATION
        
        elif current_phase == TrendPhase.PANIC:
            # 恐慌期向累积期转换的信号
            if (recent_indicators['volatility'] < older_indicators['volatility'] * 0.7 and
                recent_indicators['volume_relative'] < 1.0):
                signals.append("波动性下降，成交量回归正常")
                transition_probability += 0.4
                next_phase = TrendPhase.ACCUMULATION
        
        return {
            'transition_probability': min(transition_probability, 1.0),
            'next_phase': next_phase,
            'signals': signals,
            'current_phase_strength': self._calculate_phase_strength(historical_data, current_phase)
        }
    
    def _calculate_phase_strength(self, data: pd.DataFrame, phase: TrendPhase) -> float:
        """计算当前阶段的强度"""
        indicators = self._calculate_phase_indicators(data)
        
        if phase == TrendPhase.ACCUMULATION:
            # 累积期的强度基于横盘的稳定性
            stability_score = 1.0 - min(indicators['recent_volatility'] / 0.3, 1.0)
            volume_score = 1.0 - min(indicators['volume_relative'] / 1.5, 1.0)
            return (stability_score + volume_score) / 2
        
        elif phase == TrendPhase.PUBLIC_PARTICIPATION:
            # 公众参与期的强度基于趋势的持续性
            trend_score = min(indicators['trend_strength'] / 0.1, 1.0)
            momentum_score = min(abs(indicators['momentum_10']) / 0.05, 1.0)
            return (trend_score + momentum_score) / 2
        
        elif phase == TrendPhase.PANIC:
            # 恐慌期的强度基于市场的极端程度
            volatility_score = min(indicators['recent_volatility'] / 0.5, 1.0)
            volume_score = min(indicators['volume_relative'] / 3.0, 1.0)
            return (volatility_score + volume_score) / 2
        
        return 0.5
    
    def get_phase_characteristics(self, phase: TrendPhase) -> Dict:
        """获取阶段特征描述"""
        characteristics = {
            TrendPhase.ACCUMULATION: {
                'description': '累积期：大资金悄然建仓，价格横盘整理',
                'price_behavior': '在重要支撑位附近横盘，波动较小',
                'volume_behavior': '成交量相对较小，偶有异常放量',
                'market_sentiment': '悲观情绪逐渐消散，关注度较低',
                'investment_strategy': '逐步建仓，分批买入，设置较宽止损',
                'risk_level': 'medium',
                'typical_duration': '数月到一年'
            },
            TrendPhase.PUBLIC_PARTICIPATION: {
                'description': '公众参与期：趋势明确，市场参与度提高',
                'price_behavior': '明确突破重要位置，趋势加速发展',
                'volume_behavior': '成交量显著放大并持续活跃',
                'market_sentiment': '乐观情绪升温，媒体关注增加',
                'investment_strategy': '持有为主，适度加仓，跟踪止损',
                'risk_level': 'low',
                'typical_duration': '数月'
            },
            TrendPhase.PANIC: {
                'description': '恐慌期：情绪极端化，走势剧烈波动',
                'price_behavior': '大幅波动，可能出现长上影线或长下影线',
                'volume_behavior': '成交量达到高峰，异常活跃',
                'market_sentiment': '极度乐观或极度悲观',
                'investment_strategy': '准备反向操作，严格止损，降低仓位',
                'risk_level': 'high',
                'typical_duration': '数周到数月'
            }
        }
        
        return characteristics.get(phase, {})
    
    def validate_phase_identification(self, data: pd.DataFrame, identified_phase: TrendPhase) -> Dict:
        """验证阶段识别的准确性"""
        validation_score = 0.0
        validation_details = []
        
        indicators = self._calculate_phase_indicators(data)
        volume_analysis = VolumeAnalysis(
            current_volume=data.iloc[-1]['volume'],
            avg_volume_20d=data['volume'].tail(20).mean(),
            volume_ratio=indicators['volume_relative'],
            pattern=None,  # 简化处理
            divergence_signal=False,
            strength=SignalStrength.MEDIUM
        )
        
        # 基于阶段特征进行验证
        if identified_phase == TrendPhase.ACCUMULATION:
            if indicators['price_position'] < 0.6:
                validation_score += 0.25
                validation_details.append("价格位置符合累积期特征")
            
            if volume_analysis.volume_ratio < 1.3:
                validation_score += 0.25
                validation_details.append("成交量水平符合累积期特征")
            
            if indicators['recent_volatility'] < indicators['volatility'] * 1.2:
                validation_score += 0.25
                validation_details.append("波动性符合累积期特征")
            
            if abs(indicators['momentum_10']) < 0.03:
                validation_score += 0.25
                validation_details.append("价格动量符合累积期特征")
        
        elif identified_phase == TrendPhase.PUBLIC_PARTICIPATION:
            if 0.3 < indicators['price_position'] < 0.8:
                validation_score += 0.3
                validation_details.append("价格位置符合公众参与期特征")
            
            if 1.2 < volume_analysis.volume_ratio < 2.5:
                validation_score += 0.3
                validation_details.append("成交量水平符合公众参与期特征")
            
            if indicators['trend_strength'] > 0.02:
                validation_score += 0.2
                validation_details.append("趋势强度符合公众参与期特征")
            
            if 0.01 < abs(indicators['momentum_10']) < 0.08:
                validation_score += 0.2
                validation_details.append("价格动量符合公众参与期特征")
        
        elif identified_phase == TrendPhase.PANIC:
            if indicators['price_position'] > 0.8 or indicators['price_position'] < 0.2:
                validation_score += 0.3
                validation_details.append("价格位置符合恐慌期特征")
            
            if volume_analysis.volume_ratio > 2.0:
                validation_score += 0.3
                validation_details.append("成交量爆发符合恐慌期特征")
            
            if indicators['recent_volatility'] > indicators['volatility'] * 1.5:
                validation_score += 0.2
                validation_details.append("高波动性符合恐慌期特征")
            
            if abs(indicators['momentum_10']) > 0.05:
                validation_score += 0.2
                validation_details.append("极端动量符合恐慌期特征")
        
        return {
            'validation_score': validation_score,
            'confidence_level': 'high' if validation_score > 0.7 else 'medium' if validation_score > 0.4 else 'low',
            'validation_details': validation_details
        }