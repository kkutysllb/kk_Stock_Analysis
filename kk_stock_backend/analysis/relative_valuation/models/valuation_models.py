"""相对估值分析数据模型"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ValuationMetrics:
    """估值指标数据模型"""
    ts_code: str
    end_date: str
    
    # 基础估值倍数
    pe_ratio: Optional[float] = None  # 市盈率
    pb_ratio: Optional[float] = None  # 市净率
    ps_ratio: Optional[float] = None  # 市销率
    pcf_ratio: Optional[float] = None  # 市现率
    
    # TTM估值倍数
    pe_ttm: Optional[float] = None
    pb_ttm: Optional[float] = None
    ps_ttm: Optional[float] = None
    pcf_ttm: Optional[float] = None
    
    # 企业价值倍数
    ev_ebitda: Optional[float] = None
    ev_sales: Optional[float] = None
    
    # 基础财务数据
    market_cap: Optional[float] = None  # 总市值
    total_revenue: Optional[float] = None  # 营业收入
    net_profit: Optional[float] = None  # 净利润
    total_assets: Optional[float] = None  # 总资产
    shareholders_equity: Optional[float] = None  # 股东权益
    operating_cash_flow: Optional[float] = None  # 经营现金流
    
    # 计算时间
    calculated_at: datetime = None
    
    def __post_init__(self):
        if self.calculated_at is None:
            self.calculated_at = datetime.now()


@dataclass
class IndustryComparison:
    """行业对比数据模型"""
    ts_code: str
    industry: str
    end_date: str
    
    # 个股估值指标
    stock_metrics: ValuationMetrics
    
    # 行业统计数据
    industry_pe_median: Optional[float] = None
    industry_pe_mean: Optional[float] = None
    industry_pe_percentile: Optional[float] = None  # 个股在行业中的百分位
    
    industry_pb_median: Optional[float] = None
    industry_pb_mean: Optional[float] = None
    industry_pb_percentile: Optional[float] = None
    
    industry_ps_median: Optional[float] = None
    industry_ps_mean: Optional[float] = None
    industry_ps_percentile: Optional[float] = None
    
    # 行业样本数量
    industry_sample_count: int = 0
    
    # 相对估值评级
    pe_rating: Optional[str] = None  # 高估/合理/低估
    pb_rating: Optional[str] = None
    ps_rating: Optional[str] = None
    overall_rating: Optional[str] = None


@dataclass
class HistoricalValuation:
    """历史估值数据模型"""
    ts_code: str
    
    # 历史估值序列（按时间排序）
    historical_pe: List[Dict[str, Any]] = None  # [{"date": "20240331", "value": 15.5}, ...]
    historical_pb: List[Dict[str, Any]] = None
    historical_ps: List[Dict[str, Any]] = None
    
    # 历史统计指标
    pe_percentile_1y: Optional[float] = None  # 当前PE在过去1年的百分位
    pe_percentile_3y: Optional[float] = None  # 当前PE在过去3年的百分位
    pe_percentile_5y: Optional[float] = None  # 当前PE在过去5年的百分位
    
    pb_percentile_1y: Optional[float] = None
    pb_percentile_3y: Optional[float] = None
    pb_percentile_5y: Optional[float] = None
    
    ps_percentile_1y: Optional[float] = None
    ps_percentile_3y: Optional[float] = None
    ps_percentile_5y: Optional[float] = None
    
    # 历史估值评级
    historical_rating_1y: Optional[str] = None
    historical_rating_3y: Optional[str] = None
    historical_rating_5y: Optional[str] = None
    
    def __post_init__(self):
        if self.historical_pe is None:
            self.historical_pe = []
        if self.historical_pb is None:
            self.historical_pb = []
        if self.historical_ps is None:
            self.historical_ps = []


@dataclass
class RelativeValuationResult:
    """相对估值分析结果"""
    ts_code: str
    stock_name: str
    industry: str
    analysis_date: str
    
    # 当前估值指标
    current_metrics: ValuationMetrics
    
    # 行业对比结果
    industry_comparison: IndustryComparison
    
    # 历史估值分析
    historical_analysis: HistoricalValuation
    
    # 综合评级
    overall_rating: str  # 严重高估/高估/合理/低估/严重低估
    rating_score: float  # 评级分数 0-100
    
    # 投资建议
    investment_advice: str
    
    # 风险提示
    risk_warnings: List[str] = None
    
    # 分析摘要
    analysis_summary: str = ""
    
    # 分析时间
    analyzed_at: datetime = None
    
    def __post_init__(self):
        if self.risk_warnings is None:
            self.risk_warnings = []
        if self.analyzed_at is None:
            self.analyzed_at = datetime.now()


@dataclass
class ValuationTrend:
    """估值趋势数据模型"""
    ts_code: str
    
    # 趋势数据
    pe_trend: str  # 上升/下降/震荡
    pb_trend: str
    ps_trend: str
    
    # 趋势强度
    pe_trend_strength: float  # 0-1
    pb_trend_strength: float
    ps_trend_strength: float
    
    # 趋势持续时间（天数）
    pe_trend_duration: int
    pb_trend_duration: int
    ps_trend_duration: int