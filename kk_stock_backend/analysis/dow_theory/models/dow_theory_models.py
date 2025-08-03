#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道氏理论分析数据模型
定义道氏理论分析中使用的各种数据结构
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd


class TrendDirection(Enum):
    """趋势方向枚举"""
    UPWARD = "upward"  # 上升趋势
    DOWNWARD = "downward"  # 下降趋势
    SIDEWAYS = "sideways"  # 横盘震荡


class TrendType(Enum):
    """道氏理论趋势类型枚举"""
    PRIMARY = "primary"  # 主要趋势（月线）
    SECONDARY = "secondary"  # 次要趋势（周线）
    MINOR = "minor"  # 短期波动（日线）


class TrendPhase(Enum):
    """趋势阶段枚举"""
    ACCUMULATION = "accumulation"  # 累积期
    PUBLIC_PARTICIPATION = "public_participation"  # 公众参与期
    PANIC = "panic"  # 恐慌期


class VolumePattern(Enum):
    """成交量模式枚举"""
    PRICE_UP_VOLUME_UP = "price_up_volume_up"  # 价涨量增
    PRICE_UP_VOLUME_DOWN = "price_up_volume_down"  # 价涨量缩
    PRICE_DOWN_VOLUME_UP = "price_down_volume_up"  # 价跌量增
    PRICE_DOWN_VOLUME_DOWN = "price_down_volume_down"  # 价跌量缩


class SignalStrength(Enum):
    """信号强度枚举"""
    STRONG = "strong"  # 强信号
    MEDIUM = "medium"  # 中等信号
    WEAK = "weak"  # 弱信号


class DowRuleType(Enum):
    """道氏理论法则类型枚举"""
    RULE_123 = "rule_123"  # 123法则
    RULE_2B = "rule_2b"  # 2B法则


class RuleSignalType(Enum):
    """法则信号类型枚举"""
    TREND_REVERSAL = "trend_reversal"  # 趋势反转
    TREND_CONTINUATION = "trend_continuation"  # 趋势延续
    FALSE_BREAKOUT = "false_breakout"  # 假突破


@dataclass
class TrendLine:
    """趋势线数据结构"""
    start_point: Tuple[datetime, float]  # 起始点 (日期, 价格)
    end_point: Tuple[datetime, float]  # 结束点 (日期, 价格)
    slope: float  # 斜率
    r_squared: float  # 拟合度
    touch_count: int  # 触及次数
    is_valid: bool  # 是否有效
    trend_type: TrendType  # 趋势类型
    direction: TrendDirection  # 趋势方向


@dataclass
class SupportResistance:
    """支撑阻力位数据结构"""
    level: float  # 价格水平
    strength: SignalStrength  # 强度
    touch_count: int  # 触及次数
    last_touch_date: datetime  # 最后触及日期
    trend_type: TrendType  # 对应的时间周期
    level_type: str  # 支撑或阻力 ('support' or 'resistance')


@dataclass
class VolumeAnalysis:
    """成交量分析结果"""
    current_volume: float  # 当前成交量
    avg_volume_20d: float  # 20日平均成交量
    volume_ratio: float  # 成交量比率
    pattern: VolumePattern  # 量价模式
    divergence_signal: bool  # 是否存在背离
    strength: SignalStrength  # 信号强度


@dataclass
class TechnicalIndicators:
    """技术指标数据"""
    ma_20: float  # 20日均线
    ma_60: float  # 60日均线
    ma_250: float  # 250日均线
    macd_dif: float  # MACD DIF值
    macd_dea: float  # MACD DEA值
    macd_histogram: float  # MACD柱状线
    rsi: float  # RSI值
    current_price: float  # 当前价格


@dataclass
class BreakthroughSignal:
    """突破信号数据"""
    breakout_price: float  # 突破价格
    breakout_date: datetime  # 突破日期
    volume_confirmation: bool  # 成交量确认
    price_confirmation: bool  # 价格确认
    time_confirmation: bool  # 时间确认
    breakthrough_type: str  # 突破类型 ('upward' or 'downward')
    trend_type: TrendType  # 突破的时间周期
    strength: SignalStrength  # 突破强度


@dataclass
class Rule123Signal:
    """123法则信号数据"""
    signal_date: datetime  # 信号日期
    signal_price: float  # 信号价格
    trend_line_break: bool  # 趋势线突破
    no_new_extreme: bool  # 不再创新高/新低
    pullback_break: bool  # 回调突破
    signal_strength: SignalStrength  # 信号强度
    reversal_probability: float  # 反转概率 (0-100%)
    target_price: Optional[float]  # 目标价格
    stop_loss_price: Optional[float]  # 止损价格


