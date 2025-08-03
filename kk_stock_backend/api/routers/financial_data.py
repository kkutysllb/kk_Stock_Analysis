#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据API接口
支持三大报表、财务指标、业绩预告等数据查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import sys
import os

# 导入缓存装饰器
from api.cache_middleware import cache_endpoint
from api.global_db import db_handler

# 添加项目根目录到sys.path以便导入数据库管理器
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(api_dir)
sys.path.insert(0, project_root)


router = APIRouter()

sys.path.insert(0, project_root)


# ==================== 财务数据查询 ====================

@cache_endpoint(data_type='financial_data', ttl=14400)  # 缓存4小时
@router.get("/income/{ts_code}")
async def get_income_statement(
    ts_code: str,
    period: str = Query(default="20231231", description="报告期 YYYYMMDD"),
    limit: int = Query(default=5, description="获取期数")
):
    """
    获取利润表数据
    """
    try:
        collection = db_handler.get_collection('income')
        
        cursor = collection.find(
            {"ts_code": ts_code},
            {"_id": 0}
        ).sort("end_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "income_statements": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取利润表失败: {str(e)}")

@cache_endpoint(data_type='financial_data', ttl=14400)  # 缓存4小时
@router.get("/balancesheet/{ts_code}")
async def get_balance_sheet(
    ts_code: str,
    limit: int = Query(default=5, description="获取期数")
):
    """
    获取资产负债表数据
    """
    try:
        collection = db_handler.get_collection('balancesheet')
        
        cursor = collection.find(
            {"ts_code": ts_code},
            {"_id": 0}
        ).sort("end_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "balance_sheets": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资产负债表失败: {str(e)}")

@cache_endpoint(data_type='financial_data', ttl=14400)  # 缓存4小时
@router.get("/cashflow/{ts_code}")
async def get_cash_flow(
    ts_code: str,
    limit: int = Query(default=5, description="获取期数")
):
    """
    获取现金流量表数据
    """
    try:
        collection = db_handler.get_collection('cashflow')
        
        cursor = collection.find(
            {"ts_code": ts_code},
            {"_id": 0}
        ).sort("end_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "cash_flows": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取现金流量表失败: {str(e)}")

@cache_endpoint(data_type='financial_data', ttl=14400)  # 缓存4小时
@router.get("/indicators/{ts_code}")
async def get_financial_indicators(
    ts_code: str,
    limit: int = Query(default=5, description="获取期数")
):
    """
    获取财务指标数据
    """
    try:
        collection = db_handler.get_collection('fina_indicator')
        
        cursor = collection.find(
            {"ts_code": ts_code},
            {"_id": 0}
        ).sort("end_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "financial_indicators": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财务指标失败: {str(e)}")

@cache_endpoint(data_type='financial_data', ttl=14400)  # 缓存4小时
@router.get("/analysis/{ts_code}")
async def get_financial_analysis(
    ts_code: str,
    years: int = Query(default=3, description="分析年数")
):
    """
    获取财务分析汇总
    """
    try:
        # 获取财务指标
        fina_collection = db_handler.get_collection('fina_indicator')
        indicators = list(fina_collection.find(
            {"ts_code": ts_code},
            {"_id": 0}
        ).sort("end_date", -1).limit(years * 4))  # 假设一年4个季度
        
        if not indicators:
            raise HTTPException(status_code=404, detail="未找到财务数据")
        
        # 简单的财务分析
        latest = indicators[0] if indicators else {}
        
        analysis = {
            "profitability": {
                "roe": latest.get("roe", 0),
                "roa": latest.get("roa", 0),
                "gross_margin": latest.get("grossprofit_margin", 0),
                "net_margin": latest.get("netprofit_margin", 0)
            },
            "growth": {
                "revenue_growth": latest.get("q_gr_yoy", 0),
                "profit_growth": latest.get("q_profit_yoy", 0)
            },
            "financial_health": {
                "debt_ratio": latest.get("debt_to_assets", 0),
                "current_ratio": latest.get("current_ratio", 0),
                "quick_ratio": latest.get("quick_ratio", 0)
            }
        }
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "analysis_period": f"{years}年",
                "financial_analysis": analysis,
                "latest_period": latest.get("end_date", ""),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"财务分析失败: {str(e)}")

@cache_endpoint(data_type='financial_data', ttl=14400)  # 缓存4小时
@router.get("/express/{ts_code}")
async def get_express_report(
    ts_code: str,
    limit: int = Query(default=10, description="获取期数")
):
    """
    获取业绩快报数据
    """
    try:
        collection = db_handler.get_collection('express')
        
        cursor = collection.find(
            {"ts_code": ts_code},
            {"_id": 0}
        ).sort("ann_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "express_reports": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取业绩快报失败: {str(e)}")

@cache_endpoint(data_type='financial_data', ttl=7200)  # 缓存2小时
@router.get("/forecast")
async def get_forecast_data(
    ts_code: Optional[str] = Query(default=None, description="股票代码"),
    limit: int = Query(default=20, description="返回数量")
):
    """
    获取业绩预告数据
    """
    try:
        collection = db_handler.get_collection('forecast')
        
        query = {}
        if ts_code:
            query["ts_code"] = ts_code
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("ann_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "filter_ts_code": ts_code,
                "forecasts": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取业绩预告失败: {str(e)}")