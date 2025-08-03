#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成交量分析器
实现道氏理论中的成交量分析，包括量价关系、背离分析等
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import logging

import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from analysis.dow_theory.models.dow_theory_models import (
    VolumeAnalysis, VolumePattern, SignalStrength
)


class VolumeAnalyzer:
    """成交量分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_volume_pattern(self, data: pd.DataFrame) -> VolumeAnalysis:
        """
        分析成交量模式
        
        Args:
            data: 价格和成交量数据
            
        Returns:
            成交量分析结果
        """
        if data.empty or len(data) < 20:
            return self._create_default_volume_analysis()
        
        # 获取最新数据
        current_data = data.iloc[-1]
        recent_data = data.tail(5)  # 最近5个交易日
        
        current_volume = current_data['volume']
        current_close = current_data['close']
        
        # 计算平均成交量
        avg_volume_20d = data['volume'].tail(20).mean()
        volume_ratio = current_volume / avg_volume_20d if avg_volume_20d > 0 else 1.0
        
        # 判断量价模式
        volume_pattern = self._identify_volume_pattern(recent_data)
        
        # 检测背离信号
        divergence_signal = self._detect_volume_divergence(data)
        
        # 评估信号强度
        strength = self._evaluate_volume_strength(volume_ratio, volume_pattern, divergence_signal)
        
        return VolumeAnalysis(
            current_volume=current_volume,
            avg_volume_20d=avg_volume_20d,
            volume_ratio=volume_ratio,
            pattern=volume_pattern,
            divergence_signal=divergence_signal,
            strength=strength
        )
    
    def _create_default_volume_analysis(self) -> VolumeAnalysis:
        """创建默认的成交量分析结果"""
        return VolumeAnalysis(
            current_volume=0,
            avg_volume_20d=0,
            volume_ratio=1.0,
            pattern=VolumePattern.PRICE_UP_VOLUME_DOWN,
            divergence_signal=False,
            strength=SignalStrength.WEAK
        )
    
    def _identify_volume_pattern(self, data: pd.DataFrame) -> VolumePattern:
        """识别量价模式"""
        if data.empty or len(data) < 2:
            return VolumePattern.PRICE_UP_VOLUME_DOWN
        
        # 计算价格和成交量的变化
        price_changes = []
        volume_changes = []
        
        for i in range(1, len(data)):
            price_change = data.iloc[i]['close'] - data.iloc[i-1]['close']
            volume_change = data.iloc[i]['volume'] - data.iloc[i-1]['volume']
            
            price_changes.append(price_change)
            volume_changes.append(volume_change)
        
        # 统计各种模式的出现次数
        price_up_volume_up = 0
        price_up_volume_down = 0
        price_down_volume_up = 0
        price_down_volume_down = 0
        
        for price_change, volume_change in zip(price_changes, volume_changes):
            if price_change > 0 and volume_change > 0:
                price_up_volume_up += 1
            elif price_change > 0 and volume_change <= 0:
                price_up_volume_down += 1
            elif price_change <= 0 and volume_change > 0:
                price_down_volume_up += 1
            else:
                price_down_volume_down += 1
        
        # 返回出现次数最多的模式
        patterns = [
            (price_up_volume_up, VolumePattern.PRICE_UP_VOLUME_UP),
            (price_up_volume_down, VolumePattern.PRICE_UP_VOLUME_DOWN),
            (price_down_volume_up, VolumePattern.PRICE_DOWN_VOLUME_UP),
            (price_down_volume_down, VolumePattern.PRICE_DOWN_VOLUME_DOWN)
        ]
        
        return max(patterns, key=lambda x: x[0])[1]
    
    def _detect_volume_divergence(self, data: pd.DataFrame, window: int = 20) -> bool:
        """检测量价背离"""
        if len(data) < window:
            return False
        
        recent_data = data.tail(window)
        
        # 计算价格和成交量的相关性
        price_trend = recent_data['close'].pct_change().fillna(0)
        volume_trend = recent_data['volume'].pct_change().fillna(0)
        
        # 计算相关系数
        correlation = price_trend.corr(volume_trend)
        
        # 检测顶部背离和底部背离
        top_divergence = self._detect_top_divergence(recent_data)
        bottom_divergence = self._detect_bottom_divergence(recent_data)
        
        # 如果相关性很低（小于0.3）或者检测到明显背离，则认为存在背离
        return correlation < 0.3 or top_divergence or bottom_divergence
    
    def _detect_top_divergence(self, data: pd.DataFrame) -> bool:
        """检测顶部背离：价格创新高，成交量萎缩"""
        if len(data) < 10:
            return False
        
        # 取最近的数据
        recent_data = data.tail(10)
        
        # 找出价格高点
        price_highs = []
        volume_at_highs = []
        
        for i in range(2, len(recent_data)-2):
            current_price = recent_data.iloc[i]['high']
            if (current_price > recent_data.iloc[i-1]['high'] and 
                current_price > recent_data.iloc[i-2]['high'] and
                current_price > recent_data.iloc[i+1]['high'] and
                current_price > recent_data.iloc[i+2]['high']):
                price_highs.append(current_price)
                volume_at_highs.append(recent_data.iloc[i]['volume'])
        
        # 如果有至少两个高点，检查背离
        if len(price_highs) >= 2:
            # 价格创新高，成交量减少
            return price_highs[-1] > price_highs[-2] and volume_at_highs[-1] < volume_at_highs[-2]
        
        return False
    
    def _detect_bottom_divergence(self, data: pd.DataFrame) -> bool:
        """检测底部背离：价格创新低，成交量萎缩"""
        if len(data) < 10:
            return False
        
        # 取最近的数据
        recent_data = data.tail(10)
        
        # 找出价格低点
        price_lows = []
        volume_at_lows = []
        
        for i in range(2, len(recent_data)-2):
            current_price = recent_data.iloc[i]['low']
            if (current_price < recent_data.iloc[i-1]['low'] and 
                current_price < recent_data.iloc[i-2]['low'] and
                current_price < recent_data.iloc[i+1]['low'] and
                current_price < recent_data.iloc[i+2]['low']):
                price_lows.append(current_price)
                volume_at_lows.append(recent_data.iloc[i]['volume'])
        
        # 如果有至少两个低点，检查背离
        if len(price_lows) >= 2:
            # 价格创新低，成交量减少
            return price_lows[-1] < price_lows[-2] and volume_at_lows[-1] < volume_at_lows[-2]
        
        return False
    
    def _evaluate_volume_strength(self, volume_ratio: float, pattern: VolumePattern, 
                                 divergence_signal: bool) -> SignalStrength:
        """评估成交量信号强度"""
        score = 0
        
        # 基于成交量放大倍数评分
        if volume_ratio > 2.0:
            score += 30
        elif volume_ratio > 1.5:
            score += 20
        elif volume_ratio > 1.2:
            score += 10
        elif volume_ratio < 0.5:
            score -= 10
        
        # 基于量价模式评分
        if pattern == VolumePattern.PRICE_UP_VOLUME_UP:
            score += 25  # 价涨量增，最健康
        elif pattern == VolumePattern.PRICE_DOWN_VOLUME_DOWN:
            score += 15  # 价跌量缩，下跌动能减弱
        elif pattern == VolumePattern.PRICE_UP_VOLUME_DOWN:
            score -= 10  # 价涨量缩，上涨动能不足
        elif pattern == VolumePattern.PRICE_DOWN_VOLUME_UP:
            score -= 20  # 价跌量增，下跌加速
        
        # 背离信号扣分
        if divergence_signal:
            score -= 25
        
        # 确定强度等级
        if score >= 40:
            return SignalStrength.STRONG
        elif score >= 20:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK
    
    def analyze_volume_confirmation(self, data: pd.DataFrame, price_breakout: float, 
                                   breakout_date: datetime, breakout_type: str) -> bool:
        """分析成交量对突破的确认"""
        if data.empty:
            return False
        
        # 获取突破日的数据
        breakout_data = data[data.index == breakout_date]
        if breakout_data.empty:
            return False
        
        breakout_volume = breakout_data.iloc[0]['volume']
        
        # 计算突破前20日平均成交量
        pre_breakout_data = data[data.index < breakout_date].tail(20)
        if pre_breakout_data.empty:
            return False
        
        avg_volume = pre_breakout_data['volume'].mean()
        
        # 成交量确认标准：突破日成交量至少是平均成交量的1.5倍
        volume_confirmation = breakout_volume > avg_volume * 1.5
        
        # 后续确认：突破后几日成交量保持相对活跃
        post_breakout_data = data[data.index > breakout_date].head(3)
        if not post_breakout_data.empty:
            post_avg_volume = post_breakout_data['volume'].mean()
            sustained_volume = post_avg_volume > avg_volume * 1.2
        else:
            sustained_volume = False
        
        return volume_confirmation and sustained_volume
    
    def calculate_volume_profile(self, data: pd.DataFrame, price_levels: List[float]) -> dict:
        """计算成交量分布"""
        if data.empty:
            return {}
        
        volume_profile = {}
        
        for level in price_levels:
            total_volume = 0
            touch_count = 0
            
            for _, row in data.iterrows():
                # 如果价格在该水平附近（2%误差范围内）
                if abs(row['close'] - level) / level <= 0.02:
                    total_volume += row['volume']
                    touch_count += 1
            
            volume_profile[level] = {
                'total_volume': total_volume,
                'touch_count': touch_count,
                'avg_volume': total_volume / touch_count if touch_count > 0 else 0
            }
        
        return volume_profile
    
    def analyze_volume_trend(self, data: pd.DataFrame, window: int = 20) -> dict:
        """分析成交量趋势"""
        if len(data) < window:
            return {'trend': 'insufficient_data', 'strength': 0}
        
        recent_data = data.tail(window)
        
        # 计算成交量的移动平均
        volume_ma_short = recent_data['volume'].tail(5).mean()
        volume_ma_long = recent_data['volume'].mean()
        
        # 计算成交量趋势
        volume_trend_ratio = volume_ma_short / volume_ma_long if volume_ma_long > 0 else 1.0
        
        # 计算趋势强度
        volume_changes = recent_data['volume'].pct_change().fillna(0)
        trend_strength = abs(volume_changes.mean()) * 100
        
        if volume_trend_ratio > 1.2:
            trend = 'increasing'
        elif volume_trend_ratio < 0.8:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'strength': trend_strength,
            'ratio': volume_trend_ratio
        }
    
    def detect_volume_anomalies(self, data: pd.DataFrame, threshold: float = 3.0) -> List[dict]:
        """检测成交量异常"""
        if len(data) < 20:
            return []
        
        anomalies = []
        
        # 计算成交量的z-score
        volume_mean = data['volume'].mean()
        volume_std = data['volume'].std()
        
        if volume_std == 0:
            return anomalies
        
        for idx, row in data.iterrows():
            z_score = (row['volume'] - volume_mean) / volume_std
            
            if abs(z_score) > threshold:
                anomaly_type = 'volume_spike' if z_score > 0 else 'volume_drop'
                anomalies.append({
                    'date': idx,
                    'type': anomaly_type,
                    'volume': row['volume'],
                    'z_score': z_score,
                    'price': row['close']
                })
        
        return anomalies
    
    def calculate_relative_volume(self, data: pd.DataFrame, comparison_period: int = 50) -> pd.Series:
        """计算相对成交量"""
        if len(data) < comparison_period:
            return pd.Series(index=data.index, data=1.0)
        
        # 计算滚动平均成交量
        rolling_avg = data['volume'].rolling(window=comparison_period, min_periods=1).mean()
        
        # 计算相对成交量
        relative_volume = data['volume'] / rolling_avg
        
        return relative_volume.fillna(1.0)