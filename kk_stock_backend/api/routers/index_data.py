#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数数据API接口
支持指数基本信息、指数行情数据等高并发查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
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


sys.path.insert(0, project_root)

router = APIRouter()


# 主要指数配置
MAJOR_INDICES = {
    '000001.SH': {'name': '上证指数', 'market': '上证主板'},
    '399001.SZ': {'name': '深证成指', 'market': '深证主板'}, 
    '399006.SZ': {'name': '创业板指', 'market': '创业板'},
    '000688.SH': {'name': '科创50', 'market': '科创板'},
    '899050.BJ': {'name': '北证50', 'market': '北交所'},
    '000016.SH': {'name': '上证50', 'market': '上证主板'},
    '000300.SH': {'name': '沪深300', 'market': '沪深300'},
    '000905.SH': {'name': '中证500', 'market': '中证500'},
    '000852.SH': {'name': '中证1000', 'market': '中证1000'},
    '399303.SZ': {'name': '国证2000', 'market': '深证主板'},
    # 中小板块指数
    '000510.CSI': {'name': '中证A500', 'market': '中证指数'},
    '000142.SH': {'name': '上证380', 'market': '上证主板'},
    '399010.SZ': {'name': '深证700', 'market': '深证主板'},
    '399020.SZ': {'name': '创业小盘', 'market': '深证主板'},
    '932000.CSI': {'name': '中证2000', 'market': '中证指数'}
}

# 申万行业指数配置
SW_INDICES = {
    '801010.SI': '农林牧渔',
    '801020.SI': '采掘',
    '801030.SI': '化工',
    '801040.SI': '钢铁',
    '801050.SI': '有色金属',
    '801080.SI': '电子',
    '801110.SI': '家用电器',
    '801120.SI': '食品饮料',
    '801130.SI': '纺织服装',
    '801140.SI': '轻工制造',
    '801150.SI': '医药生物',
    '801160.SI': '公用事业',
    '801170.SI': '交通运输',
    '801180.SI': '房地产',
    '801200.SI': '商业贸易',
    '801210.SI': '休闲服务',
    '801230.SI': '综合',
    '801710.SI': '建筑材料',
    '801720.SI': '建筑装饰',
    '801730.SI': '电气设备',
    '801740.SI': '国防军工',
    '801750.SI': '计算机',
    '801760.SI': '传媒',
    '801770.SI': '通信',
    '801780.SI': '银行',
    '801790.SI': '非银金融',
    '801880.SI': '汽车',
    '801890.SI': '机械设备'
}

# ==================== 指数基本信息 ====================

@cache_endpoint(data_type='index_data', ttl=3600)  # 缓存1小时
@router.get("/basic/list")
async def get_index_list(
    market: Optional[str] = Query(default=None, description="市场类型"),
    category: Optional[str] = Query(default=None, description="指数分类"),
    limit: int = Query(default=100, description="返回数量限制")
):
    """
    获取指数列表
    支持按市场、分类筛选
    """
    try:
        collection = db_handler.get_collection('index_basic')
        
        # 构建查询条件
        query = {}
        
        if market:
            query["market"] = market
        
        if category:
            query["category"] = category
        
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
                    "category": category
                },
                "total_count": total_count,
                "returned_count": len(results),
                "indices": results,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指数列表失败: {str(e)}")

