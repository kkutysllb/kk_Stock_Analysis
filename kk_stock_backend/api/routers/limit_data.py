# -*- coding: utf-8 -*-
"""
限售股和涨跌停数据API接口
支持涨跌停统计、限售股解禁、阶梯涨跌停等数据查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel

import sys
import os
from api.global_db import db_handler

# 添加项目根目录到sys.path以便导入数据库管理器
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(api_dir)
sys.path.insert(0, project_root)

router = APIRouter()

sys.path.insert(0, project_root)


# 数据模型
class LimitListData(BaseModel):
    trade_date: str
    ts_code: str
    name: str
    close: float
    pct_chg: float
    amp: float
    fc_ratio: float
    fl_ratio: float
    fd_amount: float
    first_time: str
    last_time: str
    open_times: int
    strth: float
    limit: str

class LimitStepData(BaseModel):
    trade_date: str
    ts_code: str
    name: str
    limit_times: int
    fc_ratio: float
    fl_ratio: float
    fd_amount: float
    first_time: str
    last_time: str
    open_times: int
    strth: float
    limit: str

# ==================== 涨跌停数据 ====================

@router.get("/daily/list")
async def get_limit_list_daily(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    limit_type: Optional[str] = Query(default=None, description="涨跌停类型: U-涨停, D-跌停"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取涨跌停统计数据
    """
    try:
        collection = db_handler.get_collection('limit_list_daily')
        
        # 如果没有指定日期，获取最新交易日期
        if not trade_date:
            latest_record = collection.find_one(
                sort=[('trade_date', -1)],
                projection={'trade_date': 1}
            )
            if latest_record:
                trade_date = latest_record['trade_date']
            else:
                trade_date = datetime.now().strftime('%Y%m%d')
        
        # 构建查询条件
        query = {"trade_date": trade_date}
        
        if limit_type:
            query["limit"] = limit_type
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("pct_chg", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "limit_type": limit_type,
                "limit_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨跌停数据失败: {str(e)}")

@router.get("/daily/stats")
async def get_limit_daily_stats(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD")
):
    """
    获取涨跌停统计摘要
    """
    try:
        collection = db_handler.get_collection('limit_list_daily')
        
        # 如果没有指定日期，获取最新交易日期
        if not trade_date:
            latest_record = collection.find_one(
                sort=[('trade_date', -1)],
                projection={'trade_date': 1}
            )
            if latest_record:
                trade_date = latest_record['trade_date']
            else:
                trade_date = datetime.now().strftime('%Y%m%d')
        
        # 统计涨停和跌停数量
        up_limit_count = collection.count_documents({
            "trade_date": trade_date,
            "limit": "U"
        })
        
        down_limit_count = collection.count_documents({
            "trade_date": trade_date,
            "limit": "D"
        })
        
        # 获取涨停股票的平均封单比例（使用现有字段）
        up_limit_pipeline = [
            {"$match": {"trade_date": trade_date, "limit": "U"}},
            {"$group": {
                "_id": None,
                "avg_turnover_ratio": {"$avg": "$turnover_ratio"},
                "avg_fd_amount": {"$avg": "$fd_amount"},
                "total_fd_amount": {"$sum": "$fd_amount"},
                "count": {"$sum": 1}
            }}
        ]
        
        up_limit_stats = list(collection.aggregate(up_limit_pipeline))
        
        # 获取跌停股票的平均封单比例（使用现有字段）
        down_limit_pipeline = [
            {"$match": {"trade_date": trade_date, "limit": "D"}},
            {"$group": {
                "_id": None,
                "avg_turnover_ratio": {"$avg": "$turnover_ratio"},
                "avg_fd_amount": {"$avg": "$fd_amount"},
                "total_fd_amount": {"$sum": "$fd_amount"},
                "count": {"$sum": 1}
            }}
        ]
        
        down_limit_stats = list(collection.aggregate(down_limit_pipeline))
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "up_limit_count": up_limit_count,
                "down_limit_count": down_limit_count,
                "up_limit_stats": up_limit_stats[0] if up_limit_stats else {},
                "down_limit_stats": down_limit_stats[0] if down_limit_stats else {},
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨跌停统计失败: {str(e)}")

# ==================== 阶梯涨跌停数据 ====================

