# -*- coding: utf-8 -*-
"""
ETF数据API接口
支持ETF基本信息、ETF行情数据、指数关联等高并发查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel

import sys
import os

# 添加项目根目录到sys.path以便导入数据库管理器
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(api_dir)
sys.path.insert(0, project_root)


router = APIRouter()

sys.path.insert(0, project_root)
from api.cache_middleware import cache_endpoint
from api.global_db import db_handler


# 数据模型
class ETFBasicInfo(BaseModel):
    ts_code: str
    name: str
    management: str
    custodian: str
    fund_type: str
    found_date: str
    due_date: str
    list_date: str
    invest_type: str
    type: str
    trustee: str
    purc_startdate: str
    redm_startdate: str
    market: str

class ETFDailyData(BaseModel):
    ts_code: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    change: float
    pct_chg: float
    vol: float
    amount: float

# ==================== ETF基本信息 ====================

@cache_endpoint(data_type="etf_basic", ttl=3600)
@router.get("/basic/list")
async def get_etf_list(
    market: Optional[str] = Query(default=None, description="市场代码"),
    fund_type: Optional[str] = Query(default=None, description="基金类型"),
    limit: int = Query(default=100, description="返回数量限制")
):
    """
    获取ETF基本信息列表
    支持按市场、基金类型筛选
    """
    try:
        collection = db_handler.get_collection('infrastructure_etf_basic')
        
        # 构建查询条件
        query = {}
        
        if market:
            query["market"] = market
        
        if fund_type:
            query["fund_type"] = fund_type
        
        # 异步查询数据
        cursor = collection.find(
            query,
            {"_id": 0}
        ).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "etf_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取ETF列表失败: {str(e)}")

@router.get("/basic/{ts_code}")
async def get_etf_info(
    ts_code: str
):
    """
    获取单个ETF的基本信息
    """
    try:
        collection = db_handler.get_collection('infrastructure_etf_basic')
        
        result = collection.find_one(
            {"ts_code": ts_code},
            {"_id": 0}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail=f"ETF代码 {ts_code} 不存在")
        
        return {
            "success": True,
            "data": {
                "etf_info": result,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取ETF信息失败: {str(e)}")

# ==================== ETF行情数据 ====================

@cache_endpoint(data_type="etf_daily", ttl=1800)
@router.get("/daily/{ts_code}")
async def get_etf_daily(
    ts_code: str,
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取ETF日线数据
    """
    try:
        collection = db_handler.get_collection('etf_daily')
        
        # 构建查询条件
        query = {"ts_code": ts_code}
        
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
                "ts_code": ts_code,
                "daily_data": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取ETF日线数据失败: {str(e)}")

# ==================== ETF指数关联信息 ====================

