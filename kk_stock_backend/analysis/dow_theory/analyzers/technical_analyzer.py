#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标辅助分析器
实现道氏理论分析中常用的技术指标计算和分析
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
    TechnicalIndicators, SignalStrength
)


class TechnicalAnalyzer:
    """技术指标分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_indicators(self, data: pd.DataFrame) -> TechnicalIndicators:
        """
        计算技术指标
        
        Args:
            data: 价格数据
            
        Returns:
            技术指标数据
        """
        if data.empty:
            return self._create_default_indicators()
        
        current_price = data.iloc[-1]['close']
        
        # 计算移动平均线
        ma_20 = self._calculate_ma(data, 20)
        ma_60 = self._calculate_ma(data, 60)
        ma_250 = self._calculate_ma(data, 250)
        
        # 计算MACD
        macd_dif, macd_dea, macd_histogram = self._calculate_macd(data)
        
        # 计算RSI
        rsi = self._calculate_rsi(data)
        
        return TechnicalIndicators(
            ma_20=ma_20,
            ma_60=ma_60,
            ma_250=ma_250,
            macd_dif=macd_dif,
            macd_dea=macd_dea,
            macd_histogram=macd_histogram,
            rsi=rsi,
            current_price=current_price
        )
    
    def _create_default_indicators(self) -> TechnicalIndicators:
        """创建默认技术指标"""
        return TechnicalIndicators(
            ma_20=0.0,
            ma_60=0.0,
            ma_250=0.0,
            macd_dif=0.0,
            macd_dea=0.0,
            macd_histogram=0.0,
            rsi=50.0,
            current_price=0.0
        )
    
    def _calculate_ma(self, data: pd.DataFrame, period: int) -> float:
        """计算移动平均线"""
        if len(data) < period:
            return data['close'].mean() if not data.empty else 0.0
        
        return data['close'].tail(period).mean()
    
    def _calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """计算MACD指标"""
        if len(data) < slow:
            return 0.0, 0.0, 0.0
        
        close_prices = data['close']
        
        # 计算EMA
        ema_fast = close_prices.ewm(span=fast).mean()
        ema_slow = close_prices.ewm(span=slow).mean()
        
        # 计算DIF线
        dif = ema_fast - ema_slow
        
        # 计算DEA线（MACD信号线）
        dea = dif.ewm(span=signal).mean()
        
        # 计算MACD柱状线
        histogram = 2 * (dif - dea)
        
        return dif.iloc[-1], dea.iloc[-1], histogram.iloc[-1]
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> float:
        """计算RSI指标"""
        if len(data) < period + 1:
            return 50.0
        
        close_prices = data['close']
        delta = close_prices.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50.0
    
    def calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """计算布林带"""
        if len(data) < period:
            current_price = data['close'].iloc[-1] if not data.empty else 0.0
            return {
                'upper_band': current_price,
                'middle_band': current_price,
                'lower_band': current_price,
                'band_width': 0.0,
                'position': 0.5
            }
        
        close_prices = data['close'].tail(period)
        middle_band = close_prices.mean()
        std = close_prices.std()
        
        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)
        
        current_price = data['close'].iloc[-1]
        band_width = (upper_band - lower_band) / middle_band if middle_band > 0 else 0.0
        
        # 计算价格在布林带中的位置
        if upper_band > lower_band:
            position = (current_price - lower_band) / (upper_band - lower_band)
        else:
            position = 0.5
        
        return {
            'upper_band': upper_band,
            'middle_band': middle_band,
            'lower_band': lower_band,
            'band_width': band_width,
            'position': position
        }
    
    def calculate_kdj(self, data: pd.DataFrame, k_period: int = 9, d_period: int = 3, j_period: int = 3) -> Dict[str, float]:
        """计算KDJ指标"""
        if len(data) < k_period:
            return {'k': 50.0, 'd': 50.0, 'j': 50.0}
        
        high_prices = data['high']
        low_prices = data['low']
        close_prices = data['close']
        
        # 计算最近k_period周期的最高价和最低价
        lowest_low = low_prices.rolling(window=k_period).min()
        highest_high = high_prices.rolling(window=k_period).max()
        
        # 计算RSV
        rsv = (close_prices - lowest_low) / (highest_high - lowest_low) * 100
        rsv = rsv.fillna(50.0)
        
        # 计算K值
        k_values = []
        k = 50.0  # 初始值
        for rsv_val in rsv:
            k = (2/3) * k + (1/3) * rsv_val
            k_values.append(k)
        
        k_series = pd.Series(k_values, index=rsv.index)
        
        # 计算D值
        d_values = []
        d = 50.0  # 初始值
        for k_val in k_values:
            d = (2/3) * d + (1/3) * k_val
            d_values.append(d)
        
        # 计算J值
        j = 3 * k_values[-1] - 2 * d_values[-1]
        
        return {
            'k': k_values[-1],
            'd': d_values[-1],
            'j': j
        }
    
    def calculate_williams_r(self, data: pd.DataFrame, period: int = 14) -> float:
        """计算威廉指标"""
        if len(data) < period:
            return -50.0
        
        recent_data = data.tail(period)
        highest_high = recent_data['high'].max()
        lowest_low = recent_data['low'].min()
        current_close = data.iloc[-1]['close']
        
        if highest_high == lowest_low:
            return -50.0
        
        williams_r = (highest_high - current_close) / (highest_high - lowest_low) * -100
        
        return williams_r
    
    def calculate_cci(self, data: pd.DataFrame, period: int = 20) -> float:
        """计算顺势指标CCI"""
        if len(data) < period:
            return 0.0
        
        # 计算典型价格
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        
        # 计算移动平均
        sma = typical_price.rolling(window=period).mean()
        
        # 计算平均偏差
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        
        # 计算CCI
        cci = (typical_price - sma) / (0.015 * mad)
        
        return cci.iloc[-1] if not np.isnan(cci.iloc[-1]) else 0.0
    
    def analyze_ma_alignment(self, indicators: TechnicalIndicators) -> Dict[str, any]:
        """分析移动平均线排列"""
        current_price = indicators.current_price
        ma_20 = indicators.ma_20
        ma_60 = indicators.ma_60
        ma_250 = indicators.ma_250
        
        # 多头排列
        if current_price > ma_20 > ma_60 > ma_250:
            alignment = 'bullish'
            strength = SignalStrength.STRONG
        # 空头排列
        elif current_price < ma_20 < ma_60 < ma_250:
            alignment = 'bearish'
            strength = SignalStrength.STRONG
        # 部分多头
        elif current_price > ma_20 > ma_60:
            alignment = 'partial_bullish'
            strength = SignalStrength.MEDIUM
        # 部分空头
        elif current_price < ma_20 < ma_60:
            alignment = 'partial_bearish'
            strength = SignalStrength.MEDIUM
        else:
            alignment = 'mixed'
            strength = SignalStrength.WEAK
        
        return {
            'alignment': alignment,
            'strength': strength,
            'description': self._get_ma_description(alignment)
        }
    
    def _get_ma_description(self, alignment: str) -> str:
        """获取移动平均线排列描述"""
        descriptions = {
            'bullish': '完全多头排列，趋势强劲向上',
            'bearish': '完全空头排列，趋势强劲向下',
            'partial_bullish': '部分多头排列，上升趋势初现',
            'partial_bearish': '部分空头排列，下降趋势初现',
            'mixed': '均线混乱排列，趋势不明'
        }
        return descriptions.get(alignment, '未知排列')
    
    def analyze_macd_signals(self, data: pd.DataFrame) -> Dict[str, any]:
        """分析MACD信号"""
        if len(data) < 26:
            return {'signal': 'insufficient_data', 'strength': SignalStrength.WEAK}
        
        # 计算MACD历史数据
        close_prices = data['close']
        ema_12 = close_prices.ewm(span=12).mean()
        ema_26 = close_prices.ewm(span=26).mean()
        dif = ema_12 - ema_26
        dea = dif.ewm(span=9).mean()
        histogram = 2 * (dif - dea)
        
        current_dif = dif.iloc[-1]
        current_dea = dea.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        prev_dif = dif.iloc[-2] if len(dif) > 1 else current_dif
        prev_dea = dea.iloc[-2] if len(dea) > 1 else current_dea
        
        signals = []
        
        # 金叉信号
        if current_dif > current_dea and prev_dif <= prev_dea:
            signals.append('golden_cross')
        
        # 死叉信号
        if current_dif < current_dea and prev_dif >= prev_dea:
            signals.append('death_cross')
        
        # 零轴突破
        if current_dif > 0 and prev_dif <= 0:
            signals.append('zero_axis_breakthrough_up')
        elif current_dif < 0 and prev_dif >= 0:
            signals.append('zero_axis_breakthrough_down')
        
        # 背离分析
        price_trend = data['close'].tail(10).diff().sum()
        macd_trend = dif.tail(10).diff().sum()
        
        if price_trend > 0 and macd_trend < 0:
            signals.append('bearish_divergence')
        elif price_trend < 0 and macd_trend > 0:
            signals.append('bullish_divergence')
        
        # 评估信号强度
        strength = self._evaluate_macd_strength(current_dif, current_dea, current_histogram, signals)
        
        return {
            'signals': signals,
            'strength': strength,
            'dif': current_dif,
            'dea': current_dea,
            'histogram': current_histogram
        }
    
    def _evaluate_macd_strength(self, dif: float, dea: float, histogram: float, signals: List[str]) -> SignalStrength:
        """评估MACD信号强度"""
        score = 0
        
        # 基于信号类型评分
        for signal in signals:
            if signal in ['golden_cross', 'zero_axis_breakthrough_up']:
                score += 25
            elif signal in ['death_cross', 'zero_axis_breakthrough_down']:
                score += 20
            elif signal in ['bullish_divergence', 'bearish_divergence']:
                score += 30
        
        # 基于MACD数值评分
        if abs(dif - dea) > 0.5:  # DIF和DEA差距较大
            score += 15
        
        if abs(histogram) > 0.3:  # 柱状线较强
            score += 10
        
        if score >= 50:
            return SignalStrength.STRONG
        elif score >= 25:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK
    
    def analyze_rsi_signals(self, rsi: float) -> Dict[str, any]:
        """分析RSI信号"""
        if rsi >= 80:
            signal = 'overbought'
            strength = SignalStrength.STRONG
            description = '严重超买，注意风险'
        elif rsi >= 70:
            signal = 'mild_overbought'
            strength = SignalStrength.MEDIUM
            description = '轻微超买，谨慎操作'
        elif rsi <= 20:
            signal = 'oversold'
            strength = SignalStrength.STRONG
            description = '严重超卖，关注机会'
        elif rsi <= 30:
            signal = 'mild_oversold'
            strength = SignalStrength.MEDIUM
            description = '轻微超卖，可以关注'
        elif 40 <= rsi <= 60:
            signal = 'neutral'
            strength = SignalStrength.WEAK
            description = '处于中性区间'
        else:
            signal = 'normal'
            strength = SignalStrength.WEAK
            description = '正常波动区间'
        
        return {
            'signal': signal,
            'strength': strength,
            'description': description,
            'value': rsi
        }
    
    def comprehensive_technical_analysis(self, data: pd.DataFrame) -> Dict[str, any]:
        """综合技术分析"""
        if data.empty:
            return {'error': 'No data available'}
        
        # 计算基础指标
        indicators = self.calculate_indicators(data)
        
        # 各项分析
        ma_analysis = self.analyze_ma_alignment(indicators)
        macd_analysis = self.analyze_macd_signals(data)
        rsi_analysis = self.analyze_rsi_signals(indicators.rsi)
        bollinger_analysis = self.calculate_bollinger_bands(data)
        kdj_analysis = self.calculate_kdj(data)
        
        # 综合评分
        total_score = 0
        max_score = 0
        
        # 移动平均线评分
        if ma_analysis['strength'] == SignalStrength.STRONG:
            total_score += 30
        elif ma_analysis['strength'] == SignalStrength.MEDIUM:
            total_score += 15
        max_score += 30
        
        # MACD评分
        if macd_analysis['strength'] == SignalStrength.STRONG:
            total_score += 25
        elif macd_analysis['strength'] == SignalStrength.MEDIUM:
            total_score += 12
        max_score += 25
        
        # RSI评分
        if rsi_analysis['strength'] == SignalStrength.STRONG:
            total_score += 20
        elif rsi_analysis['strength'] == SignalStrength.MEDIUM:
            total_score += 10
        max_score += 20
        
        # 布林带位置评分
        bb_position = bollinger_analysis['position']
        if bb_position > 0.8 or bb_position < 0.2:
            total_score += 15  # 极端位置
        max_score += 15
        
        # KDJ评分
        k_val = kdj_analysis['k']
        if k_val > 80 or k_val < 20:
            total_score += 10  # 极端位置
        max_score += 10
        
        # 计算综合评分
        comprehensive_score = (total_score / max_score * 100) if max_score > 0 else 50
        
        return {
            'indicators': indicators,
            'ma_analysis': ma_analysis,
            'macd_analysis': macd_analysis,
            'rsi_analysis': rsi_analysis,
            'bollinger_bands': bollinger_analysis,
            'kdj': kdj_analysis,
            'comprehensive_score': comprehensive_score,
            'recommendation': self._generate_technical_recommendation(comprehensive_score, ma_analysis, macd_analysis, rsi_analysis)
        }
    
    def _generate_technical_recommendation(self, score: float, ma_analysis: Dict, 
                                         macd_analysis: Dict, rsi_analysis: Dict) -> str:
        """生成技术分析建议"""
        if score >= 80:
            return 'strong_buy'
        elif score >= 65:
            return 'buy'
        elif score >= 55:
            return 'weak_buy'
        elif score >= 45:
            return 'hold'
        elif score >= 35:
            return 'weak_sell'
        elif score >= 20:
            return 'sell'
        else:
            return 'strong_sell'