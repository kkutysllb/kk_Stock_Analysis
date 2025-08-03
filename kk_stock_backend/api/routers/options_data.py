# -*- coding: utf-8 -*-
"""
期权数据API接口
支持期权基本信息、期权行情数据等高并发查询
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel

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


# 数据模型
class OptionsBasicInfo(BaseModel):
    ts_code: str
    exchange: str
    name: str
    per_unit: str
    opt_code: str
    opt_type: str
    call_put: str
    exercise_type: str
    exercise_price: float
    s_month: str
    maturity_date: str
    list_price: float
    list_date: str
    delist_date: str
    last_edate: str
    last_ddate: str
    quote_unit: str
    min_price_chg: float

class OptionsDailyData(BaseModel):
    ts_code: str
    trade_date: str
    exchange: str
    ts_code: str
    pre_close: float
    pre_settle: float
    open: float
    high: float
    low: float
    close: float
    settle: float
    vol: float
    amount: float
    oi: float

# ==================== 期权基本信息 ====================

@cache_endpoint(data_type='options_basic', ttl=3600)  # 缓存1小时
@router.get("/basic/list")
async def get_options_list(
    exchange: Optional[str] = Query(default=None, description="交易所代码"),
    call_put: Optional[str] = Query(default=None, description="期权类型: C-看涨, P-看跌"),
    opt_type: Optional[str] = Query(default=None, description="期权品种类型"),
    limit: int = Query(default=100, description="返回数量限制")
):
    """
    获取期权基本信息列表
    支持按交易所、期权类型筛选
    """
    try:
        collection = db_handler.get_collection('opt_basic')
        
        # 构建查询条件
        query = {}
        
        if exchange:
            query["exchange"] = exchange
        
        if call_put:
            query["call_put"] = call_put
        
        if opt_type:
            query["opt_type"] = opt_type
        
        # 异步查询数据
        cursor = collection.find(
            query,
            {"_id": 0}
        ).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "options_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期权列表失败: {str(e)}")

@cache_endpoint(data_type='options_basic', ttl=3600)  # 缓存1小时
@router.get("/basic/{ts_code}")
async def get_options_info(
    ts_code: str
):
    """
    获取单个期权的基本信息
    """
    try:
        collection = db_handler.get_collection('opt_basic')
        
        result = collection.find_one(
            {"ts_code": ts_code},
            {"_id": 0}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail=f"期权代码 {ts_code} 不存在")
        
        return {
            "success": True,
            "data": {
                "options_info": result,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期权信息失败: {str(e)}")

# ==================== 期权行情数据 ====================

@cache_endpoint(data_type='options_daily', ttl=1800)  # 缓存30分钟
@router.get("/daily/{ts_code}")
async def get_options_daily(
    ts_code: str,
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取期权日线数据
    """
    try:
        collection = db_handler.get_collection('opt_daily')
        
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
        raise HTTPException(status_code=500, detail=f"获取期权日线数据失败: {str(e)}")

# ==================== 期权链查询 ====================