@router.get("/basic/search")
async def search_indices(
    keyword: str = Query(..., description="搜索关键字（指数代码、名称）"),
    limit: int = Query(default=20, description="返回结果数量限制")
):
    """
    搜索指数信息
    支持按指数代码、名称搜索
    """
    try:
        collection = db_handler.get_collection('index_basic')
        
        # 构建搜索条件
        search_query = {
            "$or": [
                {"ts_code": {"$regex": keyword.upper(), "$options": "i"}},
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
                "indices": results,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索指数失败: {str(e)}")

@router.get("/basic/detail/{ts_code}")
async def get_index_detail(ts_code: str):
    """
    获取指数详细信息
    包含基本信息、最新行情等
    """
    try:
        # 获取指数基本信息
        index_basic = db_handler.get_collection('index_basic')
        basic_info = index_basic.find_one({"ts_code": ts_code}, {"_id": 0})
        
        if not basic_info:
            raise HTTPException(status_code=404, detail="指数不存在")
        
        # 获取最新日线行情
        daily_collection = db_handler.get_collection('index_daily')
        latest_daily = daily_collection.find_one(
            {"ts_code": ts_code},
            {"_id": 0},
            sort=[("trade_date", -1)]
        )
        
        return {
            "success": True,
            "data": {
                "basic_info": basic_info,
                "latest_quote": latest_daily,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取指数详情失败: {str(e)}")

# ==================== 主要指数数据 ====================

@router.get("/major")
async def get_major_indices(
    period: str = Query(default="daily", description="数据周期：daily、weekly、monthly"),
    limit: int = Query(default=30, description="获取数据条数")
):
    """
    获取主要指数数据
    包括上证指数、深证成指、创业板指等
    """
    try:
        # 根据周期选择集合
        collection_map = {
            'daily': 'index_daily',
            'weekly': 'index_weekly',
            'monthly': 'index_monthly'
        }
        
        collection_name = collection_map.get(period, 'index_daily')
        collection = db_handler.get_collection(collection_name)
        
        # 获取所有主要指数的最新数据
        indices_data = []
        for ts_code, info in MAJOR_INDICES.items():
            # 获取该指数的最新数据
            cursor = collection.find(
                {'ts_code': ts_code},
                {'_id': 0}
            ).sort('trade_date', -1).limit(limit)
            
            data_list = list(cursor)
            if data_list:
                latest_data = data_list[0]
                indices_data.append({
                    'ts_code': ts_code,
                    'name': info['name'],
                    'market': info['market'],
                    'latest_data': latest_data,
                    'history_data': data_list[:limit] if len(data_list) > 1 else []
                })
        
        return {
            "success": True,
            "data": {
                "period": period,
                "indices": indices_data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取主要指数数据失败: {str(e)}")

# ==================== 指数K线数据 ====================

@router.get("/kline/{ts_code}")
async def get_index_kline(
    ts_code: str,
    period: str = Query(default="daily", description="数据周期：daily、weekly、monthly"),
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=200, description="获取数据条数")
):
    """
    获取指数K线数据
    支持日线、周线、月线数据
    支持申万行业指数查询
    """
    try:
        # 检查是否为申万行业指数
        is_sw_index = ts_code in SW_INDICES or ts_code.endswith('.SI')
        
        if is_sw_index:
            # 申万行业指数只支持日线数据，使用sw_daily集合
            collection = db_handler.get_collection('sw_daily')
        else:
            # 根据周期选择集合
            collection_map = {
                'daily': 'index_daily',
                'weekly': 'index_weekly',
                'monthly': 'index_monthly'
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
        
        # 计算统计指标
        if kline_data:
            # 计算涨跌统计
            up_count = sum(1 for item in kline_data if item.get("pct_chg", 0) > 0)
            down_count = sum(1 for item in kline_data if item.get("pct_chg", 0) < 0)
            
            # 最高和最低点位
            points = [item.get("close", 0) for item in kline_data if item.get("close")]
            highest_point = max(points) if points else 0
            lowest_point = min(points) if points else 0
            
            # 计算平均成交额
            amounts = [item.get("amount", 0) for item in kline_data if item.get("amount")]
            avg_amount = sum(amounts) / len(amounts) if amounts else 0
            
            stats = {
                "total_days": len(kline_data),
                "up_days": up_count,
                "down_days": down_count,
                "highest_point": highest_point,
                "lowest_point": lowest_point,
                "avg_amount": avg_amount
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
        raise HTTPException(status_code=500, detail=f"获取指数K线数据失败: {str(e)}")

# ==================== 申万行业指数 ====================

@router.get("/shenwan/industries")
async def get_shenwan_industries():
    """
    获取申万行业分类列表
    从index_member_all集合中获取一级行业信息
    """
    try:
        collection = db_handler.get_collection('index_member_all')
        
        # 使用聚合查询获取所有一级行业的唯一值
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "l1_code": "$l1_code",
                        "l1_name": "$l1_name"
                    },
                    "stock_count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "code": "$_id.l1_code",
                    "name": "$_id.l1_name",
                    "stock_count": 1
                }
            },
            {
                "$match": {
                    "code": {"$ne": None},
                    "name": {"$ne": None}
                }
            },
            {
                "$sort": {"stock_count": -1}
            }
        ]
        
        industries = list(collection.aggregate(pipeline))
        
        # 为每个行业添加颜色配置（与前端现有配置保持一致）
        color_map = {
            '801010.SI': '#3b82f6',
            '801020.SI': '#10b981',
            '801030.SI': '#f59e0b',
            '801040.SI': '#ef4444',
            '801050.SI': '#8b5cf6',
            '801080.SI': '#ec4899',
            '801110.SI': '#14b8a6',
            '801120.SI': '#6366f1',
            '801130.SI': '#d946ef',
            '801140.SI': '#f97316',
            '801150.SI': '#22c55e',
            '801160.SI': '#64748b',
            '801170.SI': '#0ea5e9',
            '801180.SI': '#eab308',
            '801200.SI': '#a855f7',
            '801210.SI': '#06b6d4',
            '801230.SI': '#94a3b8',
            '801710.SI': '#f43f5e',
            '801720.SI': '#10b981',
            '801730.SI': '#6366f1',
            '801740.SI': '#d946ef',
            '801750.SI': '#f97316',
            '801760.SI': '#22c55e',
            '801770.SI': '#64748b',
            '801780.SI': '#0ea5e9',
            '801790.SI': '#eab308',
            '801880.SI': '#a855f7',
            '801890.SI': '#06b6d4'
        }
        
        # 为每个行业添加颜色
        for industry in industries:
            industry['color'] = color_map.get(industry['code'], '#666666')
        
        return {
            "success": True,
            "data": {
                "industries": industries,
                "total_count": len(industries),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取申万行业分类失败: {str(e)}")

@router.get("/shenwan")
async def get_shenwan_indices(
    period: str = Query(default="daily", description="数据周期"),
    limit: int = Query(default=10, description="获取最新数据条数")
):
    """
    获取申万行业指数数据
    """
    try:
        collection_map = {
            'daily': 'index_daily',
            'weekly': 'index_weekly',
            'monthly': 'index_monthly'
        }
        
        collection_name = collection_map.get(period, 'index_daily')
        collection = db_handler.get_collection(collection_name)
        
        # 获取申万行业指数数据
        sw_data = []
        for ts_code, industry_name in SW_INDICES.items():
            cursor = collection.find(
                {'ts_code': ts_code},
                {'_id': 0}
            ).sort('trade_date', -1).limit(limit)
            
            data_list = list(cursor)
            if data_list:
                latest_data = data_list[0]
                sw_data.append({
                    'ts_code': ts_code,
                    'industry_name': industry_name,
                    'latest_data': latest_data,
                    'history_data': data_list[1:] if len(data_list) > 1 else []
                })
        
        # 按涨跌幅排序
        sw_data.sort(key=lambda x: x['latest_data'].get('pct_chg', 0), reverse=True)
        
        return {
            "success": True,
            "data": {
                "period": period,
                "shenwan_indices": sw_data,
                "count": len(sw_data),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取申万行业指数失败: {str(e)}")

# ==================== 指数表现分析 ====================

@router.get("/performance/{ts_code}")
async def get_index_performance(
    ts_code: str,
    days: int = Query(default=30, description="分析天数")
):
    """
    获取指数表现分析
    包括涨跌幅统计、波动率等
    """
    try:
        collection = db_handler.get_collection('index_daily')
        
        # 获取指定天数的数据
        cursor = collection.find(
            {"ts_code": ts_code},
            {"_id": 0, "trade_date": 1, "close": 1, "high": 1, "low": 1, "pct_chg": 1, "amount": 1}
        ).sort("trade_date", -1).limit(days)
        
        data = list(cursor)
        
        if not data:
            raise HTTPException(status_code=404, detail="未找到该指数的数据")
        
        # 计算性能指标
        pct_changes = [item.get("pct_chg", 0) for item in data]
        closes = [item.get("close", 0) for item in data]
        amounts = [item.get("amount", 0) for item in data]
        
        # 累计涨跌幅
        cumulative_return = sum(pct_changes)
        
        # 波动率（标准差）
        avg_change = sum(pct_changes) / len(pct_changes) if pct_changes else 0
        variance = sum((x - avg_change) ** 2 for x in pct_changes) / len(pct_changes) if pct_changes else 0
        volatility = variance ** 0.5
        
        # 最大回撤
        peak = max(closes) if closes else 0
        trough = min(closes) if closes else 0
        max_drawdown = (peak - trough) / peak * 100 if peak > 0 else 0
        
        # 涨跌天数统计
        up_days = sum(1 for x in pct_changes if x > 0)
        down_days = sum(1 for x in pct_changes if x < 0)
        
        performance_metrics = {
            "analysis_period": days,
            "cumulative_return": round(cumulative_return, 2),
            "average_daily_return": round(avg_change, 2),
            "volatility": round(volatility, 2),
            "max_drawdown": round(max_drawdown, 2),
            "trading_days": len(data),
            "up_days": up_days,
            "down_days": down_days,
            "win_rate": round(up_days / len(data) * 100, 2) if data else 0,
            "average_amount": round(sum(amounts) / len(amounts), 0) if amounts else 0
        }
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "performance_metrics": performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取指数表现分析失败: {str(e)}")

# ==================== 指数排行榜 ====================

@router.get("/rankings/performance")
async def get_index_performance_ranking(
    period: str = Query(default="daily", description="统计周期"),
    days: int = Query(default=5, description="统计天数"),
    limit: int = Query(default=20, description="返回数量")
):
    """
    获取指数表现排行榜
    按涨跌幅排序
    """
    try:
        collection_name = f'index_{period}'
        collection = db_handler.get_collection(collection_name)
        
        # 获取最新交易日期
        latest_record = collection.find_one(
            sort=[('trade_date', -1)],
            projection={'trade_date': 1}
        )
        
        if not latest_record:
            raise HTTPException(status_code=404, detail="未找到指数数据")
        
        latest_date = latest_record['trade_date']
        
        # 如果是多天统计，需要计算累计涨跌幅
        if days == 1:
            # 当日涨跌幅排行
            cursor = collection.find(
                {"trade_date": latest_date, "pct_chg": {"$exists": True}},
                {"_id": 0}
            ).sort("pct_chg", -1).limit(limit)
            
            rankings = list(cursor)
            
        else:
            # 多日累计涨跌幅，需要聚合计算
            # 这里简化处理，仅获取主要指数
            all_ts_codes = list(MAJOR_INDICES.keys()) + list(SW_INDICES.keys())
            
            rankings = []
            for ts_code in all_ts_codes:
                cursor = collection.find(
                    {"ts_code": ts_code},
                    {"_id": 0}
                ).sort("trade_date", -1).limit(days)
                
                data_list = list(cursor)
                if data_list:
                    cumulative_change = sum(item.get("pct_chg", 0) for item in data_list)
                    rankings.append({
                        "ts_code": ts_code,
                        "cumulative_pct_chg": cumulative_change,
                        "latest_data": data_list[0]
                    })
            
            # 按累计涨跌幅排序
            rankings.sort(key=lambda x: x["cumulative_pct_chg"], reverse=True)
            rankings = rankings[:limit]
        
        return {
            "success": True,
            "data": {
                "period": period,
                "days": days,
                "trade_date": latest_date,
                "count": len(rankings),
                "rankings": rankings,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取指数排行榜失败: {str(e)}")

# ==================== 市场概览 ====================

@router.get("/market/overview")
async def get_index_market_overview():
    """
    获取指数市场概览
    统计主要指数的整体表现
    """
    try:
        collection = db_handler.get_collection('index_daily')
        
        # 获取最新交易日期
        latest_record = collection.find_one(
            sort=[('trade_date', -1)],
            projection={'trade_date': 1}
        )
        
        if not latest_record:
            raise HTTPException(status_code=404, detail="未找到指数数据")
        
        latest_date = latest_record['trade_date']
        
        # 获取主要指数的最新数据
        major_indices_data = []
        for ts_code, info in MAJOR_INDICES.items():
            latest_data = collection.find_one(
                {"ts_code": ts_code, "trade_date": latest_date},
                {"_id": 0}
            )
            
            if latest_data:
                major_indices_data.append({
                    "ts_code": ts_code,
                    "name": info["name"],
                    "market": info["market"],
                    "data": latest_data
                })
        
        # 统计市场表现
        if major_indices_data:
            pct_changes = [item["data"].get("pct_chg", 0) for item in major_indices_data]
            up_count = sum(1 for x in pct_changes if x > 0)
            down_count = sum(1 for x in pct_changes if x < 0)
            avg_change = sum(pct_changes) / len(pct_changes)
            
            market_summary = {
                "total_indices": len(major_indices_data),
                "rising_indices": up_count,
                "falling_indices": down_count,
                "average_change": round(avg_change, 2),
                "market_sentiment": "积极" if avg_change > 0 else "消极" if avg_change < 0 else "中性"
            }
        else:
            market_summary = {}
        
        return {
            "success": True,
            "data": {
                "trade_date": latest_date,
                "market_summary": market_summary,
                "major_indices": major_indices_data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取指数市场概览失败: {str(e)}")