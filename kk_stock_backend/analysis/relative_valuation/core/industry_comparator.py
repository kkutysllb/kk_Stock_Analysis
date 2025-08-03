"""行业对比分析器"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from statistics import median, mean

from analysis.relative_valuation.models.valuation_models import (
    ValuationMetrics, IndustryComparison
)
from analysis.relative_valuation.core.valuation_calculator import ValuationCalculator
from api.global_db import db_handler

logger = logging.getLogger(__name__)


class IndustryComparator:
    """行业对比分析器
    
    提供个股与行业平均水平的对比分析
    """
    
    def __init__(self):
        """初始化行业对比分析器"""
        self.db_handler = db_handler
        self.valuation_calculator = ValuationCalculator()
        
    def compare_with_industry(self, ts_code: str, end_date: str = None) -> Optional[IndustryComparison]:
        """与行业进行对比分析
        
        Args:
            ts_code: 股票代码
            end_date: 截止日期
            
        Returns:
            IndustryComparison: 行业对比结果
        """
        try:
            # 获取个股估值指标
            stock_metrics = self.valuation_calculator.calculate_valuation_metrics(ts_code, end_date)
            if not stock_metrics:
                logger.warning(f"无法获取股票 {ts_code} 的估值指标")
                return None
                
            # 获取股票所属行业
            industry = self.valuation_calculator.get_stock_industry(ts_code)
            if not industry:
                logger.warning(f"无法获取股票 {ts_code} 的行业信息")
                return None
                
            # 获取同行业股票列表
            industry_stocks = self._get_industry_stocks(industry)
            if len(industry_stocks) < 5:  # 行业样本太少
                logger.warning(f"行业 {industry} 的样本数量不足: {len(industry_stocks)}")
                return None
                
            # 计算行业估值统计数据
            industry_stats = self._calculate_industry_stats(industry_stocks, end_date)
            
            # 计算个股在行业中的百分位
            percentiles = self._calculate_percentiles(stock_metrics, industry_stats)
            
            # 生成估值评级
            ratings = self._generate_ratings(percentiles)
            
            return IndustryComparison(
                ts_code=ts_code,
                industry=industry,
                end_date=end_date or stock_metrics.end_date,
                stock_metrics=stock_metrics,
                industry_pe_median=industry_stats.get('pe_median'),
                industry_pe_mean=industry_stats.get('pe_mean'),
                industry_pe_percentile=percentiles.get('pe_percentile'),
                industry_pb_median=industry_stats.get('pb_median'),
                industry_pb_mean=industry_stats.get('pb_mean'),
                industry_pb_percentile=percentiles.get('pb_percentile'),
                industry_ps_median=industry_stats.get('ps_median'),
                industry_ps_mean=industry_stats.get('ps_mean'),
                industry_ps_percentile=percentiles.get('ps_percentile'),
                industry_sample_count=len(industry_stocks),
                pe_rating=ratings.get('pe_rating'),
                pb_rating=ratings.get('pb_rating'),
                ps_rating=ratings.get('ps_rating'),
                overall_rating=ratings.get('overall_rating')
            )
            
        except Exception as e:
            logger.error(f"行业对比分析失败: {e}")
            return None
    
    def _get_industry_stocks(self, industry: str) -> List[str]:
        """获取同行业股票列表"""
        try:
            stocks = list(self.db_handler.get_collection("infrastructure_stock_basic").find({
                "industry": industry
            }, {"ts_code": 1}))
            
            return [stock["ts_code"] for stock in stocks]
            
        except Exception as e:
            logger.error(f"获取行业股票列表失败: {e}")
            return []
    
    def _calculate_industry_stats(self, industry_stocks: List[str], end_date: str = None) -> Dict:
        """计算行业估值统计数据"""
        pe_values = []
        pb_values = []
        ps_values = []
        
        for ts_code in industry_stocks:
            try:
                metrics = self.valuation_calculator.calculate_valuation_metrics(ts_code, end_date)
                if metrics:
                    if metrics.pe_ratio and 0 < metrics.pe_ratio < 1000:  # 过滤异常值
                        pe_values.append(metrics.pe_ratio)
                    if metrics.pb_ratio and 0 < metrics.pb_ratio < 100:
                        pb_values.append(metrics.pb_ratio)
                    if metrics.ps_ratio and 0 < metrics.ps_ratio < 100:
                        ps_values.append(metrics.ps_ratio)
            except Exception as e:
                logger.debug(f"计算股票 {ts_code} 估值指标失败: {e}")
                continue
        
        stats = {}
        
        # PE统计
        if pe_values:
            stats['pe_median'] = median(pe_values)
            stats['pe_mean'] = mean(pe_values)
            stats['pe_values'] = pe_values
        
        # PB统计
        if pb_values:
            stats['pb_median'] = median(pb_values)
            stats['pb_mean'] = mean(pb_values)
            stats['pb_values'] = pb_values
        
        # PS统计
        if ps_values:
            stats['ps_median'] = median(ps_values)
            stats['ps_mean'] = mean(ps_values)
            stats['ps_values'] = ps_values
        
        return stats
    
    def _calculate_percentiles(self, stock_metrics: ValuationMetrics, industry_stats: Dict) -> Dict:
        """计算个股在行业中的百分位"""
        percentiles = {}
        
        # PE百分位
        if stock_metrics.pe_ratio and 'pe_values' in industry_stats:
            pe_values = industry_stats['pe_values']
            if pe_values:
                percentile = sum(1 for x in pe_values if x <= stock_metrics.pe_ratio) / len(pe_values) * 100
                percentiles['pe_percentile'] = percentile
        
        # PB百分位
        if stock_metrics.pb_ratio and 'pb_values' in industry_stats:
            pb_values = industry_stats['pb_values']
            if pb_values:
                percentile = sum(1 for x in pb_values if x <= stock_metrics.pb_ratio) / len(pb_values) * 100
                percentiles['pb_percentile'] = percentile
        
        # PS百分位
        if stock_metrics.ps_ratio and 'ps_values' in industry_stats:
            ps_values = industry_stats['ps_values']
            if ps_values:
                percentile = sum(1 for x in ps_values if x <= stock_metrics.ps_ratio) / len(ps_values) * 100
                percentiles['ps_percentile'] = percentile
        
        return percentiles
    
    def _generate_ratings(self, percentiles: Dict) -> Dict:
        """生成估值评级"""
        ratings = {}
        
        # PE评级
        if 'pe_percentile' in percentiles:
            pe_pct = percentiles['pe_percentile']
            if pe_pct >= 80:
                ratings['pe_rating'] = '高估'
            elif pe_pct >= 60:
                ratings['pe_rating'] = '偏高'
            elif pe_pct >= 40:
                ratings['pe_rating'] = '合理'
            elif pe_pct >= 20:
                ratings['pe_rating'] = '偏低'
            else:
                ratings['pe_rating'] = '低估'
        
        # PB评级
        if 'pb_percentile' in percentiles:
            pb_pct = percentiles['pb_percentile']
            if pb_pct >= 80:
                ratings['pb_rating'] = '高估'
            elif pb_pct >= 60:
                ratings['pb_rating'] = '偏高'
            elif pb_pct >= 40:
                ratings['pb_rating'] = '合理'
            elif pb_pct >= 20:
                ratings['pb_rating'] = '偏低'
            else:
                ratings['pb_rating'] = '低估'
        
        # PS评级
        if 'ps_percentile' in percentiles:
            ps_pct = percentiles['ps_percentile']
            if ps_pct >= 80:
                ratings['ps_rating'] = '高估'
            elif ps_pct >= 60:
                ratings['ps_rating'] = '偏高'
            elif ps_pct >= 40:
                ratings['ps_rating'] = '合理'
            elif ps_pct >= 20:
                ratings['ps_rating'] = '偏低'
            else:
                ratings['ps_rating'] = '低估'
        
        # 综合评级
        rating_scores = []
        for key in ['pe_percentile', 'pb_percentile', 'ps_percentile']:
            if key in percentiles:
                rating_scores.append(percentiles[key])
        
        if rating_scores:
            avg_percentile = mean(rating_scores)
            if avg_percentile >= 80:
                ratings['overall_rating'] = '高估'
            elif avg_percentile >= 60:
                ratings['overall_rating'] = '偏高'
            elif avg_percentile >= 40:
                ratings['overall_rating'] = '合理'
            elif avg_percentile >= 20:
                ratings['overall_rating'] = '偏低'
            else:
                ratings['overall_rating'] = '低估'
        
        return ratings
    
    def get_industry_top_stocks(self, industry: str, metric: str = 'pe_ratio', 
                               limit: int = 10, end_date: str = None) -> List[Dict]:
        """获取行业内估值指标排名靠前的股票
        
        Args:
            industry: 行业名称
            metric: 排序指标 (pe_ratio, pb_ratio, ps_ratio)
            limit: 返回数量
            end_date: 截止日期
            
        Returns:
            List[Dict]: 排名结果
        """
        try:
            industry_stocks = self._get_industry_stocks(industry)
            stock_metrics = []
            
            for ts_code in industry_stocks:
                metrics = self.valuation_calculator.calculate_valuation_metrics(ts_code, end_date)
                if metrics:
                    metric_value = getattr(metrics, metric, None)
                    if metric_value and 0 < metric_value < 1000:  # 过滤异常值
                        stock_metrics.append({
                            'ts_code': ts_code,
                            'metric_value': metric_value,
                            'metrics': metrics
                        })
            
            # 按指标值排序（升序，估值越低排名越靠前）
            stock_metrics.sort(key=lambda x: x['metric_value'])
            
            return stock_metrics[:limit]
            
        except Exception as e:
            logger.error(f"获取行业排名失败: {e}")
            return []