@cache_endpoint(data_type='options_chain', ttl=1800)  # 缓存30分钟
@router.get("/chain/{underlying}")
async def get_options_chain(
    underlying: str = Path(..., description="标的资产代码"),
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    call_put: Optional[str] = Query(default=None, description="期权类型: C-看涨, P-看跌")
):
    """
    获取期权链数据
    """
    try:
        # 首先从基本信息中查找相关期权
        basic_collection = db_handler.get_collection('opt_basic')
        
        # 构建查询条件
        query = {"opt_code": {"$regex": underlying, "$options": "i"}}
        
        if call_put:
            query["call_put"] = call_put
        
        # 获取期权基本信息
        basic_cursor = basic_collection.find(
            query,
            {"_id": 0}
        )
        
        basic_results = list(basic_cursor)
        
        if not basic_results:
            return {
                "success": True,
                "data": {
                    "underlying": underlying,
                    "options_chain": [],
                    "count": 0,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # 如果指定了交易日期，获取对应的行情数据
        if trade_date:
            daily_collection = db_handler.get_collection('opt_daily')
            ts_codes = [item['ts_code'] for item in basic_results]
            
            daily_cursor = daily_collection.find(
                {
                    "ts_code": {"$in": ts_codes},
                    "trade_date": trade_date
                },
                {"_id": 0}
            )
            
            daily_results = {item['ts_code']: item for item in daily_cursor}
            
            # 合并基本信息和行情数据
            for basic_item in basic_results:
                ts_code = basic_item['ts_code']
                if ts_code in daily_results:
                    basic_item['daily_data'] = daily_results[ts_code]
        
        return {
            "success": True,
            "data": {
                "underlying": underlying,
                "trade_date": trade_date,
                "options_chain": basic_results,
                "count": len(basic_results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期权链失败: {str(e)}")

# ==================== 批量查询接口（支持并发） ====================

@router.post("/batch/daily")
async def get_batch_options_daily(
    request_data: Dict[str, Any]
):
    """
    批量获取期权日线数据（支持并发查询）
    
    请求格式:
    {
        "ts_codes": ["10004355.SH", "10004356.SH"],
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
            raise HTTPException(status_code=400, detail="批量查询最多支持50个期权代码")
        
        # 异步并发查询
        async def fetch_single_options_data(ts_code: str):
            try:
                collection = db_handler.get_collection('opt_daily')
                
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
        tasks = [fetch_single_options_data(ts_code) for ts_code in ts_codes]
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
        raise HTTPException(status_code=500, detail=f"批量查询期权数据失败: {str(e)}")

# ==================== 期权搜索接口 ====================

@cache_endpoint(data_type='options_search', ttl=1800)  # 缓存30分钟
@router.get("/search")
async def search_options(
    keyword: str = Query(..., description="搜索关键词（期权名称或代码）"),
    limit: int = Query(default=20, description="返回数量限制")
):
    """
    搜索期权（按名称或代码）
    """
    try:
        collection = db_handler.get_collection('opt_basic')
        
        # 构建搜索条件（支持代码和名称模糊搜索）
        query = {
            "$or": [
                {"ts_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}},
                {"opt_code": {"$regex": keyword, "$options": "i"}}
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
                "options_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索期权失败: {str(e)}")

# ==================== 期权统计信息 ====================

@cache_endpoint(data_type='options_stats', ttl=7200)  # 缓存2小时
@router.get("/stats/summary")
async def get_options_stats(
    underlying: Optional[str] = Query(default=None, description="标的代码筛选"),
    call_put: Optional[str] = Query(default=None, description="期权类型筛选 C/P"),
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD")
):
    """
    获取期权统计摘要信息
    """
    try:
        basic_collection = db_handler.get_collection('opt_basic')
        daily_collection = db_handler.get_collection('opt_daily')
        
        # 构建基本查询条件
        basic_query = {}
        if underlying:
            # 使用opt_code字段进行精确匹配或模糊匹配
            basic_query["opt_code"] = {"$regex": underlying, "$options": "i"}
        if call_put:
            basic_query["call_put"] = call_put
            
        # 统计总合约数
        total_contracts = basic_collection.count_documents(basic_query)
        
        # 确定查询日期
        if not trade_date:
            latest_result = daily_collection.find_one(
                {},
                {"trade_date": 1},
                sort=[("trade_date", -1)]
            )
            if latest_result:
                trade_date = latest_result["trade_date"]
            else:
                trade_date = datetime.now().strftime("%Y%m%d")
        
        # 构建日线数据查询条件
        daily_query = {"trade_date": trade_date}
        
        # 如果有筛选条件，需要通过基本信息表获取对应的ts_code列表
        if underlying or call_put:
            basic_codes = list(basic_collection.find(basic_query, {"ts_code": 1}))
            if basic_codes:
                daily_query["ts_code"] = {"$in": [item["ts_code"] for item in basic_codes]}
            else:
                daily_query["ts_code"] = {"$in": []}  # 空结果
        
        # 统计活跃合约数（有交易量的合约）
        active_contracts = daily_collection.count_documents({
            **daily_query,
            "vol": {"$gt": 0}
        })
        
        # 统计总交易量、总成交额、总持仓量
        pipeline = [
            {"$match": daily_query},
            {"$group": {
                "_id": None,
                "total_volume": {"$sum": "$vol"},
                "total_amount": {"$sum": "$amount"},
                "total_oi": {"$sum": "$oi"},
                "count": {"$sum": 1}
            }}
        ]
        
        stats_result = list(daily_collection.aggregate(pipeline))
        
        if stats_result:
            stats = stats_result[0]
            total_volume = stats.get("total_volume", 0)
            total_amount = stats.get("total_amount", 0)
            total_oi = stats.get("total_oi", 0)
            count = stats.get("count", 1)
        else:
            total_volume = 0
            total_amount = 0
            total_oi = 0
            count = 1
        
        # 计算平均值
        avg_volume = total_volume / count if count > 0 else 0
        avg_oi = total_oi / count if count > 0 else 0
        
        return {
            "success": True,
            "data": {
                "total_contracts": total_contracts,
                "active_contracts": active_contracts,
                "total_volume": int(total_volume),
                "total_amount": int(total_amount),
                "total_oi": int(total_oi),
                "avg_volume": round(avg_volume, 2),
                "avg_oi": round(avg_oi, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期权统计信息失败: {str(e)}")

# ==================== 期权到期日查询 ====================

@cache_endpoint(data_type='options_expiry', ttl=3600)  # 缓存1小时
@router.get("/expiry")
async def get_options_by_expiry(
    start_date: Optional[str] = Query(default=None, description="开始到期日 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束到期日 YYYYMMDD"),
    limit: int = Query(default=100, description="返回数量限制")
):
    """
    按到期日查询期权
    """
    try:
        collection = db_handler.get_collection('opt_basic')
        
        # 构建查询条件
        query = {}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["maturity_date"] = date_query
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("maturity_date", 1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "start_date": start_date,
                "end_date": end_date,
                "options_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"按到期日查询期权失败: {str(e)}")

# ==================== 期权最新数据查询 ====================

@cache_endpoint(data_type='options_latest', ttl=1800)  # 缓存30分钟
@router.get("/latest")
async def get_latest_options_data(
    underlying: Optional[str] = Query(default=None, description="标的代码筛选"),
    call_put: Optional[str] = Query(default=None, description="期权类型: C-看涨, P-看跌"),
    limit: int = Query(default=50, description="返回数量限制")
):
    """
    获取最新期权交易数据
    """
    try:
        # 获取最新交易日期
        daily_collection = db_handler.get_collection('opt_daily')
        latest_date_result = daily_collection.find_one(
            {},
            {"trade_date": 1},
            sort=[("trade_date", -1)]
        )
        
        if not latest_date_result:
            raise HTTPException(status_code=404, detail="未找到期权交易数据")
        
        latest_date = latest_date_result['trade_date']
        
        # 构建查询条件
        query = {"trade_date": latest_date}
        
        # 获取基本信息用于筛选
        basic_collection = db_handler.get_collection('opt_basic')
        basic_query = {}
        
        if underlying:
            basic_query["opt_code"] = {"$regex": underlying, "$options": "i"}
        
        if call_put:
            basic_query["call_put"] = call_put
        
        # 如果有筛选条件，先获取符合条件的ts_code
        if basic_query:
            basic_cursor = basic_collection.find(basic_query, {"ts_code": 1})
            ts_codes = [item['ts_code'] for item in basic_cursor]
            if ts_codes:
                query["ts_code"] = {"$in": ts_codes}
            else:
                return {
                    "success": True,
                    "data": {
                        "latest_date": latest_date,
                        "options_data": [],
                        "count": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                }
        
        # 获取最新交易数据，按交易量排序
        cursor = daily_collection.find(
            query,
            {"_id": 0}
        ).sort("vol", -1).limit(limit)
        
        results = list(cursor)
        
        # 补充基本信息
        if results:
            ts_codes = [item['ts_code'] for item in results]
            basic_cursor = basic_collection.find(
                {"ts_code": {"$in": ts_codes}},
                {"_id": 0, "ts_code": 1, "name": 1, "opt_code": 1, "call_put": 1, "exercise_price": 1}
            )
            basic_info = {item['ts_code']: item for item in basic_cursor}
            
            for item in results:
                ts_code = item['ts_code']
                if ts_code in basic_info:
                    item.update(basic_info[ts_code])
        
        return {
            "success": True,
            "data": {
                "latest_date": latest_date,
                "underlying_filter": underlying,
                "call_put_filter": call_put,
                "options_data": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新期权数据失败: {str(e)}")

# ==================== 期权活跃度分析 ====================

@cache_endpoint(data_type='options_activity', ttl=3600)  # 缓存1小时
@router.get("/activity")
async def get_options_activity(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD，默认最新交易日"),
    underlying: Optional[str] = Query(default=None, description="标的代码筛选"),
    call_put: Optional[str] = Query(default=None, description="期权类型: C-看涨, P-看跌"),
    limit: int = Query(default=50, description="返回数量限制")
):
    """
    获取期权活跃度数据
    """
    try:
        daily_collection = db_handler.get_collection('opt_daily')
        
        # 确定查询日期
        if not trade_date:
            latest_result = daily_collection.find_one(
                {},
                {"trade_date": 1},
                sort=[("trade_date", -1)]
            )
            if not latest_result:
                raise HTTPException(status_code=404, detail="未找到期权交易数据")
            trade_date = latest_result['trade_date']
        
        # 构建查询条件
        query = {"trade_date": trade_date}
        
        # 如果有筛选条件，需要通过基本信息表获取对应的ts_code列表
        if underlying or call_put:
            basic_collection = db_handler.get_collection('opt_basic')
            basic_query = {}
            
            if underlying:
                basic_query["opt_code"] = {"$regex": underlying, "$options": "i"}
            if call_put:
                basic_query["call_put"] = call_put
            
            basic_codes = list(basic_collection.find(basic_query, {"ts_code": 1}))
            if basic_codes:
                query["ts_code"] = {"$in": [item["ts_code"] for item in basic_codes]}
            else:
                return {
                    "success": True,
                    "data": {
                        "trade_date": trade_date,
                        "total_volume": 0,
                        "total_amount": 0,
                        "total_oi": 0,
                        "active_contracts": 0,
                        "top_by_volume": [],
                        "top_by_oi": [],
                        "timestamp": datetime.now().isoformat()
                    }
                }
        
        # 统计总体数据
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "total_volume": {"$sum": "$vol"},
                    "total_amount": {"$sum": "$amount"},
                    "total_oi": {"$sum": "$oi"},
                    "active_contracts": {
                        "$sum": {
                            "$cond": [{"$gt": ["$vol", 0]}, 1, 0]
                        }
                    }
                }
            }
        ]
        
        stats_result = list(daily_collection.aggregate(pipeline))
        stats = stats_result[0] if stats_result else {
            "total_volume": 0,
            "total_amount": 0,
            "total_oi": 0,
            "active_contracts": 0
        }
        
        # 获取按交易量排序的前N个合约
        top_by_volume = list(daily_collection.find(
            query,
            {"_id": 0, "ts_code": 1, "vol": 1, "amount": 1, "oi": 1, "close": 1}
        ).sort("vol", -1).limit(limit))
        
        # 获取按持仓量排序的前N个合约
        top_by_oi = list(daily_collection.find(
            query,
            {"_id": 0, "ts_code": 1, "vol": 1, "amount": 1, "oi": 1, "close": 1}
        ).sort("oi", -1).limit(limit))
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "total_volume": stats.get("total_volume", 0),
                "total_amount": stats.get("total_amount", 0),
                "total_oi": stats.get("total_oi", 0),
                "active_contracts": stats.get("active_contracts", 0),
                "top_by_volume": top_by_volume,
                "top_by_oi": top_by_oi,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期权活跃度数据失败: {str(e)}")

@cache_endpoint(data_type='options_activity_analysis', ttl=3600)  # 缓存1小时
@router.get("/activity/analysis")
async def get_options_activity_analysis(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD，默认最新交易日"),
    underlying: Optional[str] = Query(default=None, description="标的代码筛选"),
    top_n: int = Query(default=20, description="返回前N个活跃合约")
):
    """
    获取期权活跃度分析
    """
    try:
        daily_collection = db_handler.get_collection('opt_daily')
        
        # 确定查询日期
        if not trade_date:
            latest_result = daily_collection.find_one(
                {},
                {"trade_date": 1},
                sort=[("trade_date", -1)]
            )
            if not latest_result:
                raise HTTPException(status_code=404, detail="未找到期权交易数据")
            trade_date = latest_result['trade_date']
        
        # 构建查询条件
        query = {"trade_date": trade_date}
        
        # 如果有筛选条件，需要通过基本信息表获取对应的ts_code列表
        if underlying:
            basic_collection = db_handler.get_collection('opt_basic')
            basic_query = {}
            
            if underlying:
                basic_query["opt_code"] = {"$regex": underlying, "$options": "i"}
            
            basic_codes = list(basic_collection.find(basic_query, {"ts_code": 1}))
            if basic_codes:
                query["ts_code"] = {"$in": [item["ts_code"] for item in basic_codes]}
            else:
                # 如果没有匹配的合约，返回空结果
                return {
                    "success": True,
                    "data": {
                        "trade_date": trade_date,
                        "total_oi": 0,
                        "avg_oi": 0,
                        "max_oi": 0,
                        "min_oi": 0,
                        "contract_count": 0,
                        "active_contracts": 0,
                        "top_contracts": [],
                        "timestamp": datetime.now().isoformat()
                    }
                 }
        
        # 获取当日所有交易数据
        cursor = daily_collection.find(query, {"_id": 0})
        all_data = list(cursor)
        
        if not all_data:
            raise HTTPException(status_code=404, detail=f"未找到{trade_date}的期权交易数据")
        
        # 计算活跃度指标
        total_volume = sum(item.get('vol', 0) for item in all_data)
        total_amount = sum(item.get('amount', 0) for item in all_data)
        total_oi = sum(item.get('oi', 0) for item in all_data)
        active_contracts = len([item for item in all_data if item.get('vol', 0) > 0])
        
        # 按交易量排序获取最活跃合约
        sorted_by_volume = sorted(all_data, key=lambda x: x.get('vol', 0), reverse=True)[:top_n]
        
        # 按持仓量排序获取最大持仓合约
        sorted_by_oi = sorted(all_data, key=lambda x: x.get('oi', 0), reverse=True)[:top_n]
        
        # 补充基本信息
        basic_collection = db_handler.get_collection('opt_basic')
        all_ts_codes = list(set([item['ts_code'] for item in sorted_by_volume + sorted_by_oi]))
        basic_cursor = basic_collection.find(
            {"ts_code": {"$in": all_ts_codes}},
            {"_id": 0, "ts_code": 1, "name": 1, "opt_code": 1, "call_put": 1, "exercise_price": 1}
        )
        basic_info = {item['ts_code']: item for item in basic_cursor}
        
        # 为活跃合约添加基本信息
        for item in sorted_by_volume:
            ts_code = item['ts_code']
            if ts_code in basic_info:
                item.update(basic_info[ts_code])
        
        for item in sorted_by_oi:
            ts_code = item['ts_code']
            if ts_code in basic_info:
                item.update(basic_info[ts_code])
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "underlying_filter": underlying,
                "analysis": {
                    "total_contracts": len(all_data),
                    "active_contracts": active_contracts,
                    "total_volume": total_volume,
                    "total_amount": round(total_amount, 2),
                    "total_open_interest": total_oi,
                    "avg_volume_per_contract": round(total_volume / len(all_data), 2) if all_data else 0
                },
                "top_volume_contracts": sorted_by_volume,
                "top_oi_contracts": sorted_by_oi,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期权活跃度分析失败: {str(e)}")

# ==================== 期权价格趋势分析 ====================

@cache_endpoint(data_type='options_trend', ttl=3600)  # 缓存1小时
@router.get("/trend/{code}")
async def get_options_price_trend(
    code: str,
    days: int = Query(default=30, description="获取最近天数"),
    indicator: str = Query(default="close", description="价格指标: close/settle/vol/oi")
):
    """
    获取期权价格趋势数据
    支持 ts_code 或 opt_code 格式
    """
    try:
        basic_collection = db_handler.get_collection('opt_basic')
        daily_collection = db_handler.get_collection('opt_daily')
        
        # 判断输入的是 ts_code 还是 opt_code
        if code.startswith('IO'):
            # 输入的是 ts_code
            ts_code = code
        else:
            # 输入的是 opt_code，需要转换为 ts_code
            basic_info = basic_collection.find_one(
                {"opt_code": code},
                {"ts_code": 1}
            )
            if not basic_info:
                raise HTTPException(status_code=404, detail=f"期权代码 {code} 不存在")
            ts_code = basic_info['ts_code']
        
        # 计算N天前的日期（基于当前系统时间）
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y%m%d')
        
        # 获取最近N天的数据（按日期范围筛选）
        cursor = daily_collection.find(
            {
                "ts_code": ts_code,
                "trade_date": {"$gte": start_date_str}
            },
            {"_id": 0, "trade_date": 1, "close": 1, "settle": 1, "vol": 1, "oi": 1, "amount": 1}
        ).sort("trade_date", -1)
        
        results = list(cursor)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"期权代码 {code} 无交易数据")
        
        # 按日期正序排列
        results.reverse()
        
        # 提取趋势数据
        trend_data = []
        values = []
        
        for item in results:
            value = item.get(indicator, 0)
            trend_data.append({
                "trade_date": item['trade_date'],
                "close": item.get('close', 0),
                "settle": item.get('settle', 0),
                "vol": item.get('vol', 0),
                "oi": item.get('oi', 0)
            })
            if value is not None:
                values.append(value)
        
        # 计算统计指标
        if values:
            avg_value = sum(values) / len(values)
            max_value = max(values)
            min_value = min(values)
            latest_value = values[-1] if values else 0
            change_rate = ((latest_value - values[0]) / values[0] * 100) if values[0] != 0 else 0
        else:
            avg_value = max_value = min_value = latest_value = change_rate = 0
        
        # 获取基本信息
        basic_collection = db_handler.get_collection('opt_basic')
        basic_info = basic_collection.find_one(
            {"ts_code": ts_code},
            {"_id": 0, "name": 1, "opt_code": 1, "call_put": 1, "exercise_price": 1}
        )
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "basic_info": basic_info,
                "indicator": indicator,
                "days": days,
                "statistics": {
                    "latest_value": latest_value,
                    "avg_value": round(avg_value, 4),
                    "max_value": max_value,
                    "min_value": min_value,
                    "change_rate": round(change_rate, 2)
                },
                "trend_data": trend_data,
                "count": len(trend_data),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期权趋势数据失败: {str(e)}")

# ==================== 期权持仓量分析 ====================

@cache_endpoint(data_type='options_oi_analysis', ttl=3600)  # 缓存1小时
@router.get("/oi-analysis")
async def get_options_oi_analysis_dash(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD，默认最新交易日"),
    underlying: Optional[str] = Query(default=None, description="标的代码筛选")
):
    """
    获取期权持仓量分析（带横杠路径）
    """
    return await get_options_oi_analysis(trade_date, underlying)

@cache_endpoint(data_type='options_oi_analysis_slash', ttl=3600)  # 缓存1小时
@router.get("/oi/analysis")
async def get_options_oi_analysis(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD，默认最新交易日"),
    underlying: Optional[str] = Query(default=None, description="标的代码筛选")
):
    """
    获取期权持仓量分析
    """
    try:
        daily_collection = db_handler.get_collection('opt_daily')
        
        # 确定查询日期
        if not trade_date:
            latest_result = daily_collection.find_one(
                {},
                {"trade_date": 1},
                sort=[("trade_date", -1)]
            )
            if not latest_result:
                raise HTTPException(status_code=404, detail="未找到期权交易数据")
            trade_date = latest_result['trade_date']
        
        # 构建查询条件
        query = {"trade_date": trade_date}
        
        # 如果指定标的，需要先从基本信息获取相关合约
        if underlying:
            basic_collection = db_handler.get_collection('opt_basic')
            basic_cursor = basic_collection.find(
                {"opt_code": {"$regex": underlying, "$options": "i"}},
                {"ts_code": 1}
            )
            ts_codes = [item['ts_code'] for item in basic_cursor]
            if ts_codes:
                query["ts_code"] = {"$in": ts_codes}
        
        # 聚合分析持仓量数据
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "total_oi": {"$sum": "$oi"},
                    "avg_oi": {"$avg": "$oi"},
                    "max_oi": {"$max": "$oi"},
                    "min_oi": {"$min": "$oi"},
                    "contract_count": {"$sum": 1},
                    "active_contracts": {
                        "$sum": {
                            "$cond": [{"$gt": ["$oi", 0]}, 1, 0]
                        }
                    }
                }
            }
        ]
        
        oi_stats = list(daily_collection.aggregate(pipeline))
        
        if not oi_stats:
            raise HTTPException(status_code=404, detail=f"未找到{trade_date}的期权数据")
        
        stats = oi_stats[0]
        
        # 获取持仓量分布（按区间统计）
        distribution_pipeline = [
            {"$match": query},
            {
                "$bucket": {
                    "groupBy": "$oi",
                    "boundaries": [0, 100, 500, 1000, 2000, 5000, float('inf')],
                    "default": "Other",
                    "output": {
                        "count": {"$sum": 1},
                        "total_oi": {"$sum": "$oi"}
                    }
                }
            }
        ]
        
        distribution_raw = list(daily_collection.aggregate(distribution_pipeline))
        
        # 转换分布数据格式，使其更易于前端处理
        distribution = []
        for item in distribution_raw:
            boundary = item.get('_id', 0)
            range_name = ""
            if boundary == 0:
                range_name = "0-100"
            elif boundary == 100:
                range_name = "100-500"
            elif boundary == 500:
                range_name = "500-1K"
            elif boundary == 1000:
                range_name = "1K-2K"
            elif boundary == 2000:
                range_name = "2K-5K"
            elif boundary == 5000:
                range_name = "5K+"
            else:
                range_name = f"{boundary}+"
            
            distribution.append({
                "range": range_name,
                "count": item.get('count', 0),
                "total_oi": item.get('total_oi', 0)
            })
        
        # 获取前20大持仓合约
        top_oi_cursor = daily_collection.find(
            query,
            {"_id": 0}
        ).sort("oi", -1).limit(20)
        
        top_oi_contracts = list(top_oi_cursor)
        
        # 补充基本信息
        if top_oi_contracts:
            basic_collection = db_handler.get_collection('opt_basic')
            ts_codes = [item['ts_code'] for item in top_oi_contracts]
            basic_cursor = basic_collection.find(
                {"ts_code": {"$in": ts_codes}},
                {"_id": 0, "ts_code": 1, "name": 1, "opt_code": 1, "call_put": 1, "exercise_price": 1}
            )
            basic_info = {item['ts_code']: item for item in basic_cursor}
            
            for item in top_oi_contracts:
                ts_code = item['ts_code']
                if ts_code in basic_info:
                    item.update(basic_info[ts_code])
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "underlying_filter": underlying,
                "oi_statistics": {
                    "total_oi": stats.get('total_oi', 0),
                    "avg_oi": round(stats.get('avg_oi', 0), 2),
                    "max_oi": stats.get('max_oi', 0),
                    "min_oi": stats.get('min_oi', 0),
                    "contract_count": stats.get('contract_count', 0),
                    "active_contracts": stats.get('active_contracts', 0)
                },
                "oi_distribution": distribution,
                "top_oi_contracts": top_oi_contracts,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期权持仓量分析失败: {str(e)}")