@dataclass
class Rule2BSignal:
    """2B法则信号数据"""
    signal_date: datetime  # 信号日期
    signal_price: float  # 信号价格
    false_breakout_price: float  # 假突破价格
    breakout_date: datetime  # 突破日期
    reversal_confirmation: bool  # 反转确认
    volume_divergence: bool  # 成交量背离
    signal_strength: SignalStrength  # 信号强度
    reversal_probability: float  # 反转概率 (0-100%)
    target_price: Optional[float]  # 目标价格
    stop_loss_price: Optional[float]  # 止损价格


@dataclass
class DowRulesAnalysis:
    """道氏理论法则分析结果"""
    analysis_date: datetime  # 分析日期
    current_trend: TrendDirection  # 当前趋势
    rule_123_signals: List[Rule123Signal]  # 123法则信号
    rule_2b_signals: List[Rule2BSignal]  # 2B法则信号
    active_signals: List[Union[Rule123Signal, Rule2BSignal]]  # 活跃信号
    overall_signal_strength: SignalStrength  # 整体信号强度
    reversal_probability: float  # 整体反转概率
    trading_recommendation: str  # 交易建议
    key_levels_to_watch: List[float]  # 关键观察位


@dataclass
class TrendAnalysis:
    """单一时间周期趋势分析结果"""
    trend_type: TrendType  # 时间周期类型
    direction: TrendDirection  # 趋势方向
    phase: TrendPhase  # 趋势阶段
    trend_line: Optional[TrendLine]  # 趋势线
    support_resistance: List[SupportResistance]  # 支撑阻力位
    volume_analysis: VolumeAnalysis  # 成交量分析
    technical_indicators: TechnicalIndicators  # 技术指标
    dow_rules_analysis: Optional[DowRulesAnalysis]  # 道氏理论法则分析
    breakthrough_signals: List[BreakthroughSignal]  # 突破信号
    confidence_score: float  # 信心指数 (0-100)
    analysis_date: datetime  # 分析日期


@dataclass
class MultiTimeFrameConfirmation:
    """多时间周期确认结果"""
    primary_secondary_alignment: bool  # 主要趋势与次要趋势一致性
    secondary_minor_alignment: bool  # 次要趋势与短期波动一致性
    overall_alignment: bool  # 整体一致性
    confirmation_strength: SignalStrength  # 确认强度
    conflicting_signals: List[str]  # 冲突信号描述


@dataclass
class RiskAssessment:
    """风险评估结果"""
    risk_level: str  # 风险等级 ('low', 'medium', 'high')
    stop_loss_price: float  # 止损价位
    target_price: float  # 目标价位
    position_suggestion: float  # 建议仓位 (0-100%)
    key_risk_factors: List[str]  # 关键风险因子


@dataclass
class DowTheoryAnalysisResult:
    """道氏理论完整分析结果"""
    stock_code: str  # 股票代码
    stock_name: str  # 股票名称
    analysis_date: datetime  # 分析日期
    current_price: float  # 当前价格
    
    # 各时间周期分析
    monthly_analysis: TrendAnalysis  # 月线分析（主要趋势）
    weekly_analysis: TrendAnalysis  # 周线分析（次要趋势）
    daily_analysis: TrendAnalysis  # 日线分析（短期波动）
    
    # 多重确认
    multi_timeframe_confirmation: MultiTimeFrameConfirmation
    
    # 综合评价
    overall_trend: TrendDirection  # 综合趋势方向
    overall_phase: TrendPhase  # 综合趋势阶段
    overall_confidence: float  # 综合信心指数
    
    # 操作建议
    action_recommendation: str  # 操作建议 ('buy', 'sell', 'hold', 'wait')
    risk_assessment: RiskAssessment
    
    # 关键观察点
    key_levels: List[float]  # 关键价格位
    next_review_date: datetime  # 下次复核日期
    
    # 分析说明
    analysis_summary: str  # 分析摘要
    detailed_analysis: Dict[str, str]  # 详细分析报告


@dataclass
class HistoricalPattern:
    """历史模式数据"""
    pattern_name: str  # 模式名称
    start_date: datetime  # 开始日期
    end_date: datetime  # 结束日期
    pattern_type: str  # 模式类型
    success_rate: float  # 成功率
    similar_conditions: List[str]  # 相似条件


@dataclass
class MarketContext:
    """市场环境数据"""
    market_trend: TrendDirection  # 大盘趋势
    sector_trend: TrendDirection  # 板块趋势
    market_volume: float  # 市场成交量
    market_sentiment: str  # 市场情绪
    correlation_with_market: float  # 与大盘相关性