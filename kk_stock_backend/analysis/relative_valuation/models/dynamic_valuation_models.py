"""动态估值分析数据模型"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class GrowthMetrics:
    """成长性指标数据模型"""
    ts_code: str
    
    # 营收增长率
    revenue_growth_1y: Optional[float] = None  # 1年营收增长率
    revenue_growth_3y: Optional[float] = None  # 3年年化营收增长率
    revenue_growth_5y: Optional[float] = None  # 5年年化营收增长率
    revenue_growth_ttm: Optional[float] = None  # TTM营收增长率
    
    # 净利润增长率
    profit_growth_1y: Optional[float] = None
    profit_growth_3y: Optional[float] = None
    profit_growth_5y: Optional[float] = None
    profit_growth_ttm: Optional[float] = None
    
    # 经营现金流增长率
    cashflow_growth_1y: Optional[float] = None
    cashflow_growth_3y: Optional[float] = None
    cashflow_growth_5y: Optional[float] = None
    
    # 成长质量指标
    revenue_growth_stability: Optional[float] = None  # 营收增长稳定性（方差系数）
    profit_growth_stability: Optional[float] = None   # 利润增长稳定性
    
    # 成长持续性评分
    growth_sustainability_score: Optional[float] = None  # 0-100分
    growth_trend: Optional[str] = None  # 加速/减速/稳定/波动
    
    def __post_init__(self):
        """计算综合成长性评分"""
        if not hasattr(self, 'calculated_at'):
            self.calculated_at = datetime.now()


@dataclass
class ProfitabilityMetrics:
    """盈利能力指标数据模型"""
    ts_code: str
    
    # 盈利能力指标
    roe: Optional[float] = None          # 净资产收益率
    roa: Optional[float] = None          # 总资产收益率
    roic: Optional[float] = None         # 投入资本回报率
    gross_margin: Optional[float] = None # 毛利率
    net_margin: Optional[float] = None   # 净利率
    
    # 盈利质量指标
    operating_margin: Optional[float] = None      # 营业利润率
    ebitda_margin: Optional[float] = None         # EBITDA利润率
    cash_conversion_ratio: Optional[float] = None # 现金转换率（经营现金流/净利润）
    
    # 盈利趋势
    roe_trend: Optional[str] = None      # ROE趋势：上升/下降/稳定
    margin_trend: Optional[str] = None   # 利润率趋势
    
    # 与行业对比
    roe_vs_industry: Optional[float] = None      # ROE行业百分位
    margin_vs_industry: Optional[float] = None   # 利润率行业百分位
    
    # 综合评分
    profitability_score: Optional[float] = None  # 盈利能力综合评分
    quality_score: Optional[float] = None        # 盈利质量评分


@dataclass
class DynamicValuationMetrics:
    """动态估值指标数据模型"""
    ts_code: str
    
    # PEG相关指标
    peg_1y: Optional[float] = None       # 基于1年增长率的PEG
    peg_3y: Optional[float] = None       # 基于3年增长率的PEG
    peg_forecast: Optional[float] = None # 基于预测增长率的PEG
    
    # 动态PE指标
    pe_to_growth: Optional[float] = None # PE/增长率比值
    forward_pe: Optional[float] = None   # 预测PE（基于增长预测）
    
    # 现金流估值
    dcf_value: Optional[float] = None    # DCF估值
    fcf_yield: Optional[float] = None    # 自由现金流收益率
    ev_ebitda: Optional[float] = None    # 企业价值倍数
    
    # 相对估值调整
    adjusted_pe: Optional[float] = None  # 成长调整后PE
    adjusted_pb: Optional[float] = None  # 质量调整后PB
    
    # 估值评级
    peg_rating: Optional[str] = None     # PEG评级
    growth_adjusted_rating: Optional[str] = None  # 成长调整评级
    
    def __post_init__(self):
        if not hasattr(self, 'calculated_at'):
            self.calculated_at = datetime.now()


@dataclass
class ValuationForecast:
    """估值预测数据模型"""
    ts_code: str
    
    # 增长预测
    revenue_forecast_1y: Optional[float] = None
    revenue_forecast_2y: Optional[float] = None
    profit_forecast_1y: Optional[float] = None
    profit_forecast_2y: Optional[float] = None
    
    # 估值预测
    target_pe: Optional[float] = None
    target_price: Optional[float] = None
    price_range: Optional[Dict[str, float]] = None  # 价格区间
    
    # 风险调整
    beta: Optional[float] = None
    volatility: Optional[float] = None
    downside_risk: Optional[float] = None
    
    # 情景分析
    bull_case_price: Optional[float] = None
    bear_case_price: Optional[float] = None
    base_case_price: Optional[float] = None
    
    def __post_init__(self):
        if self.price_range is None:
            self.price_range = {}


@dataclass
class ComprehensiveDynamicValuation:
    """综合动态估值结果"""
    ts_code: str
    stock_name: str
    industry: str
    analysis_date: str
    
    # 基础静态估值
    static_valuation: Any  # ValuationMetrics对象
    
    # 动态估值组件
    growth_metrics: GrowthMetrics
    profitability_metrics: ProfitabilityMetrics
    dynamic_valuation: DynamicValuationMetrics
    valuation_forecast: ValuationForecast
    
    # 综合评级
    static_rating: str      # 静态估值评级
    dynamic_rating: str     # 动态估值评级
    comprehensive_rating: str  # 综合评级
    
    # 评分
    static_score: float     # 静态估值评分 0-100
    growth_score: float     # 成长性评分 0-100
    quality_score: float    # 质量评分 0-100
    comprehensive_score: float  # 综合评分 0-100
    
    # 投资建议
    investment_action: str  # 买入/持有/卖出
    confidence_level: str   # 信心等级：高/中/低
    time_horizon: str       # 投资期限建议
    key_risks: List[str]    # 主要风险点
    catalysts: List[str]    # 催化因素
    
    # 分析摘要
    analysis_summary: str
    recommendation_rationale: str  # 推荐理由
    
    def __post_init__(self):
        if self.key_risks is None:
            self.key_risks = []
        if self.catalysts is None:
            self.catalysts = []
        if not hasattr(self, 'analyzed_at'):
            self.analyzed_at = datetime.now()


@dataclass
class IndustryGrowthBenchmark:
    """行业成长性基准数据模型"""
    industry: str
    
    # 行业平均增长率
    avg_revenue_growth: Optional[float] = None
    avg_profit_growth: Optional[float] = None
    avg_roe: Optional[float] = None
    
    # 行业中位数
    median_peg: Optional[float] = None
    median_roe: Optional[float] = None
    
    # 行业增长预期
    industry_outlook: Optional[str] = None  # 看好/中性/谨慎
    growth_drivers: List[str] = None        # 增长驱动因素
    
    def __post_init__(self):
        if self.growth_drivers is None:
            self.growth_drivers = []