@router.get("/index-info/{ts_code}")
async def get_etf_index_info(
    ts_code: str
):
    """
    获取ETF对应的指数信息
    """
    try:
        collection = db_handler.get_collection('etf_index_info')
        
        result = collection.find_one(
            {"fund_code": ts_code},
            {"_id": 0}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail=f"ETF代码 {ts_code} 的指数信息不存在")
        
        return {
            "success": True,
            "data": {
                "etf_index_info": result,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取ETF指数信息失败: {str(e)}")

@cache_endpoint(data_type="etf_index", ttl=3600)
@router.get("/index-info/list")
async def get_etf_index_list(
    limit: int = Query(default=100, description="返回数量限制")
):
    """
    获取所有ETF指数关联信息列表
    """
    try:
        collection = db_handler.get_collection('etf_index_info')
        
        cursor = collection.find(
            {},
            {"_id": 0}
        ).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "etf_index_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取ETF指数列表失败: {str(e)}")

# ==================== 批量查询接口（支持并发） ====================

@cache_endpoint(data_type="etf_batch", ttl=1800)
@router.post("/batch/daily")
async def get_batch_etf_daily(
    request_data: Dict[str, Any]
):
    """
    批量获取ETF日线数据（支持并发查询）
    
    请求格式:
    {
        "ts_codes": ["510300.SH", "159919.SZ"],
        "start_date": "20241201",
        "end_date": "20241231",
        "limit": 100
    }
    """
    try:
        ts_codes = request_data.get('ts_codes', [])
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        limit = request_data.get('limit', 100)
        
        if not ts_codes:
            raise HTTPException(status_code=400, detail="ts_codes 不能为空")
        
        if len(ts_codes) > 50:
            raise HTTPException(status_code=400, detail="批量查询最多支持50个ETF代码")
        
        # 异步并发查询
        async def fetch_single_etf_data(ts_code: str):
            try:
                collection = db_handler.get_collection('etf_daily')
                
                query = {"ts_code": ts_code}
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
                
                return {
                    "ts_code": ts_code,
                    "data": list(cursor),
                    "success": True
                }
                
            except Exception as e:
                return {
                    "ts_code": ts_code,
                    "data": [],
                    "success": False,
                    "error": str(e)
                }
        
        # 并发执行查询
        tasks = [fetch_single_etf_data(ts_code) for ts_code in ts_codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        
        return {
            "success": True,
            "data": {
                "results": results,
                "total_requested": len(ts_codes),
                "success_count": success_count,
                "failed_count": len(ts_codes) - success_count,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量查询ETF数据失败: {str(e)}")

@cache_endpoint(data_type="etf_batch_basic", ttl=3600)
@router.post("/batch/basic")
async def get_batch_etf_basic(
    request_data: Dict[str, Any]
):
    """
    批量获取ETF基本信息（支持并发查询）
    
    请求格式:
    {
        "ts_codes": ["510300.SH", "159919.SZ"]
    }
    """
    try:
        ts_codes = request_data.get('ts_codes', [])
        
        if not ts_codes:
            raise HTTPException(status_code=400, detail="ts_codes 不能为空")
        
        if len(ts_codes) > 100:
            raise HTTPException(status_code=400, detail="批量查询最多支持100个ETF代码")
        
        # 异步并发查询
        async def fetch_single_etf_basic(ts_code: str):
            try:
                collection = db_handler.get_collection('infrastructure_etf_basic')
                
                result = collection.find_one(
                    {"ts_code": ts_code},
                    {"_id": 0}
                )
                
                return {
                    "ts_code": ts_code,
                    "data": result,
                    "success": True
                }
                
            except Exception as e:
                return {
                    "ts_code": ts_code,
                    "data": None,
                    "success": False,
                    "error": str(e)
                }
        
        # 并发执行查询
        tasks = [fetch_single_etf_basic(ts_code) for ts_code in ts_codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        
        return {
            "success": True,
            "data": {
                "results": results,
                "total_requested": len(ts_codes),
                "success_count": success_count,
                "failed_count": len(ts_codes) - success_count,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量查询ETF基本信息失败: {str(e)}")

# ==================== ETF搜索接口 ====================

@router.get("/search")
async def search_etf(
    keyword: str = Query(..., description="搜索关键词（ETF名称或代码）"),
    limit: int = Query(default=20, description="返回数量限制")
):
    """
    搜索ETF（按名称或代码）
    """
    try:
        collection = db_handler.get_collection('infrastructure_etf_basic')
        
        # 构建搜索条件（支持代码和名称模糊搜索）
        query = {
            "$or": [
                {"ts_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}}
            ]
        }
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "keyword": keyword,
                "etf_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索ETF失败: {str(e)}")

# ==================== ETF统计信息 ====================

@cache_endpoint(data_type="etf_stats", ttl=7200)
@router.get("/stats/summary")
async def get_etf_stats():
    """
    获取ETF统计摘要信息
    """
    try:
        collection = db_handler.get_collection('infrastructure_etf_basic')
        
        # 统计总数
        total_count = collection.count_documents({})
        
        # 按市场统计
        market_stats = list(collection.aggregate([
            {"$group": {
                "_id": "$market",
                "count": {"$sum": 1}
            }}
        ]))
        
        # 按基金类型统计
        fund_type_stats = list(collection.aggregate([
            {"$group": {
                "_id": "$fund_type",
                "count": {"$sum": 1}
            }}
        ]))
        
        return {
            "success": True,
            "data": {
                "total_count": total_count,
                "market_distribution": market_stats,
                "fund_type_distribution": fund_type_stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取ETF统计信息失败: {str(e)}")