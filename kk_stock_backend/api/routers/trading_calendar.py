# -*- coding: utf-8 -*-
"""
交易日历API接口
支持交易日历查询、交易日判断、工作日计算等功能
"""

from fastapi import APIRouter, HTTPException, Query, Depends
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

from routers.user import get_current_user
from api.global_db import db_handler

router = APIRouter()

sys.path.insert(0, project_root)


# 数据模型
class TradingCalendarInfo(BaseModel):
    exchange: str
    cal_date: str
    is_open: int
    pretrade_date: Optional[str] = None

class TradingDayRequest(BaseModel):
    date: str
    exchange: Optional[str] = "SSE"

class TradingDaysRequest(BaseModel):
    start_date: str
    end_date: str
    exchange: Optional[str] = "SSE"
    is_open: Optional[int] = None

class WorkdayCalculateRequest(BaseModel):
    start_date: str
    days: int
    exchange: Optional[str] = "SSE"
    direction: str = "forward"  # forward or backward

# ==================== 交易日历基础查询 ====================

@cache_endpoint(data_type='trading_calendar', ttl=86400)  # 缓存24小时
@router.get("/basic")
async def get_trading_calendar_basic(
    exchange: str = Query(default="SSE", description="交易所代码（SSE/SZSE/CFFEX等）"),
    start_date: Optional[str] = Query(default=None, description="开始日期（YYYYMMDD）"),
    end_date: Optional[str] = Query(default=None, description="结束日期（YYYYMMDD）"),
    limit: int = Query(default=100, description="返回结果数量限制")
):
    """
    获取交易日历基础信息
    支持按交易所、日期范围查询
    """
    try:
        collection = db_handler.get_collection('infrastructure_trading_calendar')
        
        # 构建查询条件
        query = {"exchange": exchange}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["cal_date"] = date_query
        
        # 执行查询
        cursor = collection.find(query).sort("cal_date", 1).limit(limit)
        results = list(cursor)
        
        # 处理结果
        calendar_data = []
        for doc in results:
            doc.pop('_id', None)
            calendar_data.append(doc)
        
        return {
            "success": True,
            "data": calendar_data,
            "count": len(calendar_data),
            "exchange": exchange,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询交易日历失败: {str(e)}")

@router.get("/exchanges")
async def get_supported_exchanges():
    """
    获取支持的交易所列表
    """
    try:
        collection = db_handler.get_collection('infrastructure_trading_calendar')
        
        # 获取所有交易所
        exchanges = collection.distinct("exchange")
        
        # 交易所信息映射
        exchange_info = {
            "SSE": "上海证券交易所",
            "SZSE": "深圳证券交易所", 
            "CFFEX": "中国金融期货交易所",
            "SHFE": "上海期货交易所",
            "DCE": "大连商品交易所",
            "CZCE": "郑州商品交易所",
            "INE": "上海国际能源交易中心"
        }
        
        exchange_list = []
        for exchange in exchanges:
            exchange_list.append({
                "code": exchange,
                "name": exchange_info.get(exchange, exchange),
                "type": "股票交易所" if exchange in ["SSE", "SZSE"] else "期货交易所"
            })
        
        return {
            "success": True,
            "data": exchange_list,
            "count": len(exchange_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易所列表失败: {str(e)}")

# ==================== 交易日判断和计算 ====================

@router.get("/is-trading-day")
async def is_trading_day(
    date: str = Query(..., description="查询日期（YYYYMMDD）"),
    exchange: str = Query(default="SSE", description="交易所代码")
):
    """
    判断指定日期是否为交易日
    """
    try:
        collection = db_handler.get_collection('infrastructure_trading_calendar')
        
        # 查询指定日期
        result = collection.find_one({
            "exchange": exchange,
            "cal_date": date
        })
        
        if not result:
            return {
                "success": True,
                "date": date,
                "exchange": exchange,
                "is_trading_day": False,
                "message": "未找到该日期的交易日历信息"
            }
        
        is_open = bool(result.get('is_open', 0))
        
        return {
            "success": True,
            "date": date,
            "exchange": exchange,
            "is_trading_day": is_open,
            "pretrade_date": result.get('pretrade_date'),
            "message": "交易日" if is_open else "非交易日"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询交易日失败: {str(e)}")

@router.get("/trading-days")
async def get_trading_days(
    start_date: str = Query(..., description="开始日期（YYYYMMDD）"),
    end_date: str = Query(..., description="结束日期（YYYYMMDD）"),
    exchange: str = Query(default="SSE", description="交易所代码"),
    is_open: Optional[int] = Query(default=None, description="是否交易日（1=交易日，0=非交易日）")
):
    """
    获取指定日期范围内的交易日列表
    """
    try:
        collection = db_handler.get_collection('infrastructure_trading_calendar')
        
        # 构建查询条件
        query = {
            "exchange": exchange,
            "cal_date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        if is_open is not None:
            query["is_open"] = is_open
        
        # 执行查询
        cursor = collection.find(query).sort("cal_date", 1)
        results = list(cursor)
        
        # 处理结果
        trading_days = []
        for doc in results:
            trading_days.append({
                "date": doc["cal_date"],
                "is_open": bool(doc.get("is_open", 0)),
                "pretrade_date": doc.get("pretrade_date")
            })
        
        # 统计信息
        total_days = len(trading_days)
        trading_day_count = sum(1 for day in trading_days if day["is_open"])
        non_trading_day_count = total_days - trading_day_count
        
        return {
            "success": True,
            "data": trading_days,
            "statistics": {
                "total_days": total_days,
                "trading_days": trading_day_count,
                "non_trading_days": non_trading_day_count,
                "start_date": start_date,
                "end_date": end_date,
                "exchange": exchange
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易日列表失败: {str(e)}")

@router.get("/next-trading-day")
async def get_next_trading_day(
    date: str = Query(..., description="基准日期（YYYYMMDD）"),
    exchange: str = Query(default="SSE", description="交易所代码"),
    days: int = Query(default=1, description="向后查找的交易日数量")
):
    """
    获取指定日期之后的第N个交易日
    """
    try:
        collection = db_handler.get_collection('infrastructure_trading_calendar')
        
        # 查找指定日期之后的交易日
        cursor = collection.find({
            "exchange": exchange,
            "cal_date": {"$gt": date},
            "is_open": 1
        }).sort("cal_date", 1).limit(days)
        
        results = list(cursor)
        
        if len(results) < days:
            return {
                "success": False,
                "message": f"未找到足够的交易日数据，需要{days}个，找到{len(results)}个",
                "base_date": date,
                "exchange": exchange,
                "found_days": len(results)
            }
        
        target_date = results[days-1]["cal_date"]
        
        return {
            "success": True,
            "base_date": date,
            "target_date": target_date,
            "exchange": exchange,
            "days_forward": days,
            "message": f"{date}之后第{days}个交易日是{target_date}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取下一交易日失败: {str(e)}")

@router.get("/prev-trading-day")
async def get_prev_trading_day(
    date: str = Query(..., description="基准日期（YYYYMMDD）"),
    exchange: str = Query(default="SSE", description="交易所代码"),
    days: int = Query(default=1, description="向前查找的交易日数量")
):
    """
    获取指定日期之前的第N个交易日
    """
    try:
        collection = db_handler.get_collection('infrastructure_trading_calendar')
        
        # 查找指定日期之前的交易日
        cursor = collection.find({
            "exchange": exchange,
            "cal_date": {"$lt": date},
            "is_open": 1
        }).sort("cal_date", -1).limit(days)
        
        results = list(cursor)
        
        if len(results) < days:
            return {
                "success": False,
                "message": f"未找到足够的交易日数据，需要{days}个，找到{len(results)}个",
                "base_date": date,
                "exchange": exchange,
                "found_days": len(results)
            }
        
        target_date = results[days-1]["cal_date"]
        
        return {
            "success": True,
            "base_date": date,
            "target_date": target_date,
            "exchange": exchange,
            "days_backward": days,
            "message": f"{date}之前第{days}个交易日是{target_date}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取前一交易日失败: {str(e)}")

# ==================== 交易日统计和分析 ====================

@router.get("/statistics")
async def get_trading_calendar_statistics(
    year: Optional[int] = Query(default=None, description="统计年份"),
    exchange: str = Query(default="SSE", description="交易所代码")
):
    """
    获取交易日历统计信息
    """
    try:
        collection = db_handler.get_collection('infrastructure_trading_calendar')
        
        # 构建查询条件
        query = {"exchange": exchange}
        
        if year:
            start_date = f"{year}0101"
            end_date = f"{year}1231"
            query["cal_date"] = {
                "$gte": start_date,
                "$lte": end_date
            }
        
        # 聚合统计
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$is_open",
                    "count": {"$sum": 1},
                    "dates": {"$push": "$cal_date"}
                }
            }
        ]
        
        results = list(collection.aggregate(pipeline))
        
        # 处理统计结果
        statistics = {
            "exchange": exchange,
            "year": year,
            "total_days": 0,
            "trading_days": 0,
            "non_trading_days": 0,
            "trading_day_ratio": 0.0
        }
        
        for result in results:
            count = result["count"]
            statistics["total_days"] += count
            
            if result["_id"] == 1:  # 交易日
                statistics["trading_days"] = count
            else:  # 非交易日
                statistics["non_trading_days"] = count
        
        # 计算交易日比例
        if statistics["total_days"] > 0:
            statistics["trading_day_ratio"] = round(
                statistics["trading_days"] / statistics["total_days"] * 100, 2
            )
        
        return {
            "success": True,
            "data": statistics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/monthly-summary")
async def get_monthly_trading_summary(
    year: int = Query(..., description="年份"),
    exchange: str = Query(default="SSE", description="交易所代码")
):
    """
    获取指定年份的月度交易日统计
    """
    try:
        collection = db_handler.get_collection('infrastructure_trading_calendar')
        
        # 聚合查询：按月统计交易日
        pipeline = [
            {
                "$match": {
                    "exchange": exchange,
                    "cal_date": {
                        "$gte": f"{year}0101",
                        "$lte": f"{year}1231"
                    }
                }
            },
            {
                "$addFields": {
                    "month": {"$substr": ["$cal_date", 4, 2]}
                }
            },
            {
                "$group": {
                    "_id": {
                        "month": "$month",
                        "is_open": "$is_open"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.month": 1}}
        ]
        
        results = list(collection.aggregate(pipeline))
        
        # 处理结果
        monthly_summary = {}
        for i in range(1, 13):
            month_str = f"{i:02d}"
            monthly_summary[month_str] = {
                "month": month_str,
                "total_days": 0,
                "trading_days": 0,
                "non_trading_days": 0
            }
        
        for result in results:
            month = result["_id"]["month"]
            is_open = result["_id"]["is_open"]
            count = result["count"]
            
            if month in monthly_summary:
                monthly_summary[month]["total_days"] += count
                if is_open == 1:
                    monthly_summary[month]["trading_days"] = count
                else:
                    monthly_summary[month]["non_trading_days"] = count
        
        return {
            "success": True,
            "data": {
                "year": year,
                "exchange": exchange,
                "monthly_data": list(monthly_summary.values())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取月度统计失败: {str(e)}")

# ==================== 批量查询接口 ====================

@router.post("/batch-check")
async def batch_check_trading_days(
    dates: List[str],
    exchange: str = Query(default="SSE", description="交易所代码")
):
    """
    批量检查多个日期是否为交易日
    """
    try:
        if len(dates) > 100:
            raise HTTPException(status_code=400, detail="批量查询日期数量不能超过100个")
        
        collection = db_handler.get_collection('infrastructure_trading_calendar')
        
        # 批量查询
        cursor = collection.find({
            "exchange": exchange,
            "cal_date": {"$in": dates}
        })
        
        results = list(cursor)
        
        # 构建结果映射
        result_map = {}
        for doc in results:
            result_map[doc["cal_date"]] = {
                "date": doc["cal_date"],
                "is_trading_day": bool(doc.get("is_open", 0)),
                "pretrade_date": doc.get("pretrade_date")
            }
        
        # 处理未找到的日期
        batch_results = []
        for date in dates:
            if date in result_map:
                batch_results.append(result_map[date])
            else:
                batch_results.append({
                    "date": date,
                    "is_trading_day": False,
                    "pretrade_date": None,
                    "message": "未找到该日期的交易日历信息"
                })
        
        return {
            "success": True,
            "data": batch_results,
            "exchange": exchange,
            "total_checked": len(dates)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量查询失败: {str(e)}")