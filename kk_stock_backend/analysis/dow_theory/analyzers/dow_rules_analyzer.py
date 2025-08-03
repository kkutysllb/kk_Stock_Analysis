#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道氏理论123法则和2B法则分析器
实现道氏理论中的经典交易法则
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import logging

# 添加项目根目录到路径
import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from analysis.dow_theory.models.dow_theory_models import (
    DowRuleType, RuleSignalType, SignalStrength, TrendDirection,
    Rule123Signal, Rule2BSignal, DowRulesAnalysis
)
from analysis.dow_theory.utils.data_fetcher import DataFetcher
from typing import Union
from enum import Enum

# 定义趋势类型枚举
class TrendType(Enum):
    MAJOR = "MAJOR"
    INTERMEDIATE = "INTERMEDIATE" 
    MINOR = "MINOR"


class DowRulesAnalyzer:
    """道氏理论123法则和2B法则分析器"""
    
    def __init__(self, data_fetcher: Optional[DataFetcher] = None):
        self.logger = logging.getLogger(__name__)
        self.data_fetcher = data_fetcher or DataFetcher()
    
    def _safe_array_compare(self, array_or_series, operator_func):
        """
        安全的数组比较方法，防止 'The truth value of an empty array is ambiguous' 错误
        
        Args:
            array_or_series: pandas Series 或 numpy array
            operator_func: 比较函数，返回布尔数组
            
        Returns:
            bool: 比较结果
        """
        try:
            if hasattr(array_or_series, '__len__') and len(array_or_series) == 0:
                return False
            
            comparison_result = operator_func(array_or_series)
            
            if hasattr(comparison_result, 'any'):
                return len(comparison_result) > 0 and comparison_result.any()
            elif hasattr(comparison_result, '__len__'):
                return len(comparison_result) > 0 and any(comparison_result)
            else:
                return bool(comparison_result)
                
        except Exception as e:
            self.logger.warning(f"数组比较失败: {e}")
            return False
        
    def analyze_with_factors(self, ts_code: str, start_date: str, end_date: str, 
                           trend_type: str = 'MINOR') -> Dict[str, Any]:
        """
        基于技术因子数据进行道氏理论分析
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期（字符串格式）
            end_date: 结束日期（字符串格式）
            trend_type: 趋势类型
            
        Returns:
            综合分析结果
        """
        try:
            # 转换字符串日期为datetime对象
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # 获取价格数据和技术因子数据
            price_data = self.data_fetcher.get_daily_data(ts_code, start_date, end_date)
            factor_data = self.data_fetcher.get_factor_data(ts_code, start_date, end_date)
            
            if price_data.empty or factor_data.empty:
                return self._empty_comprehensive_result()
            
            # 合并数据
            combined_data = self._merge_price_and_factors(price_data, factor_data)
            
            # 基于MACD等技术因子增强趋势识别
            enhanced_trend = self._identify_enhanced_trend(combined_data)
            
            # 执行123法则分析
            rule_123_result = self.analyze_123_rule_enhanced(combined_data, enhanced_trend)
            
            # 执行2B法则分析
            rule_2b_result = self.analyze_2b_rule_enhanced(combined_data, enhanced_trend)
            
            # MACD信号分析
            macd_signals = self._analyze_macd_signals(combined_data)
            
            # 综合评分
            comprehensive_score = self._calculate_comprehensive_score(
                rule_123_result, rule_2b_result, macd_signals, enhanced_trend
            )
            
            return {
                'ts_code': ts_code,
                'analysis_period': {'start': start_date, 'end': end_date},
                'enhanced_trend': enhanced_trend,
                'rule_123_analysis': rule_123_result,
                'rule_2b_analysis': rule_2b_result,
                'macd_signals': macd_signals,
                'comprehensive_score': comprehensive_score,
                'final_recommendation': self._generate_final_recommendation(
                    comprehensive_score, rule_123_result, rule_2b_result, macd_signals, enhanced_trend
                ),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"技术因子分析失败: {e}")
            return self._empty_comprehensive_result()
    
    def analyze_123_rule(self, data: pd.DataFrame, trend_type: str = 'MINOR') -> Dict[str, Any]:
        """
        分析123法则信号
        
        123法则判断趋势反转的三个条件：
        1. 趋势线被突破
        2. 上升趋势不再创新高，或下降趋势不再创新低
        3. 在上升趋势中，价格向下穿越先前的短期回档低点；
           或在下降趋势中，价格向上穿越先前的短期反弹高点
        
        Args:
            data: 价格数据
            trend_type: 趋势类型
            
        Returns:
            123法则分析结果
        """
        if len(data) < 20:
            return self._empty_123_result()
        
        try:
            # 识别当前趋势
            current_trend = self._identify_current_trend(data)
            
            # 检查123法则的三个条件
            condition1 = self._check_trendline_break(data, current_trend)
            condition2 = self._check_no_new_extreme(data, current_trend)
            condition3 = self._check_retracement_break(data, current_trend)
            
            # 计算信号强度
            signal_strength = self._calculate_123_signal_strength(condition1, condition2, condition3)
            
            # 生成交易信号
            trading_signal = self._generate_123_trading_signal(
                current_trend, condition1, condition2, condition3, signal_strength
            )
            
            return {
                'rule_type': '123法则',
                'current_trend': current_trend,
                'condition1_trendline_break': condition1,
                'condition2_no_new_extreme': condition2,
                'condition3_retracement_break': condition3,
                'signal_strength': signal_strength,
                'trading_signal': trading_signal,
                'reversal_probability': self._calculate_reversal_probability(condition1, condition2, condition3),
                'analysis_date': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"123法则分析失败: {e}")
            return self._empty_123_result()
    
    def analyze_2b_rule(self, data: pd.DataFrame, trend_type: str = 'MINOR') -> Dict[str, Any]:
        """
        分析2B法则信号
        
        2B法则识别假突破：
        - 在上升趋势中：价格突破前期高点但未能持续，随后跌破该高点
        - 在下降趋势中：价格跌破前期低点但未能持续，随后升破该低点
        
        Args:
            data: 价格数据
            trend_type: 趋势类型
            
        Returns:
            2B法则分析结果
        """
        if len(data) < 20:
            return self._empty_2b_result()
        
        try:
            # 识别当前趋势
            current_trend = self._identify_current_trend(data)
            
            # 检测假突破模式
            false_breakout = self._detect_false_breakout(data, current_trend)
            
            # 验证2B法则条件
            conditions_met = self._validate_2b_conditions(data, false_breakout, current_trend)
            
            # 计算信号强度
            signal_strength = self._calculate_2b_signal_strength(false_breakout, conditions_met)
            
            # 生成交易信号
            trading_signal = self._generate_2b_trading_signal(
                current_trend, false_breakout, conditions_met, signal_strength
            )
            
            return {
                'rule_type': '2B法则',
                'current_trend': current_trend,
                'false_breakout': false_breakout,
                'conditions_met': conditions_met,
                'signal_strength': signal_strength,
                'trading_signal': trading_signal,
                'reversal_probability': self._calculate_2b_reversal_probability(false_breakout, conditions_met),
                'analysis_date': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"2B法则分析失败: {e}")
            return self._empty_2b_result()
    
    def analyze_123_rule_enhanced(self, data: pd.DataFrame, enhanced_trend: Dict) -> Dict[str, Any]:
        """
        基于技术因子的增强版123法则分析
        """
        try:
            base_result = self.analyze_123_rule(data)
            
            # 结合技术因子增强分析
            trend_confirmation = enhanced_trend.get('macd_confirmation', {})
            ma_analysis = enhanced_trend.get('ma_analysis', {})
            
            # 调整信号强度
            enhanced_strength = base_result.get('signal_strength', SignalStrength.WEAK)
            if trend_confirmation.get('confirmed', False):
                if enhanced_strength == SignalStrength.WEAK:
                    enhanced_strength = SignalStrength.MEDIUM
                elif enhanced_strength == SignalStrength.MEDIUM:
                    enhanced_strength = SignalStrength.STRONG
            
            base_result['enhanced_signal_strength'] = enhanced_strength
            base_result['trend_confirmation'] = trend_confirmation
            base_result['ma_analysis'] = ma_analysis
            
            return base_result
            
        except Exception as e:
            self.logger.error(f"增强版123法则分析失败: {e}")
            return self._empty_123_result()
    
    def analyze_2b_rule_enhanced(self, data: pd.DataFrame, enhanced_trend: Dict) -> Dict[str, Any]:
        """
        基于技术因子的增强版2B法则分析
        """
        try:
            base_result = self.analyze_2b_rule(data)
            
            # 结合技术因子增强分析
            trend_confirmation = enhanced_trend.get('macd_confirmation', {})
            rsi_analysis = enhanced_trend.get('rsi_analysis', {})
            
            # 调整信号强度
            enhanced_strength = base_result.get('signal_strength', SignalStrength.WEAK)
            if trend_confirmation.get('reversal_signal', False):
                if enhanced_strength == SignalStrength.WEAK:
                    enhanced_strength = SignalStrength.MEDIUM
                elif enhanced_strength == SignalStrength.MEDIUM:
                    enhanced_strength = SignalStrength.STRONG
            
            base_result['enhanced_signal_strength'] = enhanced_strength
            base_result['trend_confirmation'] = trend_confirmation
            base_result['rsi_analysis'] = rsi_analysis
            
            return base_result
            
        except Exception as e:
            self.logger.error(f"增强版2B法则分析失败: {e}")
            return self._empty_2b_result()
    
    def _empty_comprehensive_result(self) -> Dict[str, Any]:
        """
        返回空的综合分析结果
        """
        return {
            'ts_code': '',
            'analysis_period': {'start': '', 'end': ''},
            'enhanced_trend': {},
            'rule_123_analysis': self._empty_123_result(),
            'rule_2b_analysis': self._empty_2b_result(),
            'macd_signals': {},
            'comprehensive_score': {'total_score': 0, 'signal_components': []},
            'final_recommendation': {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'reasons': ['数据不足'],
                'risk_factors': ['分析失败']
            },
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _detect_macd_crossovers(self, dif_values: pd.Series, dea_values: pd.Series) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        检测MACD金叉死叉信号
        """
        try:
            if len(dif_values) < 3 or len(dea_values) < 3:
                return None, None
            
            # 对齐数据
            common_index = dif_values.index.intersection(dea_values.index)
            if len(common_index) < 3:
                return None, None
            
            dif_aligned = dif_values.loc[common_index]
            dea_aligned = dea_values.loc[common_index]
            
            golden_cross = None
            death_cross = None
            
            # 检查最近的交叉
            for i in range(len(common_index) - 1, max(0, len(common_index) - 10), -1):
                if i == 0:
                    continue
                    
                prev_dif = dif_aligned.iloc[i-1]
                curr_dif = dif_aligned.iloc[i]
                prev_dea = dea_aligned.iloc[i-1]
                curr_dea = dea_aligned.iloc[i]
                
                # 金叉：DIF从下方穿越DEA
                if prev_dif <= prev_dea and curr_dif > curr_dea and not golden_cross:
                    golden_cross = {
                        'date': common_index[i],
                        'dif_value': curr_dif,
                        'dea_value': curr_dea,
                        'days_ago': len(common_index) - 1 - i,
                        'strength': abs(curr_dif - curr_dea) / max(abs(curr_dea), 0.001)
                    }
                
                # 死叉：DIF从上方穿越DEA
                if prev_dif >= prev_dea and curr_dif < curr_dea and not death_cross:
                    death_cross = {
                        'date': common_index[i],
                        'dif_value': curr_dif,
                        'dea_value': curr_dea,
                        'days_ago': len(common_index) - 1 - i,
                        'strength': abs(curr_dif - curr_dea) / max(abs(curr_dea), 0.001)
                    }
                
                # 如果都找到了，就停止搜索
                if golden_cross and death_cross:
                    break
            
            return golden_cross, death_cross
            
        except Exception as e:
            self.logger.error(f"MACD交叉检测失败: {e}")
            return None, None
    
    def _analyze_macd_histogram(self, macd_values: pd.Series) -> Dict[str, Any]:
        """
        分析MACD柱状图趋势
        """
        try:
            if len(macd_values) < 5:
                return {'trend': 'insufficient_data', 'strength': 0}
            
            recent_values = macd_values.tail(5)
            
            # 计算趋势
            trend_slope = recent_values.diff().mean()
            
            # 当前值
            current_value = recent_values.iloc[-1]
            
            # 判断趋势
            if trend_slope > 0.001:
                trend = 'rising'
                strength = min(1.0, abs(trend_slope) * 1000)
            elif trend_slope < -0.001:
                trend = 'falling'
                strength = min(1.0, abs(trend_slope) * 1000)
            else:
                trend = 'flat'
                strength = 0.3
            
            # 零轴位置
            above_zero = current_value > 0
            
            return {
                'trend': trend,
                'strength': strength,
                'current_value': current_value,
                'above_zero': above_zero,
                'trend_slope': trend_slope
            }
            
        except Exception as e:
            self.logger.error(f"MACD柱状图分析失败: {e}")
            return {'trend': 'error', 'strength': 0}
    
    def _detect_macd_divergence(self, data: pd.DataFrame, dif_values: pd.Series) -> Dict[str, Any]:
        """
        检测MACD背离信号
        """
        try:
            if len(dif_values) < 20 or 'close' not in data.columns:
                return {'bullish_divergence': False, 'bearish_divergence': False}
            
            # 获取价格数据
            price_data = data['close'].dropna()
            
            # 对齐数据
            common_index = dif_values.index.intersection(price_data.index)
            if len(common_index) < 20:
                return {'bullish_divergence': False, 'bearish_divergence': False}
            
            dif_aligned = dif_values.loc[common_index].tail(20)
            price_aligned = price_data.loc[common_index].tail(20)
            
            # 寻找价格和DIF的高点、低点
            price_highs = []
            price_lows = []
            dif_highs = []
            dif_lows = []
            
            # 简化的峰谷检测
            for i in range(2, len(dif_aligned) - 2):
                # 高点检测
                if (price_aligned.iloc[i] > price_aligned.iloc[i-1] and 
                    price_aligned.iloc[i] > price_aligned.iloc[i+1] and
                    price_aligned.iloc[i] > price_aligned.iloc[i-2] and 
                    price_aligned.iloc[i] > price_aligned.iloc[i+2]):
                    price_highs.append((i, price_aligned.iloc[i]))
                    dif_highs.append((i, dif_aligned.iloc[i]))
                
                # 低点检测
                if (price_aligned.iloc[i] < price_aligned.iloc[i-1] and 
                    price_aligned.iloc[i] < price_aligned.iloc[i+1] and
                    price_aligned.iloc[i] < price_aligned.iloc[i-2] and 
                    price_aligned.iloc[i] < price_aligned.iloc[i+2]):
                    price_lows.append((i, price_aligned.iloc[i]))
                    dif_lows.append((i, dif_aligned.iloc[i]))
            
            bullish_divergence = False
            bearish_divergence = False
            
            # 检测看涨背离（价格创新低，DIF不创新低）
            if len(price_lows) >= 2 and len(dif_lows) >= 2:
                recent_price_low = price_lows[-1][1]
                prev_price_low = price_lows[-2][1]
                recent_dif_low = dif_lows[-1][1]
                prev_dif_low = dif_lows[-2][1]
                
                if recent_price_low < prev_price_low and recent_dif_low > prev_dif_low:
                    bullish_divergence = True
            
            # 检测看跌背离（价格创新高，DIF不创新高）
            if len(price_highs) >= 2 and len(dif_highs) >= 2:
                recent_price_high = price_highs[-1][1]
                prev_price_high = price_highs[-2][1]
                recent_dif_high = dif_highs[-1][1]
                prev_dif_high = dif_highs[-2][1]
                
                if recent_price_high > prev_price_high and recent_dif_high < prev_dif_high:
                    bearish_divergence = True
            
            return {
                'bullish_divergence': bullish_divergence,
                'bearish_divergence': bearish_divergence,
                'price_highs_count': len(price_highs),
                'price_lows_count': len(price_lows)
            }
            
        except Exception as e:
            self.logger.error(f"MACD背离检测失败: {e}")
            return {'bullish_divergence': False, 'bearish_divergence': False}
    
    def _calculate_macd_signal_strength(self, golden_cross: Optional[Dict], death_cross: Optional[Dict],
                                      histogram_trend: Dict, divergence_signals: Dict) -> SignalStrength:
        """
        计算MACD信号强度
        """
        score = 0
        
        # 金叉死叉评分
        if golden_cross and golden_cross['days_ago'] <= 5:
            score += 30 + min(20, golden_cross['strength'] * 100)
        elif death_cross and death_cross['days_ago'] <= 5:
            score -= 30 + min(20, death_cross['strength'] * 100)
        
        # 柱状图趋势评分
        if histogram_trend['trend'] == 'rising' and histogram_trend['above_zero']:
            score += 20
        elif histogram_trend['trend'] == 'falling' and not histogram_trend['above_zero']:
            score -= 20
        
        # 背离信号评分
        if divergence_signals['bullish_divergence']:
            score += 25
        elif divergence_signals['bearish_divergence']:
            score -= 25
        
        # 转换为信号强度
        if score >= 60:
            return SignalStrength.STRONG
        elif score >= 30:
            return SignalStrength.MEDIUM
        elif score >= 10:
            return SignalStrength.WEAK
        elif score <= -60:
            return SignalStrength.STRONG  # 强烈看跌
        elif score <= -30:
            return SignalStrength.MEDIUM  # 中等看跌
        elif score <= -10:
            return SignalStrength.WEAK    # 弱看跌
        else:
            return SignalStrength.WEAK
    
    def _calculate_comprehensive_score(self, rule_123_result: Dict, rule_2b_result: Dict, 
                                     macd_analysis: Dict, enhanced_trend: Dict) -> Dict[str, Any]:
        """
        计算综合评分
        """
        try:
            total_score = 0
            signal_components = []
            
            # 123法则评分 (权重: 30%)
            if rule_123_result.get('signal_strength') != SignalStrength.WEAK:
                rule_123_score = self._get_signal_score(rule_123_result.get('signal_strength', SignalStrength.WEAK))
                total_score += rule_123_score * 0.3
                signal_components.append({
                    'component': '123_rule',
                    'score': rule_123_score,
                    'weight': 0.3,
                    'contribution': rule_123_score * 0.3
                })
            
            # 2B法则评分 (权重: 25%)
            if rule_2b_result.get('signal_strength') != SignalStrength.WEAK:
                rule_2b_score = self._get_signal_score(rule_2b_result.get('signal_strength', SignalStrength.WEAK))
                total_score += rule_2b_score * 0.25
                signal_components.append({
                    'component': '2b_rule',
                    'score': rule_2b_score,
                    'weight': 0.25,
                    'contribution': rule_2b_score * 0.25
                })
            
            # MACD分析评分 (权重: 25%)
            macd_score = self._get_signal_score(macd_analysis.get('signal_strength', SignalStrength.WEAK))
            total_score += macd_score * 0.25
            signal_components.append({
                'component': 'macd_analysis',
                'score': macd_score,
                'weight': 0.25,
                'contribution': macd_score * 0.25
            })
            
            # 增强趋势分析评分 (权重: 20%)
            trend_score = self._get_trend_score(enhanced_trend)
            total_score += trend_score * 0.2
            signal_components.append({
                'component': 'enhanced_trend',
                'score': trend_score,
                'weight': 0.2,
                'contribution': trend_score * 0.2
            })
            
            # 标准化评分到-100到100
            normalized_score = max(-100, min(100, total_score))
            
            return {
                'total_score': normalized_score,
                'signal_components': signal_components,
                'score_breakdown': {
                    'rule_123': rule_123_result.get('signal_strength', SignalStrength.WEAK).name,
                    'rule_2b': rule_2b_result.get('signal_strength', SignalStrength.WEAK).name,
                    'macd': macd_analysis.get('signal_strength', SignalStrength.WEAK).name,
                    'trend': enhanced_trend.get('trend_strength', 'WEAK')
                }
            }
            
        except Exception as e:
            self.logger.error(f"综合评分计算失败: {e}")
            return {
                'total_score': 0,
                'signal_components': [],
                'score_breakdown': {}
            }
    
    def _get_signal_score(self, signal_strength: SignalStrength) -> float:
        """
        将信号强度转换为数值评分
        """
        score_mapping = {
            SignalStrength.STRONG: 80,
            SignalStrength.MEDIUM: 50,
            SignalStrength.WEAK: 20,
            SignalStrength.WEAK: 0
        }
        return score_mapping.get(signal_strength, 0)
    
    def _get_trend_score(self, enhanced_trend: Dict) -> float:
        """
        计算趋势评分
        """
        try:
            trend_direction = enhanced_trend.get('trend_direction', 'sideways')
            trend_strength = enhanced_trend.get('trend_strength', 'WEAK')
            
            # 基础评分
            base_score = 0
            if trend_direction == 'uptrend':
                base_score = 60
            elif trend_direction == 'downtrend':
                base_score = -60
            else:  # sideways
                base_score = 0
            
            # 强度调整
            strength_multiplier = {
                'STRONG': 1.0,
                'MEDIUM': 0.7,
                'WEAK': 0.4
            }.get(trend_strength, 0.4)
            
            return base_score * strength_multiplier
            
        except Exception:
            return 0
    
    def _generate_final_recommendation(self, comprehensive_score: Dict, 
                                     rule_123_result: Dict, rule_2b_result: Dict,
                                     macd_analysis: Dict, enhanced_trend: Dict) -> Dict[str, Any]:
        """
        生成最终交易推荐
        """
        try:
            total_score = comprehensive_score.get('total_score', 0)
            
            # 基于综合评分确定推荐
            if total_score >= 60:
                recommendation = 'STRONG_BUY'
                confidence = min(95, 60 + (total_score - 60) * 0.5)
            elif total_score >= 30:
                recommendation = 'BUY'
                confidence = min(80, 50 + (total_score - 30) * 0.5)
            elif total_score >= 10:
                recommendation = 'WEAK_BUY'
                confidence = min(65, 40 + (total_score - 10) * 0.5)
            elif total_score <= -60:
                recommendation = 'STRONG_SELL'
                confidence = min(95, 60 + abs(total_score + 60) * 0.5)
            elif total_score <= -30:
                recommendation = 'SELL'
                confidence = min(80, 50 + abs(total_score + 30) * 0.5)
            elif total_score <= -10:
                recommendation = 'WEAK_SELL'
                confidence = min(65, 40 + abs(total_score + 10) * 0.5)
            else:
                recommendation = 'HOLD'
                confidence = 30 + abs(total_score) * 0.5
            
            # 生成推荐理由
            reasons = self._generate_recommendation_reasons(
                rule_123_result, rule_2b_result, macd_analysis, enhanced_trend
            )
            
            # 风险提示
            risk_factors = self._identify_risk_factors(
                rule_123_result, rule_2b_result, macd_analysis, enhanced_trend
            )
            
            return {
                'recommendation': recommendation,
                'confidence': round(confidence, 1),
                'total_score': total_score,
                'reasons': reasons,
                'risk_factors': risk_factors,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"生成最终推荐失败: {e}")
            return {
                'recommendation': 'HOLD',
                'confidence': 30.0,
                'total_score': 0,
                'reasons': ['分析过程中出现错误'],
                'risk_factors': ['数据分析不完整'],
                'timestamp': pd.Timestamp.now().isoformat()
            }
    
    def _generate_recommendation_reasons(self, rule_123_result: Dict, rule_2b_result: Dict,
                                       macd_analysis: Dict, enhanced_trend: Dict) -> List[str]:
        """
        生成推荐理由
        """
        reasons = []
        
        # 123法则理由
        if rule_123_result.get('signal_strength') in [SignalStrength.STRONG, SignalStrength.MEDIUM]:
            trend_direction = rule_123_result.get('trend_direction', 'unknown')
            if trend_direction == 'uptrend':
                reasons.append('123法则显示上升趋势确认信号')
            elif trend_direction == 'downtrend':
                reasons.append('123法则显示下降趋势确认信号')
        
        # 2B法则理由
        if rule_2b_result.get('signal_strength') in [SignalStrength.STRONG, SignalStrength.MEDIUM]:
            reasons.append('2B法则检测到趋势反转信号')
        
        # MACD理由
        macd_signals = macd_analysis.get('signals', {})
        if macd_signals.get('golden_cross'):
            reasons.append('MACD出现金叉信号')
        elif macd_signals.get('death_cross'):
            reasons.append('MACD出现死叉信号')
        
        if macd_signals.get('divergence', {}).get('bullish_divergence'):
            reasons.append('MACD显示看涨背离')
        elif macd_signals.get('divergence', {}).get('bearish_divergence'):
            reasons.append('MACD显示看跌背离')
        
        # 趋势理由
        trend_direction = enhanced_trend.get('trend_direction', 'sideways')
        trend_strength = enhanced_trend.get('trend_strength', 'WEAK')
        if trend_strength in ['STRONG', 'MEDIUM']:
            if trend_direction == 'uptrend':
                reasons.append(f'技术指标确认{trend_strength.lower()}上升趋势')
            elif trend_direction == 'downtrend':
                reasons.append(f'技术指标确认{trend_strength.lower()}下降趋势')
        
        return reasons if reasons else ['综合技术分析结果']
    
    def _identify_risk_factors(self, rule_123_result: Dict, rule_2b_result: Dict,
                             macd_analysis: Dict, enhanced_trend: Dict) -> List[str]:
        """
        识别风险因素
        """
        risk_factors = []
        
        # 信号冲突风险
        signals = []
        if rule_123_result.get('signal_strength') != SignalStrength.WEAK:
            signals.append(rule_123_result.get('trend_direction', 'unknown'))
        if rule_2b_result.get('signal_strength') != SignalStrength.WEAK:
            signals.append('reversal')  # 2B法则是反转信号
        
        if len(set(signals)) > 1 and 'unknown' not in signals:
            risk_factors.append('多个信号存在冲突，需谨慎操作')
        
        # 趋势强度风险
        trend_strength = enhanced_trend.get('trend_strength', 'WEAK')
        if trend_strength == 'WEAK':
            risk_factors.append('趋势强度较弱，可能出现震荡')
        
        # MACD风险
        macd_signals = macd_analysis.get('signals', {})
        histogram = macd_signals.get('histogram', {})
        if histogram.get('trend') == 'flat':
            risk_factors.append('MACD动能不足，信号可靠性降低')
        
        # 数据质量风险
        if not rule_123_result or not rule_2b_result or not macd_analysis:
            risk_factors.append('部分技术指标数据不足，分析结果可能不完整')
        
        return risk_factors if risk_factors else ['正常市场风险']
    
    def _get_best_macd_column(self, data: pd.DataFrame, indicator_type: str) -> Optional[str]:
        """
        获取最佳的MACD相关列名（优先前复权，其次不复权，最后后复权）
        """
        prefixes = ['qfq', 'bfq', 'hfq']  # 前复权 > 不复权 > 后复权
        
        for prefix in prefixes:
            if indicator_type == 'macd':
                col_name = f'macd_{prefix}'
            elif indicator_type == 'dif':
                col_name = f'macd_dif_{prefix}'
            elif indicator_type == 'dea':
                col_name = f'macd_dea_{prefix}'
            else:
                continue
                
            if col_name in data.columns and not data[col_name].isna().all():
                return col_name
        
        return None
    
    def _get_macd_trend_confirmation(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        MACD趋势确认
        """
        try:
            dif_col = self._get_best_macd_column(data, 'dif')
            dea_col = self._get_best_macd_column(data, 'dea')
            
            if not dif_col or not dea_col:
                return {'trend': TrendDirection.SIDEWAYS, 'confidence': 0.3}
            
            dif_values = data[dif_col].dropna()
            dea_values = data[dea_col].dropna()
            
            if len(dif_values) < 5:
                return {'trend': TrendDirection.SIDEWAYS, 'confidence': 0.3}
            
            # 当前DIF和DEA的关系
            current_dif = dif_values.iloc[-1]
            current_dea = dea_values.iloc[-1]
            
            # DIF趋势（最近5天）
            recent_dif_trend = dif_values.tail(5).diff().mean()
            
            # 确定趋势
            if current_dif > current_dea and recent_dif_trend > 0:
                trend = TrendDirection.UPWARD
                confidence = min(0.9, 0.6 + abs(recent_dif_trend) * 100)
            elif current_dif < current_dea and recent_dif_trend < 0:
                trend = TrendDirection.DOWNWARD
                confidence = min(0.9, 0.6 + abs(recent_dif_trend) * 100)
            else:
                trend = TrendDirection.SIDEWAYS
                confidence = 0.4
            
            return {
                'trend': trend,
                'confidence': confidence,
                'dif_above_dea': current_dif > current_dea,
                'dif_trend': 'rising' if recent_dif_trend > 0 else 'falling'
            }
            
        except Exception as e:
            self.logger.error(f"MACD趋势确认失败: {e}")
            return {'trend': TrendDirection.SIDEWAYS, 'confidence': 0.3}
    
    def _get_ma_trend_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        移动平均线趋势分析
        """
        try:
            # 优先使用前复权数据
            ma_columns = {
                'ma5': self._get_best_ma_column(data, 5),
                'ma10': self._get_best_ma_column(data, 10),
                'ma20': self._get_best_ma_column(data, 20),
                'ma60': self._get_best_ma_column(data, 60)
            }
            
            # 检查是否有足够的MA数据
            available_mas = {k: v for k, v in ma_columns.items() if v and v in data.columns}
            
            if len(available_mas) < 2:
                return {'alignment': 'insufficient_data', 'strength': 0.3}
            
            # 获取当前价格
            current_price = data['close'].iloc[-1] if 'close' in data.columns else None
            if current_price is None:
                return {'alignment': 'no_price_data', 'strength': 0.3}
            
            # 分析MA排列
            ma_values = {}
            for name, col in available_mas.items():
                if not data[col].isna().iloc[-1]:
                    ma_values[name] = data[col].iloc[-1]
            
            if len(ma_values) < 2:
                return {'alignment': 'insufficient_ma_data', 'strength': 0.3}
            
            # 判断多头/空头排列
            sorted_mas = sorted(ma_values.items(), key=lambda x: x[1], reverse=True)
            
            # 多头排列：价格 > MA5 > MA10 > MA20 > MA60
            # 空头排列：价格 < MA5 < MA10 < MA20 < MA60
            
            if current_price > max(ma_values.values()):
                alignment = 'bullish'
                strength = 0.8
            elif current_price < min(ma_values.values()):
                alignment = 'bearish'
                strength = 0.8
            else:
                alignment = 'mixed'
                strength = 0.5
            
            return {
                'alignment': alignment,
                'strength': strength,
                'ma_values': ma_values,
                'current_price': current_price
            }
            
        except Exception as e:
            self.logger.error(f"MA趋势分析失败: {e}")
            return {'alignment': 'error', 'strength': 0.3}
    
    def _get_best_ma_column(self, data: pd.DataFrame, period: int) -> Optional[str]:
        """
        获取最佳的移动平均线列名
        """
        prefixes = ['qfq', 'bfq', 'hfq']
        
        for prefix in prefixes:
            col_name = f'ma_{prefix}_{period}'
            if col_name in data.columns and not data[col_name].isna().all():
                return col_name
        
        return None
    
    def _get_rsi_trend_strength(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        RSI趋势强度分析
        """
        try:
            # 寻找RSI列
            rsi_col = None
            for prefix in ['qfq', 'bfq', 'hfq']:
                for period in [6, 12, 24]:
                    col_name = f'rsi_{prefix}_{period}'
                    if col_name in data.columns and not data[col_name].isna().all():
                        rsi_col = col_name
                        break
                if rsi_col:
                    break
            
            if not rsi_col:
                return {'strength': 'no_data', 'value': 50, 'signal': 'neutral'}
            
            rsi_values = data[rsi_col].dropna()
            if len(rsi_values) < 5:
                return {'strength': 'insufficient_data', 'value': 50, 'signal': 'neutral'}
            
            current_rsi = rsi_values.iloc[-1]
            
            # RSI信号判断
            if current_rsi > 70:
                signal = 'overbought'
                strength = 'strong'
            elif current_rsi > 60:
                signal = 'bullish'
                strength = 'medium'
            elif current_rsi < 30:
                signal = 'oversold'
                strength = 'strong'
            elif current_rsi < 40:
                signal = 'bearish'
                strength = 'medium'
            else:
                signal = 'neutral'
                strength = 'weak'
            
            return {
                'strength': strength,
                'value': current_rsi,
                'signal': signal,
                'column_used': rsi_col
            }
            
        except Exception as e:
            self.logger.error(f"RSI趋势强度分析失败: {e}")
            return {'strength': 'error', 'value': 50, 'signal': 'neutral'}
    
    def _merge_price_and_factors(self, price_data: pd.DataFrame, factor_data: pd.DataFrame) -> pd.DataFrame:
        """
        合并价格数据和技术因子数据
        """
        try:
            # 确保两个数据框都有trade_date列作为索引
            if 'trade_date' in price_data.columns:
                price_data = price_data.set_index('trade_date')
            if 'trade_date' in factor_data.columns:
                factor_data = factor_data.set_index('trade_date')
            
            # 识别重复列并处理
            price_columns = set(price_data.columns)
            factor_columns = set(factor_data.columns)
            overlapping_columns = price_columns.intersection(factor_columns)
            
            # 对于重复的价格字段，优先使用价格数据中的字段
            price_priority_columns = {'open', 'high', 'low', 'close', 'volume', 'turnover', 'amount'}
            
            # 从技术因子数据中移除与价格数据重复的基础价格字段
            factor_data_cleaned = factor_data.copy()
            for col in overlapping_columns:
                if col in price_priority_columns:
                    factor_data_cleaned = factor_data_cleaned.drop(columns=[col])
            
            # 合并数据，使用内连接确保数据一致性
            combined = pd.merge(price_data, factor_data_cleaned, left_index=True, right_index=True, how='inner')
            
            # 按日期排序
            combined = combined.sort_index()
            
            # 验证关键字段存在
            required_fields = ['open', 'high', 'low', 'close']
            missing_fields = [field for field in required_fields if field not in combined.columns]
            if missing_fields:
                self.logger.warning(f"合并后缺少关键字段: {missing_fields}")
            
            return combined
            
        except Exception as e:
            self.logger.error(f"合并数据失败: {e}")
            return pd.DataFrame()
    
    def _identify_enhanced_trend(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        基于技术因子增强的趋势识别
        """
        try:
            # 基础趋势识别
            basic_trend = self._identify_current_trend(data)
            
            # MACD趋势确认
            macd_trend = self._get_macd_trend_confirmation(data)
            
            # 移动平均线趋势
            ma_trend = self._get_ma_trend_analysis(data)
            
            # RSI趋势强度
            rsi_strength = self._get_rsi_trend_strength(data)
            
            # 综合趋势评估
            trend_confidence = self._calculate_trend_confidence(
                basic_trend, macd_trend, ma_trend, rsi_strength
            )
            
            return {
                'primary_trend': basic_trend,
                'macd_confirmation': macd_trend,
                'ma_alignment': ma_trend,
                'rsi_strength': rsi_strength,
                'trend_confidence': trend_confidence,
                'final_trend_direction': self._determine_final_trend(
                    basic_trend, macd_trend, ma_trend, trend_confidence
                )
            }
            
        except Exception as e:
            self.logger.error(f"增强趋势识别失败: {e}")
            return {
                'primary_trend': TrendDirection.SIDEWAYS,
                'trend_confidence': 0.3,
                'final_trend_direction': TrendDirection.SIDEWAYS
            }
    
    def _analyze_macd_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析MACD信号
        """
        try:
            # 优先使用前复权数据，如果没有则使用不复权数据
            macd_col = self._get_best_macd_column(data, 'macd')
            dif_col = self._get_best_macd_column(data, 'dif')
            dea_col = self._get_best_macd_column(data, 'dea')
            
            if not all([macd_col, dif_col, dea_col]):
                return self._empty_macd_result()
            
            macd_values = data[macd_col].dropna()
            dif_values = data[dif_col].dropna()
            dea_values = data[dea_col].dropna()
            
            if len(macd_values) < 10:
                return self._empty_macd_result()
            
            # 金叉死叉信号
            golden_cross, death_cross = self._detect_macd_crossovers(dif_values, dea_values)
            
            # MACD柱状图分析
            macd_histogram_trend = self._analyze_macd_histogram(macd_values)
            
            # MACD背离分析
            divergence_signals = self._detect_macd_divergence(data, dif_values)
            
            # MACD信号强度
            signal_strength = self._calculate_macd_signal_strength(
                golden_cross, death_cross, macd_histogram_trend, divergence_signals
            )
            
            return {
                'golden_cross': golden_cross,
                'death_cross': death_cross,
                'histogram_trend': macd_histogram_trend,
                'divergence_signals': divergence_signals,
                'signal_strength': signal_strength,
                'current_macd': macd_values.iloc[-1] if len(macd_values) > 0 else 0,
                'current_dif': dif_values.iloc[-1] if len(dif_values) > 0 else 0,
                'current_dea': dea_values.iloc[-1] if len(dea_values) > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"MACD信号分析失败: {e}")
            return self._empty_macd_result()
    
    def _identify_current_trend(self, data: pd.DataFrame) -> TrendDirection:
        """识别当前趋势方向"""
        # 使用多个周期的移动平均线判断趋势
        close_prices = data['close']
        
        # 计算不同周期的移动平均线
        ma5 = close_prices.rolling(window=5).mean()
        ma10 = close_prices.rolling(window=10).mean()
        ma20 = close_prices.rolling(window=20).mean()
        
        current_price = close_prices.iloc[-1]
        current_ma5 = ma5.iloc[-1]
        current_ma10 = ma10.iloc[-1]
        current_ma20 = ma20.iloc[-1]
        
        # 判断趋势
        if current_price > current_ma5 > current_ma10 > current_ma20:
            return TrendDirection.UPWARD
        elif current_price < current_ma5 < current_ma10 < current_ma20:
            return TrendDirection.DOWNWARD
        else:
            return TrendDirection.SIDEWAYS
    
    def _check_trendline_break(self, data: pd.DataFrame, trend: TrendDirection) -> Dict[str, Any]:
        """检查趋势线突破（123法则条件1）"""
        try:
            # 计算简单趋势线
            if trend == TrendDirection.UPWARD:
                # 上升趋势：连接最近的两个低点
                lows = data['low'].rolling(window=5).min()
                low_points = []
                for i in range(5, len(data)):
                    if data['low'].iloc[i] == lows.iloc[i]:
                        low_points.append((i, data['low'].iloc[i]))
                
                if len(low_points) >= 2:
                    # 取最近的两个低点
                    p1, p2 = low_points[-2], low_points[-1]
                    slope = (p2[1] - p1[1]) / (p2[0] - p1[0]) if p2[0] != p1[0] else 0
                    
                    # 检查最近价格是否跌破趋势线
                    current_idx = len(data) - 1
                    expected_price = p2[1] + slope * (current_idx - p2[0])
                    current_low = data['low'].iloc[-1]
                    
                    is_broken = current_low < expected_price * 0.98  # 允许2%误差
                    
                    return {
                        'is_broken': is_broken,
                        'trend_line_slope': slope,
                        'expected_price': expected_price,
                        'actual_price': current_low,
                        'break_percentage': (expected_price - current_low) / expected_price * 100 if expected_price > 0 else 0
                    }
            
            elif trend == TrendDirection.DOWNWARD:
                # 下降趋势：连接最近的两个高点
                highs = data['high'].rolling(window=5).max()
                high_points = []
                for i in range(5, len(data)):
                    if data['high'].iloc[i] == highs.iloc[i]:
                        high_points.append((i, data['high'].iloc[i]))
                
                if len(high_points) >= 2:
                    # 取最近的两个高点
                    p1, p2 = high_points[-2], high_points[-1]
                    slope = (p2[1] - p1[1]) / (p2[0] - p1[0]) if p2[0] != p1[0] else 0
                    
                    # 检查最近价格是否突破趋势线
                    current_idx = len(data) - 1
                    expected_price = p2[1] + slope * (current_idx - p2[0])
                    current_high = data['high'].iloc[-1]
                    
                    is_broken = current_high > expected_price * 1.02  # 允许2%误差
                    
                    return {
                        'is_broken': is_broken,
                        'trend_line_slope': slope,
                        'expected_price': expected_price,
                        'actual_price': current_high,
                        'break_percentage': (current_high - expected_price) / expected_price * 100 if expected_price > 0 else 0
                    }
            
            return {'is_broken': False, 'reason': '无法确定趋势线'}
            
        except Exception as e:
            self.logger.error(f"检查趋势线突破失败: {e}")
            return {'is_broken': False, 'reason': f'分析错误: {e}'}
    
    def _check_no_new_extreme(self, data: pd.DataFrame, trend: TrendDirection) -> Dict[str, Any]:
        """检查是否不再创新高/新低（123法则条件2）"""
        try:
            recent_data = data.tail(20)  # 最近20个交易日
            
            if trend == TrendDirection.UPWARD:
                # 上升趋势：检查是否不再创新高
                recent_high = recent_data['high'].max()
                previous_high = data['high'].iloc[:-10].max()  # 之前的最高价
                
                no_new_high = recent_high <= previous_high * 1.01  # 允许1%误差
                
                return {
                    'no_new_extreme': no_new_high,
                    'recent_extreme': recent_high,
                    'previous_extreme': previous_high,
                    'extreme_type': 'high',
                    'comparison_ratio': recent_high / previous_high if previous_high > 0 else 1
                }
            
            elif trend == TrendDirection.DOWNWARD:
                # 下降趋势：检查是否不再创新低
                recent_low = recent_data['low'].min()
                previous_low = data['low'].iloc[:-10].min()  # 之前的最低价
                
                no_new_low = recent_low >= previous_low * 0.99  # 允许1%误差
                
                return {
                    'no_new_extreme': no_new_low,
                    'recent_extreme': recent_low,
                    'previous_extreme': previous_low,
                    'extreme_type': 'low',
                    'comparison_ratio': recent_low / previous_low if previous_low > 0 else 1
                }
            
            return {'no_new_extreme': False, 'reason': '横盘趋势'}
            
        except Exception as e:
            self.logger.error(f"检查新极值失败: {e}")
            return {'no_new_extreme': False, 'reason': f'分析错误: {e}'}
    
    def _check_retracement_break(self, data: pd.DataFrame, trend: TrendDirection) -> Dict[str, Any]:
        """检查回调突破（123法则条件3）"""
        try:
            if trend == TrendDirection.UPWARD:
                # 上升趋势：检查是否跌破前期回调低点
                recent_data = data.tail(30)
                
                # 找到最近的回调低点
                lows = recent_data['low']
                min_low_idx = lows.idxmin()
                min_low_value = lows.min()
                
                # 检查当前价格是否跌破该低点
                current_low = data['low'].iloc[-1]
                is_broken = current_low < min_low_value * 0.99
                
                return {
                    'retracement_broken': is_broken,
                    'retracement_level': min_low_value,
                    'current_level': current_low,
                    'break_percentage': (min_low_value - current_low) / min_low_value * 100 if min_low_value > 0 else 0,
                    'retracement_date': min_low_idx
                }
            
            elif trend == TrendDirection.DOWNWARD:
                # 下降趋势：检查是否突破前期反弹高点
                recent_data = data.tail(30)
                
                # 找到最近的反弹高点
                highs = recent_data['high']
                max_high_idx = highs.idxmax()
                max_high_value = highs.max()
                
                # 检查当前价格是否突破该高点
                current_high = data['high'].iloc[-1]
                is_broken = current_high > max_high_value * 1.01
                
                return {
                    'retracement_broken': is_broken,
                    'retracement_level': max_high_value,
                    'current_level': current_high,
                    'break_percentage': (current_high - max_high_value) / max_high_value * 100 if max_high_value > 0 else 0,
                    'retracement_date': max_high_idx
                }
            
            return {'retracement_broken': False, 'reason': '横盘趋势'}
            
        except Exception as e:
            self.logger.error(f"检查回调突破失败: {e}")
            return {'retracement_broken': False, 'reason': f'分析错误: {e}'}
    
    def _detect_false_breakout(self, data: pd.DataFrame, trend: TrendDirection) -> Optional[Dict[str, Any]]:
        """检测假突破模式（2B法则核心）"""
        try:
            # 确保数据不为空
            if data.empty or len(data) < 10:
                return None
                
            recent_data = data.tail(30)
            if recent_data.empty or len(recent_data) < 10:
                return None
            
            if trend == TrendDirection.UPWARD:
                # 上升趋势中的假突破：突破前高但未能持续
                if 'high' not in recent_data.columns:
                    return None
                    
                highs = recent_data['high']
                if highs.empty:
                    return None
                
                # 找到前期高点
                for i in range(len(recent_data) - 5, 5, -1):
                    try:
                        potential_high = highs.iloc[i]
                        if pd.isna(potential_high):
                            continue
                        
                        # 检查是否有突破该高点
                        subsequent_data = recent_data.iloc[i+1:]
                        if len(subsequent_data) < 3 or 'high' not in subsequent_data.columns:
                            continue
                        
                        # 安全的数组比较，使用self._safe_array_compare方法
                        breakout_occurred = self._safe_array_compare(
                            subsequent_data['high'], 
                            lambda x: x > potential_high * 1.01
                        )
                        
                        if breakout_occurred:
                            # 检查突破后是否快速回落
                            max_after_breakout = subsequent_data['high'].max()
                            if 'close' not in data.columns:
                                continue
                                
                            current_price = data['close'].iloc[-1]
                            if pd.isna(current_price) or pd.isna(max_after_breakout):
                                continue
                            
                            # 如果当前价格低于突破点，可能是假突破
                            if current_price < potential_high * 0.99:
                                return {
                                    'type': 'upward_false_breakout',
                                    'breakout_level': potential_high,
                                    'max_after_breakout': max_after_breakout,
                                    'current_price': current_price,
                                    'breakout_date': recent_data.index[i],
                                    'failure_percentage': (max_after_breakout - current_price) / max_after_breakout * 100 if max_after_breakout > 0 else 0
                                }
                    except Exception as inner_e:
                        self.logger.debug(f"检测上升假突破内部错误 i={i}: {inner_e}")
                        continue
            
            elif trend == TrendDirection.DOWNWARD:
                # 下降趋势中的假突破：跌破前低但未能持续
                if 'low' not in recent_data.columns:
                    return None
                    
                lows = recent_data['low']
                if lows.empty:
                    return None
                
                # 找到前期低点
                for i in range(len(recent_data) - 5, 5, -1):
                    try:
                        potential_low = lows.iloc[i]
                        if pd.isna(potential_low):
                            continue
                        
                        # 检查是否有跌破该低点
                        subsequent_data = recent_data.iloc[i+1:]
                        if len(subsequent_data) < 3 or 'low' not in subsequent_data.columns:
                            continue
                        
                        # 安全的数组比较，使用self._safe_array_compare方法
                        breakout_occurred = self._safe_array_compare(
                            subsequent_data['low'],
                            lambda x: x < potential_low * 0.99
                        )
                        
                        if breakout_occurred:
                            # 检查突破后是否快速反弹
                            min_after_breakout = subsequent_data['low'].min()
                            if 'close' not in data.columns:
                                continue
                                
                            current_price = data['close'].iloc[-1]
                            if pd.isna(current_price) or pd.isna(min_after_breakout):
                                continue
                            
                            # 如果当前价格高于突破点，可能是假突破
                            if current_price > potential_low * 1.01:
                                return {
                                    'type': 'downward_false_breakout',
                                    'breakout_level': potential_low,
                                    'min_after_breakout': min_after_breakout,
                                    'current_price': current_price,
                                    'breakout_date': recent_data.index[i],
                                    'recovery_percentage': (current_price - min_after_breakout) / min_after_breakout * 100 if min_after_breakout > 0 else 0
                                }
                    except Exception as inner_e:
                        self.logger.debug(f"检测下降假突破内部错误 i={i}: {inner_e}")
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"检测假突破失败: {e}")
            import traceback
            self.logger.error(f"假突破检测异常详情: {traceback.format_exc()}")
            return None
    
    def _validate_2b_conditions(self, data: pd.DataFrame, false_breakout: Optional[Dict], trend: TrendDirection) -> bool:
        """验证2B法则条件"""
        if not false_breakout:
            return False
        
        try:
            # 2B法则需要满足的条件：
            # 1. 存在假突破
            # 2. 突破后快速失败
            # 3. 成交量配合（突破时放量，失败时缩量）
            
            # 条件1：已经通过false_breakout检测
            
            # 条件2：检查失败的速度（在5个交易日内失败）
            breakout_date = false_breakout['breakout_date']
            breakout_idx = data.index.get_loc(breakout_date)
            
            if len(data) - breakout_idx <= 5:  # 在5个交易日内失败
                return True
            
            # 条件3：成交量分析（简化版）
            recent_volume = data['volume'].iloc[-5:].mean()
            breakout_volume = data['volume'].iloc[breakout_idx:breakout_idx+3].mean()
            
            # 突破时成交量应该放大
            volume_expansion = breakout_volume > recent_volume * 1.2
            
            return volume_expansion
            
        except Exception as e:
            self.logger.error(f"验证2B条件失败: {e}")
            return False
    
    def _determine_final_trend(self, basic_trend: TrendDirection, macd_trend: Dict, 
                              ma_trend: Dict, trend_confidence: float) -> TrendDirection:
        """确定最终趋势方向"""
        try:
            # 如果置信度很高，直接使用基础趋势
            if trend_confidence > 0.8:
                return basic_trend
            
            # 如果置信度较低，结合技术指标确认
            confirmations = []
            
            # MACD确认
            if isinstance(macd_trend, dict) and macd_trend.get('trend_direction') == basic_trend:
                confirmations.append('macd')
            
            # MA确认
            if isinstance(ma_trend, dict) and ma_trend.get('trend_direction') == basic_trend:
                confirmations.append('ma')
            
            # 如果有足够的确认，使用基础趋势
            if len(confirmations) >= 1:
                return basic_trend
            
            # 否则返回横盘
            return TrendDirection.SIDEWAYS
            
        except Exception as e:
            self.logger.error(f"确定最终趋势失败: {e}")
            return TrendDirection.SIDEWAYS
    
    def _calculate_123_signal_strength(self, cond1: Dict, cond2: Dict, cond3: Dict) -> SignalStrength:
        """计算123法则信号强度"""
        score = 0
        
        # 条件1：趋势线突破
        if cond1.get('is_broken', False):
            score += 30
            if cond1.get('break_percentage', 0) > 3:  # 突破幅度大于3%
                score += 10
        
        # 条件2：不再创新极值
        if cond2.get('no_new_extreme', False):
            score += 30
        
        # 条件3：回调突破
        if cond3.get('retracement_broken', False):
            score += 40
            if cond3.get('break_percentage', 0) > 2:  # 突破幅度大于2%
                score += 10
        
        if score >= 80:
            return SignalStrength.STRONG
        elif score >= 50:
            return SignalStrength.MEDIUM
        elif score >= 20:
            return SignalStrength.WEAK
        else:
            return SignalStrength.WEAK
    
    def _calculate_2b_signal_strength(self, false_breakout: Optional[Dict], is_2b: bool) -> SignalStrength:
        """计算2B法则信号强度"""
        if not false_breakout or not is_2b:
            return SignalStrength.WEAK
        
        score = 50  # 基础分数
        
        # 失败幅度越大，信号越强
        if 'failure_percentage' in false_breakout:
            failure_pct = false_breakout['failure_percentage']
            if failure_pct > 5:
                score += 30
            elif failure_pct > 3:
                score += 20
            elif failure_pct > 1:
                score += 10
        
        if 'recovery_percentage' in false_breakout:
            recovery_pct = false_breakout['recovery_percentage']
            if recovery_pct > 5:
                score += 30
            elif recovery_pct > 3:
                score += 20
            elif recovery_pct > 1:
                score += 10
        
        if score >= 80:
            return SignalStrength.STRONG
        elif score >= 65:
            return SignalStrength.MEDIUM
        elif score >= 50:
            return SignalStrength.WEAK
        else:
            return SignalStrength.WEAK
    
    def _generate_123_trading_signal(self, trend: TrendDirection, cond1: Dict, 
                                   cond2: Dict, cond3: Dict, strength: SignalStrength) -> str:
        """生成123法则交易信号"""
        conditions_met = sum([
            cond1.get('is_broken', False),
            cond2.get('no_new_extreme', False),
            cond3.get('retracement_broken', False)
        ])
        
        if conditions_met >= 3:
            # 三个条件都满足，强烈反转信号
            if trend == TrendDirection.UPWARD:
                return 'strong_sell'  # 上升趋势反转，卖出
            else:
                return 'strong_buy'   # 下降趋势反转，买入
        elif conditions_met >= 2:
            # 两个条件满足，中等反转信号
            if trend == TrendDirection.UPWARD:
                return 'sell'
            else:
                return 'buy'
        elif conditions_met >= 1:
            # 一个条件满足，弱反转信号
            return 'watch'  # 观察
        else:
            return 'hold'   # 保持
    
    def _generate_2b_trading_signal(self, trend: TrendDirection, false_breakout: Optional[Dict], 
                                  is_2b: bool, strength: SignalStrength) -> str:
        """生成2B法则交易信号"""
        if not false_breakout or not is_2b:
            return 'hold'
        
        if strength == SignalStrength.STRONG:
            if false_breakout['type'] == 'upward_false_breakout':
                return 'strong_sell'  # 向上假突破，强烈卖出信号
            else:
                return 'strong_buy'   # 向下假突破，强烈买入信号
        elif strength == SignalStrength.MEDIUM:
            if false_breakout['type'] == 'upward_false_breakout':
                return 'sell'
            else:
                return 'buy'
        else:
            return 'watch'
    
    def _calculate_reversal_probability(self, cond1: Dict, cond2: Dict, cond3: Dict) -> float:
        """计算123法则反转概率"""
        base_probability = 0.3  # 基础概率30%
        
        if cond1.get('is_broken', False):
            base_probability += 0.2
        if cond2.get('no_new_extreme', False):
            base_probability += 0.2
        if cond3.get('retracement_broken', False):
            base_probability += 0.3
        
        return min(0.95, base_probability)  # 最高95%
    
    def _calculate_2b_reversal_probability(self, false_breakout: Optional[Dict], is_2b: bool) -> float:
        """计算2B法则反转概率"""
        if not false_breakout or not is_2b:
            return 0.1
        
        base_probability = 0.6  # 2B法则基础概率较高
        
        # 根据失败幅度调整概率
        if 'failure_percentage' in false_breakout:
            failure_pct = false_breakout['failure_percentage']
            if failure_pct > 5:
                base_probability += 0.2
            elif failure_pct > 3:
                base_probability += 0.1
        
        if 'recovery_percentage' in false_breakout:
            recovery_pct = false_breakout['recovery_percentage']
            if recovery_pct > 5:
                base_probability += 0.2
            elif recovery_pct > 3:
                base_probability += 0.1
        
        return min(0.9, base_probability)  # 最高90%
    
    def _empty_123_result(self) -> Dict[str, Any]:
        """返回空的123法则结果"""
        return {
            'rule_type': '123法则',
            'current_trend': TrendDirection.SIDEWAYS,
            'condition1_trendline_break': {'is_broken': False},
            'condition2_no_new_extreme': {'no_new_extreme': False},
            'condition3_retracement_break': {'retracement_broken': False},
            'signal_strength': SignalStrength.WEAK,
            'trading_signal': 'hold',
            'reversal_probability': 0.1,
            'analysis_date': datetime.now()
        }
    
    def _empty_2b_result(self) -> Dict[str, Any]:
        """返回空的2B法则结果"""
        return {
            'rule_type': '2B法则',
            'current_trend': TrendDirection.SIDEWAYS,
            'false_breakout_detected': False,
            'false_breakout_details': None,
            'is_2b_signal': False,
            'signal_strength': SignalStrength.WEAK,
            'trading_signal': 'hold',
            'reversal_probability': 0.1,
            'analysis_date': datetime.now()
        }
    
    def _calculate_trend_confidence(self, basic_trend: TrendDirection, 
                                  macd_trend: Dict, ma_trend: Dict, rsi_strength: float) -> float:
        """计算趋势置信度"""
        try:
            confidence = 0.0
            
            # 基础趋势权重 40%
            if basic_trend == TrendDirection.UPWARD:
                confidence += 0.4
            elif basic_trend == TrendDirection.DOWNWARD:
                confidence += 0.4
            else:  # SIDEWAYS
                confidence += 0.2
            
            # MACD趋势确认权重 30%
            if macd_trend.get('trend_confirmed', False):
                confidence += 0.3
            elif macd_trend.get('trend_direction') == basic_trend:
                confidence += 0.2
            
            # MA趋势确认权重 20%
            if ma_trend.get('trend_confirmed', False):
                confidence += 0.2
            elif ma_trend.get('trend_direction') == basic_trend:
                confidence += 0.1
            
            # RSI强度权重 10%
            if isinstance(rsi_strength, (int, float)):
                if rsi_strength > 0.7:
                    confidence += 0.1
                elif rsi_strength > 0.5:
                    confidence += 0.05
            elif isinstance(rsi_strength, dict):
                # 如果rsi_strength是字典，尝试获取数值
                rsi_value = rsi_strength.get('strength', 0.5)
                if isinstance(rsi_value, (int, float)):
                    if rsi_value > 0.7:
                        confidence += 0.1
                    elif rsi_value > 0.5:
                        confidence += 0.05
            
            return min(1.0, confidence)
            
        except Exception as e:
            self.logger.error(f"计算趋势置信度失败: {e}")
            return 0.5