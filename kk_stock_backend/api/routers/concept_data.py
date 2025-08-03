# -*- coding: utf-8 -*-
"""
概念板块和行业数据API接口
支持涨跌停概念数据、申万行业指数等数据查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel, Field

import sys
import os
from api.global_db import db_handler

# 添加项目根目录到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


sys.path.insert(0, project_root)


# 创建路由器
router = APIRouter(prefix="/concept", tags=["概念板块数据"])


# ==================== 数据模型定义 ====================

class BatchLimitDataRequest(BaseModel):
    """批量涨跌停数据查询请求模型"""
    trade_dates: List[str] = Field(..., description="交易日期列表(YYYYMMDD格式)")
    limit_per_date: int = Field(default=100, description="每个日期返回的最大条数")
    limit_type: Optional[str] = Field(default=None, description="涨跌停类型: U-涨停, D-跌停")

class BatchSWDailyRequest(BaseModel):
    """批量申万行业日线数据查询请求模型"""
    trade_dates: List[str] = Field(..., description="交易日期列表(YYYYMMDD格式)")
    industry_codes: Optional[List[str]] = Field(default=None, description="行业代码列表")
    limit_per_date: int = Field(default=100, description="每个日期返回的最大条数")


# ==================== 涨跌停概念数据 ====================

@router.get("/limit/list")
async def get_limit_concept_list(
    trade_date: Optional[str] = Query(default=None, description="交易日期(YYYYMMDD)"),
    limit_type: Optional[str] = Query(default=None, description="涨跌停类型: U-涨停, D-跌停"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取涨跌停概念数据列表
    """
    try:
        collection = db_handler.get_collection('limit_cpt_list')
        
        # 构建查询条件
        query = {}
        
        if trade_date:
            query["trade_date"] = trade_date
        
        if limit_type:
            query["limit_type"] = limit_type
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("trade_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "limit_type": limit_type,
                "limit_concepts": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨跌停概念数据失败: {str(e)}")

@router.get("/limit/search")
async def search_limit_concepts(
    keyword: str = Query(description="搜索关键词（股票名称或代码）"),
    start_date: Optional[str] = Query(default=None, description="开始日期(YYYYMMDD)"),
    end_date: Optional[str] = Query(default=None, description="结束日期(YYYYMMDD)"),
    limit: int = Query(default=50, description="返回条数")
):
    """
    搜索涨跌停概念数据（支持名称和代码模糊匹配）
    """
    try:
        collection = db_handler.get_collection('limit_cpt_list')
        
        # 构建搜索条件
        query = {
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"ts_code": {"$regex": keyword, "$options": "i"}}
            ]
        }
        
        # 添加日期范围条件
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["trade_date"] = date_query
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("trade_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "limit_concepts": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索涨跌停概念数据失败: {str(e)}")

# ==================== 申万行业指数数据 ====================

