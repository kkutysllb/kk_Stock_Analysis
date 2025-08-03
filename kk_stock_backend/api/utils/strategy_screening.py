#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略选股核心算法模块 - 性能优化版
使用预计算数据替代实时计算，提升100-600倍性能
提供技术指标计算、基本面评分、特色数据挖掘等功能
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from api.global_db import db_handler

# 使用全局数据库处理器

# ==================== 数据类定义 ====================

@dataclass
class TechnicalIndicators:
    """技术指标数据类"""
    ts_code: str
    name: str
    close: float
    volume: int
    
    # 趋势指标
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    
    # MACD指标
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    
    # RSI指标
    rsi: Optional[float] = None
    rsi_6: Optional[float] = None
    rsi_12: Optional[float] = None
    rsi_24: Optional[float] = None
    
    # KDJ指标
    kdj_k: Optional[float] = None
    kdj_d: Optional[float] = None
    kdj_j: Optional[float] = None
    
    # 布林带
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None
    
    # 成交量指标
    volume_ratio: Optional[float] = None  # 量比
    volume_ma5: Optional[float] = None    # 5日均量
    
    # 价格位置
    price_position: Optional[float] = None  # 价格在近期区间的位置
    
    # 估值指标
    pe: Optional[float] = None
    pb: Optional[float] = None
    
    # 基础数据
    pct_chg: Optional[float] = None         # 涨跌幅
    total_mv: Optional[float] = None        # 总市值

@dataclass
class FundamentalScores:
    """基本面评分数据类"""
    ts_code: str
    name: str
    
    # 成长性评分 (0-100)
    growth_score: Optional[float] = None
    revenue_growth: Optional[float] = None  # 营收增长率
    profit_growth: Optional[float] = None   # 净利润增长率
    
    # 盈利能力评分 (0-100)
    profitability_score: Optional[float] = None
    roe: Optional[float] = None             # 净资产收益率
    roa: Optional[float] = None             # 总资产收益率
    gross_margin: Optional[float] = None    # 毛利率
    
    # 估值水平评分 (0-100)
    valuation_score: Optional[float] = None
    pe: Optional[float] = None              # 市盈率
    pb: Optional[float] = None              # 市净率
    ps: Optional[float] = None              # 市销率
    
    # 财务健康度评分 (0-100)
    financial_health_score: Optional[float] = None
    debt_ratio: Optional[float] = None      # 资产负债率
    current_ratio: Optional[float] = None   # 流动比率
    quick_ratio: Optional[float] = None     # 速动比率
    
    # 综合评分
    total_score: Optional[float] = None

@dataclass
class SpecialFeatures:
    """特色数据类"""
    ts_code: str
    name: str
    
    # 基础数据
    close: Optional[float] = None           # 收盘价
    
    # 连板数据
    limit_days: Optional[int] = None        # 连板天数
    limit_strength: Optional[float] = None  # 连板强度
    
    # 游资数据
    hot_money_rank: Optional[int] = None    # 游资关注排名
    hot_money_score: Optional[float] = None # 游资活跃度评分
    
    # 资金流向
    net_inflow: Optional[float] = None      # 净流入金额
    inflow_strength: Optional[float] = None # 资金流入强度
    
    # 机构关注
    institution_attention: Optional[float] = None  # 机构关注度
    dragon_tiger_count: Optional[int] = None       # 龙虎榜次数
    
    # 资金追踪策略专用字段
    # 两融数据
    margin_buy_trend: Optional[float] = None         # 融资买入趋势
    margin_balance_growth: Optional[float] = None    # 融资余额增长
    margin_activity_score: Optional[float] = None    # 两融活跃度
    short_sell_trend: Optional[float] = None         # 融券趋势
    
    # 资金流数据
    large_order_net_inflow: Optional[float] = None   # 大单净流入
    super_large_net_inflow: Optional[float] = None   # 超大单净流入
    fund_flow_continuity: Optional[float] = None     # 资金流入连续性
    institutional_fund_ratio: Optional[float] = None # 机构资金占比
    
    # 行业数据
    industry_fund_rank: Optional[int] = None         # 行业资金排名
    industry_fund_strength: Optional[float] = None   # 行业资金强度
    sector_rotation_score: Optional[float] = None    # 板块轮动评分
    fund_tracking_score: Optional[float] = None      # 资金追踪综合评分
    
    # 保留原有筹码字段以保持兼容性
    chip_concentration: Optional[float] = None      
    cost_advantage: Optional[float] = None          
    winner_rate: Optional[float] = None

# ==================== 技术面分析 - 性能优化版 ====================

