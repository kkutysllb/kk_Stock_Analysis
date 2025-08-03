"""相对估值综合分析器"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from analysis.relative_valuation.models.valuation_models import (
    RelativeValuationResult, ValuationTrend
)
from analysis.relative_valuation.core.valuation_calculator import ValuationCalculator
from analysis.relative_valuation.core.industry_comparator import IndustryComparator
from analysis.relative_valuation.core.historical_analyzer import HistoricalAnalyzer
from api.global_db import db_handler

logger = logging.getLogger(__name__)


class RelativeValuationAnalyzer:
    """相对估值综合分析器
    
    整合估值计算、行业对比、历史分析等功能
    """
    
    def __init__(self):
        """初始化相对估值分析器"""
        self.db_handler = db_handler
        self.valuation_calculator = ValuationCalculator()
        self.industry_comparator = IndustryComparator()
        self.historical_analyzer = HistoricalAnalyzer()
        
    def analyze_stock_valuation(self, ts_code: str, end_date: str = None) -> Optional[RelativeValuationResult]:
        """综合分析个股相对估值
        
        Args:
            ts_code: 股票代码
            end_date: 截止日期
            
        Returns:
            RelativeValuationResult: 综合分析结果
        """
        try:
            # 获取股票基本信息
            stock_info = self._get_stock_info(ts_code)
            if not stock_info:
                logger.warning(f"无法获取股票 {ts_code} 的基本信息")
                return None
                
            # 计算当前估值指标
            current_metrics = self.valuation_calculator.calculate_valuation_metrics(ts_code, end_date)
            if not current_metrics:
                logger.warning(f"无法计算股票 {ts_code} 的估值指标")
                return None
                
            # 行业对比分析
            industry_comparison = self.industry_comparator.compare_with_industry(ts_code, end_date)
            if not industry_comparison:
                logger.warning(f"无法进行股票 {ts_code} 的行业对比分析")
                return None
                
            # 历史估值分析
            historical_analysis = self.historical_analyzer.analyze_historical_valuation(ts_code, end_date)
            if not historical_analysis:
                logger.warning(f"无法进行股票 {ts_code} 的历史估值分析")
                return None
                
            # 生成综合评级
            overall_rating, rating_score = self._generate_overall_rating(
                industry_comparison, historical_analysis
            )
            
            # 生成投资建议
            investment_advice = self._generate_investment_advice(overall_rating, rating_score)
            
            # 生成风险提示
            risk_warnings = self._generate_risk_warnings(
                current_metrics, industry_comparison, historical_analysis
            )
            
            # 生成分析摘要
            analysis_summary = self._generate_analysis_summary(
                stock_info, current_metrics, industry_comparison, 
                historical_analysis, overall_rating
            )
            
            return RelativeValuationResult(
                ts_code=ts_code,
                stock_name=stock_info.get('name', ''),
                industry=stock_info.get('industry', ''),
                analysis_date=end_date or datetime.now().strftime('%Y%m%d'),
                current_metrics=current_metrics,
                industry_comparison=industry_comparison,
                historical_analysis=historical_analysis,
                overall_rating=overall_rating,
                rating_score=rating_score,
                investment_advice=investment_advice,
                risk_warnings=risk_warnings,
                analysis_summary=analysis_summary
            )
            
        except Exception as e:
            logger.error(f"相对估值分析失败: {e}")
            return None
    
    def get_valuation_trend(self, ts_code: str, days: int = 252) -> Optional[ValuationTrend]:
        """获取估值趋势分析
        
        Args:
            ts_code: 股票代码
            days: 分析天数
            
        Returns:
            ValuationTrend: 趋势分析结果
        """
        try:
            trend_data = self.historical_analyzer.get_valuation_trend(ts_code, days)
            if not trend_data:
                return None
                
            return ValuationTrend(
                ts_code=ts_code,
                pe_trend=trend_data.get('pe_trend', {}).get('direction', '数据不足'),
                pb_trend=trend_data.get('pb_trend', {}).get('direction', '数据不足'),
                ps_trend=trend_data.get('ps_trend', {}).get('direction', '数据不足'),
                pe_trend_strength=trend_data.get('pe_trend', {}).get('strength', 0.0),
                pb_trend_strength=trend_data.get('pb_trend', {}).get('strength', 0.0),
                ps_trend_strength=trend_data.get('ps_trend', {}).get('strength', 0.0),
                pe_trend_duration=trend_data.get('pe_trend', {}).get('duration', 0),
                pb_trend_duration=trend_data.get('pb_trend', {}).get('duration', 0),
                ps_trend_duration=trend_data.get('ps_trend', {}).get('duration', 0)
            )
            
        except Exception as e:
            logger.error(f"获取估值趋势失败: {e}")
            return None
    
    def batch_analyze_stocks(self, ts_codes: List[str], end_date: str = None) -> Dict[str, RelativeValuationResult]:
        """批量分析多只股票的相对估值
        
        Args:
            ts_codes: 股票代码列表
            end_date: 截止日期
            
        Returns:
            Dict[str, RelativeValuationResult]: 分析结果字典
        """
        results = {}
        
        for ts_code in ts_codes:
            try:
                result = self.analyze_stock_valuation(ts_code, end_date)
                if result:
                    results[ts_code] = result
                else:
                    logger.warning(f"股票 {ts_code} 分析失败")
            except Exception as e:
                logger.error(f"分析股票 {ts_code} 时出错: {e}")
                continue
                
        return results
    
    def _get_stock_info(self, ts_code: str) -> Optional[Dict]:
        """获取股票基本信息"""
        try:
            stock_basic = list(self.db_handler.get_collection("infrastructure_stock_basic").find({
                "ts_code": ts_code
            }).limit(1))
            
            if stock_basic:
                return stock_basic[0]
            return None
            
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            return None
    
    def _generate_overall_rating(self, industry_comparison, historical_analysis) -> tuple:
        """生成综合评级"""
        scores = []
        
        # 行业对比评分
        industry_scores = []
        if industry_comparison.industry_pe_percentile:
            industry_scores.append(industry_comparison.industry_pe_percentile)
        if industry_comparison.industry_pb_percentile:
            industry_scores.append(industry_comparison.industry_pb_percentile)
        if industry_comparison.industry_ps_percentile:
            industry_scores.append(industry_comparison.industry_ps_percentile)
            
        if industry_scores:
            industry_avg = sum(industry_scores) / len(industry_scores)
            scores.append(industry_avg)
        
        # 历史对比评分（使用3年数据）
        historical_scores = []
        if historical_analysis.pe_percentile_3y:
            historical_scores.append(historical_analysis.pe_percentile_3y)
        if historical_analysis.pb_percentile_3y:
            historical_scores.append(historical_analysis.pb_percentile_3y)
        if historical_analysis.ps_percentile_3y:
            historical_scores.append(historical_analysis.ps_percentile_3y)
            
        if historical_scores:
            historical_avg = sum(historical_scores) / len(historical_scores)
            scores.append(historical_avg)
        
        # 计算综合评分
        if scores:
            rating_score = sum(scores) / len(scores)
        else:
            rating_score = 50.0  # 默认中性评分
        
        # 生成评级
        if rating_score >= 90:
            overall_rating = '严重高估'
        elif rating_score >= 75:
            overall_rating = '高估'
        elif rating_score >= 60:
            overall_rating = '偏高'
        elif rating_score >= 40:
            overall_rating = '合理'
        elif rating_score >= 25:
            overall_rating = '偏低'
        elif rating_score >= 10:
            overall_rating = '低估'
        else:
            overall_rating = '严重低估'
        
        return overall_rating, rating_score
    
    def _generate_investment_advice(self, overall_rating: str, rating_score: float) -> str:
        """生成投资建议"""
        advice_map = {
            '严重高估': '建议回避，估值过高，存在较大回调风险',
            '高估': '谨慎持有，可考虑减仓，等待更好买入时机',
            '偏高': '中性观点，可适量持有，关注基本面变化',
            '合理': '可以持有，估值相对合理，关注业绩增长',
            '偏低': '可以考虑买入，估值偏低，具有一定安全边际',
            '低估': '建议买入，估值较低，具有较好投资价值',
            '严重低估': '强烈建议买入，估值严重偏低，投资机会较好'
        }
        
        return advice_map.get(overall_rating, '数据不足，建议谨慎投资')
    
    def _generate_risk_warnings(self, current_metrics, industry_comparison, historical_analysis) -> List[str]:
        """生成风险提示"""
        warnings = []
        
        # 估值风险
        if industry_comparison.industry_pe_percentile and industry_comparison.industry_pe_percentile > 80:
            warnings.append('市盈率在行业中处于高位，存在估值回调风险')
        
        if historical_analysis.pe_percentile_3y and historical_analysis.pe_percentile_3y > 85:
            warnings.append('当前估值接近历史高位，需关注估值风险')
        
        # 财务风险
        if current_metrics.pe_ratio and current_metrics.pe_ratio > 100:
            warnings.append('市盈率过高，盈利能力需要关注')
        
        if current_metrics.pb_ratio and current_metrics.pb_ratio > 10:
            warnings.append('市净率较高，资产质量需要关注')
        
        # 行业风险
        if industry_comparison.industry_sample_count < 10:
            warnings.append('行业样本数量较少，对比结果可能存在偏差')
        
        return warnings
    
    def _generate_analysis_summary(self, stock_info, current_metrics, 
                                 industry_comparison, historical_analysis, overall_rating) -> str:
        """生成分析摘要"""
        summary_parts = []
        
        # 基本信息
        stock_name = stock_info.get('name', '')
        industry = stock_info.get('industry', '')
        summary_parts.append(f"{stock_name}({current_metrics.ts_code})属于{industry}行业")
        
        # 当前估值
        if current_metrics.pe_ratio:
            summary_parts.append(f"当前市盈率{current_metrics.pe_ratio:.2f}倍")
        if current_metrics.pb_ratio:
            summary_parts.append(f"市净率{current_metrics.pb_ratio:.2f}倍")
        
        # 行业对比
        if industry_comparison.overall_rating:
            summary_parts.append(f"行业对比评级为{industry_comparison.overall_rating}")
        
        # 历史对比
        if historical_analysis.historical_rating_3y:
            summary_parts.append(f"3年历史估值水平为{historical_analysis.historical_rating_3y}")
        
        # 综合评级
        summary_parts.append(f"综合评级为{overall_rating}")
        
        return "，".join(summary_parts) + "。"