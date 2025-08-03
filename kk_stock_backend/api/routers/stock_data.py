#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据API接口
支持股票基本信息、K线数据、公司信息等高并发查询
"""

from fastapi import APIRouter, HTTPException, Query, Depends
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

from api.routers.user import get_current_user
from api.cache_middleware import cache_endpoint
from api.global_db import db_handler

router = APIRouter()

# 数据模型
class StockBasicInfo(BaseModel):
    ts_code: str
    symbol: str
    name: str
    area: str
    industry: str
    market: str
    list_date: str

class StockKlineData(BaseModel):
    ts_code: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    vol: float
    amount: float
    pct_chg: float

class StockSearchRequest(BaseModel):
    keyword: str
    limit: int = 20

class StockListRequest(BaseModel):
    market: Optional[str] = None
    industry: Optional[str] = None
    limit: int = 100

class KlineRequest(BaseModel):
    ts_codes: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: str = "daily"

# ==================== 股票基本信息 ====================

@router.get("/basic/search")
@cache_endpoint(data_type='stock_search', ttl=1800)  # 缓存30分钟
async def search_stocks(
    keyword: str = Query(..., description="搜索关键字（股票代码、名称）"),
    limit: int = Query(default=20, description="返回结果数量限制")
):
    """
    搜索股票基本信息
    支持按股票代码、简称、全称搜索
    """
    try:
        collection = db_handler.get_collection('infrastructure_stock_basic')
        
        # 构建搜索条件
        search_query = {
            "$or": [
                {"ts_code": {"$regex": keyword.upper(), "$options": "i"}},
                {"symbol": {"$regex": keyword.upper(), "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}},
                {"fullname": {"$regex": keyword, "$options": "i"}}
            ]
        }
        
        # 查询数据
        cursor = collection.find(
            search_query,
            {"_id": 0}
        ).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "keyword": keyword,
                "count": len(results),
                "stocks": results,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索股票失败: {str(e)}")

@router.get("/basic/list")
@cache_endpoint(data_type='stock_list', ttl=3600)  # 缓存1小时
async def get_stock_list(
    market: Optional[str] = Query(default=None, description="市场：主板、创业板、科创板、北交所"),
    industry: Optional[str] = Query(default=None, description="行业"),
    is_hs: Optional[str] = Query(default=None, description="是否沪深港通标的：S=沪股通，H=深股通"),
    list_status: str = Query(default="L", description="上市状态：L=上市，D=退市，P=暂停上市"),
    limit: int = Query(default=100, description="返回数量限制")
):
    """
    获取股票列表
    支持按市场、行业、沪深港通标的筛选
    """
    try:
        collection = db_handler.get_collection('stock_basic')
        
        # 构建查询条件
        query = {"list_status": list_status}
        
        if market:
            query["market"] = market
        
        if industry:
            query["industry"] = industry
            
        if is_hs:
            query["is_hs"] = is_hs
        
        # 查询数据
        cursor = collection.find(
            query,
            {"_id": 0}
        ).limit(limit)
        
        results = list(cursor)
        
        # 统计信息
        total_count = collection.count_documents(query)
        
        return {
            "success": True,
            "data": {
                "filters": {
                    "market": market,
                    "industry": industry,
                    "is_hs": is_hs,
                    "list_status": list_status
                },
                "total_count": total_count,
                "returned_count": len(results),
                "stocks": results,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")

@router.get("/basic/detail/{ts_code}")
@cache_endpoint(data_type='stock_detail', ttl=14400)  # 缓存4小时
async def get_stock_detail(ts_code: str):
    """
    获取股票详细信息
    包含基本信息、公司信息、最新行情等
    """
    try:
        # 获取股票基本信息
        stock_basic = db_handler.get_collection('infrastructure_stock_basic')
        basic_info = stock_basic.find_one({"ts_code": ts_code}, {"_id": 0})
        
        if not basic_info:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 获取公司基本信息
        stock_company = db_handler.get_collection('infrastructure_stock_company')
        company_info = stock_company.find_one({"ts_code": ts_code}, {"_id": 0})
        
        # 获取最新日线行情
        daily_collection = db_handler.get_collection('stock_kline_daily')
        latest_daily = daily_collection.find_one(
            {"ts_code": ts_code},
            {"_id": 0},
            sort=[("trade_date", -1)]
        )
        
        return {
            "success": True,
            "data": {
                "basic_info": basic_info,
                "company_info": company_info,
                "latest_quote": latest_daily,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取股票详情失败: {str(e)}")

# ==================== K线数据 ====================

@router.get("/kline/{ts_code}")
@cache_endpoint(data_type='stock_kline', ttl=7200)  # 缓存2小时
async def get_stock_kline(
    ts_code: str,
    period: str = Query(default="daily", description="数据周期：daily、weekly、monthly"),
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=200, description="获取数据条数")
):
    """
    获取股票K线数据
    支持日线、周线、月线数据
    """
    try:
        # 根据周期选择集合
        collection_map = {
            'daily': 'stock_kline_daily',
            'weekly': 'stock_kline_weekly',
            'monthly': 'stock_kline_monthly'
        }
        
        collection_name = collection_map.get(period)
        if not collection_name:
            raise HTTPException(status_code=400, detail="无效的数据周期")
        
        collection = db_handler.get_collection(collection_name)
        
        # 构建查询条件
        query = {"ts_code": ts_code}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["trade_date"] = date_query
        
        # 查询数据
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("trade_date", -1).limit(limit)
        
        kline_data = list(cursor)
        
        # 计算简单技术指标
        if kline_data:
            # 计算涨跌统计
            up_count = sum(1 for item in kline_data if item.get("pct_chg", 0) > 0)
            down_count = sum(1 for item in kline_data if item.get("pct_chg", 0) < 0)
            
            # 最高和最低价
            prices = [item.get("close", 0) for item in kline_data if item.get("close")]
            highest_price = max(prices) if prices else 0
            lowest_price = min(prices) if prices else 0
            
            # 计算平均成交量
            volumes = [item.get("vol", 0) for item in kline_data if item.get("vol")]
            avg_volume = sum(volumes) / len(volumes) if volumes else 0
            
            stats = {
                "total_days": len(kline_data),
                "up_days": up_count,
                "down_days": down_count,
                "highest_price": highest_price,
                "lowest_price": lowest_price,
                "avg_volume": avg_volume
            }
        else:
            stats = {}
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "period": period,
                "count": len(kline_data),
                "statistics": stats,
                "kline_data": kline_data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")

@router.post("/kline/batch")
@cache_endpoint(data_type='stock_kline_batch', ttl=7200)  # 缓存2小时
async def get_batch_kline(request: KlineRequest):
    """
    批量获取多只股票的K线数据
    最多支持50只股票同时查询
    """
    try:
        if len(request.ts_codes) > 50:
            raise HTTPException(status_code=400, detail="批量查询最多支持50只股票")
        
        # 根据周期选择集合
        collection_map = {
            'daily': 'stock_daily',
            'weekly': 'stock_weekly',
            'monthly': 'stock_monthly'
        }
        
        collection_name = collection_map.get(request.period)
        if not collection_name:
            raise HTTPException(status_code=400, detail="无效的数据周期")
        
        collection = db_handler.get_collection(collection_name)
        
        # 构建查询条件
        query = {"ts_code": {"$in": request.ts_codes}}
        
        if request.start_date or request.end_date:
            date_query = {}
            if request.start_date:
                date_query["$gte"] = request.start_date
            if request.end_date:
                date_query["$lte"] = request.end_date
            query["trade_date"] = date_query
        
        # 查询数据
        cursor = collection.find(query, {"_id": 0})
        all_data = list(cursor)
        
        # 按股票代码分组
        stock_data = {}
        for item in all_data:
            ts_code = item["ts_code"]
            if ts_code not in stock_data:
                stock_data[ts_code] = []
            stock_data[ts_code].append(item)
        
        # 对每只股票的数据按日期排序
        for ts_code in stock_data:
            stock_data[ts_code].sort(key=lambda x: x["trade_date"], reverse=True)
        
        return {
            "success": True,
            "data": {
                "ts_codes": request.ts_codes,
                "period": request.period,
                "date_range": {
                    "start_date": request.start_date,
                    "end_date": request.end_date
                },
                "stock_count": len(stock_data),
                "stock_data": stock_data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"批量获取K线数据失败: {str(e)}")

# ==================== 技术分析 ====================

@router.get("/technical/{ts_code}")
@cache_endpoint(data_type='stock_technical', ttl=3600)  # 缓存1小时
async def get_technical_analysis(
    ts_code: str,
    days: int = Query(default=20, description="分析天数")
):
    """
    获取股票技术分析指标
    包括移动平均线、RSI、布林带等
    """
    try:
        collection = db_handler.get_collection('stock_kline_daily')
        
        # 获取指定天数的数据
        cursor = collection.find(
            {"ts_code": ts_code},
            {"_id": 0, "trade_date": 1, "close": 1, "high": 1, "low": 1, "vol": 1, "pct_chg": 1}
        ).sort("trade_date", -1).limit(days)
        
        data = list(cursor)
        
        if not data:
            raise HTTPException(status_code=404, detail="未找到该股票的数据")
        
        # 计算技术指标
        closes = [item["close"] for item in reversed(data)]
        highs = [item["high"] for item in reversed(data)]
        lows = [item["low"] for item in reversed(data)]
        
        # 简单移动平均线
        ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else None
        ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else None
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else None
        
        # 最新价格
        latest_price = closes[-1] if closes else 0
        
        # 计算支撑位和阻力位（简化版）
        recent_lows = lows[-10:] if len(lows) >= 10 else lows
        recent_highs = highs[-10:] if len(highs) >= 10 else highs
        
        support_level = min(recent_lows) if recent_lows else 0
        resistance_level = max(recent_highs) if recent_highs else 0
        
        # 计算波动率
        pct_changes = [abs(item.get("pct_chg", 0)) for item in data]
        volatility = sum(pct_changes) / len(pct_changes) if pct_changes else 0
        
        technical_indicators = {
            "moving_averages": {
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20
            },
            "price_levels": {
                "latest_price": latest_price,
                "support_level": support_level,
                "resistance_level": resistance_level
            },
            "risk_metrics": {
                "volatility": round(volatility, 2),
                "days_analyzed": len(data)
            }
        }
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "analysis_period": days,
                "technical_indicators": technical_indicators,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"技术分析失败: {str(e)}")

# ==================== 排行榜 ====================

@router.get("/rankings/gainers")
@cache_endpoint(data_type="stock_gainers", ttl=600)
async def get_top_gainers(
    limit: int = Query(default=20, description="返回数量"),
    market: Optional[str] = Query(default=None, description="市场筛选")
):
    """
    获取涨幅榜
    """
    try:
        collection = db_handler.get_collection('stock_kline_daily')
        
        # 获取最新交易日期
        latest_record = collection.find_one(
            sort=[('trade_date', -1)],
            projection={'trade_date': 1}
        )
        
        if not latest_record:
            raise HTTPException(status_code=404, detail="未找到交易数据")
        
        latest_date = latest_record['trade_date']
        
        # 构建查询条件
        query = {"trade_date": latest_date, "pct_chg": {"$exists": True}}
        
        # 查询涨幅榜
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("pct_chg", -1).limit(limit)
        
        gainers = list(cursor)
        
        # 如果需要，添加股票基本信息
        if gainers:
            ts_codes = [item["ts_code"] for item in gainers]
            stock_basic = db_handler.get_collection('infrastructure_stock_basic')
            basic_info = {
                item["ts_code"]: item 
                for item in stock_basic.find(
                    {"ts_code": {"$in": ts_codes}},
                    {"_id": 0, "ts_code": 1, "name": 1, "industry": 1, "market": 1}
                )
            }
            
            # 合并基本信息
            for item in gainers:
                if item["ts_code"] in basic_info:
                    item.update(basic_info[item["ts_code"]])
        
        return {
            "success": True,
            "data": {
                "trade_date": latest_date,
                "type": "gainers",
                "count": len(gainers),
                "rankings": gainers,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取涨幅榜失败: {str(e)}")

@router.get("/rankings/losers")
@cache_endpoint(data_type="stock_losers", ttl=600)
async def get_top_losers(
    limit: int = Query(default=20, description="返回数量")
):
    """
    获取跌幅榜
    """
    try:
        collection = db_handler.get_collection('stock_daily')
        
        # 获取最新交易日期
        latest_record = collection.find_one(
            sort=[('trade_date', -1)],
            projection={'trade_date': 1}
        )
        
        if not latest_record:
            raise HTTPException(status_code=404, detail="未找到交易数据")
        
        latest_date = latest_record['trade_date']
        
        # 查询跌幅榜
        cursor = collection.find(
            {"trade_date": latest_date, "pct_chg": {"$exists": True}},
            {"_id": 0}
        ).sort("pct_chg", 1).limit(limit)
        
        losers = list(cursor)
        
        # 添加股票基本信息
        if losers:
            ts_codes = [item["ts_code"] for item in losers]
            stock_basic = db_handler.get_collection('stock_basic')
            basic_info = {
                item["ts_code"]: item 
                for item in stock_basic.find(
                    {"ts_code": {"$in": ts_codes}},
                    {"_id": 0, "ts_code": 1, "name": 1, "industry": 1, "market": 1}
                )
            }
            
            for item in losers:
                if item["ts_code"] in basic_info:
                    item.update(basic_info[item["ts_code"]])
        
        return {
            "success": True,
            "data": {
                "trade_date": latest_date,
                "type": "losers",
                "count": len(losers),
                "rankings": losers,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取跌幅榜失败: {str(e)}")

@router.get("/rankings/volume")
@cache_endpoint(data_type="stock_volume", ttl=600)
async def get_top_volume(
    limit: int = Query(default=20, description="返回数量")
):
    """
    获取成交量排行榜
    """
    try:
        collection = db_handler.get_collection('stock_daily')
        
        # 获取最新交易日期
        latest_record = collection.find_one(
            sort=[('trade_date', -1)],
            projection={'trade_date': 1}
        )
        
        if not latest_record:
            raise HTTPException(status_code=404, detail="未找到交易数据")
        
        latest_date = latest_record['trade_date']
        
        # 查询成交量排行
        cursor = collection.find(
            {"trade_date": latest_date, "vol": {"$exists": True}},
            {"_id": 0}
        ).sort("vol", -1).limit(limit)
        
        volume_leaders = list(cursor)
        
        # 添加股票基本信息
        if volume_leaders:
            ts_codes = [item["ts_code"] for item in volume_leaders]
            stock_basic = db_handler.get_collection('stock_basic')
            basic_info = {
                item["ts_code"]: item 
                for item in stock_basic.find(
                    {"ts_code": {"$in": ts_codes}},
                    {"_id": 0, "ts_code": 1, "name": 1, "industry": 1, "market": 1}
                )
            }
            
            for item in volume_leaders:
                if item["ts_code"] in basic_info:
                    item.update(basic_info[item["ts_code"]])
        
        return {
            "success": True,
            "data": {
                "trade_date": latest_date,
                "type": "volume",
                "count": len(volume_leaders),
                "rankings": volume_leaders,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取成交量排行失败: {str(e)}")

# ==================== 市场概览 ====================

@router.get("/market/overview")
@cache_endpoint(data_type="market_overview", ttl=300)
async def get_market_overview():
    """
    获取市场概览数据
    包括涨跌家数、成交金额等统计信息
    """
    try:
        collection = db_handler.get_collection('stock_daily')
        
        # 获取最新交易日期
        latest_record = collection.find_one(
            sort=[('trade_date', -1)],
            projection={'trade_date': 1}
        )
        
        if not latest_record:
            raise HTTPException(status_code=404, detail="未找到交易数据")
        
        latest_date = latest_record['trade_date']
        
        # 统计市场数据
        pipeline = [
            {"$match": {"trade_date": latest_date}},
            {"$group": {
                "_id": None,
                "total_stocks": {"$sum": 1},
                "rising_stocks": {
                    "$sum": {"$cond": [{"$gt": ["$pct_chg", 0]}, 1, 0]}
                },
                "falling_stocks": {
                    "$sum": {"$cond": [{"$lt": ["$pct_chg", 0]}, 1, 0]}
                },
                "unchanged_stocks": {
                    "$sum": {"$cond": [{"$eq": ["$pct_chg", 0]}, 1, 0]}
                },
                "total_volume": {"$sum": "$vol"},
                "total_amount": {"$sum": "$amount"},
                "avg_pct_chg": {"$avg": "$pct_chg"}
            }}
        ]
        
        result = list(collection.aggregate(pipeline))
        
        if not result:
            raise HTTPException(status_code=404, detail="未找到市场数据")
        
        market_stats = result[0]
        
        return {
            "success": True,
            "data": {
                "trade_date": latest_date,
                "market_statistics": {
                    "total_stocks": market_stats.get("total_stocks", 0),
                    "rising_stocks": market_stats.get("rising_stocks", 0),
                    "falling_stocks": market_stats.get("falling_stocks", 0),
                    "unchanged_stocks": market_stats.get("unchanged_stocks", 0),
                    "total_volume": market_stats.get("total_volume", 0),
                    "total_amount": market_stats.get("total_amount", 0),
                    "average_change": round(market_stats.get("avg_pct_chg", 0), 2)
                },
                "market_sentiment": {
                    "bullish_ratio": round(
                        market_stats.get("rising_stocks", 0) / max(market_stats.get("total_stocks", 1), 1) * 100, 2
                    ),
                    "bearish_ratio": round(
                        market_stats.get("falling_stocks", 0) / max(market_stats.get("total_stocks", 1), 1) * 100, 2
                    )
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")

# ==================== 用户自选股（需要登录） ====================

@router.get("/watchlist", dependencies=[Depends(get_current_user)])
async def get_user_watchlist(user=Depends(get_current_user)):
    """
    获取用户自选股列表
    """
    try:
        # 这里可以扩展用户自选股功能
        # 目前返回示例数据
        return {
            "success": True,
            "data": {
                "user_id": user["user_id"],
                "watchlist": [],
                "message": "自选股功能开发中",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自选股失败: {str(e)}")