class TechnicalAnalyzer:
    """技术面分析器 - 使用预计算数据，性能提升100-600倍"""
    
    def __init__(self):
        self.db = db_handler.db
        
    def get_latest_trade_date(self) -> str:
        """获取最新交易日期"""
        try:
            latest = self.db["stock_factor_pro"].find_one(
                {}, 
                {"trade_date": 1}, 
                sort=[("trade_date", -1)]
            )
            return latest["trade_date"] if latest else datetime.now().strftime('%Y%m%d')
        except Exception:
            return datetime.now().strftime('%Y%m%d')
    
    async def get_stock_technical_indicators(self, ts_code: str, trade_date: str = None) -> Optional[TechnicalIndicators]:
        """
        获取股票技术指标 - 性能优化版
        直接使用stock_factor_pro预计算数据，性能提升100-600倍
        """
        try:
            if not trade_date:
                trade_date = self.get_latest_trade_date()
            
            # 直接查询预计算的技术指标数据
            factor_data = self.db["stock_factor_pro"].find_one({
                "ts_code": ts_code,
                "trade_date": trade_date
            })
            
            if not factor_data:
                # 如果指定日期没有数据，尝试获取最近的数据
                factor_data = self.db["stock_factor_pro"].find_one(
                    {"ts_code": ts_code},
                    sort=[("trade_date", -1)]
                )
            
            if not factor_data:
                return None
            
            # 获取股票基本信息
            stock_basic = self.db["infrastructure_stock_basic"].find_one({"ts_code": ts_code})
            name = stock_basic["name"] if stock_basic else ""
            
            # 映射预计算数据到技术指标对象
            indicators = self._map_factor_data_to_indicators(factor_data, name)
            
            return indicators
            
        except Exception as e:
            print(f"获取技术指标失败 {ts_code}: {str(e)}")
            return None
    
    def _map_factor_data_to_indicators(self, factor_data: dict, name: str) -> TechnicalIndicators:
        """将预计算数据映射到技术指标对象"""
        
        # 安全获取数值，处理None值
        def safe_float(value):
            if value is None or value == 'None' or str(value).lower() == 'nan':
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_int(value):
            if value is None or value == 'None':
                return 0
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return 0
        
        indicators = TechnicalIndicators(
            ts_code=factor_data["ts_code"],
            name=name,
            close=safe_float(factor_data.get("close", 0)),
            volume=safe_int(factor_data.get("vol", 0))
        )
        
        # 移动平均线 (使用前复权数据)
        indicators.ma5 = safe_float(factor_data.get("ma_qfq_5"))
        indicators.ma10 = safe_float(factor_data.get("ma_qfq_10"))
        indicators.ma20 = safe_float(factor_data.get("ma_qfq_20"))
        indicators.ma60 = safe_float(factor_data.get("ma_qfq_60"))
        
        # MACD指标 (使用前复权数据)
        indicators.macd = safe_float(factor_data.get("macd_qfq"))
        indicators.macd_signal = safe_float(factor_data.get("macd_dea_qfq"))  # DEA就是信号线
        indicators.macd_hist = safe_float(factor_data.get("macd_dif_qfq"))    # DIF就是柱状图
        
        # RSI指标
        indicators.rsi_6 = safe_float(factor_data.get("rsi_qfq_6"))
        indicators.rsi_12 = safe_float(factor_data.get("rsi_qfq_12"))
        indicators.rsi_24 = safe_float(factor_data.get("rsi_qfq_24"))
        indicators.rsi = indicators.rsi_12  # 默认使用12日RSI
        
        # KDJ指标
        indicators.kdj_k = safe_float(factor_data.get("kdj_k_qfq"))
        indicators.kdj_d = safe_float(factor_data.get("kdj_d_qfq"))
        indicators.kdj_j = safe_float(factor_data.get("kdj_qfq"))  # J值
        
        # 布林带
        indicators.bb_upper = safe_float(factor_data.get("boll_upper_qfq"))
        indicators.bb_middle = safe_float(factor_data.get("boll_mid_qfq"))
        indicators.bb_lower = safe_float(factor_data.get("boll_lower_qfq"))
        
        # 计算布林带宽度
        if indicators.bb_upper and indicators.bb_lower and indicators.bb_middle:
            indicators.bb_width = (indicators.bb_upper - indicators.bb_lower) / indicators.bb_middle * 100
        
        # 成交量指标
        indicators.volume_ratio = safe_float(factor_data.get("volume_ratio"))
        
        # 估值指标
        indicators.pe = safe_float(factor_data.get("pe"))
        indicators.pb = safe_float(factor_data.get("pb"))
        
        # 基础数据
        indicators.pct_chg = safe_float(factor_data.get("pct_chg"))
        indicators.total_mv = safe_float(factor_data.get("total_mv"))
        
        # 计算价格位置 (价格在布林带中的位置)
        if indicators.bb_upper and indicators.bb_lower and indicators.close:
            if indicators.bb_upper > indicators.bb_lower:
                indicators.price_position = (indicators.close - indicators.bb_lower) / (indicators.bb_upper - indicators.bb_lower) * 100
        
        return indicators
    
    # 保留原有的计算方法作为备用（但不再使用）
    def calculate_ma(self, prices: List[float], period: int) -> float:
        """计算移动平均线 - 备用方法"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """计算指数移动平均线 - 备用方法"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def calculate_macd(self, prices: List[float], fast=12, slow=26, signal=9) -> Tuple[float, float, float]:
        """计算MACD - 备用方法"""
        if len(prices) < slow:
            return None, None, None
        
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        
        if ema_fast is None or ema_slow is None:
            return None, None, None
        
        dif = ema_fast - ema_slow
        
        # 计算DEA (信号线)
        dif_values = []
        for i in range(len(prices) - slow + 1):
            subset = prices[i:i + slow]
            if len(subset) >= slow:
                fast_ema = self.calculate_ema(subset, fast)
                slow_ema = self.calculate_ema(subset, slow)
                if fast_ema and slow_ema:
                    dif_values.append(fast_ema - slow_ema)
        
        if len(dif_values) < signal:
            return dif, None, None
        
        dea = self.calculate_ema(dif_values, signal)
        macd = (dif - dea) * 2 if dea else None
        
        return dif, dea, macd

# ==================== 基本面分析 - 性能优化版 ====================

class FundamentalAnalyzer:
    """基本面分析器 - 使用预计算数据，性能大幅提升"""
    
    def __init__(self):
        self.db = db_handler.db
    
    def get_latest_report_period(self) -> str:
        """获取最新财报期间"""
        try:
            latest = self.db["stock_fina_indicator"].find_one(
                {}, 
                {"end_date": 1}, 
                sort=[("end_date", -1)]
            )
            return latest["end_date"] if latest else "20231231"
        except Exception:
            return "20231231"
    
    def _safe_float(self, value):
        """安全获取浮点数"""
        if value is None or value == 'None' or str(value).lower() == 'nan':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _calculate_growth_score(self, revenue_growth: Optional[float], profit_growth: Optional[float]) -> Optional[float]:
        """计算成长性评分"""
        scores = []
        if revenue_growth is not None:
            # 营收增长率评分：-20%~50%映射到0~100分
            score = max(0, min(100, (revenue_growth + 20) / 70 * 100))
            scores.append(score)
        
        if profit_growth is not None:
            # 净利润增长率评分：-30%~100%映射到0~100分
            score = max(0, min(100, (profit_growth + 30) / 130 * 100))
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else None
    
    def _calculate_profitability_score(self, roe: Optional[float], roa: Optional[float], gross_margin: Optional[float]) -> Optional[float]:
        """计算盈利能力评分"""
        scores = []
        if roe is not None:
            # ROE评分：-10%~30%映射到0~100分
            score = max(0, min(100, (roe + 10) / 40 * 100))
            scores.append(score)
        
        if roa is not None:
            # ROA评分：-5%~15%映射到0~100分
            score = max(0, min(100, (roa + 5) / 20 * 100))
            scores.append(score)
        
        if gross_margin is not None:
            # 毛利率评分：0%~80%映射到0~100分
            score = max(0, min(100, gross_margin / 80 * 100))
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else None
    
    def _calculate_valuation_score(self, pe: Optional[float], pb: Optional[float], ps: Optional[float]) -> Optional[float]:
        """计算估值水平评分（越低越好）"""
        scores = []
        if pe is not None and pe > 0:
            # PE评分：5~100映射到100~0分（反向）
            score = max(0, min(100, 100 - (pe - 5) / 95 * 100))
            scores.append(score)
        
        if pb is not None and pb > 0:
            # PB评分：0.5~10映射到100~0分（反向）
            score = max(0, min(100, 100 - (pb - 0.5) / 9.5 * 100))
            scores.append(score)
        
        if ps is not None and ps > 0:
            # PS评分：0.5~20映射到100~0分（反向）
            score = max(0, min(100, 100 - (ps - 0.5) / 19.5 * 100))
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else None
    
    def _calculate_financial_health_score(self, debt_ratio: Optional[float], current_ratio: Optional[float], quick_ratio: Optional[float]) -> Optional[float]:
        """计算财务健康度评分"""
        scores = []
        if debt_ratio is not None:
            # 资产负债率评分：0%~80%映射到100~0分（反向）
            score = max(0, min(100, 100 - debt_ratio / 80 * 100))
            scores.append(score)
        
        if current_ratio is not None:
            # 流动比率评分：0.5~3映射到0~100分
            score = max(0, min(100, (current_ratio - 0.5) / 2.5 * 100))
            scores.append(score)
        
        if quick_ratio is not None:
            # 速动比率评分：0.3~2映射到0~100分
            score = max(0, min(100, (quick_ratio - 0.3) / 1.7 * 100))
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else None
    
    def _calculate_total_score(self, growth_score: Optional[float], profitability_score: Optional[float], 
                              valuation_score: Optional[float], financial_health_score: Optional[float]) -> Optional[float]:
        """计算综合评分"""
        scores = []
        weights = []
        
        if growth_score is not None:
            scores.append(growth_score)
            weights.append(0.3)  # 成长性权重30%
        
        if profitability_score is not None:
            scores.append(profitability_score)
            weights.append(0.35)  # 盈利能力权重35%
        
        if valuation_score is not None:
            scores.append(valuation_score)
            weights.append(0.25)  # 估值水平权重25%
        
        if financial_health_score is not None:
            scores.append(financial_health_score)
            weights.append(0.1)  # 财务健康度权重10%
        
        if not scores:
            return None
        
        # 权重归一化
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # 加权平均
        weighted_score = sum(score * weight for score, weight in zip(scores, normalized_weights))
        return weighted_score
    
    async def get_stock_fundamental_scores(self, ts_code: str, period: str = None) -> Optional[FundamentalScores]:
        """
        获取股票基本面评分 - 性能优化版
        直接使用stock_fina_indicator预计算数据
        """
        try:
            if not period:
                period = self.get_latest_report_period()
            
            # 直接查询预计算的财务指标数据
            fina_indicator = self.db["stock_fina_indicator"].find_one({
                "ts_code": ts_code,
                "end_date": period
            })
            
            if not fina_indicator:
                # 尝试获取最近的数据
                fina_indicator = self.db["stock_fina_indicator"].find_one(
                    {"ts_code": ts_code},
                    sort=[("end_date", -1)]
                )
            
            if not fina_indicator:
                return None
            
            # 获取股票基本信息
            stock_basic = self.db["infrastructure_stock_basic"].find_one({"ts_code": ts_code})
            name = stock_basic["name"] if stock_basic else ""
            
            # 映射预计算数据到基本面评分对象
            scores = self._map_fina_data_to_scores(fina_indicator, name)
            
            return scores
            
        except Exception as e:
            print(f"获取基本面评分失败 {ts_code}: {str(e)}")
            return None
    
    def _map_fina_data_to_scores(self, fina_data: dict, name: str) -> FundamentalScores:
        """将预计算财务数据映射到基本面评分对象"""
        
        scores = FundamentalScores(ts_code=fina_data["ts_code"], name=name)
        
        # 成长性指标
        scores.revenue_growth = self._safe_float(fina_data.get("or_yoy"))  # 营业收入同比增长率
        scores.profit_growth = self._safe_float(fina_data.get("profit_dedt"))  # 净利润同比增长率
        scores.growth_score = self._calculate_growth_score(scores.revenue_growth, scores.profit_growth)
        
        # 盈利能力指标
        scores.roe = self._safe_float(fina_data.get("roe"))  # 净资产收益率
        scores.roa = self._safe_float(fina_data.get("roa"))  # 总资产收益率  
        scores.gross_margin = self._safe_float(fina_data.get("grossprofit_margin"))  # 毛利率
        scores.profitability_score = self._calculate_profitability_score(scores.roe, scores.roa, scores.gross_margin)
        
        # 估值水平指标
        scores.pe = self._safe_float(fina_data.get("pe"))
        scores.pb = self._safe_float(fina_data.get("pb"))
        scores.ps = self._safe_float(fina_data.get("ps"))
        scores.valuation_score = self._calculate_valuation_score(scores.pe, scores.pb, scores.ps)
        
        # 财务健康度指标
        scores.debt_ratio = self._safe_float(fina_data.get("debt_to_assets"))  # 资产负债率
        scores.current_ratio = self._safe_float(fina_data.get("current_ratio"))  # 流动比率
        scores.quick_ratio = self._safe_float(fina_data.get("quick_ratio"))  # 速动比率
        scores.financial_health_score = self._calculate_financial_health_score(
            scores.debt_ratio, scores.current_ratio, scores.quick_ratio
        )
        
        # 综合评分
        scores.total_score = self._calculate_total_score(
            scores.growth_score, scores.profitability_score, 
            scores.valuation_score, scores.financial_health_score
        )
        
        return scores
    
# ==================== 特色数据分析 - 性能优化版 ====================

