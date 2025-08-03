"""
融资融券数据分析接口
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import numpy as np
from api.global_db import db_handler

router = APIRouter(prefix="/api/margin-trading", tags=["融资融券分析"])

class MarginTradingData(BaseModel):
    """融资融券单日数据"""
    trade_date: str
    ts_code: str
    rqchl: float  # 融券偿还量
    rqmcl: float  # 融券卖出量
    rqye: float   # 融券余额
    rzche: float  # 融资偿还额
    rzmre: float  # 融资买入额
    rzye: float   # 融资余额

class MarginTradingAnalysis(BaseModel):
    """融资融券分析结果"""
    stock_code: str
    stock_name: Optional[str] = None
    analysis_period: str
    data_count: int
    
    # 基础统计
    latest_data: MarginTradingData
    avg_financing_balance: float  # 平均融资余额
    avg_securities_balance: float  # 平均融券余额
    
    # 趋势分析
    financing_trend: str  # 融资趋势: 'increasing', 'decreasing', 'stable'
    securities_trend: str  # 融券趋势: 'increasing', 'decreasing', 'stable'
    
    # 活跃度分析
    avg_financing_buy: float  # 平均融资买入额
    avg_financing_repay: float  # 平均融资偿还额
    avg_securities_sell: float  # 平均融券卖出量
    avg_securities_repay: float  # 平均融券偿还量
    
    # 净流入分析
    net_financing_flow: float  # 净融资流入 = 买入额 - 偿还额
    net_securities_flow: float  # 净融券流入 = 卖出量 - 偿还量
    
    # 比率分析
    financing_turnover_ratio: float  # 融资周转率
    securities_turnover_ratio: float  # 融券周转率
    
    # 波动性分析
    financing_balance_volatility: float  # 融资余额波动率
    securities_balance_volatility: float  # 融券余额波动率
    
    # 风险指标
    risk_level: str  # 风险等级: 'low', 'medium', 'high'
    risk_factors: List[str]  # 风险因子
    
    # 综合评分
    overall_score: float  # 综合评分 0-100
    recommendation: str  # 建议: 'bullish', 'bearish', 'neutral'
    
    analysis_time: datetime

class MarginTradingAnalyzer:
    """融资融券数据分析器"""
    
    def __init__(self):
        self.db_handler = db_handler
    
    def get_stock_margin_data(self, stock_code: str, days: int = 30) -> List[Dict]:
        """获取个股融资融券数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 转换日期格式
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        
        # 构建查询条件
        query = {
            "ts_code": stock_code,
            "trade_date": {
                "$gte": start_date_str,
                "$lte": end_date_str
            }
        }
        
        # 使用DBHandler查询数据
        try:
            collection = self.db_handler.get_collection("margin_detail")
            cursor = collection.find(query).sort("trade_date", 1)
            data = list(cursor)
            
            # 转换ObjectId为字符串，避免序列化问题
            for item in data:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
            
            return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
    
    def calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return 'stable'
        
        # 使用线性回归计算趋势
        x = np.arange(len(values))
        y = np.array(values)
        
        # 计算斜率
        slope = np.polyfit(x, y, 1)[0]
        
        # 计算相对变化率
        relative_change = slope / np.mean(y) if np.mean(y) != 0 else 0
        
        if relative_change > 0.01:  # 1%以上增长
            return 'increasing'
        elif relative_change < -0.01:  # 1%以上下降
            return 'decreasing'
        else:
            return 'stable'
    
    def calculate_volatility(self, values: List[float]) -> float:
        """计算波动率"""
        if len(values) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                returns.append((values[i] - values[i-1]) / values[i-1])
        
        return float(np.std(returns)) if returns else 0.0
    
    def assess_risk_level(self, financing_volatility: float, securities_volatility: float, 
                         net_financing_flow: float, net_securities_flow: float) -> tuple:
        """评估风险等级"""
        risk_factors = []
        risk_score = 0
        
        # 波动性风险
        if financing_volatility > 0.1:  # 10%以上波动
            risk_factors.append("融资余额波动较大")
            risk_score += 30
        
        if securities_volatility > 0.15:  # 15%以上波动
            risk_factors.append("融券余额波动较大")
            risk_score += 20
        
        # 流入流出风险
        if net_financing_flow < 0 and abs(net_financing_flow) > 1000000:  # 大额净流出
            risk_factors.append("融资大额净流出")
            risk_score += 25
        
        if net_securities_flow > 0 and net_securities_flow > 100000:  # 大额净做空
            risk_factors.append("融券大额净增加")
            risk_score += 25
        
        # 确定风险等级
        if risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 25:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return risk_level, risk_factors
    
    def calculate_overall_score(self, financing_trend: str, securities_trend: str,
                              net_financing_flow: float, net_securities_flow: float,
                              risk_level: str) -> tuple:
        """计算综合评分和建议"""
        score = 50  # 基础分
        
        # 融资趋势评分
        if financing_trend == 'increasing':
            score += 15
        elif financing_trend == 'decreasing':
            score -= 10
        
        # 融券趋势评分
        if securities_trend == 'decreasing':
            score += 10
        elif securities_trend == 'increasing':
            score -= 15
        
        # 净流入评分
        if net_financing_flow > 0:
            score += 15
        else:
            score -= 10
        
        if net_securities_flow < 0:  # 融券净减少为正面
            score += 10
        else:
            score -= 10
        
        # 风险等级调整
        if risk_level == 'low':
            score += 10
        elif risk_level == 'high':
            score -= 20
        
        # 限制评分范围
        score = max(0, min(100, score))
        
        # 确定建议
        if score >= 70:
            recommendation = 'bullish'
        elif score <= 30:
            recommendation = 'bearish'
        else:
            recommendation = 'neutral'
        
        return float(score), recommendation
    
    def analyze_margin_trading(self, stock_code: str, days: int = 30) -> MarginTradingAnalysis:
        """分析融资融券数据"""
        # 获取数据
        data = self.get_stock_margin_data(stock_code, days)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"未找到股票 {stock_code} 的融资融券数据")
        
        # 提取各项数据
        financing_balances = [item['rzye'] for item in data]
        securities_balances = [item['rqye'] for item in data]
        financing_buys = [item['rzmre'] for item in data]
        financing_repays = [item['rzche'] for item in data]
        securities_sells = [item['rqmcl'] for item in data]
        securities_repays = [item['rqchl'] for item in data]
        
        # 基础统计
        latest_data = MarginTradingData(**data[-1])
        avg_financing_balance = float(np.mean(financing_balances))
        avg_securities_balance = float(np.mean(securities_balances))
        
        # 趋势分析
        financing_trend = self.calculate_trend(financing_balances)
        securities_trend = self.calculate_trend(securities_balances)
        
        # 活跃度分析
        avg_financing_buy = float(np.mean(financing_buys))
        avg_financing_repay = float(np.mean(financing_repays))
        avg_securities_sell = float(np.mean(securities_sells))
        avg_securities_repay = float(np.mean(securities_repays))
        
        # 净流入分析
        net_financing_flow = float(np.sum(financing_buys) - np.sum(financing_repays))
        net_securities_flow = float(np.sum(securities_sells) - np.sum(securities_repays))
        
        # 比率分析
        financing_turnover_ratio = float(avg_financing_buy / avg_financing_balance) if avg_financing_balance > 0 else 0
        securities_turnover_ratio = float(avg_securities_sell / avg_securities_balance) if avg_securities_balance > 0 else 0
        
        # 波动性分析
        financing_balance_volatility = self.calculate_volatility(financing_balances)
        securities_balance_volatility = self.calculate_volatility(securities_balances)
        
        # 风险评估
        risk_level, risk_factors = self.assess_risk_level(
            financing_balance_volatility, securities_balance_volatility,
            net_financing_flow, net_securities_flow
        )
        
        # 综合评分
        overall_score, recommendation = self.calculate_overall_score(
            financing_trend, securities_trend, net_financing_flow, net_securities_flow, risk_level
        )
        
        # 分析周期
        start_date = data[0]['trade_date']
        end_date = data[-1]['trade_date']
        analysis_period = f"{start_date} 至 {end_date}"
        
        return MarginTradingAnalysis(
            stock_code=stock_code,
            analysis_period=analysis_period,
            data_count=len(data),
            latest_data=latest_data,
            avg_financing_balance=avg_financing_balance,
            avg_securities_balance=avg_securities_balance,
            financing_trend=financing_trend,
            securities_trend=securities_trend,
            avg_financing_buy=avg_financing_buy,
            avg_financing_repay=avg_financing_repay,
            avg_securities_sell=avg_securities_sell,
            avg_securities_repay=avg_securities_repay,
            net_financing_flow=net_financing_flow,
            net_securities_flow=net_securities_flow,
            financing_turnover_ratio=financing_turnover_ratio,
            securities_turnover_ratio=securities_turnover_ratio,
            financing_balance_volatility=financing_balance_volatility,
            securities_balance_volatility=securities_balance_volatility,
            risk_level=risk_level,
            risk_factors=risk_factors,
            overall_score=overall_score,
            recommendation=recommendation,
            analysis_time=datetime.now()
        )

# 初始化分析器
def get_analyzer():
    return MarginTradingAnalyzer()

@router.get("/analysis/{stock_code}", response_model=MarginTradingAnalysis)
async def get_margin_trading_analysis(
    stock_code: str,
    days: int = Query(30, ge=1, le=365, description="分析天数，默认30天")
):
    """
    获取个股融资融券数据分析
    
    - **stock_code**: 股票代码，如 002594.SZ
    - **days**: 分析天数，默认30天，最大365天
    """
    try:
        analyzer = get_analyzer()
        result = analyzer.analyze_margin_trading(stock_code, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.get("/data/{stock_code}")
async def get_margin_trading_data(
    stock_code: str,
    days: int = Query(30, ge=1, le=365, description="查询天数，默认30天")
):
    """
    获取个股融资融券原始数据
    
    - **stock_code**: 股票代码，如 002594.SZ  
    - **days**: 查询天数，默认30天，最大365天
    """
    try:
        analyzer = get_analyzer()
        data = analyzer.get_stock_margin_data(stock_code, days)
        return {
            "stock_code": stock_code,
            "data_count": len(data),
            "period": f"近{days}天",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")