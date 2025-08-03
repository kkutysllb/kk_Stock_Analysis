#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道氏理论分析核心引擎
实现道氏理论的核心分析逻辑
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from pymongo import MongoClient

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from analysis.dow_theory.models.dow_theory_models import (
    DowTheoryAnalysisResult, TrendAnalysis, TrendDirection, TrendType, 
    TrendPhase, VolumeAnalysis, TechnicalIndicators, MultiTimeFrameConfirmation,
    RiskAssessment, TrendLine, SupportResistance, BreakthroughSignal,
    VolumePattern, SignalStrength
)
from analysis.dow_theory.analyzers.trend_analyzer import TrendAnalyzer
from analysis.dow_theory.analyzers.volume_analyzer import VolumeAnalyzer
from analysis.dow_theory.analyzers.phase_analyzer import PhaseAnalyzer
from analysis.dow_theory.analyzers.technical_analyzer import TechnicalAnalyzer
from analysis.dow_theory.analyzers.dow_rules_analyzer import DowRulesAnalyzer
from analysis.dow_theory.utils.data_fetcher import DataFetcher
from analysis.dow_theory.utils.confirmation_validator import ConfirmationValidator


class DowTheoryEngine:
    """道氏理论分析核心引擎"""
    
    def __init__(self, db_config: Optional[Dict] = None):
        """
        初始化道氏理论分析引擎
        
        Args:
            db_config: 数据库配置
        """
        self.logger = self._setup_logger()
        self.data_fetcher = DataFetcher(db_config)
        self.trend_analyzer = TrendAnalyzer()
        self.volume_analyzer = VolumeAnalyzer()
        self.phase_analyzer = PhaseAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.dow_rules_analyzer = DowRulesAnalyzer()
        self.confirmation_validator = ConfirmationValidator()
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('DowTheoryEngine')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_historical_data(self, stock_code: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        获取股票历史数据用于图表展示
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            包含历史数据的字典
        """
        try:
            # 获取日线数据
            daily_data = self.data_fetcher.get_daily_data(stock_code, start_date, end_date)
            
            if daily_data.empty:
                raise ValueError(f"无法获取股票 {stock_code} 的历史数据")
            
            # 格式化数据，清理NaN值
            formatted_data = {
                "dates": daily_data.index.strftime('%Y-%m-%d').tolist(),
                "prices": {
                    "open": daily_data['open'].fillna(0).round(2).tolist(),
                    "high": daily_data['high'].fillna(0).round(2).tolist(),
                    "low": daily_data['low'].fillna(0).round(2).tolist(),
                    "close": daily_data['close'].fillna(0).round(2).tolist()
                },
                "volume": daily_data['volume'].fillna(0).astype(int).tolist(),
                "technical_indicators": {}
            }
            
            # 计算技术指标
            if len(daily_data) >= 20:
                ma20 = daily_data['close'].rolling(window=20).mean().fillna(0)
                formatted_data["technical_indicators"]["ma20"] = ma20.round(2).tolist()
            
            if len(daily_data) >= 60:
                ma60 = daily_data['close'].rolling(window=60).mean().fillna(0)
                formatted_data["technical_indicators"]["ma60"] = ma60.round(2).tolist()
            
            # 计算RSI
            if len(daily_data) >= 14:
                rsi = self._calculate_rsi(daily_data['close']).fillna(0)
                formatted_data["technical_indicators"]["rsi"] = rsi.round(2).tolist()
            
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"获取股票 {stock_code} 历史数据失败: {e}")
            raise
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def analyze_stock(self, stock_code: str, analysis_date: Optional[datetime] = None) -> DowTheoryAnalysisResult:
        """
        对单只股票进行完整的道氏理论分析
        
        Args:
            stock_code: 股票代码
            analysis_date: 分析日期，默认为当前日期
            
        Returns:
            道氏理论分析结果
        """
        if analysis_date is None:
            analysis_date = datetime.now()
            
        self.logger.info(f"开始分析股票 {stock_code}")
        
        try:
            # 1. 获取多时间周期数据
            stock_data = self._fetch_multi_timeframe_data(stock_code, analysis_date)
            
            return self._perform_analysis(stock_code, stock_data, analysis_date)
            
        except Exception as e:
            self.logger.error(f"分析股票 {stock_code} 失败: {e}")
            raise

    def analyze_stock_range(self, stock_code: str, start_date: datetime, end_date: datetime) -> DowTheoryAnalysisResult:
        """
        对股票在指定时间范围内进行道氏理论分析
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            道氏理论分析结果
        """
        self.logger.info(f"开始分析股票 {stock_code}，时间范围: {start_date.date()} 至 {end_date.date()}")
        
        try:
            # 1. 获取指定时间范围的多时间周期数据
            stock_data = self._fetch_multi_timeframe_data_range(stock_code, start_date, end_date)
            
            return self._perform_analysis(stock_code, stock_data, end_date)
            
        except Exception as e:
            self.logger.error(f"分析股票 {stock_code} 失败: {e}")
            raise

    def _perform_analysis(self, stock_code: str, stock_data: Dict, analysis_date: datetime) -> DowTheoryAnalysisResult:
        """
        执行具体的分析逻辑
        
        Args:
            stock_code: 股票代码
            stock_data: 股票数据
            analysis_date: 分析日期
            
        Returns:
            道氏理论分析结果
        """
        try:
            # 2. 进行各时间周期分析
            monthly_analysis = self._analyze_timeframe(
                stock_data['monthly'], TrendType.PRIMARY, stock_code
            )
            weekly_analysis = self._analyze_timeframe(
                stock_data['weekly'], TrendType.SECONDARY, stock_code
            )
            daily_analysis = self._analyze_timeframe(
                stock_data['daily'], TrendType.MINOR, stock_code
            )
            
            # 3. 多重确认分析
            multi_confirmation = self._validate_multi_timeframe_confirmation(
                monthly_analysis, weekly_analysis, daily_analysis
            )
            
            # 4. 综合评价
            overall_assessment = self._generate_overall_assessment(
                monthly_analysis, weekly_analysis, daily_analysis, multi_confirmation
            )
            
            # 5. 风险评估和操作建议
            risk_assessment = self._assess_risk(
                stock_data, monthly_analysis, weekly_analysis, daily_analysis
            )
            
            # 6. 生成分析报告
            analysis_result = self._compile_analysis_result(
                stock_code, analysis_date, stock_data,
                monthly_analysis, weekly_analysis, daily_analysis,
                multi_confirmation, overall_assessment, risk_assessment
            )
            
            self.logger.info(f"完成股票 {stock_code} 分析")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"分析股票 {stock_code} 时发生错误: {e}")
            raise
    
    def _fetch_multi_timeframe_data(self, stock_code: str, analysis_date: datetime) -> Dict[str, pd.DataFrame]:
        """获取多时间周期数据"""
        self.logger.info(f"获取股票 {stock_code} 的多时间周期数据")
        
        # 计算数据范围
        end_date = analysis_date
        start_date = end_date - timedelta(days=1000)  # 获取足够的历史数据
        
        # 获取各时间周期数据
        daily_data = self.data_fetcher.get_daily_data(stock_code, start_date, end_date)
        weekly_data = self.data_fetcher.get_weekly_data(stock_code, start_date, end_date)
        monthly_data = self.data_fetcher.get_monthly_data(stock_code, start_date, end_date)
        
        # 获取技术因子数据
        factor_data = self.data_fetcher.get_factor_data(stock_code, start_date, end_date)
        
        return {
            'daily': daily_data,
            'weekly': weekly_data,
            'monthly': monthly_data,
            'factors': factor_data
        }
    
    def _fetch_multi_timeframe_data_range(self, stock_code: str, start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        """获取指定时间范围的多时间周期数据"""
        self.logger.info(f"获取股票 {stock_code} 在时间范围 {start_date.date()} 至 {end_date.date()} 的多时间周期数据")
        
        # 获取各时间周期数据
        daily_data = self.data_fetcher.get_daily_data(stock_code, start_date, end_date)
        weekly_data = self.data_fetcher.get_weekly_data(stock_code, start_date, end_date)
        monthly_data = self.data_fetcher.get_monthly_data(stock_code, start_date, end_date)
        
        # 获取技术因子数据
        factor_data = self.data_fetcher.get_factor_data(stock_code, start_date, end_date)
        
        return {
            'daily': daily_data,
            'weekly': weekly_data,
            'monthly': monthly_data,
            'factors': factor_data
        }
    
    def _analyze_timeframe(self, data: pd.DataFrame, trend_type: TrendType, stock_code: str) -> TrendAnalysis:
        """分析单一时间周期"""
        self.logger.debug(f"分析 {trend_type.value} 时间周期")
        
        if data.empty:
            raise ValueError(f"数据为空，无法进行 {trend_type.value} 分析")
        
        # 趋势分析
        trend_direction, trend_line = self.trend_analyzer.analyze_trend(data, trend_type)
        
        # 支撑阻力位分析
        support_resistance = self.trend_analyzer.identify_support_resistance(data, trend_type)
        
        # 成交量分析
        volume_analysis = self.volume_analyzer.analyze_volume_pattern(data)
        
        # 技术指标分析
        technical_indicators = self.technical_analyzer.calculate_indicators(data)
        
        # 趋势阶段识别
        trend_phase = self.phase_analyzer.identify_phase(data, trend_direction, volume_analysis)
        
        # 道氏理论123法则和2B法则分析
        try:
            # 分别执行123法则和2B法则分析
            try:
                self.logger.debug(f"开始123法则分析，数据长度: {len(data)}")
                rule_123_result = self.dow_rules_analyzer.analyze_123_rule(data)
                self.logger.debug("123法则分析完成")
            except Exception as e123:
                self.logger.error(f"123法则分析失败: {e123}")
                import traceback
                self.logger.error(f"123法则分析异常详情: {traceback.format_exc()}")
                raise e123
            
            try:
                self.logger.debug(f"开始2B法则分析，数据长度: {len(data)}")
                rule_2b_result = self.dow_rules_analyzer.analyze_2b_rule(data)
                self.logger.debug("2B法则分析完成")
            except Exception as e2b:
                self.logger.error(f"2B法则分析失败: {e2b}")
                import traceback
                self.logger.error(f"2B法则分析异常详情: {traceback.format_exc()}")
                raise e2b
            
            # 创建综合的道氏法则分析结果
            from ..models.dow_theory_models import DowRulesAnalysis, SignalStrength
            dow_rules_analysis = DowRulesAnalysis(
                analysis_date=datetime.now(),
                current_trend=trend_direction,
                rule_123_signals=[],  # 简化处理，实际应该从结果中提取
                rule_2b_signals=[],   # 简化处理，实际应该从结果中提取
                active_signals=[],
                overall_signal_strength=SignalStrength.MEDIUM,
                reversal_probability=0.5,
                trading_recommendation="观望",
                key_levels_to_watch=[]
            )
            # 确保道氏法则分析结果可以JSON序列化
            dow_rules_analysis = self._make_json_serializable(dow_rules_analysis)
        except Exception as e:
            self.logger.error(f"道氏法则分析失败: {e}")
            # 创建空的分析结果
            from ..models.dow_theory_models import DowRulesAnalysis, SignalStrength
            dow_rules_analysis = DowRulesAnalysis(
                analysis_date=datetime.now(),
                current_trend=trend_direction,
                rule_123_signals=[],
                rule_2b_signals=[],
                active_signals=[],
                overall_signal_strength=SignalStrength.WEAK,
                reversal_probability=0.0,
                trading_recommendation="数据不足",
                key_levels_to_watch=[]
            )
            # 确保道氏法则分析结果可以JSON序列化
            dow_rules_analysis = self._make_json_serializable(dow_rules_analysis)
        
        # 突破信号检测
        breakthrough_signals = self.trend_analyzer.detect_breakthrough_signals(
            data, support_resistance, volume_analysis
        )
        
        # 计算信心指数
        confidence_score = self._calculate_confidence_score(
            trend_direction, trend_line, volume_analysis, technical_indicators
        )
        
        return TrendAnalysis(
            trend_type=trend_type,
            direction=trend_direction,
            phase=trend_phase,
            trend_line=trend_line,
            support_resistance=support_resistance,
            volume_analysis=volume_analysis,
            technical_indicators=technical_indicators,
            dow_rules_analysis=dow_rules_analysis,
            breakthrough_signals=breakthrough_signals,
            confidence_score=confidence_score,
            analysis_date=datetime.now()
        )
    
    def _validate_multi_timeframe_confirmation(
        self, 
        monthly: TrendAnalysis, 
        weekly: TrendAnalysis, 
        daily: TrendAnalysis
    ) -> MultiTimeFrameConfirmation:
        """验证多时间周期确认"""
        return self.confirmation_validator.validate_confirmation(monthly, weekly, daily)
    
    def _generate_overall_assessment(
        self,
        monthly: TrendAnalysis,
        weekly: TrendAnalysis,
        daily: TrendAnalysis,
        confirmation: MultiTimeFrameConfirmation
    ) -> Dict[str, Any]:
        """生成综合评价"""
        # 综合趋势方向（优先级：月线 > 周线 > 日线）
        if confirmation.overall_alignment:
            overall_trend = monthly.direction
        else:
            # 权重分配：月线50%，周线30%，日线20%
            trend_scores = {
                TrendDirection.UPWARD: 0,
                TrendDirection.DOWNWARD: 0,
                TrendDirection.SIDEWAYS: 0
            }
            
            trend_scores[monthly.direction] += 0.5 * monthly.confidence_score
            trend_scores[weekly.direction] += 0.3 * weekly.confidence_score
            trend_scores[daily.direction] += 0.2 * daily.confidence_score
            
            overall_trend = max(trend_scores, key=trend_scores.get)
        
        # 综合趋势阶段
        overall_phase = monthly.phase  # 以月线为准
        
        # 综合信心指数
        overall_confidence = (
            monthly.confidence_score * 0.5 +
            weekly.confidence_score * 0.3 +
            daily.confidence_score * 0.2
        )
        
        # 调整信心指数（如果存在分歧则降低）
        if not confirmation.overall_alignment:
            overall_confidence *= 0.7
        
        return {
            'overall_trend': overall_trend,
            'overall_phase': overall_phase,
            'overall_confidence': overall_confidence
        }
    
    def _assess_risk(
        self,
        stock_data: Dict[str, pd.DataFrame],
        monthly: TrendAnalysis,
        weekly: TrendAnalysis,
        daily: TrendAnalysis
    ) -> RiskAssessment:
        """风险评估"""
        current_price = stock_data['daily'].iloc[-1]['close']
        
        # 确定风险等级
        risk_factors = []
        risk_score = 0
        
        # 基于趋势一致性评估风险
        if monthly.direction != weekly.direction:
            risk_factors.append("月线和周线趋势不一致")
            risk_score += 30
            
        if weekly.direction != daily.direction:
            risk_factors.append("周线和日线趋势不一致")
            risk_score += 20
        
        # 基于成交量分析评估风险
        if monthly.volume_analysis.divergence_signal:
            risk_factors.append("存在量价背离信号")
            risk_score += 25
        
        # 基于技术指标评估风险
        if monthly.technical_indicators.rsi > 80:
            risk_factors.append("RSI超买")
            risk_score += 15
        elif monthly.technical_indicators.rsi < 20:
            risk_factors.append("RSI超卖")
            risk_score += 10
        
        # 确定风险等级
        if risk_score <= 20:
            risk_level = "low"
        elif risk_score <= 50:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # 计算止损位和目标位
        stop_loss_price = self._calculate_stop_loss(current_price, monthly, weekly, daily)
        target_price = self._calculate_target_price(current_price, monthly, weekly, daily)
        
        # 验证价格关系的合理性
        if stop_loss_price >= target_price:
            self.logger.warning(f"检测到异常价格关系: stop_loss={stop_loss_price:.2f}, target={target_price:.2f}, current={current_price:.2f}")
            # 修正价格关系
            if monthly.direction == TrendDirection.UPWARD:
                # 上升趋势：确保目标价 > 当前价 > 止损价
                target_price = max(target_price, current_price * 1.05)
                stop_loss_price = min(stop_loss_price, current_price * 0.95)
            else:
                # 下降趋势：调整为反弹目标
                target_price = min(target_price, current_price * 1.03)
                stop_loss_price = min(stop_loss_price, current_price * 0.92)
        
        # 最终验证
        if stop_loss_price >= target_price:
            # 强制修正
            if monthly.direction == TrendDirection.UPWARD:
                target_price = current_price * 1.08
                stop_loss_price = current_price * 0.92
            else:
                target_price = current_price * 1.03
                stop_loss_price = current_price * 0.90
        
        # 建议仓位
        if risk_level == "low" and monthly.direction == TrendDirection.UPWARD:
            position_suggestion = 80.0
        elif risk_level == "medium":
            position_suggestion = 50.0
        elif risk_level == "high":
            position_suggestion = 20.0
        else:
            position_suggestion = 30.0
        
        return RiskAssessment(
            risk_level=risk_level,
            stop_loss_price=stop_loss_price,
            target_price=target_price,
            position_suggestion=position_suggestion,
            key_risk_factors=risk_factors
        )
    
    def _calculate_stop_loss(
        self, 
        current_price: float, 
        monthly: TrendAnalysis, 
        weekly: TrendAnalysis, 
        daily: TrendAnalysis
    ) -> float:
        """计算止损位"""
        # 基于多时间周期支撑位设置止损
        support_levels = []
        
        # 收集各时间周期的支撑位，按权重排序（日线->周线->月线）
        weighted_supports = []
        for analysis, weight in [(daily, 0.5), (weekly, 0.3), (monthly, 0.2)]:
            for sr in analysis.support_resistance:
                if sr.level_type == 'support' and sr.level < current_price:
                    # 转换强度为数值
                    strength_value = 1
                    if hasattr(sr.strength, 'value'):
                        if sr.strength.value == 'strong':
                            strength_value = 3
                        elif sr.strength.value == 'medium':
                            strength_value = 2
                        elif sr.strength.value == 'weak':
                            strength_value = 1
                    
                    weighted_supports.append({
                        'level': sr.level,
                        'weight': weight,
                        'strength': strength_value
                    })
        
        if weighted_supports:
            # 选择最近的强支撑位（距离当前价格最近且强度高的）
            weighted_supports.sort(key=lambda x: (current_price - x['level'], -x['strength']))
            stop_loss = weighted_supports[0]['level']
            # 留一定安全边际
            stop_loss *= 0.98
        else:
            # 默认以8%作为止损（更合理的比例）
            stop_loss = current_price * 0.92
        
        # 确保止损价在合理范围内
        min_stop_loss = current_price * 0.85  # 最大止损15%
        max_stop_loss = current_price * 0.98  # 最小止损2%
        stop_loss = max(min_stop_loss, min(stop_loss, max_stop_loss))
        
        return stop_loss
    
    def _calculate_target_price(
        self, 
        current_price: float, 
        monthly: TrendAnalysis, 
        weekly: TrendAnalysis, 
        daily: TrendAnalysis
    ) -> float:
        """计算目标价位"""
        # 基于阻力位和趋势强度计算目标价
        
        # 收集各时间周期的阻力位，按权重排序
        weighted_resistances = []
        for analysis, weight in [(daily, 0.5), (weekly, 0.3), (monthly, 0.2)]:
            for sr in analysis.support_resistance:
                if sr.level_type == 'resistance' and sr.level > current_price:
                    # 转换强度为数值
                    strength_value = 1
                    if hasattr(sr.strength, 'value'):
                        if sr.strength.value == 'strong':
                            strength_value = 3
                        elif sr.strength.value == 'medium':
                            strength_value = 2
                        elif sr.strength.value == 'weak':
                            strength_value = 1
                    
                    weighted_resistances.append({
                        'level': sr.level,
                        'weight': weight,
                        'strength': strength_value
                    })
        
        # 根据整体趋势方向确定目标价
        if monthly.direction == TrendDirection.UPWARD:
            # 上升趋势：寻找合适的阻力位作为目标
            if weighted_resistances:
                # 选择最近的强阻力位
                weighted_resistances.sort(key=lambda x: (x['level'] - current_price, -x['strength']))
                target_price = weighted_resistances[0]['level']
            else:
                # 基于趋势强度设定目标：5%-25%的上涨空间
                multiplier = 1.05 + (monthly.confidence_score / 100) * 0.2
                target_price = current_price * multiplier
        elif monthly.direction == TrendDirection.DOWNWARD:
            # 下降趋势：目标价应该是支撑位，用于反弹交易
            support_levels = []
            for analysis in [monthly, weekly, daily]:
                for sr in analysis.support_resistance:
                    if sr.level_type == 'support' and sr.level < current_price:
                        support_levels.append(sr.level)
            
            if support_levels:
                # 选择最近的支撑位作为反弹目标
                target_price = max(support_levels)
            else:
                # 保守估计：轻微反弹
                target_price = current_price * 1.03
        else:
            # 横盘趋势：基于波动区间设定目标
            if weighted_resistances:
                target_price = min(weighted_resistances, key=lambda x: x['level'] - current_price)['level']
            else:
                # 横盘时保守目标：3%-8%
                multiplier = 1.03 + (monthly.confidence_score / 100) * 0.05
                target_price = current_price * multiplier
        
        # 确保目标价在合理范围内
        min_target = current_price * 1.02  # 最小2%收益
        max_target = current_price * 1.50  # 最大50%收益
        target_price = max(min_target, min(target_price, max_target))
        
        return target_price
    
    def _calculate_confidence_score(
        self,
        trend_direction: TrendDirection,
        trend_line: Optional[TrendLine],
        volume_analysis: VolumeAnalysis,
        technical_indicators: TechnicalIndicators
    ) -> float:
        """计算信心指数"""
        score = 50  # 基础分数
        
        # 趋势线质量加分
        if trend_line and trend_line.is_valid:
            score += trend_line.r_squared * 20  # R²越高加分越多
            score += min(trend_line.touch_count * 5, 20)  # 触及次数加分
        
        # 成交量确认加分
        if volume_analysis.pattern in [VolumePattern.PRICE_UP_VOLUME_UP, VolumePattern.PRICE_DOWN_VOLUME_DOWN]:
            score += 15
        elif volume_analysis.divergence_signal:
            score -= 20
        
        # 技术指标加分
        current_price = technical_indicators.current_price
        if current_price > technical_indicators.ma_20 > technical_indicators.ma_60:
            score += 10
        elif current_price < technical_indicators.ma_20 < technical_indicators.ma_60:
            score += 10
        
        # 趋势方向确认加分
        if trend_direction == TrendDirection.UPWARD and technical_indicators.macd_dif > 0:
            score += 5
        elif trend_direction == TrendDirection.DOWNWARD and technical_indicators.macd_dif < 0:
            score += 5
        
        # MACD确认
        if technical_indicators.macd_dif > technical_indicators.macd_dea:
            score += 5
        
        return max(0, min(100, score))
    
    def _compile_analysis_result(
        self,
        stock_code: str,
        analysis_date: datetime,
        stock_data: Dict[str, pd.DataFrame],
        monthly: TrendAnalysis,
        weekly: TrendAnalysis,
        daily: TrendAnalysis,
        multi_confirmation: MultiTimeFrameConfirmation,
        overall_assessment: Dict[str, Any],
        risk_assessment: RiskAssessment
    ) -> DowTheoryAnalysisResult:
        """编译最终分析结果"""
        
        current_price = stock_data['daily'].iloc[-1]['close']
        
        # 生成操作建议
        action_recommendation = self._generate_action_recommendation(
            overall_assessment, multi_confirmation, risk_assessment
        )
        
        # 生成关键价格位
        key_levels = self._extract_key_levels(monthly, weekly, daily)
        
        # 生成分析摘要
        analysis_summary = self._generate_analysis_summary(
            overall_assessment, multi_confirmation, action_recommendation
        )
        
        # 生成详细分析报告
        detailed_analysis = self._generate_detailed_analysis(
            monthly, weekly, daily, multi_confirmation
        )
        
        result = DowTheoryAnalysisResult(
            stock_code=stock_code,
            stock_name=self._get_stock_name(stock_code),
            analysis_date=analysis_date,
            current_price=current_price,
            monthly_analysis=monthly,
            weekly_analysis=weekly,
            daily_analysis=daily,
            multi_timeframe_confirmation=multi_confirmation,
            overall_trend=overall_assessment['overall_trend'],
            overall_phase=overall_assessment['overall_phase'],
            overall_confidence=overall_assessment['overall_confidence'],
            action_recommendation=action_recommendation,
            risk_assessment=risk_assessment,
            key_levels=key_levels,
            next_review_date=analysis_date + timedelta(days=7),
            analysis_summary=analysis_summary,
            detailed_analysis=detailed_analysis
        )
        
        # 返回原始对象，JSON序列化在API层处理
        return result
    
    def _generate_action_recommendation(
        self,
        overall_assessment: Dict[str, Any],
        multi_confirmation: MultiTimeFrameConfirmation,
        risk_assessment: RiskAssessment
    ) -> str:
        """生成操作建议"""
        trend = overall_assessment['overall_trend']
        confidence = overall_assessment['overall_confidence']
        risk_level = risk_assessment.risk_level
        
        if trend == TrendDirection.UPWARD and confidence > 70 and risk_level in ['low', 'medium']:
            return 'buy'
        elif trend == TrendDirection.DOWNWARD and confidence > 70:
            return 'sell'
        elif multi_confirmation.overall_alignment and confidence > 60:
            return 'hold'
        else:
            return 'wait'
    
    def _extract_key_levels(self, monthly: TrendAnalysis, weekly: TrendAnalysis, daily: TrendAnalysis) -> List[float]:
        """提取关键价格位"""
        key_levels = []
        
        # 收集所有支撑阻力位
        for analysis in [monthly, weekly, daily]:
            for sr in analysis.support_resistance:
                if sr.strength in [SignalStrength.STRONG, SignalStrength.MEDIUM]:
                    key_levels.append(sr.level)
        
        # 去重并排序
        key_levels = sorted(list(set(key_levels)))
        
        return key_levels
    
    def _generate_analysis_summary(
        self,
        overall_assessment: Dict[str, Any],
        multi_confirmation: MultiTimeFrameConfirmation,
        action_recommendation: str
    ) -> str:
        """生成分析摘要"""
        trend = overall_assessment['overall_trend']
        phase = overall_assessment['overall_phase']
        confidence = overall_assessment['overall_confidence']
        
        summary = f"综合趋势：{trend.value}，"
        summary += f"当前阶段：{phase.value}，"
        summary += f"信心指数：{confidence:.1f}%。"
        
        if multi_confirmation.overall_alignment:
            summary += "多时间周期趋势一致，信号较为可靠。"
        else:
            summary += "多时间周期存在分歧，需谨慎操作。"
        
        summary += f"建议操作：{action_recommendation}。"
        
        return summary
    
    def _generate_detailed_analysis(
        self,
        monthly: TrendAnalysis,
        weekly: TrendAnalysis,
        daily: TrendAnalysis,
        multi_confirmation: MultiTimeFrameConfirmation
    ) -> Dict[str, str]:
        """生成详细分析报告"""
        return {
            'monthly_analysis': self._format_timeframe_analysis(monthly, "月线"),
            'weekly_analysis': self._format_timeframe_analysis(weekly, "周线"),
            'daily_analysis': self._format_timeframe_analysis(daily, "日线"),
            'confirmation_analysis': self._format_confirmation_analysis(multi_confirmation)
        }
    
    def _format_timeframe_analysis(self, analysis: TrendAnalysis, timeframe_name: str) -> str:
        """格式化时间周期分析"""
        report = f"{timeframe_name}分析：\n"
        report += f"趋势方向：{analysis.direction.value}\n"
        report += f"趋势阶段：{analysis.phase.value}\n"
        report += f"信心指数：{analysis.confidence_score:.1f}%\n"
        
        if analysis.support_resistance:
            support_levels = [sr.level for sr in analysis.support_resistance if sr.level_type == 'support']
            resistance_levels = [sr.level for sr in analysis.support_resistance if sr.level_type == 'resistance']
            
            if support_levels:
                report += f"支撑位：{', '.join([f'{level:.2f}' for level in support_levels])}\n"
            if resistance_levels:
                report += f"阻力位：{', '.join([f'{level:.2f}' for level in resistance_levels])}\n"
        
        return report
    
    def _format_confirmation_analysis(self, confirmation: MultiTimeFrameConfirmation) -> str:
        """格式化确认分析"""
        report = "多时间周期确认分析：\n"
        report += f"主要趋势与次要趋势一致性：{'是' if confirmation.primary_secondary_alignment else '否'}\n"
        report += f"次要趋势与短期波动一致性：{'是' if confirmation.secondary_minor_alignment else '否'}\n"
        report += f"整体一致性：{'是' if confirmation.overall_alignment else '否'}\n"
        report += f"确认强度：{confirmation.confirmation_strength.value}\n"
        
        if confirmation.conflicting_signals:
            report += f"冲突信号：{', '.join(confirmation.conflicting_signals)}\n"
        
        return report
    
    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        try:
            stock_basic = self.data_fetcher.get_stock_basic_info(stock_code)
            return stock_basic.get('name', stock_code)
        except:
            return stock_code
    
    def _make_json_serializable(self, obj, visited=None):
        """将对象转换为JSON可序列化的格式，防止循环引用"""
        if visited is None:
            visited = set()
        
        # 防止循环引用
        obj_id = id(obj)
        if obj_id in visited:
            return "<circular reference>"
        
        # 处理基本类型
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        elif hasattr(obj, 'value'):  # 处理枚举类型 - 提前检查
            return obj.value
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat() if obj else None
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (pd.Series, pd.DataFrame)):
            if obj.empty:
                return [] if isinstance(obj, pd.Series) else {}
            return obj.to_dict() if isinstance(obj, pd.Series) else obj.to_dict('records')
        elif hasattr(obj, '__len__') and len(obj) == 0:
            # 处理空的可迭代对象
            return None
        else:
            # 安全地检查pd.isna，只对标量值使用
            try:
                if pd.isna(obj):
                    return None
            except (ValueError, TypeError):
                # 如果pd.isna失败，跳过这个检查
                pass
        
        # 对于复杂对象，加入访问集合
        visited.add(obj_id)
        
        try:
            if isinstance(obj, list):
                result = [self._make_json_serializable(item, visited) for item in obj]
            elif isinstance(obj, dict):
                result = {key: self._make_json_serializable(value, visited) for key, value in obj.items()}
            elif hasattr(obj, '__dict__'):
                result = {}
                for key, value in obj.__dict__.items():
                    # 跳过私有属性和特殊属性
                    if not key.startswith('_'):
                        result[key] = self._make_json_serializable(value, visited)
            else:
                result = str(obj)
        finally:
            # 处理完后从访问集合中移除
            visited.discard(obj_id)
        
        return result