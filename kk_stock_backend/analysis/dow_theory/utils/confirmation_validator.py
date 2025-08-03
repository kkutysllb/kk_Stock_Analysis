#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多时间周期确认验证器
实现道氏理论中的多重确认机制
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
    TrendAnalysis, MultiTimeFrameConfirmation, TrendDirection, TrendPhase,
    SignalStrength, VolumePattern
)


class ConfirmationValidator:
    """多时间周期确认验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_confirmation(self, monthly: TrendAnalysis, weekly: TrendAnalysis, 
                            daily: TrendAnalysis) -> MultiTimeFrameConfirmation:
        """
        验证多时间周期确认
        
        Args:
            monthly: 月线分析结果
            weekly: 周线分析结果
            daily: 日线分析结果
            
        Returns:
            多时间周期确认结果
        """
        # 检查主要趋势与次要趋势的一致性
        primary_secondary_alignment = self._check_primary_secondary_alignment(monthly, weekly)
        
        # 检查次要趋势与短期波动的一致性
        secondary_minor_alignment = self._check_secondary_minor_alignment(weekly, daily)
        
        # 检查整体一致性
        overall_alignment = primary_secondary_alignment and secondary_minor_alignment
        
        # 评估确认强度
        confirmation_strength = self._evaluate_confirmation_strength(
            monthly, weekly, daily, primary_secondary_alignment, 
            secondary_minor_alignment, overall_alignment
        )
        
        # 识别冲突信号
        conflicting_signals = self._identify_conflicting_signals(monthly, weekly, daily)
        
        return MultiTimeFrameConfirmation(
            primary_secondary_alignment=primary_secondary_alignment,
            secondary_minor_alignment=secondary_minor_alignment,
            overall_alignment=overall_alignment,
            confirmation_strength=confirmation_strength,
            conflicting_signals=conflicting_signals
        )
    
    def _check_primary_secondary_alignment(self, monthly: TrendAnalysis, weekly: TrendAnalysis) -> bool:
        """检查主要趋势与次要趋势的一致性"""
        # 基本趋势方向一致性
        direction_alignment = monthly.direction == weekly.direction
        
        # 如果方向一致，进一步检查其他因素
        if direction_alignment:
            return True
        
        # 如果方向不一致，检查是否为合理的调整
        if monthly.direction == TrendDirection.UPWARD and weekly.direction == TrendDirection.DOWNWARD:
            # 上升趋势中的调整：检查调整幅度和时间
            return self._is_reasonable_correction(monthly, weekly, 'uptrend')
        elif monthly.direction == TrendDirection.DOWNWARD and weekly.direction == TrendDirection.UPWARD:
            # 下降趋势中的反弹：检查反弹幅度和时间
            return self._is_reasonable_correction(monthly, weekly, 'downtrend')
        elif monthly.direction == TrendDirection.SIDEWAYS:
            # 横盘期间，周线可以有一定的波动
            return True
        
        # 严格不一致的情况
        return False
    
    def _check_secondary_minor_alignment(self, weekly: TrendAnalysis, daily: TrendAnalysis) -> bool:
        """检查次要趋势与短期波动的一致性"""
        # 基本趋势方向一致性
        direction_alignment = weekly.direction == daily.direction
        
        if direction_alignment:
            return True
        
        # 短期波动可能与中期趋势有所不同，但不应该持续太久
        # 这里简化处理，主要看信心指数
        confidence_threshold = 60
        
        if weekly.confidence_score > confidence_threshold:
            # 周线趋势比较确定时，日线的反向波动可能是短期调整
            return True
        
        return False
    
    def _is_reasonable_correction(self, primary: TrendAnalysis, secondary: TrendAnalysis, 
                                 trend_type: str) -> bool:
        """判断是否为合理的调整"""
        # 检查信心指数差异
        confidence_diff = abs(primary.confidence_score - secondary.confidence_score)
        
        # 如果主要趋势信心指数明显高于次要趋势，则认为是合理调整
        if primary.confidence_score > secondary.confidence_score + 15:  # 降低阈值
            return True
        
        # 检查趋势阶段
        if trend_type == 'uptrend':
            # 上升趋势中，如果主要趋势处于公众参与期，次要趋势的调整是正常的
            if primary.phase == TrendPhase.PUBLIC_PARTICIPATION:
                return True
        elif trend_type == 'downtrend':
            # 下降趋势中，如果主要趋势处于恐慌期，次要趋势的反弹是正常的
            if primary.phase == TrendPhase.PANIC:
                return True
        
        # 其他情况不认为是合理调整
        return False
    
    def _evaluate_confirmation_strength(self, monthly: TrendAnalysis, weekly: TrendAnalysis,
                                       daily: TrendAnalysis, primary_secondary: bool,
                                       secondary_minor: bool, overall: bool) -> SignalStrength:
        """评估确认强度"""
        strength_score = 0
        
        # 基于一致性评分
        if overall:
            strength_score += 40
        elif primary_secondary:
            strength_score += 25
        elif secondary_minor:
            strength_score += 15
        
        # 基于各时间周期的信心指数
        avg_confidence = (monthly.confidence_score + weekly.confidence_score + daily.confidence_score) / 3
        strength_score += avg_confidence * 0.3
        
        # 基于成交量确认
        volume_confirmations = 0
        for analysis in [monthly, weekly, daily]:
            if analysis.volume_analysis.pattern in [VolumePattern.PRICE_UP_VOLUME_UP, VolumePattern.PRICE_DOWN_VOLUME_DOWN]:
                volume_confirmations += 1
        
        strength_score += volume_confirmations * 5
        
        # 基于突破信号
        breakthrough_count = len(monthly.breakthrough_signals) + len(weekly.breakthrough_signals) + len(daily.breakthrough_signals)
        strength_score += min(breakthrough_count * 3, 15)
        
        # 确定强度等级
        if strength_score >= 70:
            return SignalStrength.STRONG
        elif strength_score >= 50:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK
    
    def _identify_conflicting_signals(self, monthly: TrendAnalysis, weekly: TrendAnalysis,
                                     daily: TrendAnalysis) -> List[str]:
        """识别冲突信号"""
        conflicts = []
        
        # 趋势方向冲突
        if monthly.direction != weekly.direction:
            conflicts.append(f"月线趋势({monthly.direction.value})与周线趋势({weekly.direction.value})不一致")
        
        if weekly.direction != daily.direction:
            conflicts.append(f"周线趋势({weekly.direction.value})与日线趋势({daily.direction.value})不一致")
        
        # 成交量背离
        divergence_count = 0
        for analysis in [monthly, weekly, daily]:
            if analysis.volume_analysis.divergence_signal:
                divergence_count += 1
        
        if divergence_count >= 2:
            conflicts.append("多个时间周期出现量价背离信号")
        
        # 趋势阶段冲突
        phases = [monthly.phase, weekly.phase, daily.phase]
        unique_phases = set(phases)
        if len(unique_phases) == 3:
            conflicts.append("三个时间周期处于不同的趋势阶段")
        
        # 技术指标冲突
        tech_conflicts = self._check_technical_conflicts(monthly, weekly, daily)
        conflicts.extend(tech_conflicts)
        
        return conflicts
    
    def _check_technical_conflicts(self, monthly: TrendAnalysis, weekly: TrendAnalysis,
                                  daily: TrendAnalysis) -> List[str]:
        """检查技术指标冲突"""
        conflicts = []
        
        # 检查MACD信号冲突
        macd_signals = []
        for analysis, period in [(monthly, "月线"), (weekly, "周线"), (daily, "日线")]:
            macd_dif = analysis.technical_indicators.macd_dif
            macd_dea = analysis.technical_indicators.macd_dea
            
            if macd_dif > macd_dea:
                macd_signals.append((period, "多头"))
            else:
                macd_signals.append((period, "空头"))
        
        # 检查MACD信号是否一致
        macd_bull_count = sum(1 for _, signal in macd_signals if signal == "多头")
        if macd_bull_count == 1 or macd_bull_count == 2:  # 不是全部一致
            conflicts.append("MACD信号在不同时间周期存在分歧")
        
        # 检查RSI极端值冲突
        rsi_values = [
            (monthly.technical_indicators.rsi, "月线"),
            (weekly.technical_indicators.rsi, "周线"),
            (daily.technical_indicators.rsi, "日线")
        ]
        
        overbought_count = sum(1 for rsi, _ in rsi_values if rsi > 70)
        oversold_count = sum(1 for rsi, _ in rsi_values if rsi < 30)
        
        if overbought_count > 0 and oversold_count > 0:
            conflicts.append("不同时间周期的RSI显示相反的超买超卖信号")
        
        return conflicts
    
    def validate_trend_consistency(self, analyses: List[TrendAnalysis]) -> Dict:
        """验证趋势一致性"""
        if len(analyses) < 2:
            return {'is_consistent': True, 'consistency_score': 100}
        
        # 趋势方向一致性
        directions = [analysis.direction for analysis in analyses]
        direction_consistency = len(set(directions)) == 1
        
        # 信心指数一致性
        confidence_scores = [analysis.confidence_score for analysis in analyses]
        confidence_std = np.std(confidence_scores)
        confidence_consistency = confidence_std < 20  # 标准差小于20认为一致
        
        # 成交量模式一致性
        volume_patterns = [analysis.volume_analysis.pattern for analysis in analyses]
        healthy_patterns = [VolumePattern.PRICE_UP_VOLUME_UP, VolumePattern.PRICE_DOWN_VOLUME_DOWN]
        healthy_count = sum(1 for pattern in volume_patterns if pattern in healthy_patterns)
        volume_consistency = healthy_count >= len(analyses) * 0.6  # 60%以上为健康模式
        
        # 计算综合一致性得分
        consistency_score = 0
        if direction_consistency:
            consistency_score += 40
        if confidence_consistency:
            consistency_score += 30
        if volume_consistency:
            consistency_score += 30
        
        return {
            'is_consistent': direction_consistency and confidence_consistency,
            'consistency_score': consistency_score,
            'direction_consistency': direction_consistency,
            'confidence_consistency': confidence_consistency,
            'volume_consistency': volume_consistency,
            'details': {
                'directions': directions,
                'confidence_scores': confidence_scores,
                'confidence_std': confidence_std,
                'volume_patterns': [pattern.value for pattern in volume_patterns]
            }
        }
    
    def check_breakthrough_confirmation(self, analyses: List[TrendAnalysis]) -> Dict:
        """检查突破确认"""
        all_breakthroughs = []
        for analysis in analyses:
            all_breakthroughs.extend(analysis.breakthrough_signals)
        
        if not all_breakthroughs:
            return {
                'has_breakthrough': False,
                'confirmation_level': 'none'
            }
        
        # 统计突破类型
        upward_breakthroughs = [bt for bt in all_breakthroughs if bt.breakthrough_type == 'upward']
        downward_breakthroughs = [bt for bt in all_breakthroughs if bt.breakthrough_type == 'downward']
        
        # 检查确认程度
        confirmed_breakthroughs = [
            bt for bt in all_breakthroughs 
            if bt.price_confirmation and bt.volume_confirmation and bt.time_confirmation
        ]
        
        confirmation_rate = len(confirmed_breakthroughs) / len(all_breakthroughs) if all_breakthroughs else 0
        
        if confirmation_rate >= 0.8:
            confirmation_level = 'strong'
        elif confirmation_rate >= 0.5:
            confirmation_level = 'medium'
        else:
            confirmation_level = 'weak'
        
        return {
            'has_breakthrough': len(all_breakthroughs) > 0,
            'breakthrough_count': len(all_breakthroughs),
            'upward_count': len(upward_breakthroughs),
            'downward_count': len(downward_breakthroughs),
            'confirmed_count': len(confirmed_breakthroughs),
            'confirmation_rate': confirmation_rate,
            'confirmation_level': confirmation_level
        }
    
    def generate_confirmation_report(self, confirmation: MultiTimeFrameConfirmation) -> str:
        """生成确认报告"""
        report = "多时间周期确认分析报告：\n\n"
        
        # 一致性分析
        report += f"主要趋势与次要趋势一致性：{'✓' if confirmation.primary_secondary_alignment else '✗'}\n"
        report += f"次要趋势与短期波动一致性：{'✓' if confirmation.secondary_minor_alignment else '✗'}\n"
        report += f"整体趋势一致性：{'✓' if confirmation.overall_alignment else '✗'}\n\n"
        
        # 确认强度
        strength_desc = {
            SignalStrength.STRONG: "强",
            SignalStrength.MEDIUM: "中等",
            SignalStrength.WEAK: "弱"
        }
        report += f"确认强度：{strength_desc[confirmation.confirmation_strength]}\n\n"
        
        # 冲突信号
        if confirmation.conflicting_signals:
            report += "发现的冲突信号：\n"
            for i, signal in enumerate(confirmation.conflicting_signals, 1):
                report += f"{i}. {signal}\n"
        else:
            report += "未发现明显冲突信号\n"
        
        # 操作建议
        report += "\n操作建议：\n"
        if confirmation.overall_alignment and confirmation.confirmation_strength == SignalStrength.STRONG:
            report += "多时间周期高度一致，可以积极操作"
        elif confirmation.overall_alignment:
            report += "多时间周期基本一致，可以谨慎操作"
        elif confirmation.primary_secondary_alignment:
            report += "主要趋势和次要趋势一致，建议关注日线确认信号"
        else:
            report += "多时间周期存在分歧，建议观望等待明确信号"
        
        return report
    
    def calculate_confidence_weighted_score(self, analyses: List[TrendAnalysis], 
                                          weights: List[float] = None) -> float:
        """计算信心指数加权得分"""
        if not analyses:
            return 0.0
        
        if weights is None:
            weights = [0.5, 0.3, 0.2]  # 默认权重：月线50%，周线30%，日线20%
        
        if len(weights) != len(analyses):
            weights = [1/len(analyses)] * len(analyses)  # 平均权重
        
        weighted_score = sum(
            analysis.confidence_score * weight 
            for analysis, weight in zip(analyses, weights)
        )
        
        return weighted_score