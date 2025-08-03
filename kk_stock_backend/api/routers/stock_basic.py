# -*- coding: utf-8 -*-
"""
股票基本信息和股本结构数据API接口
支持股票基本信息、股本结构、股东信息等数据查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel

# 导入缓存装饰器
from api.cache_middleware import cache_endpoint

import sys
import os

# 添加项目根目录到sys.path以便导入数据库管理器
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(api_dir)
sys.path.insert(0, project_root)

from data_collector_new.db_handler import DBHandler
from api.global_db import db_handler

router = APIRouter()

sys.path.insert(0, project_root)


# 数据模型
class StockBasicInfo(BaseModel):
    ts_code: str
    symbol: str
    name: str
    area: str
    industry: str
    market: str
    list_date: str
    is_hs: str

class ShareFloatData(BaseModel):
    ts_code: str
    ann_date: str
    float_date: str
    float_share: float
    float_ratio: float
    holder_name: str
    share_type: str

# ==================== 股票基本信息 ====================

@cache_endpoint(data_type='stock_basic', ttl=3600)  # 缓存1小时
@router.get("/basic/info")
async def get_stock_basic_info(
    ts_code: Optional[str] = Query(default=None, description="股票代码"),
    exchange: Optional[str] = Query(default=None, description="交易所: SSE-上交所, SZSE-深交所"),
    market: Optional[str] = Query(default=None, description="市场类型: 主板, 创业板, 科创板"),
    industry: Optional[str] = Query(default=None, description="行业"),
    area: Optional[str] = Query(default=None, description="地区"),
    is_hs: Optional[str] = Query(default=None, description="是否沪深港通: N-否, H-沪股通, S-深股通"),
    list_status: Optional[str] = Query(default="L", description="上市状态: L-上市, D-退市, P-暂停"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取股票基本信息
    """
    try:
        collection = db_handler.get_collection('infrastructure_stock_basic')
        
        # 构建查询条件
        query = {}
        
        if ts_code:
            query["ts_code"] = ts_code
        
        if exchange:
            query["exchange"] = exchange
        
        if market:
            query["market"] = market
        
        if industry:
            query["industry"] = {"$regex": industry, "$options": "i"}
        
        if area:
            query["area"] = area
        
        if is_hs:
            query["is_hs"] = is_hs
        
        if list_status:
            query["list_status"] = list_status
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("list_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "stocks": results,
                "count": len(results),
                "filters": {
                    "ts_code": ts_code,
                    "exchange": exchange,
                    "market": market,
                    "industry": industry,
                    "area": area,
                    "is_hs": is_hs,
                    "list_status": list_status
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票基本信息失败: {str(e)}")

@cache_endpoint(data_type='stock_search', ttl=1800)  # 缓存30分钟
@router.get("/basic/search")
async def search_stocks(
    keyword: str = Query(description="搜索关键词（股票代码或名称）"),
    limit: int = Query(default=20, description="返回条数")
):
    """
    搜索股票（支持代码和名称模糊匹配）
    """
    try:
        collection = db_handler.get_collection('infrastructure_stock_basic')
        
        # 构建搜索条件（代码或名称匹配）
        query = {
            "$or": [
                {"ts_code": {"$regex": keyword, "$options": "i"}},
                {"symbol": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}}
            ],
            "list_status": "L"  # 只返回上市股票
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
                "stocks": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索股票失败: {str(e)}")

@cache_endpoint(data_type='stock_stats', ttl=3600)  # 缓存1小时
@router.get("/basic/stats")
async def get_stock_basic_stats():
    """
    获取股票基本信息统计
    """
    try:
        collection = db_handler.get_collection('infrastructure_stock_basic')
        
        # 统计各种维度的数据
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_count": {"$sum": 1},
                    "listed_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$list_status", "L"]}, 1, 0]
                        }
                    },
                    "delisted_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$list_status", "D"]}, 1, 0]
                        }
                    }
                }
            }
        ]
        
        basic_stats = list(collection.aggregate(pipeline))
        
        # 按交易所统计
        exchange_pipeline = [
            {"$match": {"list_status": "L"}},
            {
                "$group": {
                    "_id": "$exchange",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        exchange_stats = list(collection.aggregate(exchange_pipeline))
        
        # 按市场类型统计
        market_pipeline = [
            {"$match": {"list_status": "L"}},
            {
                "$group": {
                    "_id": "$market",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        market_stats = list(collection.aggregate(market_pipeline))
        
        # 按行业统计（前10）
        industry_pipeline = [
            {"$match": {"list_status": "L"}},
            {
                "$group": {
                    "_id": "$industry",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        industry_stats = list(collection.aggregate(industry_pipeline))
        
        return {
            "success": True,
            "data": {
                "basic_stats": basic_stats[0] if basic_stats else {},
                "exchange_stats": exchange_stats,
                "market_stats": market_stats,
                "top_industries": industry_stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票统计信息失败: {str(e)}")

# ==================== 股本结构数据 ====================

@cache_endpoint(data_type='share_float', ttl=7200)  # 缓存2小时
@router.get("/share/float")
async def get_share_float(
    ts_code: Optional[str] = Query(default=None, description="股票代码"),
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取限售股解禁数据
    """
    try:
        collection = db_handler.get_collection('share_float')
        
        # 构建查询条件
        query = {}
        
        if ts_code:
            query["ts_code"] = ts_code
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["float_date"] = date_query
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("float_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "start_date": start_date,
                "end_date": end_date,
                "share_float": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取限售股解禁数据失败: {str(e)}")

# ==================== 股东信息 ====================

@cache_endpoint(data_type='holders', ttl=14400)  # 缓存4小时
@router.get("/holders/top10")
async def get_top10_holders(
    ts_code: str = Query(description="股票代码"),
    period: Optional[str] = Query(default=None, description="报告期 YYYYMMDD"),
    limit: int = Query(default=10, description="返回条数")
):
    """
    获取前十大股东信息
    """
    try:
        collection = db_handler.get_collection('top10_holders')
        
        # 构建查询条件
        query = {"ts_code": ts_code}
        
        if period:
            query["end_date"] = period
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("end_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "period": period,
                "holders": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取前十大股东信息失败: {str(e)}")

@router.get("/holders/float")
async def get_top10_float_holders(
    ts_code: str = Query(description="股票代码"),
    period: Optional[str] = Query(default=None, description="报告期 YYYYMMDD"),
    limit: int = Query(default=10, description="返回条数")
):
    """
    获取前十大流通股东信息
    """
    try:
        collection = db_handler.get_collection('top10_floatholders')
        
        # 构建查询条件
        query = {"ts_code": ts_code}
        
        if period:
            query["end_date"] = period
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("end_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "period": period,
                "float_holders": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取前十大流通股东信息失败: {str(e)}")

# ==================== 批量查询接口（支持并发） ====================

@router.post("/batch/basic")
async def get_batch_stock_basic(
    request_data: Dict[str, Any]
):
    """
    批量获取股票基本信息（支持并发查询）
    
    请求格式:
    {
        "ts_codes": ["000001.SZ", "000002.SZ"],
        "fields": ["ts_code", "name", "industry", "market"]
    }
    """
    try:
        ts_codes = request_data.get('ts_codes', [])
        fields = request_data.get('fields', [])
        
        if not ts_codes:
            raise HTTPException(status_code=400, detail="ts_codes 不能为空")
        
        if len(ts_codes) > 100:
            raise HTTPException(status_code=400, detail="批量查询最多支持100只股票")
        
        # 异步并发查询
        async def fetch_single_stock_basic(ts_code: str):
            try:
                collection = db_handler.get_collection('infrastructure_stock_basic')
                
                # 构建投影字段
                projection = {"_id": 0}
                if fields:
                    for field in fields:
                        projection[field] = 1
                
                result = collection.find_one(
                    {"ts_code": ts_code},
                    projection
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
        tasks = [fetch_single_stock_basic(ts_code) for ts_code in ts_codes]
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
        raise HTTPException(status_code=500, detail=f"批量查询股票基本信息失败: {str(e)}")

@router.post("/batch/holders")
async def get_batch_holders(
    request_data: Dict[str, Any]
):
    """
    批量获取股东信息（支持并发查询）
    
    请求格式:
    {
        "ts_codes": ["000001.SZ", "000002.SZ"],
        "holder_type": "top10",  // top10 或 float
        "period": "20241231"
    }
    """
    try:
        ts_codes = request_data.get('ts_codes', [])
        holder_type = request_data.get('holder_type', 'top10')
        period = request_data.get('period')
        
        if not ts_codes:
            raise HTTPException(status_code=400, detail="ts_codes 不能为空")
        
        if len(ts_codes) > 50:
            raise HTTPException(status_code=400, detail="批量查询最多支持50只股票")
        
        if holder_type not in ['top10', 'float']:
            raise HTTPException(status_code=400, detail="holder_type 必须是 'top10' 或 'float'")
        
        # 选择集合
        collection_name = 'top10_holders' if holder_type == 'top10' else 'top10_floatholders'
        
        # 异步并发查询
        async def fetch_single_stock_holders(ts_code: str):
            try:
                collection = db_handler.get_collection(collection_name)
                
                query = {"ts_code": ts_code}
                if period:
                    query["end_date"] = period
                
                cursor = collection.find(
                    query,
                    {"_id": 0}
                ).sort("end_date", -1).limit(10)
                
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
        tasks = [fetch_single_stock_holders(ts_code) for ts_code in ts_codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        
        return {
            "success": True,
            "data": {
                "holder_type": holder_type,
                "period": period,
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
        raise HTTPException(status_code=500, detail=f"批量查询股东信息失败: {str(e)}")

# ==================== 新股信息 ====================

@router.get("/new/list")
async def get_new_share_list(
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取新股申购信息
    """
    try:
        collection = db_handler.get_collection('new_share')
        
        # 构建查询条件
        query = {}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["sub_date"] = date_query
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("sub_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "start_date": start_date,
                "end_date": end_date,
                "new_shares": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新股申购信息失败: {str(e)}")