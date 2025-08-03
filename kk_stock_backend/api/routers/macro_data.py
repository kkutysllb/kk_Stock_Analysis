#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宏观数据API接口
支持SHIBOR利率、宏观经济指标等数据查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
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


router = APIRouter()


# ==================== SHIBOR利率数据查询 ====================

@cache_endpoint(data_type='macro_data', ttl=7200)  # 缓存2小时
@router.get("/shibor")
async def get_shibor_rates(
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=30, description="获取记录数量")
):
    """
    获取SHIBOR利率数据
    
    Args:
        start_date: 开始日期，格式YYYYMMDD
        end_date: 结束日期，格式YYYYMMDD  
        limit: 获取记录数量
    
    Returns:
        SHIBOR利率数据列表
    """
    try:
        collection = db_handler.get_collection('macro_shibor_rates')
        
        # 构建查询条件
        query = {}
        if start_date and end_date:
            query["date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query["date"] = {"$gte": start_date}
        elif end_date:
            query["date"] = {"$lte": end_date}
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("date", -1).limit(limit)
        
        results = list(cursor)
        
        # 计算统计信息
        stats = {}
        if results:
            # 计算各期限利率的平均值和最新值
            latest = results[0]
            rate_fields = ['on', '1w', '2w', '1m', '3m', '6m', '9m', '1y']
            
            for field in rate_fields:
                if field in latest:
                    rates = [r.get(field, 0) for r in results if r.get(field) is not None]
                    if rates:
                        stats[field] = {
                            "latest": latest.get(field, 0),
                            "average": round(sum(rates) / len(rates), 4),
                            "max": max(rates),
                            "min": min(rates)
                        }
        
        return {
            "success": True,
            "data": {
                "query_params": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit
                },
                "shibor_rates": results,
                "statistics": stats,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取SHIBOR利率数据失败: {str(e)}")

@cache_endpoint(data_type='macro_data', ttl=14400)  # 缓存4小时
@router.get("/shibor/latest")
async def get_latest_shibor():
    """
    获取最新SHIBOR利率数据
    """
    try:
        collection = db_handler.get_collection('macro_shibor_rates')
        
        latest_record = collection.find_one(
            {},
            {"_id": 0}
        , sort=[("date", -1)])
        
        if not latest_record:
            raise HTTPException(status_code=404, detail="未找到SHIBOR利率数据")
        
        # 格式化利率数据
        rate_data = {
            "date": latest_record.get("date"),
            "rates": {
                "overnight": latest_record.get("on", 0),
                "1_week": latest_record.get("1w", 0),
                "2_weeks": latest_record.get("2w", 0),
                "1_month": latest_record.get("1m", 0),
                "3_months": latest_record.get("3m", 0),
                "6_months": latest_record.get("6m", 0),
                "9_months": latest_record.get("9m", 0),
                "1_year": latest_record.get("1y", 0)
            }
        }
        
        return {
            "success": True,
            "data": {
                "latest_shibor": rate_data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取最新SHIBOR利率失败: {str(e)}")

@cache_endpoint(data_type='macro_data', ttl=7200)  # 缓存2小时
@router.get("/shibor/trend")
async def get_shibor_trend(
    period: str = Query(default="1m", description="利率期限: on,1w,2w,1m,3m,6m,9m,1y"),
    days: int = Query(default=30, description="获取最近天数")
):
    """
    获取SHIBOR利率趋势数据
    
    Args:
        period: 利率期限 (on/1w/2w/1m/3m/6m/9m/1y)
        days: 获取最近天数
    
    Returns:
        指定期限的利率趋势数据
    """
    try:
        collection = db_handler.get_collection('macro_shibor_rates')
        
        # 验证期限参数，支持大小写不敏感
        valid_periods = ['on', '1w', '2w', '1m', '3m', '6m', '9m', '1y']
        period_lower = period.lower()
        if period_lower not in valid_periods:
            raise HTTPException(status_code=400, detail=f"无效的期限参数，支持: {valid_periods}")
        
        # 使用小写的period进行查询
        period = period_lower
        
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y%m%d')
        
        cursor = collection.find(
            {"date": {"$gte": start_date, "$lte": end_date}},
            {"_id": 0, "date": 1, period: 1}
        ).sort("date", 1)
        
        results = list(cursor)
        
        # 提取趋势数据
        trend_data = []
        for record in results:
            if record.get(period) is not None:
                trend_data.append({
                    "date": record["date"],
                    "rate": record[period]
                })
        
        # 计算变化趋势
        trend_analysis = {}
        if len(trend_data) >= 2:
            latest_rate = trend_data[-1]["rate"]
            first_rate = trend_data[0]["rate"]
            change = latest_rate - first_rate
            change_pct = (change / first_rate * 100) if first_rate != 0 else 0
            
            trend_analysis = {
                "period_start": trend_data[0]["date"],
                "period_end": trend_data[-1]["date"],
                "start_rate": first_rate,
                "end_rate": latest_rate,
                "absolute_change": round(change, 4),
                "percentage_change": round(change_pct, 2)
            }
        
        return {
            "success": True,
            "data": {
                "period": period,
                "days": days,
                "trend_data": trend_data,
                "trend_analysis": trend_analysis,
                "count": len(trend_data),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取SHIBOR利率趋势失败: {str(e)}")

@cache_endpoint(data_type='macro_data', ttl=7200)  # 缓存2小时
@router.get("/shibor/analysis")
async def get_shibor_analysis(
    analysis_days: int = Query(default=90, description="分析天数")
):
    """
    获取SHIBOR利率分析报告
    
    Args:
        analysis_days: 分析天数
    
    Returns:
        SHIBOR利率分析报告
    """
    try:
        collection = db_handler.get_collection('macro_shibor_rates')
        
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=analysis_days-1)).strftime('%Y%m%d')
        
        cursor = collection.find(
            {"date": {"$gte": start_date, "$lte": end_date}},
            {"_id": 0}
        ).sort("date", 1)
        
        results = list(cursor)
        
        if not results:
            raise HTTPException(status_code=404, detail="指定时间范围内无数据")
        
        # 利率分析
        rate_fields = ['on', '1w', '2w', '1m', '3m', '6m', '9m', '1y']
        analysis = {}
        
        for field in rate_fields:
            rates = [r.get(field) for r in results if r.get(field) is not None]
            if rates:
                latest = rates[-1]
                first = rates[0]
                avg_rate = sum(rates) / len(rates)
                volatility = sum((r - avg_rate) ** 2 for r in rates) / len(rates) ** 0.5
                
                analysis[field] = {
                    "current": latest,
                    "period_start": first,
                    "average": round(avg_rate, 4),
                    "max": max(rates),
                    "min": min(rates),
                    "volatility": round(volatility, 4),
                    "change": round(latest - first, 4),
                    "change_pct": round((latest - first) / first * 100, 2) if first != 0 else 0
                }
        
        # 利率曲线分析
        latest_record = results[-1]
        yield_curve = {field: latest_record.get(field, 0) for field in rate_fields if latest_record.get(field) is not None}
        
        # 判断曲线形态
        curve_shape = "正常"
        if len(yield_curve) >= 3:
            short_rates = [yield_curve.get('on', 0), yield_curve.get('1w', 0), yield_curve.get('2w', 0)]
            long_rates = [yield_curve.get('6m', 0), yield_curve.get('9m', 0), yield_curve.get('1y', 0)]
            
            avg_short = sum(r for r in short_rates if r > 0) / len([r for r in short_rates if r > 0])
            avg_long = sum(r for r in long_rates if r > 0) / len([r for r in long_rates if r > 0])
            
            if avg_short > avg_long:
                curve_shape = "倒挂"
            elif abs(avg_short - avg_long) < 0.1:
                curve_shape = "平坦"
        
        return {
            "success": True,
            "data": {
                "analysis_period": f"{analysis_days}天",
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "rate_analysis": analysis,
                "yield_curve": {
                    "current_curve": yield_curve,
                    "curve_shape": curve_shape
                },
                "data_points": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"SHIBOR利率分析失败: {str(e)}")