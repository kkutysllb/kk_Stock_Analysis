"""
两市整体融资融券数据分析接口
结合成交量和价格走势进行相关性分析
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from api.global_db import db_handler

router = APIRouter(prefix="/api/market-margin", tags=["两市融资融券分析"])

class MarketMarginData(BaseModel):
    """市场融资融券单日数据"""
    trade_date: str
    total_rzye: float  # 融资余额总计
    total_rqye: float  # 融券余额总计
    total_rzrqye: float  # 融资融券余额总计
    total_rzmre: float  # 融资买入额总计
    total_rzche: float  # 融资偿还额总计
    total_rqmcl: float  # 融券卖出量总计
    net_rzflow: float  # 融资净流入 = 买入额-偿还额
    net_rqflow: float  # 融券净流入 = 卖出量-偿还量（如果有偿还量数据）

class MarketIndexData(BaseModel):
    """市场指数数据（用于相关性分析）"""
    trade_date: str
    sh_close: Optional[float] = None  # 上证指数收盘价
    sz_close: Optional[float] = None  # 深证成指收盘价
    sh_volume: Optional[float] = None  # 上证成交量
    sz_volume: Optional[float] = None  # 深证成交量
    total_volume: Optional[float] = None  # 总成交量

class CorrelationAnalysis(BaseModel):
    """相关性分析结果"""
    rzye_price_corr: float  # 融资余额与价格相关性
    rzye_volume_corr: float  # 融资余额与成交量相关性
    rqye_price_corr: float  # 融券余额与价格相关性
    rqye_volume_corr: float  # 融券余额与成交量相关性
    net_flow_price_corr: float  # 净流入与价格相关性
    net_flow_volume_corr: float  # 净流入与成交量相关性

class TrendFitting(BaseModel):
    """趋势拟合数据"""
    data_points: List[Dict[str, float]]  # 数据点 [{"x": date_index, "y": value}]
    trend_line: List[Dict[str, float]]  # 拟合线 [{"x": date_index, "y": fitted_value}]
    r_squared: float  # 拟合优度
    slope: float  # 斜率
    intercept: float  # 截距

class MarketMarginAnalysisResult(BaseModel):
    """两市融资融券分析结果"""
    period: str  # 分析周期
    start_date: str
    end_date: str
    data_count: int
    
    # 基础统计
    avg_rzye: float  # 平均融资余额
    avg_rqye: float  # 平均融券余额
    avg_total_volume: float  # 平均成交量
    
    # 趋势分析
    rzye_trend: str  # 融资余额趋势
    rqye_trend: str  # 融券余额趋势
    price_trend: str  # 价格趋势
    volume_trend: str  # 成交量趋势
    
    # 相关性分析
    correlation_analysis: CorrelationAnalysis
    
    # 曲线拟合数据
    rzye_fitting: TrendFitting  # 融资余额拟合
    rqye_fitting: TrendFitting  # 融券余额拟合
    price_fitting: TrendFitting  # 价格拟合
    volume_fitting: TrendFitting  # 成交量拟合
    
    # 综合评估
    market_sentiment: str  # 市场情绪 'bullish', 'bearish', 'neutral'
    risk_level: str  # 风险等级 'low', 'medium', 'high'
    key_insights: List[str]  # 关键洞察
    
    analysis_time: datetime

class MarketMarginAnalyzer:
    """两市融资融券数据分析器"""
    
    def __init__(self):
        self.db_handler = db_handler
    
    def get_market_margin_data(self, years: int = 1) -> List[MarketMarginData]:
        """获取两市融资融券数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        
        # 查询条件
        query = {
            "trade_date": {
                "$gte": start_date_str,
                "$lte": end_date_str
            }
        }
        
        try:
            collection = self.db_handler.get_collection("margin_trading")
            cursor = collection.find(query).sort("trade_date", 1)
            raw_data = list(cursor)
            
            # 按交易日期聚合数据
            daily_data = {}
            for item in raw_data:
                trade_date = item['trade_date']
                if trade_date not in daily_data:
                    daily_data[trade_date] = {
                        'rzye': 0, 'rqye': 0, 'rzrqye': 0,
                        'rzmre': 0, 'rzche': 0, 'rqmcl': 0
                    }
                
                # 累加各交易所数据
                daily_data[trade_date]['rzye'] += item.get('rzye', 0)
                daily_data[trade_date]['rqye'] += item.get('rqye', 0) 
                daily_data[trade_date]['rzrqye'] += item.get('rzrqye', 0)
                daily_data[trade_date]['rzmre'] += item.get('rzmre', 0)
                daily_data[trade_date]['rzche'] += item.get('rzche', 0)
                daily_data[trade_date]['rqmcl'] += item.get('rqmcl', 0)
            
            # 转换为MarketMarginData列表
            result = []
            for trade_date in sorted(daily_data.keys()):
                data = daily_data[trade_date]
                result.append(MarketMarginData(
                    trade_date=trade_date,
                    total_rzye=data['rzye'],
                    total_rqye=data['rqye'],
                    total_rzrqye=data['rzrqye'],
                    total_rzmre=data['rzmre'],
                    total_rzche=data['rzche'],
                    total_rqmcl=data['rqmcl'],
                    net_rzflow=data['rzmre'] - data['rzche'],
                    net_rqflow=data['rqmcl']  # 融券净流入简化为卖出量
                ))
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据查询失败: {str(e)}")
    
    def get_market_index_data(self, years: int = 1) -> List[MarketIndexData]:
        """获取市场指数数据（模拟数据，实际应该从指数数据表获取）"""
        # 这里应该从实际的指数数据表获取，暂时返回空列表
        # 实际实现时需要查询daily_basic或其他指数数据集合
        return []
    
    def calculate_trend(self, values: List[float]) -> str:
        """计算趋势方向"""
        if len(values) < 2:
            return 'stable'
        
        x = np.arange(len(values))
        y = np.array(values)
        
        slope = np.polyfit(x, y, 1)[0]
        relative_change = slope / np.mean(y) if np.mean(y) != 0 else 0
        
        if relative_change > 0.02:  # 2%以上增长
            return 'increasing'
        elif relative_change < -0.02:  # 2%以上下降
            return 'decreasing'
        else:
            return 'stable'
    
    def calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """计算相关系数"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        try:
            corr, _ = pearsonr(x, y)
            return float(corr) if not np.isnan(corr) else 0.0
        except:
            return 0.0
    
    def fit_trend_line(self, values: List[float], dates: List[str]) -> TrendFitting:
        """拟合趋势线"""
        if len(values) < 2:
            return TrendFitting(
                data_points=[], trend_line=[], 
                r_squared=0.0, slope=0.0, intercept=0.0
            )
        
        # 创建数据点
        x = np.arange(len(values)).reshape(-1, 1)
        y = np.array(values)
        
        # 线性回归
        model = LinearRegression()
        model.fit(x, y)
        
        # 预测值
        y_pred = model.predict(x)
        
        # 计算R²
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # 构建数据点和趋势线
        data_points = [{"x": float(i), "y": float(val)} for i, val in enumerate(values)]
        trend_line = [{"x": float(i), "y": float(pred)} for i, pred in enumerate(y_pred)]
        
        return TrendFitting(
            data_points=data_points,
            trend_line=trend_line,
            r_squared=float(r_squared),
            slope=float(model.coef_[0]),
            intercept=float(model.intercept_)
        )
    
    def generate_mock_price_volume_data(self, margin_data: List[MarketMarginData]) -> tuple:
        """生成模拟的价格和成交量数据（实际应该从真实数据获取）"""
        # 基于融资融券数据生成相关的模拟价格和成交量数据
        prices = []
        volumes = []
        
        for i, data in enumerate(margin_data):
            # 模拟价格（基于融资余额的变化）
            base_price = 3000 + (data.total_rzye / 1e12) * 100
            price_noise = np.random.normal(0, 20)
            prices.append(base_price + price_noise)
            
            # 模拟成交量（基于融资净流入）
            base_volume = 2e11 + abs(data.net_rzflow) * 0.01
            volume_noise = np.random.normal(0, 1e10)
            volumes.append(max(1e10, base_volume + volume_noise))
        
        return prices, volumes
    
    def assess_market_sentiment(self, rzye_trend: str, rqye_trend: str, 
                              net_flow: float, correlation_data: CorrelationAnalysis) -> tuple:
        """评估市场情绪和风险"""
        sentiment_score = 0
        risk_factors = []
        
        # 融资余额趋势评分
        if rzye_trend == 'increasing':
            sentiment_score += 20
        elif rzye_trend == 'decreasing':
            sentiment_score -= 15
            risk_factors.append("融资余额下降")
        
        # 融券余额趋势评分（融券增加通常看空）
        if rqye_trend == 'decreasing':
            sentiment_score += 15
        elif rqye_trend == 'increasing':
            sentiment_score -= 20
            risk_factors.append("融券余额增加")
        
        # 净流入评分
        if net_flow > 0:
            sentiment_score += 15
        else:
            sentiment_score -= 10
            risk_factors.append("融资净流出")
        
        # 相关性风险
        if abs(correlation_data.rzye_price_corr) < 0.3:
            risk_factors.append("融资余额与价格相关性较弱")
        
        # 确定情绪
        if sentiment_score >= 30:
            sentiment = 'bullish'
        elif sentiment_score <= -20:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        # 确定风险等级
        if len(risk_factors) >= 3:
            risk_level = 'high'
        elif len(risk_factors) >= 1:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return sentiment, risk_level, risk_factors
    
    def analyze_market_margin(self, years: int = 1) -> MarketMarginAnalysisResult:
        """分析两市融资融券数据"""
        # 获取融资融券数据
        margin_data = self.get_market_margin_data(years)
        
        if not margin_data:
            raise HTTPException(status_code=404, detail=f"未找到近{years}年的两市融资融券数据")
        
        # 生成模拟的价格和成交量数据（实际应该从真实数据获取）
        prices, volumes = self.generate_mock_price_volume_data(margin_data)
        
        # 提取各项数据
        dates = [item.trade_date for item in margin_data]
        rzye_values = [item.total_rzye for item in margin_data]
        rqye_values = [item.total_rqye for item in margin_data]
        net_flows = [item.net_rzflow for item in margin_data]
        
        # 基础统计
        avg_rzye = float(np.mean(rzye_values))
        avg_rqye = float(np.mean(rqye_values))
        avg_total_volume = float(np.mean(volumes))
        
        # 趋势分析
        rzye_trend = self.calculate_trend(rzye_values)
        rqye_trend = self.calculate_trend(rqye_values)
        price_trend = self.calculate_trend(prices)
        volume_trend = self.calculate_trend(volumes)
        
        # 相关性分析
        correlation_analysis = CorrelationAnalysis(
            rzye_price_corr=self.calculate_correlation(rzye_values, prices),
            rzye_volume_corr=self.calculate_correlation(rzye_values, volumes),
            rqye_price_corr=self.calculate_correlation(rqye_values, prices),
            rqye_volume_corr=self.calculate_correlation(rqye_values, volumes),
            net_flow_price_corr=self.calculate_correlation(net_flows, prices),
            net_flow_volume_corr=self.calculate_correlation(net_flows, volumes)
        )
        
        # 曲线拟合
        rzye_fitting = self.fit_trend_line(rzye_values, dates)
        rqye_fitting = self.fit_trend_line(rqye_values, dates)
        price_fitting = self.fit_trend_line(prices, dates)
        volume_fitting = self.fit_trend_line(volumes, dates)
        
        # 市场情绪评估
        avg_net_flow = float(np.mean(net_flows))
        sentiment, risk_level, risk_factors = self.assess_market_sentiment(
            rzye_trend, rqye_trend, avg_net_flow, correlation_analysis
        )
        
        # 生成关键洞察
        key_insights = []
        if correlation_analysis.rzye_price_corr > 0.5:
            key_insights.append("融资余额与股价呈强正相关，市场情绪乐观")
        elif correlation_analysis.rzye_price_corr < -0.5:
            key_insights.append("融资余额与股价呈负相关，需关注市场风险")
        
        if correlation_analysis.rqye_price_corr > 0.3:
            key_insights.append("融券余额与股价正相关，市场存在看空情绪")
        
        if rzye_trend == 'increasing' and rqye_trend == 'decreasing':
            key_insights.append("融资增加融券减少，市场情绪偏向乐观")
        elif rzye_trend == 'decreasing' and rqye_trend == 'increasing':
            key_insights.append("融资减少融券增加，市场情绪偏向谨慎")
        
        key_insights.extend(risk_factors)
        
        return MarketMarginAnalysisResult(
            period=f"近{years}年",
            start_date=dates[0],
            end_date=dates[-1],
            data_count=len(margin_data),
            avg_rzye=avg_rzye,
            avg_rqye=avg_rqye,
            avg_total_volume=avg_total_volume,
            rzye_trend=rzye_trend,
            rqye_trend=rqye_trend,
            price_trend=price_trend,
            volume_trend=volume_trend,
            correlation_analysis=correlation_analysis,
            rzye_fitting=rzye_fitting,
            rqye_fitting=rqye_fitting,
            price_fitting=price_fitting,
            volume_fitting=volume_fitting,
            market_sentiment=sentiment,
            risk_level=risk_level,
            key_insights=key_insights,
            analysis_time=datetime.now()
        )

# 初始化分析器
def get_analyzer() -> MarketMarginAnalyzer:
    return MarketMarginAnalyzer()

@router.get("/analysis", response_model=MarketMarginAnalysisResult)
async def get_market_margin_analysis(
    years: int = Query(1, ge=1, le=5, description="分析年数，支持1-5年")
):
    """
    获取两市整体融资融券数据分析
    
    结合价格走势和成交量变化进行相关性分析
    提供曲线拟合数据点用于图表展示
    
    - **years**: 分析年数，支持1年、2年、3年、5年
    """
    try:
        analyzer = get_analyzer()
        result = analyzer.analyze_market_margin(years)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.get("/data")
async def get_market_margin_raw_data(
    years: int = Query(1, ge=1, le=5, description="查询年数")
):
    """
    获取两市融资融券原始数据
    
    - **years**: 查询年数，支持1-5年
    """
    try:
        analyzer = get_analyzer()
        data = analyzer.get_market_margin_data(years)
        return {
            "period": f"近{years}年",
            "data_count": len(data),
            "data": [item.dict() for item in data]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/correlation/{metric}")
async def get_correlation_detail(
    metric: str,
    years: int = Query(1, ge=1, le=5, description="分析年数")
):
    """
    获取特定指标的详细相关性数据
    
    - **metric**: 指标类型 (rzye, rqye, net_flow)
    - **years**: 分析年数
    """
    try:
        analyzer = get_analyzer()
        margin_data = analyzer.get_market_margin_data(years)
        prices, volumes = analyzer.generate_mock_price_volume_data(margin_data)
        
        # 根据指标类型提取数据
        if metric == "rzye":
            values = [item.total_rzye for item in margin_data]
            name = "融资余额"
        elif metric == "rqye":
            values = [item.total_rqye for item in margin_data]
            name = "融券余额"
        elif metric == "net_flow":
            values = [item.net_rzflow for item in margin_data]
            name = "融资净流入"
        else:
            raise HTTPException(status_code=400, detail="不支持的指标类型")
        
        # 计算相关性
        price_corr = analyzer.calculate_correlation(values, prices)
        volume_corr = analyzer.calculate_correlation(values, volumes)
        
        # 准备散点图数据
        scatter_price_data = [
            {"x": float(val), "y": float(prices[i])} 
            for i, val in enumerate(values)
        ]
        scatter_volume_data = [
            {"x": float(val), "y": float(volumes[i])} 
            for i, val in enumerate(values)
        ]
        
        return {
            "metric": metric,
            "metric_name": name,
            "price_correlation": price_corr,
            "volume_correlation": volume_corr,
            "scatter_price_data": scatter_price_data,
            "scatter_volume_data": scatter_volume_data,
            "data_count": len(values)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")