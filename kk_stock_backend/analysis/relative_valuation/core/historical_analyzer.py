"""历史估值分析器"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from statistics import median, mean

from analysis.relative_valuation.models.valuation_models import (
    ValuationMetrics, HistoricalValuation
)
from analysis.relative_valuation.core.valuation_calculator import ValuationCalculator
from api.global_db import db_handler

logger = logging.getLogger(__name__)


class HistoricalAnalyzer:
    """历史估值分析器
    
    分析个股历史估值水平和趋势
    """
    
    def __init__(self):
        """初始化历史估值分析器"""
        self.db_handler = db_handler
        self.valuation_calculator = ValuationCalculator()
        
    def analyze_historical_valuation(self, ts_code: str, end_date: str = None) -> Optional[HistoricalValuation]:
        """分析历史估值水平
        
        Args:
            ts_code: 股票代码
            end_date: 截止日期
            
        Returns:
            HistoricalValuation: 历史估值分析结果
        """
        try:
            # 获取历史估值数据
            historical_data = self._get_historical_valuation_data(ts_code, end_date)
            if not historical_data:
                logger.warning(f"无法获取股票 {ts_code} 的历史估值数据")
                return None
                
            # 获取当前估值指标
            current_metrics = self.valuation_calculator.calculate_valuation_metrics(ts_code, end_date)
            if not current_metrics:
                logger.warning(f"无法获取股票 {ts_code} 的当前估值指标")
                return None
                
            # 计算历史百分位
            percentiles = self._calculate_historical_percentiles(current_metrics, historical_data)
            
            # 生成历史估值评级
            ratings = self._generate_historical_ratings(percentiles)
            
            return HistoricalValuation(
                ts_code=ts_code,
                historical_pe=historical_data.get('pe_data', []),
                historical_pb=historical_data.get('pb_data', []),
                historical_ps=historical_data.get('ps_data', []),
                pe_percentile_1y=percentiles.get('pe_1y'),
                pe_percentile_3y=percentiles.get('pe_3y'),
                pe_percentile_5y=percentiles.get('pe_5y'),
                pb_percentile_1y=percentiles.get('pb_1y'),
                pb_percentile_3y=percentiles.get('pb_3y'),
                pb_percentile_5y=percentiles.get('pb_5y'),
                ps_percentile_1y=percentiles.get('ps_1y'),
                ps_percentile_3y=percentiles.get('ps_3y'),
                ps_percentile_5y=percentiles.get('ps_5y'),
                historical_rating_1y=ratings.get('rating_1y'),
                historical_rating_3y=ratings.get('rating_3y'),
                historical_rating_5y=ratings.get('rating_5y')
            )
            
        except Exception as e:
            logger.error(f"历史估值分析失败: {e}")
            return None
    
    def _get_historical_valuation_data(self, ts_code: str, end_date: str = None) -> Optional[Dict]:
        """获取历史估值数据"""
        try:
            # 计算时间范围
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y%m%d')
            else:
                end_dt = datetime.now()
                
            # 获取过去5年的数据
            start_dt = end_dt - timedelta(days=5*365)
            start_date = start_dt.strftime('%Y%m%d')
            
            # 构建查询条件
            query = {
                "ts_code": ts_code,
                "end_date": {
                    "$gte": start_date,
                    "$lte": end_date or end_dt.strftime('%Y%m%d')
                }
            }
            
            # 获取历史财务指标数据
            historical_fina = list(self.db_handler.get_collection("stock_fina_indicator").find(
                query
            ).sort("end_date", 1))
            
            if not historical_fina:
                return None
                
            # 提取估值数据
            pe_data = []
            pb_data = []
            ps_data = []
            
            for record in historical_fina:
                end_date_str = record.get('end_date')
                if not end_date_str:
                    continue
                    
                # 计算该期间的估值指标
                metrics = self.valuation_calculator.calculate_valuation_metrics(
                    ts_code, end_date_str
                )
                
                if metrics:
                    if metrics.pe_ratio and 0 < metrics.pe_ratio < 1000:
                        pe_data.append({
                            'date': end_date_str,
                            'value': metrics.pe_ratio
                        })
                    
                    if metrics.pb_ratio and 0 < metrics.pb_ratio < 100:
                        pb_data.append({
                            'date': end_date_str,
                            'value': metrics.pb_ratio
                        })
                    
                    if metrics.ps_ratio and 0 < metrics.ps_ratio < 100:
                        ps_data.append({
                            'date': end_date_str,
                            'value': metrics.ps_ratio
                        })
            
            return {
                'pe_data': pe_data,
                'pb_data': pb_data,
                'ps_data': ps_data
            }
            
        except Exception as e:
            logger.error(f"获取历史估值数据失败: {e}")
            return None
    
    def _calculate_historical_percentiles(self, current_metrics: ValuationMetrics, 
                                        historical_data: Dict) -> Dict:
        """计算当前估值在历史数据中的百分位"""
        percentiles = {}
        
        # 计算时间节点
        if current_metrics.end_date:
            end_dt = datetime.strptime(current_metrics.end_date, '%Y%m%d')
        else:
            end_dt = datetime.now()
            
        date_1y = (end_dt - timedelta(days=365)).strftime('%Y%m%d')
        date_3y = (end_dt - timedelta(days=3*365)).strftime('%Y%m%d')
        date_5y = (end_dt - timedelta(days=5*365)).strftime('%Y%m%d')
        
        # PE百分位计算
        if current_metrics.pe_ratio and 'pe_data' in historical_data:
            pe_data = historical_data['pe_data']
            
            # 1年百分位
            pe_1y = [item['value'] for item in pe_data if item['date'] >= date_1y]
            if pe_1y:
                percentiles['pe_1y'] = self._calculate_percentile(current_metrics.pe_ratio, pe_1y)
            
            # 3年百分位
            pe_3y = [item['value'] for item in pe_data if item['date'] >= date_3y]
            if pe_3y:
                percentiles['pe_3y'] = self._calculate_percentile(current_metrics.pe_ratio, pe_3y)
            
            # 5年百分位
            pe_5y = [item['value'] for item in pe_data if item['date'] >= date_5y]
            if pe_5y:
                percentiles['pe_5y'] = self._calculate_percentile(current_metrics.pe_ratio, pe_5y)
        
        # PB百分位计算
        if current_metrics.pb_ratio and 'pb_data' in historical_data:
            pb_data = historical_data['pb_data']
            
            # 1年百分位
            pb_1y = [item['value'] for item in pb_data if item['date'] >= date_1y]
            if pb_1y:
                percentiles['pb_1y'] = self._calculate_percentile(current_metrics.pb_ratio, pb_1y)
            
            # 3年百分位
            pb_3y = [item['value'] for item in pb_data if item['date'] >= date_3y]
            if pb_3y:
                percentiles['pb_3y'] = self._calculate_percentile(current_metrics.pb_ratio, pb_3y)
            
            # 5年百分位
            pb_5y = [item['value'] for item in pb_data if item['date'] >= date_5y]
            if pb_5y:
                percentiles['pb_5y'] = self._calculate_percentile(current_metrics.pb_ratio, pb_5y)
        
        # PS百分位计算
        if current_metrics.ps_ratio and 'ps_data' in historical_data:
            ps_data = historical_data['ps_data']
            
            # 1年百分位
            ps_1y = [item['value'] for item in ps_data if item['date'] >= date_1y]
            if ps_1y:
                percentiles['ps_1y'] = self._calculate_percentile(current_metrics.ps_ratio, ps_1y)
            
            # 3年百分位
            ps_3y = [item['value'] for item in ps_data if item['date'] >= date_3y]
            if ps_3y:
                percentiles['ps_3y'] = self._calculate_percentile(current_metrics.ps_ratio, ps_3y)
            
            # 5年百分位
            ps_5y = [item['value'] for item in ps_data if item['date'] >= date_5y]
            if ps_5y:
                percentiles['ps_5y'] = self._calculate_percentile(current_metrics.ps_ratio, ps_5y)
        
        return percentiles
    
    def _calculate_percentile(self, current_value: float, historical_values: List[float]) -> float:
        """计算百分位"""
        if not historical_values:
            return 50.0
            
        count_below = sum(1 for x in historical_values if x <= current_value)
        return (count_below / len(historical_values)) * 100
    
    def _generate_historical_ratings(self, percentiles: Dict) -> Dict:
        """生成历史估值评级"""
        ratings = {}
        
        # 计算各时间段的综合百分位
        for period in ['1y', '3y', '5y']:
            period_percentiles = []
            
            for metric in ['pe', 'pb', 'ps']:
                key = f'{metric}_{period}'
                if key in percentiles:
                    period_percentiles.append(percentiles[key])
            
            if period_percentiles:
                avg_percentile = mean(period_percentiles)
                
                if avg_percentile >= 80:
                    rating = '历史高位'
                elif avg_percentile >= 60:
                    rating = '偏高水平'
                elif avg_percentile >= 40:
                    rating = '中等水平'
                elif avg_percentile >= 20:
                    rating = '偏低水平'
                else:
                    rating = '历史低位'
                
                ratings[f'rating_{period}'] = rating
        
        return ratings
    
    def get_valuation_trend(self, ts_code: str, days: int = 252) -> Optional[Dict]:
        """获取估值趋势分析
        
        Args:
            ts_code: 股票代码
            days: 分析天数
            
        Returns:
            Dict: 趋势分析结果
        """
        try:
            # 获取指定时间段的估值数据
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=days)
            
            historical_data = self._get_historical_valuation_data(
                ts_code, 
                end_dt.strftime('%Y%m%d')
            )
            
            if not historical_data:
                return None
                
            trends = {}
            
            # 分析PE趋势
            if 'pe_data' in historical_data:
                pe_trend = self._analyze_trend(historical_data['pe_data'], days)
                trends['pe_trend'] = pe_trend
            
            # 分析PB趋势
            if 'pb_data' in historical_data:
                pb_trend = self._analyze_trend(historical_data['pb_data'], days)
                trends['pb_trend'] = pb_trend
            
            # 分析PS趋势
            if 'ps_data' in historical_data:
                ps_trend = self._analyze_trend(historical_data['ps_data'], days)
                trends['ps_trend'] = ps_trend
            
            return trends
            
        except Exception as e:
            logger.error(f"获取估值趋势失败: {e}")
            return None
    
    def _analyze_trend(self, data: List[Dict], days: int) -> Dict:
        """分析单个指标的趋势"""
        if len(data) < 2:
            return {
                'direction': '数据不足',
                'strength': 0.0,
                'duration': 0
            }
        
        # 按日期排序
        sorted_data = sorted(data, key=lambda x: x['date'])
        
        # 计算趋势方向
        values = [item['value'] for item in sorted_data]
        
        # 使用线性回归计算趋势
        x = list(range(len(values)))
        if len(x) > 1:
            slope = np.polyfit(x, values, 1)[0]
            
            if slope > 0.01:  # 上升趋势阈值
                direction = '上升'
            elif slope < -0.01:  # 下降趋势阈值
                direction = '下降'
            else:
                direction = '震荡'
            
            # 计算趋势强度（基于R²）
            correlation = np.corrcoef(x, values)[0, 1]
            strength = abs(correlation) if not np.isnan(correlation) else 0.0
        else:
            direction = '震荡'
            strength = 0.0
        
        # 计算趋势持续时间（简化处理）
        duration = len(sorted_data)
        
        return {
            'direction': direction,
            'strength': strength,
            'duration': duration
        }