@router.get("/step/list")
async def get_limit_step(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    limit_type: Optional[str] = Query(default=None, description="涨跌停类型: U-涨停, D-跌停"),
    min_times: Optional[int] = Query(default=None, description="最小连续涨跌停次数"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取阶梯涨跌停数据
    """
    try:
        collection = db_handler.get_collection('limit_step')
        
        # 如果没有指定日期，获取最新交易日期
        if not trade_date:
            latest_record = collection.find_one(
                sort=[('trade_date', -1)],
                projection={'trade_date': 1}
            )
            if latest_record:
                trade_date = latest_record['trade_date']
            else:
                trade_date = datetime.now().strftime('%Y%m%d')
        
        # 构建查询条件
        query = {"trade_date": trade_date}
        
        if limit_type:
            query["limit"] = limit_type
        
        if min_times:
            query["limit_times"] = {"$gte": min_times}
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("limit_times", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "limit_type": limit_type,
                "min_times": min_times,
                "step_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取阶梯涨跌停数据失败: {str(e)}")

# ==================== 限售股解禁数据 ====================

@router.get("/concept/list")
async def get_limit_concept_list(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    limit: int = Query(default=50, description="返回条数")
):
    """
    获取最强概念板块数据
    """
    try:
        collection = db_handler.get_collection('limit_cpt_list')
        
        # 如果没有指定日期，获取最新交易日期
        if not trade_date:
            latest_record = collection.find_one(
                sort=[('trade_date', -1)],
                projection={'trade_date': 1}
            )
            if latest_record:
                trade_date = latest_record['trade_date']
            else:
                trade_date = datetime.now().strftime('%Y%m%d')
        
        # 构建查询条件
        query = {"trade_date": trade_date}
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("rank", 1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "concept_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概念板块数据失败: {str(e)}")

@router.get("/concept/trend")
async def get_concept_trend(
    days: int = Query(default=7, description="分析天数", ge=3, le=30)
):
    """
    获取概念板块轮动趋势
    """
    try:
        collection = db_handler.get_collection('limit_cpt_list')
        
        # 获取最近N天的概念板块数据
        pipeline = [
            {"$sort": {"trade_date": -1}},
            {"$group": {
                "_id": "$trade_date",
                "concepts": {"$push": {
                    "name": "$name",
                    "rank": "$rank",
                    "up_nums": "$up_nums",
                    "pct_chg": "$pct_chg",
                    "up_stat": "$up_stat"
                }}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": days}
        ]
        
        trend_data = list(collection.aggregate(pipeline))
        
        # 整理数据格式
        formatted_data = []
        for item in trend_data:
            # 只取前10个概念板块
            top_concepts = sorted(item['concepts'], key=lambda x: x['rank'])[:10]
            formatted_data.append({
                'trade_date': item['_id'],
                'concepts': top_concepts
            })
        
        return {
            "success": True,
            "data": {
                "days": days,
                "trend_data": formatted_data,
                "count": len(formatted_data),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概念板块趋势失败: {str(e)}")

@router.get("/step/stats")
async def get_limit_step_stats(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD")
):
    """
    获取连板天梯统计数据
    """
    try:
        collection = db_handler.get_collection('limit_step')
        
        # 如果没有指定日期，获取最新交易日期
        if not trade_date:
            latest_record = collection.find_one(
                sort=[('trade_date', -1)],
                projection={'trade_date': 1}
            )
            if latest_record:
                trade_date = latest_record['trade_date']
            else:
                trade_date = datetime.now().strftime('%Y%m%d')
        
        # 统计连板天梯分布
        pipeline = [
            {"$match": {"trade_date": trade_date}},
            {"$group": {
                "_id": "$nums",
                "count": {"$sum": 1},
                "stocks": {"$push": {
                    "ts_code": "$ts_code",
                    "name": "$name"
                }}
            }},
            {"$sort": {"_id": -1}}
        ]
        
        step_stats = list(collection.aggregate(pipeline))
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "step_stats": step_stats,
                "count": len(step_stats),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取连板天梯统计失败: {str(e)}")

@router.get("/cpt/stats")
async def get_limit_cpt_stats(
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD")
):
    """
    获取限售股解禁统计数据
    """
    try:
        collection = db_handler.get_collection('limit_cpt_list')
        
        # 构建查询条件
        query = {}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["ann_date"] = date_query
        
        # 统计解禁股票数量和解禁市值
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": None,
                "total_count": {"$sum": 1},
                "total_float_mv": {"$sum": "$float_mv"},
                "avg_float_mv": {"$avg": "$float_mv"},
                "total_float_ratio": {"$sum": "$float_ratio"}
            }}
        ]
        
        stats_result = list(collection.aggregate(pipeline))
        
        # 按日期统计
        date_pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$ann_date",
                "count": {"$sum": 1},
                "total_float_mv": {"$sum": "$float_mv"}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 30}
        ]
        
        date_stats = list(collection.aggregate(date_pipeline))
        
        return {
            "success": True,
            "data": {
                "start_date": start_date,
                "end_date": end_date,
                "overall_stats": stats_result[0] if stats_result else {},
                "daily_stats": date_stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取限售股解禁统计失败: {str(e)}")

# ==================== 批量查询接口（支持并发） ====================

@router.post("/batch/daily")
async def get_batch_limit_daily(
    request_data: Dict[str, Any]
):
    """
    批量获取涨跌停数据（支持并发查询）
    
    请求格式:
    {
        "trade_dates": ["20241225", "20241226"],
        "limit_type": "U",
        "limit": 100
    }
    """
    try:
        trade_dates = request_data.get('trade_dates', [])
        limit_type = request_data.get('limit_type')
        limit = request_data.get('limit', 100)
        
        if not trade_dates:
            raise HTTPException(status_code=400, detail="trade_dates 不能为空")
        
        if len(trade_dates) > 30:
            raise HTTPException(status_code=400, detail="批量查询最多支持30个交易日")
        
        # 异步并发查询
        async def fetch_single_date_data(trade_date: str):
            try:
                collection = db_handler.get_collection('limit_list_daily')
                
                query = {"trade_date": trade_date}
                if limit_type:
                    query["limit"] = limit_type
                
                cursor = collection.find(
                    query,
                    {"_id": 0}
                ).sort("pct_chg", -1).limit(limit)
                
                return {
                    "trade_date": trade_date,
                    "data": list(cursor),
                    "success": True
                }
                
            except Exception as e:
                return {
                    "trade_date": trade_date,
                    "data": [],
                    "success": False,
                    "error": str(e)
                }
        
        # 并发执行查询
        tasks = [fetch_single_date_data(trade_date) for trade_date in trade_dates]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        
        return {
            "success": True,
            "data": {
                "results": results,
                "total_requested": len(trade_dates),
                "success_count": success_count,
                "failed_count": len(trade_dates) - success_count,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量查询涨跌停数据失败: {str(e)}")

# ==================== 涨跌停趋势分析 ====================

@router.get("/trend/analysis")
async def get_limit_trend_analysis(
    days: int = Query(default=30, description="分析天数", ge=7, le=90)
):
    """
    获取涨跌停趋势分析
    """
    try:
        collection = db_handler.get_collection('limit_list_daily')
        
        # 获取最近N天的涨跌停统计
        pipeline = [
            {"$group": {
                "_id": {
                    "trade_date": "$trade_date",
                    "limit_type": "$limit"
                },
                "count": {"$sum": 1},
                "avg_fc_ratio": {"$avg": "$fc_ratio"},
                "total_fd_amount": {"$sum": "$fd_amount"}
            }},
            {"$sort": {"_id.trade_date": -1}},
            {"$limit": days * 2}  # 涨停和跌停各一条记录
        ]
        
        trend_data = list(collection.aggregate(pipeline))
        
        # 整理数据格式
        daily_stats = {}
        for item in trend_data:
            trade_date = item['_id']['trade_date']
            limit_type = item['_id']['limit_type']
            
            if trade_date not in daily_stats:
                daily_stats[trade_date] = {
                    'trade_date': trade_date,
                    'up_limit_count': 0,
                    'down_limit_count': 0,
                    'up_limit_amount': 0,
                    'down_limit_amount': 0
                }
            
            if limit_type == 'U':
                daily_stats[trade_date]['up_limit_count'] = item['count']
                daily_stats[trade_date]['up_limit_amount'] = item['total_fd_amount']
            elif limit_type == 'D':
                daily_stats[trade_date]['down_limit_count'] = item['count']
                daily_stats[trade_date]['down_limit_amount'] = item['total_fd_amount']
        
        # 转换为列表并按日期排序
        trend_list = sorted(daily_stats.values(), key=lambda x: x['trade_date'], reverse=True)
        
        return {
            "success": True,
            "data": {
                "days": days,
                "trend_data": trend_list,
                "count": len(trend_list),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨跌停趋势分析失败: {str(e)}")