@router.get("/sw/daily")
async def get_sw_industry_daily(
    ts_code: Optional[str] = Query(default=None, description="申万行业指数代码"),
    trade_date: Optional[str] = Query(default=None, description="交易日期(YYYYMMDD)"),
    start_date: Optional[str] = Query(default=None, description="开始日期(YYYYMMDD)"),
    end_date: Optional[str] = Query(default=None, description="结束日期(YYYYMMDD)"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取申万行业指数日线数据
    """
    try:
        collection = db_handler.get_collection('sw_daily')
        
        # 构建查询条件
        query = {}
        
        if ts_code:
            query["ts_code"] = ts_code
        
        if trade_date:
            query["trade_date"] = trade_date
        elif start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["trade_date"] = date_query
        
        # 构建排序和限制
        sort_order = [("trade_date", -1)]
        
        # 当只有end_date时，我们需要获取最近的数据
        if end_date and not start_date and not trade_date:
            # 确保获取到最新的数据，按日期倒序排列
            cursor = collection.find(
                query,
                {"_id": 0}
            ).sort(sort_order).limit(limit)
        else:
            cursor = collection.find(
                query,
                {"_id": 0}
            ).sort(sort_order).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "trade_date": trade_date,
                "start_date": start_date,
                "end_date": end_date,
                "sw_industry_data": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取申万行业指数数据失败: {str(e)}")

@router.get("/sw/industries")
async def get_sw_industries(
    trade_date: Optional[str] = Query(default=None, description="交易日期(YYYYMMDD)，不指定则返回最新数据")
):
    """
    获取申万行业列表及最新行情
    """
    try:
        collection = db_handler.get_collection('sw_daily')
        
        # 如果没有指定日期，获取最新交易日
        if not trade_date:
            latest_doc = collection.find_one(
                {},
                {"trade_date": 1, "_id": 0},
                sort=[("trade_date", -1)]
            )
            if latest_doc:
                trade_date = latest_doc["trade_date"]
        
        # 获取指定日期的所有行业数据
        cursor = collection.find(
            {"trade_date": trade_date},
            {"_id": 0}
        ).sort("ts_code", 1)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "industries": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取申万行业列表失败: {str(e)}")

# ==================== 数据统计分析 ====================

@router.get("/stats")
async def get_data_stats():
    """
    获取涨跌停概念和申万行业数据统计信息
    """
    try:
        # 涨跌停概念数据统计
        limit_collection = db_handler.get_collection('limit_cpt_list')
        
        # 按涨跌停类型统计
        limit_type_pipeline = [
            {
                "$group": {
                    "_id": "$limit_type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        limit_type_stats = list(limit_collection.aggregate(limit_type_pipeline))
        
        # 最近涨跌停活跃股票统计
        recent_limit_pipeline = [
            {"$sort": {"trade_date": -1}},
            {"$limit": 1000},  # 最近1000条记录
            {
                "$group": {
                    "_id": {
                        "ts_code": "$ts_code",
                        "name": "$name"
                    },
                    "limit_count": {"$sum": 1},
                    "latest_date": {"$max": "$trade_date"}
                }
            },
            {"$sort": {"limit_count": -1}},
            {"$limit": 20}
        ]
        
        active_limit_stocks = list(limit_collection.aggregate(recent_limit_pipeline))
        
        # 申万行业数据统计
        sw_collection = db_handler.get_collection('sw_daily')
        
        # 获取最新交易日的行业表现
        latest_trade_date = sw_collection.find_one(
            {},
            {"trade_date": 1, "_id": 0},
            sort=[("trade_date", -1)]
        )
        
        if latest_trade_date:
            latest_date = latest_trade_date["trade_date"]
            
            # 最新交易日涨跌幅排行
            latest_performance_pipeline = [
                {"$match": {"trade_date": latest_date}},
                {"$sort": {"pct_change": -1}}
            ]
            
            latest_performance = list(sw_collection.aggregate(latest_performance_pipeline))
            
            # 行业数量统计
            industry_count = len(latest_performance)
        else:
            latest_date = None
            latest_performance = []
            industry_count = 0
        
        return {
            "success": True,
            "data": {
                "limit_concept_stats": {
                    "limit_type_distribution": limit_type_stats,
                    "active_limit_stocks": active_limit_stocks
                },
                "sw_industry_stats": {
                    "latest_trade_date": latest_date,
                    "industry_count": industry_count,
                    "latest_performance": latest_performance
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据统计信息失败: {str(e)}")

# ==================== 涨跌停趋势分析 ====================

@router.get("/limit/trend")
async def get_limit_trend(
    days: int = Query(default=30, description="分析天数", ge=7, le=90),
    limit_type: Optional[str] = Query(default=None, description="涨跌停类型: U-涨停, D-跌停")
):
    """
    获取涨跌停趋势分析
    """
    try:
        collection = db_handler.get_collection('limit_cpt_list')
        
        # 计算指定天数前的日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y%m%d')
        
        # 构建查询条件
        query = {
            "trade_date": {"$gte": start_date_str}
        }
        
        if limit_type:
            query["limit_type"] = limit_type
        
        # 按日期统计涨跌停数量
        daily_pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": {
                        "trade_date": "$trade_date",
                        "limit_type": "$limit_type"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.trade_date": 1}}
        ]
        
        daily_stats = list(collection.aggregate(daily_pipeline))
        
        return {
            "success": True,
            "data": {
                "analysis_days": days,
                "start_date": start_date_str,
                "limit_type": limit_type,
                "daily_trend": daily_stats,
                "count": len(daily_stats),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨跌停趋势分析失败: {str(e)}")

@router.get("/sw/performance")
async def get_sw_performance_ranking(
    trade_date: Optional[str] = Query(default=None, description="交易日期(YYYYMMDD)，不指定则返回最新数据"),
    sort_by: str = Query(default="pct_change", description="排序字段: pct_change-涨跌幅, vol-成交量, amount-成交额")
):
    """
    获取申万行业表现排行
    """
    try:
        collection = db_handler.get_collection('sw_daily')
        
        # 如果没有指定日期，获取最新交易日
        if not trade_date:
            latest_doc = collection.find_one(
                {},
                {"trade_date": 1, "_id": 0},
                sort=[("trade_date", -1)]
            )
            if latest_doc:
                trade_date = latest_doc["trade_date"]
        
        # 获取指定日期的行业表现数据
        cursor = collection.find(
            {"trade_date": trade_date},
            {"_id": 0}
        ).sort(sort_by, -1)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "sort_by": sort_by,
                "performance_ranking": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取申万行业表现排行失败: {str(e)}")

# ==================== 批量查询接口（支持并发） ====================

@router.post("/batch/limit-data")
async def batch_get_limit_data(
    request: BatchLimitDataRequest
):
    """
    批量获取涨跌停数据（支持并发查询）
    """
    try:
        if not request.trade_dates:
            raise HTTPException(status_code=400, detail="trade_dates 不能为空")
        
        if len(request.trade_dates) > 30:
            raise HTTPException(status_code=400, detail="批量查询最多支持30个交易日")
        
        # 异步并发查询
        async def get_limit_data_by_date(trade_date: str):
            try:
                collection = db_handler.get_collection('limit_cpt_list')
                cursor = collection.find(
                    {"trade_date": trade_date},
                    {"_id": 0}
                ).sort("ts_code", 1).limit(request.limit_per_date)
                
                return {
                    "trade_date": trade_date,
                    "limit_data": list(cursor),
                    "success": True
                }
                
            except Exception as e:
                return {
                    "trade_date": trade_date,
                    "limit_data": [],
                    "success": False,
                    "error": str(e)
                }
        
        # 并发查询
        tasks = [get_limit_data_by_date(date) for date in request.trade_dates]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "trade_date": request.trade_dates[i],
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        return {
            "success": True,
            "data": {
                "successful_queries": len(successful_results),
                "failed_queries": len(failed_results),
                "results": successful_results,
                "failures": failed_results,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量获取涨跌停数据失败: {str(e)}")

@router.post("/batch/sw-daily")
async def batch_get_sw_daily(
    request: BatchSWDailyRequest
):
    """
    批量获取申万行业日线数据（支持并发查询）
    """
    try:
        if not request.trade_dates:
            raise HTTPException(status_code=400, detail="trade_dates 不能为空")
        
        if len(request.trade_dates) > 30:
            raise HTTPException(status_code=400, detail="批量查询最多支持30个交易日")
        
        # 异步并发查询
        async def get_sw_daily_by_date(trade_date: str):
            collection = db_handler.get_collection('sw_daily')
            cursor = collection.find(
                {"trade_date": trade_date},
                {"_id": 0}
            ).sort("ts_code", 1)
            
            return {
                "trade_date": trade_date,
                "sw_data": list(cursor)
            }
        
        # 并发查询
        tasks = [get_sw_daily_by_date(date) for date in request.trade_dates]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "trade_date": request.trade_dates[i],
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        return {
            "success": True,
            "data": {
                "successful_queries": len(successful_results),
                "failed_queries": len(failed_results),
                "results": successful_results,
                "failures": failed_results,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量获取申万行业日线数据失败: {str(e)}")