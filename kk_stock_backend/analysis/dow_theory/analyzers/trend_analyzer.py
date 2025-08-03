#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势分析器
实现道氏理论中的趋势识别、趋势线绘制、支撑阻力位识别等功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from scipy import stats
from scipy.signal import argrelextrema
import logging

import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from analysis.dow_theory.models.dow_theory_models import (
    TrendDirection, TrendType, TrendLine, SupportResistance, BreakthroughSignal,
    SignalStrength, VolumeAnalysis
)


class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_trend(self, data: pd.DataFrame, trend_type: TrendType) -> Tuple[TrendDirection, Optional[TrendLine]]:
        """
        分析趋势方向并绘制趋势线
        
        Args:
            data: 价格数据
            trend_type: 趋势类型（主要、次要、短期）
            
        Returns:
            (趋势方向, 趋势线)
        """
        if data.empty:
            return TrendDirection.SIDEWAYS, None
        
        # 计算趋势线
        trend_line = self._calculate_trend_line(data, trend_type)
        
        # 确定趋势方向
        if trend_line and trend_line.is_valid:
            if trend_line.slope > 0:
                trend_direction = TrendDirection.UPWARD
            elif trend_line.slope < 0:
                trend_direction = TrendDirection.DOWNWARD
            else:
                trend_direction = TrendDirection.SIDEWAYS
        else:
            # 使用移动平均线判断趋势
            trend_direction = self._analyze_trend_by_ma(data)
        
        return trend_direction, trend_line
    
    def _calculate_trend_line(self, data: pd.DataFrame, trend_type: TrendType) -> Optional[TrendLine]:
        """计算趋势线"""
        try:
            # 根据趋势类型确定分析窗口
            if trend_type == TrendType.PRIMARY:
                window = min(len(data), 250)  # 月线用250个交易日
            elif trend_type == TrendType.SECONDARY:
                window = min(len(data), 60)   # 周线用60个交易日
            else:
                window = min(len(data), 20)   # 日线用20个交易日
            
            recent_data = data.tail(window).copy()
            if len(recent_data) < 10:
                return None
            
            # 找出关键点（局部极值）
            highs, lows = self._find_pivots(recent_data)
            
            # 尝试拟合上升趋势线（连接低点）
            upward_trend = self._fit_trend_line(recent_data, lows, 'upward')
            
            # 尝试拟合下降趋势线（连接高点）
            downward_trend = self._fit_trend_line(recent_data, highs, 'downward')
            
            # 选择最佳趋势线
            best_trend = self._select_best_trend_line(upward_trend, downward_trend)
            
            if best_trend:
                best_trend.trend_type = trend_type
            
            return best_trend
            
        except Exception as e:
            self.logger.error(f"计算趋势线时发生错误: {e}")
            return None
    
    def _find_pivots(self, data: pd.DataFrame, window: int = 5) -> Tuple[List[int], List[int]]:
        """找出价格的关键转折点"""
        high_prices = data['high'].values
        low_prices = data['low'].values
        
        # 找出局部最高点
        high_indices = argrelextrema(high_prices, np.greater, order=window)[0]
        
        # 找出局部最低点
        low_indices = argrelextrema(low_prices, np.less, order=window)[0]
        
        return high_indices.tolist(), low_indices.tolist()
    
    def _fit_trend_line(self, data: pd.DataFrame, pivot_indices: List[int], direction: str) -> Optional[TrendLine]:
        """拟合趋势线"""
        if len(pivot_indices) < 2:
            return None
        
        best_line = None
        best_score = 0
        
        # 尝试不同的点组合
        for i in range(len(pivot_indices)-1):
            for j in range(i+1, len(pivot_indices)):
                start_idx = pivot_indices[i]
                end_idx = pivot_indices[j]
                
                if direction == 'upward':
                    start_price = data.iloc[start_idx]['low']
                    end_price = data.iloc[end_idx]['low']
                else:
                    start_price = data.iloc[start_idx]['high']
                    end_price = data.iloc[end_idx]['high']
                
                # 计算斜率
                days_diff = end_idx - start_idx
                if days_diff == 0:
                    continue
                    
                slope = (end_price - start_price) / days_diff
                
                # 计算拟合度和触及次数
                r_squared, touch_count = self._calculate_line_quality(
                    data, start_idx, end_idx, start_price, slope, direction
                )
                
                # 评分：拟合度 + 触及次数
                score = r_squared * 100 + touch_count * 10
                
                if score > best_score and r_squared > 0.5:  # 最低拟合度要求
                    best_score = score
                    start_date = data.index[start_idx]
                    end_date = data.index[end_idx]
                    
                    trend_direction = TrendDirection.UPWARD if slope > 0 else TrendDirection.DOWNWARD
                    if abs(slope) < 0.01:  # 斜率很小视为横盘
                        trend_direction = TrendDirection.SIDEWAYS
                    
                    best_line = TrendLine(
                        start_point=(start_date, start_price),
                        end_point=(end_date, end_price),
                        slope=slope,
                        r_squared=r_squared,
                        touch_count=touch_count,
                        is_valid=r_squared > 0.6 and touch_count >= 2,
                        trend_type=TrendType.MINOR,  # 临时值，会在外部设置
                        direction=trend_direction
                    )
        
        return best_line
    
    def _calculate_line_quality(self, data: pd.DataFrame, start_idx: int, end_idx: int, 
                               start_price: float, slope: float, direction: str) -> Tuple[float, int]:
        """计算趋势线质量"""
        touch_count = 0
        errors = []
        
        for i in range(start_idx, min(end_idx + 20, len(data))):  # 延伸检验
            expected_price = start_price + slope * (i - start_idx)
            
            if direction == 'upward':
                actual_price = data.iloc[i]['low']
                error = abs(actual_price - expected_price) / expected_price
                
                # 检查是否触及趋势线（允许2%误差）
                if error < 0.02:
                    touch_count += 1
            else:
                actual_price = data.iloc[i]['high']
                error = abs(actual_price - expected_price) / expected_price
                
                if error < 0.02:
                    touch_count += 1
            
            errors.append(error)
        
        # 计算R²
        if len(errors) > 1:
            mean_error = np.mean(errors)
            ss_res = sum((error - mean_error) ** 2 for error in errors)
            ss_tot = sum((error - mean_error) ** 2 for error in errors)
            if ss_tot > 0:
                r_squared = 1 - (ss_res / ss_tot)
            else:
                r_squared = 0
        else:
            r_squared = 0
        
        return max(0, r_squared), touch_count
    
    def _select_best_trend_line(self, upward_trend: Optional[TrendLine], 
                               downward_trend: Optional[TrendLine]) -> Optional[TrendLine]:
        """选择最佳趋势线"""
        if not upward_trend and not downward_trend:
            return None
        elif not upward_trend:
            return downward_trend
        elif not downward_trend:
            return upward_trend
        else:
            # 选择拟合度和触及次数更好的
            upward_score = upward_trend.r_squared * 100 + upward_trend.touch_count * 10
            downward_score = downward_trend.r_squared * 100 + downward_trend.touch_count * 10
            
            return upward_trend if upward_score > downward_score else downward_trend
    
    def _analyze_trend_by_ma(self, data: pd.DataFrame) -> TrendDirection:
        """使用移动平均线分析趋势"""
        if len(data) < 20:
            return TrendDirection.SIDEWAYS
        
        # 计算不同周期移动平均线
        data = data.copy()
        data['ma_5'] = data['close'].rolling(5).mean()
        data['ma_20'] = data['close'].rolling(20).mean()
        data['ma_60'] = data['close'].rolling(60).mean() if len(data) >= 60 else data['close'].rolling(len(data)//3).mean()
        
        current_price = data.iloc[-1]['close']
        ma_5 = data.iloc[-1]['ma_5']
        ma_20 = data.iloc[-1]['ma_20']
        ma_60 = data.iloc[-1]['ma_60']
        
        # 多头排列
        if current_price > ma_5 > ma_20 > ma_60:
            return TrendDirection.UPWARD
        # 空头排列
        elif current_price < ma_5 < ma_20 < ma_60:
            return TrendDirection.DOWNWARD
        else:
            return TrendDirection.SIDEWAYS
    
    def identify_support_resistance(self, data: pd.DataFrame, trend_type: TrendType) -> List[SupportResistance]:
        """识别支撑阻力位"""
        support_resistance = []
        
        if data.empty:
            return support_resistance
        
        # 根据趋势类型确定分析窗口
        if trend_type == TrendType.PRIMARY:
            window = min(len(data), 250)
            min_touches = 3
        elif trend_type == TrendType.SECONDARY:
            window = min(len(data), 60)
            min_touches = 2
        else:
            window = min(len(data), 20)
            min_touches = 2
        
        recent_data = data.tail(window).copy()
        current_price = recent_data.iloc[-1]['close']
        
        # 找出关键价格位
        key_levels = self._find_key_levels(recent_data)
        
        for level in key_levels:
            # 计算触及次数和强度
            touch_count, last_touch_date = self._calculate_touch_info(recent_data, level)
            
            if touch_count >= min_touches:
                # 确定是支撑还是阻力
                level_type = 'support' if level < current_price else 'resistance'
                
                # 评估强度
                strength = self._evaluate_level_strength(touch_count, recent_data, level)
                
                support_resistance.append(SupportResistance(
                    level=level,
                    strength=strength,
                    touch_count=touch_count,
                    last_touch_date=last_touch_date,
                    trend_type=trend_type,
                    level_type=level_type
                ))
        
        # 按强度排序
        support_resistance.sort(key=lambda x: (x.strength.value, x.touch_count), reverse=True)
        
        return support_resistance[:5]  # 返回最重要的5个位置
    
    def _find_key_levels(self, data: pd.DataFrame) -> List[float]:
        """找出关键价格位"""
        key_levels = []
        
        # 历史重要高低点
        highs = data['high'].values
        lows = data['low'].values
        
        # 找出显著的高点和低点
        high_peaks = argrelextrema(highs, np.greater, order=5)[0]
        low_peaks = argrelextrema(lows, np.less, order=5)[0]
        
        # 添加重要高点
        for idx in high_peaks:
            key_levels.append(data.iloc[idx]['high'])
        
        # 添加重要低点
        for idx in low_peaks:
            key_levels.append(data.iloc[idx]['low'])
        
        # 添加整数关口（心理价位）
        price_range = [data['low'].min(), data['high'].max()]
        for price in range(int(price_range[0]), int(price_range[1]) + 1):
            if price % 5 == 0 or price % 10 == 0:  # 5元或10元的整数倍
                key_levels.append(float(price))
        
        # 去重并排序
        key_levels = sorted(list(set(key_levels)))
        
        return key_levels
    
    def _calculate_touch_info(self, data: pd.DataFrame, level: float, tolerance: float = 0.02) -> Tuple[int, datetime]:
        """计算价格位的触及信息"""
        touch_count = 0
        last_touch_date = None
        
        for idx, row in data.iterrows():
            # 检查是否触及该价格位（允许2%误差）
            if (abs(row['high'] - level) / level < tolerance or 
                abs(row['low'] - level) / level < tolerance or
                abs(row['close'] - level) / level < tolerance):
                touch_count += 1
                last_touch_date = idx
        
        return touch_count, last_touch_date or data.index[-1]
    
    def _evaluate_level_strength(self, touch_count: int, data: pd.DataFrame, level: float) -> SignalStrength:
        """评估支撑阻力位强度"""
        # 基础评分
        score = touch_count * 10
        
        # 时间跨度加分
        touches_dates = []
        for idx, row in data.iterrows():
            if (abs(row['high'] - level) / level < 0.02 or 
                abs(row['low'] - level) / level < 0.02):
                touches_dates.append(idx)
        
        if len(touches_dates) >= 2:
            time_span = (touches_dates[-1] - touches_dates[0]).days
            score += min(time_span / 10, 20)  # 时间跨度加分，最多20分
        
        # 成交量确认加分
        high_volume_touches = 0
        avg_volume = data['volume'].mean()
        
        for idx, row in data.iterrows():
            if (abs(row['high'] - level) / level < 0.02 or 
                abs(row['low'] - level) / level < 0.02):
                if row['volume'] > avg_volume * 1.5:
                    high_volume_touches += 1
        
        score += high_volume_touches * 5
        
        # 确定强度等级
        if score >= 50:
            return SignalStrength.STRONG
        elif score >= 30:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK
    
    def detect_breakthrough_signals(self, data: pd.DataFrame, 
                                   support_resistance: List[SupportResistance],
                                   volume_analysis: VolumeAnalysis) -> List[BreakthroughSignal]:
        """检测突破信号"""
        breakthrough_signals = []
        
        if data.empty or len(data) < 5:
            return breakthrough_signals
        
        current_price = data.iloc[-1]['close']
        recent_data = data.tail(5)  # 最近5个交易日
        
        for sr in support_resistance:
            # 检查是否有突破
            breakthrough_type = None
            breakthrough_date = None
            breakthrough_price = None
            
            # 检查向上突破阻力位
            if sr.level_type == 'resistance' and current_price > sr.level:
                for idx, row in recent_data.iterrows():
                    if row['close'] > sr.level and breakthrough_date is None:
                        breakthrough_type = 'upward'
                        breakthrough_date = idx
                        breakthrough_price = row['close']
                        break
            
            # 检查向下突破支撑位
            elif sr.level_type == 'support' and current_price < sr.level:
                for idx, row in recent_data.iterrows():
                    if row['close'] < sr.level and breakthrough_date is None:
                        breakthrough_type = 'downward'
                        breakthrough_date = idx
                        breakthrough_price = row['close']
                        break
            
            if breakthrough_type:
                # 验证突破的有效性
                price_confirmation = self._verify_price_breakthrough(
                    data, breakthrough_price, sr.level, breakthrough_type
                )
                
                volume_confirmation = volume_analysis.volume_ratio > 1.5
                
                time_confirmation = self._verify_time_confirmation(
                    recent_data, breakthrough_date, breakthrough_type
                )
                
                # 评估突破强度
                strength = self._evaluate_breakthrough_strength(
                    price_confirmation, volume_confirmation, time_confirmation, sr.strength
                )
                
                breakthrough_signals.append(BreakthroughSignal(
                    breakout_price=breakthrough_price,
                    breakout_date=breakthrough_date,
                    volume_confirmation=volume_confirmation,
                    price_confirmation=price_confirmation,
                    time_confirmation=time_confirmation,
                    breakthrough_type=breakthrough_type,
                    trend_type=sr.trend_type,
                    strength=strength
                ))
        
        return breakthrough_signals
    
    def _verify_price_breakthrough(self, data: pd.DataFrame, breakthrough_price: float, 
                                  level: float, breakthrough_type: str) -> bool:
        """验证价格突破幅度"""
        if breakthrough_type == 'upward':
            breakthrough_ratio = (breakthrough_price - level) / level
            return breakthrough_ratio >= 0.01  # 至少1%的突破幅度
        else:
            breakthrough_ratio = (level - breakthrough_price) / level
            return breakthrough_ratio >= 0.01
    
    def _verify_time_confirmation(self, data: pd.DataFrame, breakthrough_date: datetime, 
                                 breakthrough_type: str) -> bool:
        """验证时间确认"""
        # 检查突破后是否能维持
        post_breakthrough = data[data.index > breakthrough_date]
        
        if len(post_breakthrough) < 2:
            return False
        
        # 简单检查：突破后至少2个交易日保持在突破位之上/之下
        if breakthrough_type == 'upward':
            return all(row['close'] > row['open'] for _, row in post_breakthrough.head(2).iterrows())
        else:
            return all(row['close'] < row['open'] for _, row in post_breakthrough.head(2).iterrows())
    
    def _evaluate_breakthrough_strength(self, price_conf: bool, volume_conf: bool, 
                                       time_conf: bool, level_strength: SignalStrength) -> SignalStrength:
        """评估突破强度"""
        confirmations = sum([price_conf, volume_conf, time_conf])
        
        if confirmations >= 3 and level_strength == SignalStrength.STRONG:
            return SignalStrength.STRONG
        elif confirmations >= 2:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK