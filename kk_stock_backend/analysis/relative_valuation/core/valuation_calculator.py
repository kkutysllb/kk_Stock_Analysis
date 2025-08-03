"""估值计算器核心模块"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pymongo import MongoClient
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.relative_valuation.models.valuation_models import ValuationMetrics
from api.global_db import db_handler

logger = logging.getLogger(__name__)


class ValuationCalculator:
    """估值计算器
    
    基于数据库中的财务数据计算各种估值指标
    """
    
    def __init__(self):
        """初始化估值计算器"""
        self.db_handler = db_handler
        
    def calculate_valuation_metrics(self, ts_code: str, end_date: str = None) -> Optional[ValuationMetrics]:
        """计算个股估值指标
        
        Args:
            ts_code: 股票代码
            end_date: 截止日期，格式YYYYMMDD，默认为最新数据
            
        Returns:
            ValuationMetrics: 估值指标对象
        """
        try:
            # 获取财务数据
            financial_data = self._get_financial_data(ts_code, end_date)
            if not financial_data:
                logger.warning(f"未找到股票 {ts_code} 的财务数据")
                return None
                
            # 获取股价数据计算市值
            market_data = self._get_market_data(ts_code, end_date)
            if not market_data:
                logger.warning(f"未找到股票 {ts_code} 的市场数据")
                return None
                
            # 计算估值指标
            metrics = self._calculate_metrics(ts_code, financial_data, market_data, end_date)
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算估值指标失败: {e}")
            return None
    
    def calculate_ttm_metrics(self, ts_code: str, end_date: str = None) -> Optional[ValuationMetrics]:
        """计算TTM（过去12个月）估值指标
        
        Args:
            ts_code: 股票代码
            end_date: 截止日期
            
        Returns:
            ValuationMetrics: TTM估值指标
        """
        try:
            # 获取过去4个季度的财务数据
            ttm_data = self._get_ttm_financial_data(ts_code, end_date)
            if not ttm_data:
                return None
                
            # 获取当前市场数据
            market_data = self._get_market_data(ts_code, end_date)
            if not market_data:
                return None
                
            # 计算TTM指标
            metrics = self._calculate_ttm_metrics(ts_code, ttm_data, market_data, end_date)
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算TTM估值指标失败: {e}")
            return None
    
    def _get_financial_data(self, ts_code: str, end_date: str = None) -> Optional[Dict]:
        """获取财务数据"""
        try:
            # 构建查询条件
            query = {"ts_code": ts_code}
            if end_date:
                query["end_date"] = {"$lte": end_date}
            
            # 获取最新的财务指标数据
            fina_indicator = self.db_handler.get_collection("stock_fina_indicator").find(
                query
            ).sort("end_date", -1).limit(1)
            
            fina_data = list(fina_indicator)
            if not fina_data:
                return None
                
            latest_end_date = fina_data[0]["end_date"]
            
            # 获取对应期间的利润表数据
            income_data = list(self.db_handler.get_collection("stock_income").find({
                "ts_code": ts_code,
                "end_date": latest_end_date
            }))
            
            # 获取对应期间的资产负债表数据
            balance_data = list(self.db_handler.get_collection("stock_balance_sheet").find({
                "ts_code": ts_code,
                "end_date": latest_end_date
            }))
            
            # 获取对应期间的现金流量表数据
            cashflow_data = list(self.db_handler.get_collection("stock_cash_flow").find({
                "ts_code": ts_code,
                "end_date": latest_end_date
            }))
            
            return {
                "fina_indicator": fina_data[0] if fina_data else {},
                "income": income_data[0] if income_data else {},
                "balance_sheet": balance_data[0] if balance_data else {},
                "cash_flow": cashflow_data[0] if cashflow_data else {},
                "end_date": latest_end_date
            }
            
        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            return None
    
    def _get_market_data(self, ts_code: str, end_date: str = None) -> Optional[Dict]:
        """获取市场数据（股价、市值等）"""
        try:
            # 从stock_factor_pro表中获取最新的市值相关数据
            query = {"ts_code": ts_code}
            # 不限制日期，获取最新的市值数据
                
            factor_data = list(self.db_handler.get_collection("stock_factor_pro").find(
                query
            ).sort("trade_date", -1).limit(1))
            
            if not factor_data:
                return None
                
            data = factor_data[0]
            
            # 从stock_factor_pro中提取市值相关数据
            market_cap = None
            if "total_mv" in data and data["total_mv"]:  # 总市值（万元）
                market_cap = data["total_mv"] * 10000  # 转换为元
            
            return {
                "market_cap": market_cap,
                "end_date": data.get("trade_date")
            }
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return None
    
    def _get_ttm_financial_data(self, ts_code: str, end_date: str = None) -> Optional[Dict]:
        """获取TTM财务数据（过去4个季度累计）"""
        try:
            # 获取过去4个季度的数据
            query = {"ts_code": ts_code}
            if end_date:
                query["end_date"] = {"$lte": end_date}
                
            # 获取利润表数据（过去4个季度）
            income_data = list(self.db_handler.get_collection("stock_income").find(
                query
            ).sort("end_date", -1).limit(4))
            
            if len(income_data) < 4:
                logger.warning(f"股票 {ts_code} 的季度数据不足4个季度")
                return None
            
            # 计算TTM累计值
            ttm_revenue = sum([d.get("revenue", 0) or 0 for d in income_data])
            ttm_net_profit = sum([d.get("n_income", 0) or 0 for d in income_data])
            
            # 获取现金流数据
            cashflow_data = list(self.db_handler.get_collection("stock_cash_flow").find(
                query
            ).sort("end_date", -1).limit(4))
            
            ttm_operating_cf = 0
            if len(cashflow_data) >= 4:
                ttm_operating_cf = sum([d.get("n_cashflow_act", 0) or 0 for d in cashflow_data])
            
            # 获取最新的资产负债表数据
            balance_data = list(self.db_handler.get_collection("stock_balance_sheet").find(
                query
            ).sort("end_date", -1).limit(1))
            
            latest_balance = balance_data[0] if balance_data else {}
            
            return {
                "ttm_revenue": ttm_revenue,
                "ttm_net_profit": ttm_net_profit,
                "ttm_operating_cf": ttm_operating_cf,
                "total_assets": latest_balance.get("total_assets", 0),
                "total_liab": latest_balance.get("total_liab", 0),
                "end_date": income_data[0]["end_date"] if income_data else None
            }
            
        except Exception as e:
            logger.error(f"获取TTM财务数据失败: {e}")
            return None
    
    def _calculate_metrics(self, ts_code: str, financial_data: Dict, market_data: Dict, end_date: str) -> ValuationMetrics:
        """计算估值指标"""
        fina = financial_data.get("fina_indicator", {})
        income = financial_data.get("income", {})
        balance = financial_data.get("balance_sheet", {})
        cashflow = financial_data.get("cash_flow", {})
        
        # 基础财务数据
        market_cap = market_data.get("market_cap")
        total_revenue = income.get("revenue")
        net_profit = income.get("n_income")
        total_assets = balance.get("total_assets")
        total_liabilities = balance.get("total_liab")
        # 计算股东权益 = 总资产 - 总负债
        shareholders_equity = None
        if total_assets and total_liabilities:
            shareholders_equity = total_assets - total_liabilities
        operating_cash_flow = cashflow.get("n_cashflow_act")
        
        # 计算估值倍数
        pe_ratio = None
        pb_ratio = None
        ps_ratio = None
        pcf_ratio = None
        
        if market_cap:
            # 市盈率 = 总市值 / 净利润
            if net_profit and net_profit > 0:
                pe_ratio = market_cap / net_profit
                
            # 市净率 = 总市值 / 股东权益
            if shareholders_equity and shareholders_equity > 0:
                pb_ratio = market_cap / shareholders_equity
                
            # 市销率 = 总市值 / 营业收入
            if total_revenue and total_revenue > 0:
                ps_ratio = market_cap / total_revenue
                
            # 市现率 = 总市值 / 经营现金流
            if operating_cash_flow and operating_cash_flow > 0:
                pcf_ratio = market_cap / operating_cash_flow
        
        return ValuationMetrics(
            ts_code=ts_code,
            end_date=end_date or financial_data.get("end_date"),
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            ps_ratio=ps_ratio,
            pcf_ratio=pcf_ratio,
            market_cap=market_cap,
            total_revenue=total_revenue,
            net_profit=net_profit,
            total_assets=total_assets,
            shareholders_equity=shareholders_equity,
            operating_cash_flow=operating_cash_flow
        )
    
    def _calculate_ttm_metrics(self, ts_code: str, ttm_data: Dict, market_data: Dict, end_date: str) -> ValuationMetrics:
        """计算TTM估值指标"""
        market_cap = market_data.get("market_cap")
        ttm_revenue = ttm_data.get("ttm_revenue")
        ttm_net_profit = ttm_data.get("ttm_net_profit")
        ttm_operating_cf = ttm_data.get("ttm_operating_cf")
        total_assets = ttm_data.get("total_assets")
        total_liabilities = ttm_data.get("total_liab")
        # 计算股东权益 = 总资产 - 总负债
        shareholders_equity = None
        if total_assets and total_liabilities:
            shareholders_equity = total_assets - total_liabilities
        
        # 计算TTM估值倍数
        pe_ttm = None
        pb_ttm = None
        ps_ttm = None
        pcf_ttm = None
        
        if market_cap:
            if ttm_net_profit and ttm_net_profit > 0:
                pe_ttm = market_cap / ttm_net_profit
                
            if shareholders_equity and shareholders_equity > 0:
                pb_ttm = market_cap / shareholders_equity
                
            if ttm_revenue and ttm_revenue > 0:
                ps_ttm = market_cap / ttm_revenue
                
            if ttm_operating_cf and ttm_operating_cf > 0:
                pcf_ttm = market_cap / ttm_operating_cf
        
        return ValuationMetrics(
            ts_code=ts_code,
            end_date=end_date or ttm_data.get("end_date"),
            pe_ttm=pe_ttm,
            pb_ttm=pb_ttm,
            ps_ttm=ps_ttm,
            pcf_ttm=pcf_ttm,
            market_cap=market_cap,
            total_revenue=ttm_revenue,
            net_profit=ttm_net_profit,
            total_assets=total_assets,
            shareholders_equity=shareholders_equity,
            operating_cash_flow=ttm_operating_cf
        )
    
    def get_stock_industry(self, ts_code: str) -> Optional[str]:
        """获取股票所属行业"""
        try:
            stock_basic = list(self.db_handler.get_collection("infrastructure_stock_basic").find({
                "ts_code": ts_code
            }).limit(1))
            
            if stock_basic:
                return stock_basic[0].get("industry")
            return None
            
        except Exception as e:
            logger.error(f"获取股票行业信息失败: {e}")
            return None