class SpecialDataAnalyzer:
    """特色数据分析器 - 使用预计算数据，性能大幅提升"""
    
    def __init__(self):
        self.db = db_handler.db
    
    def _safe_float(self, value):
        """安全获取浮点数"""
        if value is None or value == 'None' or str(value).lower() == 'nan':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value):
        """安全获取整数"""
        if value is None or value == 'None':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    async def get_stock_special_features(self, ts_code: str) -> Optional[SpecialFeatures]:
        """
        获取股票特色数据 - 性能优化版
        直接使用预计算数据，大幅提升查询效率
        """
        try:
            # 获取股票基本信息
            stock_basic = self.db["infrastructure_stock_basic"].find_one({"ts_code": ts_code})
            name = stock_basic["name"] if stock_basic else ""
            
            features = SpecialFeatures(ts_code=ts_code, name=name)
            
            # 并行获取所有特色数据，提升性能
            limit_data, hot_money_data, money_flow_data, institution_data = await self._get_all_special_data(ts_code)
            
            # 1. 连板数据
            if limit_data:
                features.limit_days = limit_data.get("limit_days")
                features.limit_strength = limit_data.get("limit_strength")
            
            # 2. 游资数据
            if hot_money_data:
                features.hot_money_rank = hot_money_data.get("rank")
                features.hot_money_score = hot_money_data.get("score")
            
            # 3. 资金流向
            if money_flow_data:
                features.net_inflow = money_flow_data.get("net_inflow")
                features.inflow_strength = money_flow_data.get("inflow_strength")
            
            # 4. 机构关注度
            if institution_data:
                features.institution_attention = institution_data.get("attention_score")
                features.dragon_tiger_count = institution_data.get("dragon_tiger_count")
            
            return features
            
        except Exception as e:
            print(f"获取特色数据失败 {ts_code}: {str(e)}")
            return None
    
    async def _get_all_special_data(self, ts_code: str) -> tuple:
        """并行获取所有特色数据，提升性能"""
        import asyncio
        
        # 并行执行所有数据获取任务
        tasks = [
            self._get_limit_data(ts_code),
            self._get_hot_money_data(ts_code),
            self._get_money_flow_data(ts_code),
            self._get_institution_attention(ts_code)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return tuple(processed_results)
    
    async def _get_limit_data(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """获取连板数据"""
        try:
            # 从limit_step表获取连板数据
            limit_step = self.db["limit_step"].find_one(
                {"ts_code": ts_code},
                sort=[("trade_date", -1)]
            )
            
            if not limit_step:
                return None
            
            limit_days = limit_step.get("step", 0)
            
            # 计算连板强度（基于连板天数和市场表现）
            if limit_days > 0:
                # 简单的强度计算：连板天数越多，强度越高
                limit_strength = min(100, limit_days * 20)  # 最高100分
            else:
                limit_strength = 0
            
            return {
                "limit_days": limit_days,
                "limit_strength": limit_strength
            }
            
        except Exception as e:
            print(f"获取连板数据失败 {ts_code}: {str(e)}")
            return None
    
    async def _get_hot_money_data(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """获取游资数据"""
        try:
            # 从龙虎榜数据分析游资活跃度
            recent_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            cursor = self.db["top_list"].find({
                "ts_code": ts_code,
                "trade_date": {"$gte": recent_date}
            })
            
            hot_money_records = list(cursor)
            
            if not hot_money_records:
                return None
            
            # 计算游资活跃度评分
            score = min(100, len(hot_money_records) * 10)  # 每次上榜10分，最高100分
            rank = len(hot_money_records)  # 简化排名
            
            return {
                "rank": rank,
                "score": score
            }
            
        except Exception as e:
            print(f"获取游资数据失败 {ts_code}: {str(e)}")
            return None
    
    async def _get_money_flow_data(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """获取资金流向数据"""
        try:
            # 从资金流向表获取数据
            money_flow = self.db["stock_money_flow"].find_one(
                {"ts_code": ts_code},
                sort=[("trade_date", -1)]
            )
            
            if not money_flow:
                return None
            
            net_inflow = money_flow.get("net_mf_amount", 0)
            
            # 计算资金流入强度（相对于成交额的比例）
            trade_amount = money_flow.get("trade_amount", 1)
            if trade_amount > 0:
                inflow_strength = abs(net_inflow) / trade_amount * 100
            else:
                inflow_strength = 0
            
            return {
                "net_inflow": net_inflow,
                "inflow_strength": min(100, inflow_strength)  # 最高100分
            }
            
        except Exception as e:
            print(f"获取资金流向数据失败 {ts_code}: {str(e)}")
            return None
    
    async def _get_institution_attention(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """获取机构关注度"""
        try:
            # 统计最近3个月的龙虎榜次数
            recent_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            
            dragon_tiger_count = self.db["top_list"].count_documents({
                "ts_code": ts_code,
                "trade_date": {"$gte": recent_date}
            })
            
            # 计算机构关注度评分
            attention_score = min(100, dragon_tiger_count * 5)  # 每次上榜5分，最高100分
            
            return {
                "attention_score": attention_score,
                "dragon_tiger_count": dragon_tiger_count
            }
            
        except Exception as e:
            print(f"获取机构关注度失败 {ts_code}: {str(e)}")
            return None

# ==================== 资金追踪分析器 ====================

class FundFlowAnalyzer:
    """资金追踪分析器 - 专门用于资金追踪策略"""
    
    def __init__(self):
        self.db = db_handler.db
    
    async def analyze_fund_flow(self, ts_code: str) -> Dict[str, Any]:
        """综合资金流向分析 - 重新设计版"""
        try:
            # 获取股票基本信息
            stock_info = self.db["infrastructure_stock_basic"].find_one({"ts_code": ts_code})
            if not stock_info:
                return {}
            
            # 并行获取各类数据
            margin_data = await self._analyze_margin_trading(ts_code)
            fund_data = await self._analyze_fund_flow(ts_code)
            industry_data = await self._analyze_industry_rotation(ts_code, stock_info.get("industry"))
            
            # 计算综合评分
            fund_tracking_score = self._calculate_enhanced_fund_tracking_score(margin_data, fund_data, industry_data)
            
            return {
                "margin_analysis": margin_data,
                "fund_analysis": fund_data, 
                "industry_analysis": industry_data,
                "fund_tracking_score": fund_tracking_score
            }
            
        except Exception as e:
            print(f"资金流向分析失败 {ts_code}: {str(e)}")
            return {}
    
    async def _analyze_margin_trading(self, ts_code: str) -> Dict[str, Any]:
        """分析个股两融数据"""
        try:
            # 获取最近10个交易日的两融数据
            recent_date = (datetime.now() - timedelta(days=15)).strftime('%Y%m%d')
            
            margin_cursor = self.db["margin_detail"].find({
                "ts_code": ts_code,
                "trade_date": {"$gte": recent_date}
            }).sort("trade_date", -1).limit(10)
            
            margin_data = list(margin_cursor)
            if not margin_data:
                return {
                    "margin_buy_trend": 0,
                    "margin_balance_growth": 0,
                    "margin_activity_score": 0,
                    "short_sell_trend": 0
                }
            
            # 计算融资买入趋势
            margin_buy_trend = self._calculate_margin_buy_trend(margin_data)
            
            # 计算融资余额增长率
            margin_balance_growth = self._calculate_margin_balance_growth(margin_data)
            
            # 计算两融活跃度评分
            margin_activity_score = self._calculate_margin_activity_score(margin_data)
            
            # 计算融券卖出趋势
            short_sell_trend = self._calculate_short_sell_trend(margin_data)
            
            return {
                "margin_buy_trend": margin_buy_trend,
                "margin_balance_growth": margin_balance_growth,
                "margin_activity_score": margin_activity_score,
                "short_sell_trend": short_sell_trend
            }
            
        except Exception as e:
            print(f"两融分析失败 {ts_code}: {str(e)}")
            return {
                "margin_buy_trend": 0,
                "margin_balance_growth": 0,
                "margin_activity_score": 0,
                "short_sell_trend": 0
            }
    
    def _calculate_margin_buy_trend(self, margin_data: List[Dict]) -> float:
        """计算融资买入趋势评分"""
        if len(margin_data) < 3:
            return 0
        
        try:
            # 计算最近3天融资买入额的平均值
            recent_buy = []
            for i in range(min(3, len(margin_data))):
                buy_amount = float(margin_data[i].get("rzmre", 0))
                recent_buy.append(buy_amount)
            
            # 计算前3-6天融资买入额的平均值作为基准
            baseline_buy = []
            for i in range(3, min(6, len(margin_data))):
                buy_amount = float(margin_data[i].get("rzmre", 0))
                baseline_buy.append(buy_amount)
            
            if not recent_buy or not baseline_buy:
                return 0
            
            recent_avg = sum(recent_buy) / len(recent_buy)
            baseline_avg = sum(baseline_buy) / len(baseline_buy)
            
            if baseline_avg == 0:
                return 50  # 中性评分
            
            # 计算趋势评分：增长率转换为0-100分
            growth_rate = (recent_avg - baseline_avg) / baseline_avg
            trend_score = max(0, min(100, 50 + growth_rate * 100))
            
            return trend_score
            
        except Exception:
            return 0
    
    def _calculate_margin_balance_growth(self, margin_data: List[Dict]) -> float:
        """计算融资余额增长率"""
        if len(margin_data) < 2:
            return 0
        
        try:
            # 最新融资余额
            latest_balance = float(margin_data[0].get("rzye", 0))
            # 一周前融资余额
            week_ago_balance = float(margin_data[-1].get("rzye", 0))
            
            if week_ago_balance == 0:
                return 0
            
            # 计算增长率并转换为评分
            growth_rate = (latest_balance - week_ago_balance) / week_ago_balance * 100
            growth_score = max(0, min(100, 50 + growth_rate * 2))  # 增长25%得100分
            
            return growth_score
            
        except Exception:
            return 0
    
    def _calculate_margin_activity_score(self, margin_data: List[Dict]) -> float:
        """计算两融活跃度评分"""
        if not margin_data:
            return 0
        
        try:
            total_activity = 0
            for item in margin_data:
                # 融资买入 + 融资偿还 + 融券卖出 + 融券偿还
                rzmre = float(item.get("rzmre", 0))
                rzche = float(item.get("rzche", 0))
                rqmcl = float(item.get("rqmcl", 0))
                rqchl = float(item.get("rqchl", 0))
                
                daily_activity = rzmre + rzche + rqmcl + rqchl
                total_activity += daily_activity
            
            # 计算平均每日活跃度
            avg_activity = total_activity / len(margin_data)
            
            # 转换为评分（假设日活跃度1000万为中等水平）
            activity_score = min(100, (avg_activity / 10000000) * 50)
            
            return activity_score
            
        except Exception:
            return 0
    
    def _calculate_short_sell_trend(self, margin_data: List[Dict]) -> float:
        """计算融券卖出趋势（负值表示看空情绪）"""
        if len(margin_data) < 3:
            return 50  # 中性
        
        try:
            # 计算最近融券卖出趋势
            recent_short = []
            for i in range(min(3, len(margin_data))):
                short_amount = float(margin_data[i].get("rqmcl", 0))
                recent_short.append(short_amount)
            
            baseline_short = []
            for i in range(3, min(6, len(margin_data))):
                short_amount = float(margin_data[i].get("rqmcl", 0))
                baseline_short.append(short_amount)
            
            if not recent_short or not baseline_short:
                return 50
            
            recent_avg = sum(recent_short) / len(recent_short)
            baseline_avg = sum(baseline_short) / len(baseline_short)
            
            if baseline_avg == 0:
                return 50
            
            # 融券增加为负面信号，减少为正面信号
            change_rate = (recent_avg - baseline_avg) / baseline_avg
            # 转换为评分：融券减少得高分，增加得低分
            trend_score = max(0, min(100, 50 - change_rate * 100))
            
            return trend_score
            
        except Exception:
            return 50
    
    def _calculate_cost_advantage(self, perf_data: List[Dict]) -> float:
        """计算成本优势"""
        if not perf_data:
            return 0
        
        try:
            perf = perf_data[0]
            cost_50pct = float(perf.get("cost_50pct", 0))  # 筹码成本中位数
            
            # 获取当前价格
            current_price = float(perf.get("close", 0))
            if current_price == 0 or cost_50pct == 0:
                return 0
            
            # 计算当前价格相对于筹码成本的优势
            # 当前价格越接近筹码成本，支撑越强
            price_ratio = current_price / cost_50pct
            
            if 0.95 <= price_ratio <= 1.05:  # 价格在成本附近±5%
                return 90  # 高支撑
            elif 0.9 <= price_ratio <= 1.1:  # 价格在成本附近±10%
                return 70  # 中等支撑
            elif 0.8 <= price_ratio <= 1.2:  # 价格在成本附近±20%
                return 50  # 一般支撑
            else:
                return 30  # 支撑较弱
                
        except Exception:
            return 0
    
    async def _analyze_fund_flow(self, ts_code: str) -> Dict[str, Any]:
        """分析资金流向"""
        try:
            # 获取最近5个交易日的资金流向数据
            recent_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
            
            fund_cursor = self.db["stock_money_flow"].find({
                "ts_code": ts_code,
                "trade_date": {"$gte": recent_date}
            }).sort("trade_date", -1).limit(5)
            
            fund_data = list(fund_cursor)
            if not fund_data:
                return {"large_order_net_inflow": 0, "super_large_net_inflow": 0, 
                       "fund_flow_continuity": 0, "institutional_fund_ratio": 0}
            
            # 计算大单和超大单净流入
            large_inflow = sum(float(item.get("buy_lg_amount", 0)) - float(item.get("sell_lg_amount", 0)) 
                             for item in fund_data) / 10000  # 转换为万元
            
            super_large_inflow = sum(float(item.get("buy_elg_amount", 0)) - float(item.get("sell_elg_amount", 0)) 
                                   for item in fund_data) / 10000  # 转换为万元
            
            # 计算资金流入连续性
            continuity = self._calculate_fund_continuity(fund_data)
            
            # 计算机构资金占比
            institutional_ratio = self._calculate_institutional_ratio(fund_data)
            
            return {
                "large_order_net_inflow": large_inflow,
                "super_large_net_inflow": super_large_inflow,
                "fund_flow_continuity": continuity,
                "institutional_fund_ratio": institutional_ratio
            }
            
        except Exception as e:
            print(f"资金流向分析失败 {ts_code}: {str(e)}")
            return {"large_order_net_inflow": 0, "super_large_net_inflow": 0, 
                   "fund_flow_continuity": 0, "institutional_fund_ratio": 0}
    
    def _calculate_fund_continuity(self, fund_data: List[Dict]) -> float:
        """计算资金流入连续性"""
        if not fund_data:
            return 0
        
        try:
            # 计算每日净流入
            daily_inflows = []
            for item in fund_data:
                net_inflow = (float(item.get("buy_lg_amount", 0)) + float(item.get("buy_elg_amount", 0))) - \
                           (float(item.get("sell_lg_amount", 0)) + float(item.get("sell_elg_amount", 0)))
                daily_inflows.append(net_inflow)
            
            # 计算连续流入天数
            positive_days = sum(1 for inflow in daily_inflows if inflow > 0)
            continuity_score = (positive_days / len(daily_inflows)) * 100
            
            return min(100, continuity_score)
            
        except Exception:
            return 0
    
    def _calculate_institutional_ratio(self, fund_data: List[Dict]) -> float:
        """计算机构资金占比"""
        if not fund_data:
            return 0
        
        try:
            # 计算超大单（机构资金）占比
            total_buy = sum(float(item.get("buy_lg_amount", 0)) + float(item.get("buy_elg_amount", 0)) 
                          for item in fund_data)
            institutional_buy = sum(float(item.get("buy_elg_amount", 0)) for item in fund_data)
            
            if total_buy > 0:
                ratio = (institutional_buy / total_buy) * 100
                return min(100, ratio)
            
            return 0
            
        except Exception:
            return 0
    
    async def _analyze_industry_rotation(self, ts_code: str, industry: str) -> Dict[str, Any]:
        """分析行业轮动"""
        try:
            if not industry:
                return {"industry_fund_rank": 999, "industry_fund_strength": 0, "sector_rotation_score": 0}
            
            # 获取最近1个交易日的行业资金流向数据
            recent_date = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d')
            
            industry_cursor = self.db["money_flow_industry"].find({
                "trade_date": {"$gte": recent_date},
                "content_type": "行业"
            }).sort("trade_date", -1).limit(50)
            
            industry_data = list(industry_cursor)
            if not industry_data:
                return {"industry_fund_rank": 999, "industry_fund_strength": 0, "sector_rotation_score": 0}
            
            # 找到目标行业的数据
            target_industry = None
            for item in industry_data:
                if industry in item.get("name", ""):
                    target_industry = item
                    break
            
            if not target_industry:
                return {"industry_fund_rank": 999, "industry_fund_strength": 0, "sector_rotation_score": 0}
            
            # 计算行业排名
            industry_rank = target_industry.get("rank", 999)
            
            # 计算行业资金流入强度
            net_amount = float(target_industry.get("net_amount", 0))
            industry_strength = max(0, min(100, net_amount / 100000000 * 100))  # 标准化到0-100
            
            # 计算行业轮动评分
            rotation_score = max(0, 100 - industry_rank)  # 排名越靠前评分越高
            
            return {
                "industry_fund_rank": industry_rank,
                "industry_fund_strength": industry_strength,
                "sector_rotation_score": rotation_score
            }
            
        except Exception as e:
            print(f"行业轮动分析失败 {ts_code}: {str(e)}")
            return {"industry_fund_rank": 999, "industry_fund_strength": 0, "sector_rotation_score": 0}
    
    def _calculate_enhanced_fund_tracking_score(self, margin_data: Dict, fund_data: Dict, industry_data: Dict) -> float:
        """计算增强版资金追踪综合评分"""
        try:
            # 两融评分（权重40%）
            margin_score = (
                margin_data.get("margin_buy_trend", 0) * 0.3 +           # 融资买入趋势30%
                margin_data.get("margin_balance_growth", 0) * 0.3 +      # 融资余额增长30%  
                margin_data.get("margin_activity_score", 0) * 0.2 +      # 两融活跃度20%
                margin_data.get("short_sell_trend", 0) * 0.2             # 融券趋势20%
            )
            
            # 资金流向评分（权重35%）
            fund_score = 0
            large_inflow = fund_data.get("large_order_net_inflow", 0)
            super_large_inflow = fund_data.get("super_large_net_inflow", 0)
            
            # 大单净流入评分
            if large_inflow > 0:
                fund_score += min(30, large_inflow / 1000000 * 10)  # 百万为单位，最高30分
            
            # 超大单净流入评分  
            if super_large_inflow > 0:
                fund_score += min(30, super_large_inflow / 5000000 * 10)  # 500万为单位，最高30分
            
            # 资金流入连续性和机构占比
            fund_score += fund_data.get("fund_flow_continuity", 0) * 0.2
            fund_score += fund_data.get("institutional_fund_ratio", 0) * 0.2
            
            fund_score = min(100, fund_score)
            
            # 行业轮动评分（权重25%）
            industry_score = (
                industry_data.get("industry_fund_strength", 0) * 0.6 + 
                industry_data.get("sector_rotation_score", 0) * 0.4
            )
            
            # 综合评分
            total_score = (
                margin_score * 0.4 + 
                fund_score * 0.35 + 
                industry_score * 0.25
            )
            
            return min(100, max(0, total_score))
            
        except Exception as e:
            print(f"计算资金追踪评分失败: {str(e)}")
            return 0

# ==================== 策略选股引擎 ====================

class StrategyScreeningEngine:
    """策略选股引擎"""
    
    def __init__(self):
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.special_analyzer = SpecialDataAnalyzer()
        self.fund_flow_analyzer = FundFlowAnalyzer()
        self.db = db_handler.db
    
    async def comprehensive_screening(
        self,
        stock_pool: List[str],
        technical_conditions: Dict[str, Any] = None,
        fundamental_conditions: Dict[str, Any] = None,
        special_conditions: Dict[str, Any] = None,
        strategy_type: str = "comprehensive",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """综合选股"""
        results = []
        
        for ts_code in stock_pool:
            try:
                # 获取股票基本信息
                stock_info = await self._get_stock_basic_info(ts_code)
                if not stock_info:
                    continue
                
                score = 0
                technical_data = None
                fundamental_data = None
                special_data = None
                fund_flow_data = None
                
                # 资金追踪策略分析
                if strategy_type == "fund_flow":
                    # 获取技术指标数据以获取基础股价信息
                    technical_data = await self.technical_analyzer.get_stock_technical_indicators(ts_code)
                    
                    fund_flow_result = await self.fund_flow_analyzer.analyze_fund_flow(ts_code)
                    if fund_flow_result:
                        fund_tracking_score = fund_flow_result.get("fund_tracking_score", 0)
                        
                        # 创建增强的special_data包含资金追踪信息
                        special_data = SpecialFeatures(
                            ts_code=ts_code,
                            name=stock_info.get('name', ''),
                            close=technical_data.close if technical_data else None,
                            # 两融数据
                            margin_buy_trend=fund_flow_result.get("margin_analysis", {}).get("margin_buy_trend", 0),
                            margin_balance_growth=fund_flow_result.get("margin_analysis", {}).get("margin_balance_growth", 0),
                            margin_activity_score=fund_flow_result.get("margin_analysis", {}).get("margin_activity_score", 0),
                            short_sell_trend=fund_flow_result.get("margin_analysis", {}).get("short_sell_trend", 0),
                            # 资金流数据
                            large_order_net_inflow=fund_flow_result.get("fund_analysis", {}).get("large_order_net_inflow", 0),
                            super_large_net_inflow=fund_flow_result.get("fund_analysis", {}).get("super_large_net_inflow", 0),
                            fund_flow_continuity=fund_flow_result.get("fund_analysis", {}).get("fund_flow_continuity", 0),
                            institutional_fund_ratio=fund_flow_result.get("fund_analysis", {}).get("institutional_fund_ratio", 0),
                            # 行业数据
                            industry_fund_rank=fund_flow_result.get("industry_analysis", {}).get("industry_fund_rank", 999),
                            industry_fund_strength=fund_flow_result.get("industry_analysis", {}).get("industry_fund_strength", 0),
                            sector_rotation_score=fund_flow_result.get("industry_analysis", {}).get("sector_rotation_score", 0),
                            fund_tracking_score=fund_tracking_score
                        )
                        
                        # 检查资金追踪条件
                        if self._check_fund_flow_conditions(special_data, special_conditions or {}):
                            score = fund_tracking_score
                        
                        fund_flow_data = fund_flow_result
                
                # 技术面分析
                elif strategy_type in ["technical", "comprehensive"] and technical_conditions:
                    technical_data = await self.technical_analyzer.get_stock_technical_indicators(ts_code)
                    if technical_data and self._check_technical_conditions(technical_data, technical_conditions):
                        score += 30
                
                # 基本面分析
                if strategy_type in ["fundamental", "comprehensive"] and fundamental_conditions:
                    fundamental_data = await self.fundamental_analyzer.get_stock_fundamental_scores(ts_code)
                    if fundamental_data and self._check_fundamental_conditions(fundamental_data, fundamental_conditions):
                        score += 40
                
                # 特色数据分析
                elif strategy_type in ["special", "comprehensive"] and special_conditions:
                    special_data = await self.special_analyzer.get_stock_special_features(ts_code)
                    if special_data and self._check_special_conditions(special_data, special_conditions):
                        score += 30
                
                # 如果满足条件，加入结果
                if score > 0 or strategy_type == "comprehensive":
                    result = {
                        'ts_code': ts_code,
                        'name': stock_info.get('name', ''),
                        'industry': stock_info.get('industry', ''),
                        'market': stock_info.get('market', ''),
                        'score': score,
                        'technical': technical_data.__dict__ if technical_data else None,
                        'fundamental': fundamental_data.__dict__ if fundamental_data else None,
                        'special': special_data.__dict__ if special_data else None,
                        'fund_flow': fund_flow_data
                    }
                    results.append(result)
                    
            except Exception as e:
                print(f"处理股票 {ts_code} 时出错: {e}")
                continue
        
        # 按评分排序并限制数量
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    async def _get_stock_basic_info(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        try:
            stock_info = self.db["infrastructure_stock_basic"].find_one({"ts_code": ts_code})
            return stock_info
        except Exception:
            return None
    
    def _check_technical_conditions(self, data: Optional[TechnicalIndicators], conditions: Dict[str, Any]) -> bool:
        """检查技术面条件"""
        if not data:
            return False
        
        try:
            # RSI条件
            if "rsi_min" in conditions and data.rsi is not None:
                if data.rsi < conditions["rsi_min"]:
                    return False
            if "rsi_max" in conditions and data.rsi is not None:
                if data.rsi > conditions["rsi_max"]:
                    return False
            
            # MACD条件
            if "macd_positive" in conditions and conditions["macd_positive"]:
                if data.macd is None or data.macd <= 0:
                    return False
            
            # 均线条件
            if "above_ma20" in conditions and conditions["above_ma20"]:
                if data.ma20 is None or data.close is None or data.close <= data.ma20:
                    return False
            
            # 量比条件
            if "volume_ratio_min" in conditions and data.volume_ratio is not None:
                if data.volume_ratio < conditions["volume_ratio_min"]:
                    return False
            
            # KDJ条件
            if "kdj_k_min" in conditions and data.kdj_k is not None:
                if data.kdj_k < conditions["kdj_k_min"]:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _check_fundamental_conditions(self, data: Optional[FundamentalScores], conditions: Dict[str, Any]) -> bool:
        """检查基本面条件"""
        if not data:
            return False
        
        try:
            # 综合评分条件
            if "total_score_min" in conditions and data.total_score is not None:
                if data.total_score < conditions["total_score_min"]:
                    return False
            
            # ROE条件
            if "roe_min" in conditions and data.roe is not None:
                if data.roe < conditions["roe_min"]:
                    return False
            
            # PE条件
            if "pe_max" in conditions and data.pe is not None:
                if data.pe > conditions["pe_max"]:
                    return False
            
            # PB条件
            if "pb_max" in conditions and data.pb is not None:
                if data.pb > conditions["pb_max"]:
                    return False
            
            # 成长性评分条件
            if "growth_score_min" in conditions and data.growth_score is not None:
                if data.growth_score < conditions["growth_score_min"]:
                    return False
            
            # 盈利能力评分条件
            if "profitability_score_min" in conditions and data.profitability_score is not None:
                if data.profitability_score < conditions["profitability_score_min"]:
                    return False
            
            # 资产负债率条件
            if "debt_ratio_max" in conditions and data.debt_ratio is not None:
                if data.debt_ratio > conditions["debt_ratio_max"]:
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def screen_stocks(
        self,
        technical_conditions: Optional[Dict[str, Any]] = None,
        fundamental_conditions: Optional[Dict[str, Any]] = None,
        special_conditions: Optional[Dict[str, Any]] = None,
        stock_pool: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """综合选股（保持向后兼容）"""
        try:
            # 获取股票池
            if stock_pool:
                ts_codes = stock_pool
            else:
                # 获取所有A股股票
                cursor = self.db["infrastructure_stock_basic"].find(
                    {"market": {"$in": ["主板", "创业板", "科创板"]}},
                    {"ts_code": 1}
                )
                ts_codes = [doc["ts_code"] for doc in cursor]
            
            results = []
            processed = 0
            
            for ts_code in ts_codes:
                if processed >= limit * 3:  # 最多处理3倍数量，避免超时
                    break
                
                try:
                    # 获取各类指标
                    technical_data = None
                    fundamental_data = None
                    special_data = None
                    
                    if technical_conditions:
                        technical_data = await self.technical_analyzer.get_stock_technical_indicators(ts_code)
                        if not self._check_technical_conditions(technical_data, technical_conditions):
                            processed += 1
                            continue
                    
                    if fundamental_conditions:
                        fundamental_data = await self.fundamental_analyzer.get_stock_fundamental_scores(ts_code)
                        if not self._check_fundamental_conditions(fundamental_data, fundamental_conditions):
                            processed += 1
                            continue
                    
                    if special_conditions:
                        special_data = await self.special_analyzer.get_stock_special_features(ts_code)
                        if not self._check_special_conditions(special_data, special_conditions):
                            processed += 1
                            continue
                    
                    # 构建结果
                    result = {
                        "ts_code": ts_code,
                        "name": "",
                        "technical": technical_data.__dict__ if technical_data else None,
                        "fundamental": fundamental_data.__dict__ if fundamental_data else None,
                        "special": special_data.__dict__ if special_data else None,
                        "score": self._calculate_composite_score(technical_data, fundamental_data, special_data)
                    }
                    
                    # 获取股票名称
                    stock_basic = self.db["infrastructure_stock_basic"].find_one({"ts_code": ts_code})
                    if stock_basic:
                        result["name"] = stock_basic["name"]
                        result["industry"] = stock_basic.get("industry")
                        result["market"] = stock_basic.get("market")
                    
                    results.append(result)
                    
                    if len(results) >= limit:
                        break
                    
                except Exception as e:
                    print(f"处理股票 {ts_code} 时出错: {str(e)}")
                
                processed += 1
            
            # 按综合评分排序
            results.sort(key=lambda x: x["score"] or 0, reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            print(f"选股失败: {str(e)}")
            return []
    
    def _check_technical_conditions(self, data: Optional[TechnicalIndicators], conditions: Dict[str, Any]) -> bool:
        """检查技术面条件"""
        if not data:
            return False
        
        try:
            # RSI条件
            if "rsi_min" in conditions and data.rsi is not None:
                if data.rsi < conditions["rsi_min"]:
                    return False
            
            if "rsi_max" in conditions and data.rsi is not None:
                if data.rsi > conditions["rsi_max"]:
                    return False
            
            # MACD条件
            if "macd_positive" in conditions and conditions["macd_positive"]:
                if data.macd is None or data.macd <= 0:
                    return False
            
            # 均线条件
            if "above_ma20" in conditions and conditions["above_ma20"]:
                if data.ma20 is None or data.close <= data.ma20:
                    return False
            
            # 量比条件
            if "volume_ratio_min" in conditions and data.volume_ratio is not None:
                if data.volume_ratio < conditions["volume_ratio_min"]:
                    return False
            
            return True
            
        except Exception as e:
            print(f"检查技术条件失败: {str(e)}")
            return False
    
    def _check_fundamental_conditions(self, data: Optional[FundamentalScores], conditions: Dict[str, Any]) -> bool:
        """检查基本面条件"""
        if not data:
            return False
        
        try:
            # 总评分条件
            if "total_score_min" in conditions and data.total_score is not None:
                if data.total_score < conditions["total_score_min"]:
                    return False
            
            # ROE条件
            if "roe_min" in conditions and data.roe is not None:
                if data.roe < conditions["roe_min"]:
                    return False
            
            # PE条件
            if "pe_max" in conditions and data.pe is not None:
                if data.pe > conditions["pe_max"]:
                    return False
            
            # 成长性条件
            if "growth_score_min" in conditions and data.growth_score is not None:
                if data.growth_score < conditions["growth_score_min"]:
                    return False
            
            return True
            
        except Exception as e:
            print(f"检查基本面条件失败: {str(e)}")
            return False
    
    def _check_special_conditions(self, data: Optional[SpecialFeatures], conditions: Dict[str, Any]) -> bool:
        """检查特色条件"""
        if not data:
            return False
        
        try:
            # 连板条件
            if "limit_days_min" in conditions and data.limit_days is not None:
                if data.limit_days < conditions["limit_days_min"]:
                    return False
            
            # 资金流入条件
            if "net_inflow_positive" in conditions and conditions["net_inflow_positive"]:
                if data.net_inflow is None or data.net_inflow <= 0:
                    return False
            
            # 游资关注条件
            if "hot_money_score_min" in conditions and data.hot_money_score is not None:
                if data.hot_money_score < conditions["hot_money_score_min"]:
                    return False
            
            return True
            
        except Exception as e:
            print(f"检查特色条件失败: {str(e)}")
            return False
    
    def _check_fund_flow_conditions(self, data: Optional[SpecialFeatures], conditions: Dict[str, Any]) -> bool:
        """检查资金追踪条件 - 增强版"""
        if not data:
            return False
        
        try:
            # 两融条件检查
            if "margin_buy_trend_min" in conditions and data.margin_buy_trend is not None:
                if data.margin_buy_trend < conditions["margin_buy_trend_min"]:
                    return False
            
            if "margin_balance_growth_min" in conditions and data.margin_balance_growth is not None:
                if data.margin_balance_growth < conditions["margin_balance_growth_min"]:
                    return False
            
            if "margin_activity_min" in conditions and data.margin_activity_score is not None:
                if data.margin_activity_score < conditions["margin_activity_min"]:
                    return False
            
            if "short_sell_trend_min" in conditions and data.short_sell_trend is not None:
                if data.short_sell_trend < conditions["short_sell_trend_min"]:
                    return False
            
            # 大单净流入条件
            if "large_order_inflow_positive" in conditions and conditions["large_order_inflow_positive"]:
                if data.large_order_net_inflow is None or data.large_order_net_inflow <= 0:
                    return False
            
            if "large_order_inflow_min" in conditions and data.large_order_net_inflow is not None:
                if data.large_order_net_inflow < conditions["large_order_inflow_min"]:
                    return False
            
            # 超大单净流入条件
            if "super_large_inflow_positive" in conditions and conditions["super_large_inflow_positive"]:
                if data.super_large_net_inflow is None or data.super_large_net_inflow <= 0:
                    return False
            
            if "super_large_inflow_min" in conditions and data.super_large_net_inflow is not None:
                if data.super_large_net_inflow < conditions["super_large_inflow_min"]:
                    return False
            
            # 资金流入连续性条件
            if "fund_continuity_min" in conditions and data.fund_flow_continuity is not None:
                if data.fund_flow_continuity < conditions["fund_continuity_min"]:
                    return False
            
            # 机构资金占比条件
            if "institutional_ratio_min" in conditions and data.institutional_fund_ratio is not None:
                if data.institutional_fund_ratio < conditions["institutional_ratio_min"]:
                    return False
            
            # 行业资金排名条件
            if "industry_rank_max" in conditions and data.industry_fund_rank is not None:
                if data.industry_fund_rank > conditions["industry_rank_max"]:
                    return False
            
            # 行业资金强度条件
            if "industry_strength_min" in conditions and data.industry_fund_strength is not None:
                if data.industry_fund_strength < conditions["industry_strength_min"]:
                    return False
            
            # 资金追踪综合评分条件
            if "fund_tracking_score_min" in conditions and data.fund_tracking_score is not None:
                if data.fund_tracking_score < conditions["fund_tracking_score_min"]:
                    return False
            
            return True
            
        except Exception as e:
            print(f"检查资金追踪条件失败: {str(e)}")
            return False
    
    def _calculate_composite_score(
        self,
        technical: Optional[TechnicalIndicators],
        fundamental: Optional[FundamentalScores],
        special: Optional[SpecialFeatures]
    ) -> Optional[float]:
        """计算综合评分"""
        try:
            scores = []
            weights = []
            
            # 技术面评分（权重30%）
            if technical:
                tech_score = 0
                tech_count = 0
                
                # RSI评分（50为中性）
                if technical.rsi is not None:
                    if 30 <= technical.rsi <= 70:
                        tech_score += 70  # 中性区间较好
                    elif technical.rsi < 30:
                        tech_score += 90  # 超卖区间很好
                    else:
                        tech_score += 30  # 超买区间较差
                    tech_count += 1
                
                # MACD评分
                if technical.macd is not None and technical.macd_signal is not None:
                    if technical.macd > technical.macd_signal:
                        tech_score += 80  # 金叉较好
                    else:
                        tech_score += 40  # 死叉较差
                    tech_count += 1
                
                # 均线评分
                if technical.ma20 is not None:
                    if technical.close > technical.ma20:
                        tech_score += 70  # 站上20日线
                    else:
                        tech_score += 30  # 跌破20日线
                    tech_count += 1
                
                if tech_count > 0:
                    scores.append(tech_score / tech_count)
                    weights.append(0.3)
            
            # 基本面评分（权重40%）
            if fundamental and fundamental.total_score is not None:
                scores.append(fundamental.total_score)
                weights.append(0.4)
            
            # 特色数据评分（权重30%）
            if special:
                special_score = 0
                special_count = 0
                
                if special.limit_strength is not None:
                    special_score += special.limit_strength
                    special_count += 1
                
                if special.hot_money_score is not None:
                    special_score += special.hot_money_score
                    special_count += 1
                
                if special.inflow_strength is not None:
                    special_score += special.inflow_strength
                    special_count += 1
                
                if special_count > 0:
                    scores.append(special_score / special_count)
                    weights.append(0.3)
            
            # 计算加权平均分
            if scores:
                total_weight = sum(weights)
                if total_weight > 0:
                    weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / total_weight
                    return round(weighted_score, 2)
            
            return None
            
        except Exception as e:
            print(f"计算综合评分失败: {str(e)}")
            return None