#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析API接口
支持相关性分析、板块分析、市场情绪等复杂分析功能
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio

# 导入缓存装饰器
from api.cache_middleware import cache_endpoint

import sys
import os
from api.global_db import db_handler

# 添加项目根目录到sys.path以便导入数据库管理器
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(api_dir)
sys.path.insert(0, project_root)


sys.path.insert(0, project_root)

router = APIRouter()


@cache_endpoint(data_type='analytics', ttl=1800)  # 缓存30分钟
@router.get("/correlation")
async def get_correlation_analysis(
    ts_codes: str = Query(..., description="股票代码列表，逗号分隔"),
    days: int = Query(30, description="分析天数", ge=5, le=250),
    field: str = Query("close", description="分析字段: close, pct_chg, vol")
):
    """计算多只股票间的相关性"""
    try:
        code_list = [code.strip() for code in ts_codes.split(",") if code.strip()]
        if len(code_list) < 2:
            raise HTTPException(status_code=400, detail="至少需要2只股票进行相关性分析")
        if len(code_list) > 20:
            raise HTTPException(status_code=400, detail="相关性分析最多支持20只股票")
        
        # 获取所有股票的历史数据
        results = []
        for ts_code in code_list:
            try:
                collection = db_handler.get_collection('daily')
                cursor = collection.find(
                    {"ts_code": ts_code},
                    {"trade_date": 1, field: 1, "_id": 0}
                ).sort("trade_date", -1).limit(days)
                results.append(list(cursor))
            except Exception as e:
                results.append([])
        
        # 组织数据用于相关性计算
        stock_data = {}
        for i, ts_code in enumerate(code_list):
            if i < len(results) and results[i]:
                # 将数据按日期排序（从早到晚）
                data = sorted(results[i], key=lambda x: x["trade_date"])
                stock_data[ts_code] = {
                    "dates": [item["trade_date"] for item in data],
                    "values": [item.get(field, 0) for item in data]
                }
        
        # 简化的相关系数计算（实际应用中建议使用numpy等库）
        correlation_matrix = {}
        
        for i, code1 in enumerate(code_list):
            correlation_matrix[code1] = {}
            for j, code2 in enumerate(code_list):
                if code1 == code2:
                    correlation_matrix[code1][code2] = 1.0
                elif code1 in stock_data and code2 in stock_data:
                    # 获取共同的交易日期
                    dates1 = set(stock_data[code1]["dates"])
                    dates2 = set(stock_data[code2]["dates"])
                    common_dates = dates1.intersection(dates2)
                    
                    if len(common_dates) >= 5:  # 至少需要5个共同数据点
                        # 提取共同日期的数据
                        values1 = []
                        values2 = []
                        
                        for date in sorted(common_dates):
                            idx1 = stock_data[code1]["dates"].index(date)
                            idx2 = stock_data[code2]["dates"].index(date)
                            values1.append(stock_data[code1]["values"][idx1])
                            values2.append(stock_data[code2]["values"][idx2])
                        
                        # 计算皮尔逊相关系数
                        if len(values1) > 0:
                            correlation = calculate_correlation(values1, values2)
                            correlation_matrix[code1][code2] = round(correlation, 4)
                        else:
                            correlation_matrix[code1][code2] = None
                    else:
                        correlation_matrix[code1][code2] = None
                else:
                    correlation_matrix[code1][code2] = None
        
        return {
            "success": True,
            "data": {
                "stocks": code_list,
                "field": field,
                "analysis_period": f"{days}天",
                "correlation_matrix": correlation_matrix,
                "data_points": {code: len(stock_data.get(code, {}).get("values", [])) for code in code_list},
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"相关性分析失败: {str(e)}")

def calculate_correlation(x: List[float], y: List[float]) -> float:
    """计算皮尔逊相关系数"""
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_x2 = sum(xi * xi for xi in x)
    sum_y2 = sum(yi * yi for yi in y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

@router.get("/sector-analysis")
async def get_sector_analysis(
    trade_date: Optional[str] = Query(None, description="交易日期"),
    metric: str = Query("pct_chg", description="分析指标: pct_chg, vol, amount"),
    limit: int = Query(30, description="返回板块数量", le=100)
):
    """获取板块表现分析"""
    try:
        if not trade_date:
            collection = db_handler.get_collection('sw_daily')
            latest_data = collection.find_one(
                {},
                {"trade_date": 1}
            )
            trade_date = latest_data["trade_date"] if latest_data else datetime.now().strftime("%Y%m%d")
        
        # 获取申万行业数据
        collection = db_handler.get_collection('sw_daily')
        cursor = collection.find(
            {"trade_date": trade_date},
            {"_id": 0}
        ).sort(metric, -1).limit(limit)
        
        sector_data = list(cursor)
        
        # 计算板块统计
        if sector_data:
            values = [item.get(metric, 0) for item in sector_data if item.get(metric) is not None]
            
            sector_stats = {
                "total_sectors": len(sector_data),
                "rising_sectors": len([item for item in sector_data if item.get("pct_chg", 0) > 0]),
                "falling_sectors": len([item for item in sector_data if item.get("pct_chg", 0) < 0]),
                "avg_change": round(sum([item.get("pct_chg", 0) for item in sector_data]) / len(sector_data), 2) if sector_data else 0,
                "max_change": max([item.get("pct_chg", 0) for item in sector_data]) if sector_data else 0,
                "min_change": min([item.get("pct_chg", 0) for item in sector_data]) if sector_data else 0
            }
        else:
            sector_stats = {}
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "metric": metric,
                "sector_data": sector_data,
                "sector_statistics": sector_stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"板块分析失败: {str(e)}")

@router.get("/market-mood")
async def get_market_mood(
    trade_date: Optional[str] = Query(None, description="交易日期"),
    days: int = Query(5, description="情绪分析天数", ge=1, le=30)
):
    """获取市场情绪分析"""
    try:
        if not trade_date:
            collection = db_handler.get_collection('daily')
            latest_data = collection.find_one(
                {},
                {"trade_date": 1}
            )
            trade_date = latest_data["trade_date"] if latest_data else datetime.now().strftime("%Y%m%d")
        
        # 计算日期范围
        end_date = trade_date
        start_date = (datetime.strptime(trade_date, "%Y%m%d") - timedelta(days=days-1)).strftime("%Y%m%d")
        
        # 获取指定日期范围的数据
        collection = db_handler.get_collection('daily')
        cursor = collection.find({
            "trade_date": {"$gte": start_date, "$lte": end_date}
        })
        
        all_data = list(cursor)
        
        # 按日期分组计算情绪数据
        daily_stats = {}
        for item in all_data:
            trade_date_key = item["trade_date"]
            if trade_date_key not in daily_stats:
                daily_stats[trade_date_key] = {
                    "total_stocks": 0,
                    "rising_stocks": 0,
                    "falling_stocks": 0,
                    "strong_rising": 0,
                    "strong_falling": 0,
                    "changes": [],
                    "total_volume": 0,
                    "total_amount": 0
                }
            
            stats = daily_stats[trade_date_key]
            pct_chg = item.get("pct_chg", 0)
            
            stats["total_stocks"] += 1
            if pct_chg > 0:
                stats["rising_stocks"] += 1
            elif pct_chg < 0:
                stats["falling_stocks"] += 1
            
            if pct_chg > 5:
                stats["strong_rising"] += 1
            elif pct_chg < -5:
                stats["strong_falling"] += 1
                
            stats["changes"].append(pct_chg)
            stats["total_volume"] += item.get("vol", 0)
            stats["total_amount"] += item.get("amount", 0)
        
        # 转换为mood_data格式
        mood_data = []
        for date_key in sorted(daily_stats.keys()):
            stats = daily_stats[date_key]
            avg_change = sum(stats["changes"]) / len(stats["changes"]) if stats["changes"] else 0
            mood_data.append({
                "_id": date_key,
                "total_stocks": stats["total_stocks"],
                "rising_stocks": stats["rising_stocks"],
                "falling_stocks": stats["falling_stocks"],
                "strong_rising": stats["strong_rising"],
                "strong_falling": stats["strong_falling"],
                "avg_change": avg_change,
                "total_volume": stats["total_volume"],
                "total_amount": stats["total_amount"]
            })
        
        # 计算情绪指标
        market_mood_indicators = []
        
        for day_data in mood_data:
            total = day_data["total_stocks"]
            if total > 0:
                rise_ratio = day_data["rising_stocks"] / total
                strong_rise_ratio = day_data["strong_rising"] / total
                strong_fall_ratio = day_data["strong_falling"] / total
                
                # 计算情绪得分 (0-100)
                mood_score = (
                    rise_ratio * 40 +  # 上涨股票比例权重40%
                    strong_rise_ratio * 30 +  # 强势上涨权重30%
                    (1 - strong_fall_ratio) * 20 +  # 强势下跌惩罚权重20%
                    (day_data["avg_change"] + 10) / 20 * 10  # 平均涨跌幅权重10%
                ) * 100
                
                mood_score = max(0, min(100, mood_score))  # 限制在0-100范围
                
                # 情绪等级
                if mood_score >= 80:
                    mood_level = "极度乐观"
                elif mood_score >= 60:
                    mood_level = "乐观"
                elif mood_score >= 40:
                    mood_level = "中性"
                elif mood_score >= 20:
                    mood_level = "悲观"
                else:
                    mood_level = "极度悲观"
                
                mood_indicators = {
                    "trade_date": day_data["_id"],
                    "mood_score": round(mood_score, 2),
                    "mood_level": mood_level,
                    "rise_ratio": round(rise_ratio * 100, 2),
                    "strong_rise_ratio": round(strong_rise_ratio * 100, 2),
                    "strong_fall_ratio": round(strong_fall_ratio * 100, 2),
                    "avg_change": round(day_data["avg_change"], 2),
                    "market_activity": round(day_data["total_amount"] / 1e8, 2)  # 成交额(亿元)
                }
                
                market_mood_indicators.append(mood_indicators)
        
        # 计算整体趋势
        if len(market_mood_indicators) >= 2:
            latest_mood = market_mood_indicators[-1]["mood_score"]
            previous_mood = market_mood_indicators[-2]["mood_score"]
            mood_trend = "上升" if latest_mood > previous_mood else "下降" if latest_mood < previous_mood else "持平"
        else:
            mood_trend = "数据不足"
        
        return {
            "success": True,
            "data": {
                "analysis_period": f"{days}天",
                "latest_date": trade_date,
                "mood_trend": mood_trend,
                "daily_mood": market_mood_indicators,
                "summary": {
                    "avg_mood_score": round(sum([item["mood_score"] for item in market_mood_indicators]) / len(market_mood_indicators), 2) if market_mood_indicators else 0,
                    "mood_volatility": round(max([item["mood_score"] for item in market_mood_indicators]) - min([item["mood_score"] for item in market_mood_indicators]), 2) if market_mood_indicators else 0
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"市场情绪分析失败: {str(e)}")

@router.get("/volume-price")
async def get_volume_price_analysis(
    ts_code: str = Query(..., description="股票代码"),
    days: int = Query(30, description="分析天数", ge=5, le=250)
):
    """分析股票的量价关系"""
    try:
        # 获取股票历史数据
        collection = db_handler.get_collection('daily')
        cursor = collection.find(
            {"ts_code": ts_code},
            {"_id": 0, "trade_date": 1, "close": 1, "vol": 1, "pct_chg": 1, "amount": 1}
        ).sort("trade_date", -1).limit(days)
        
        kline_data = list(cursor)
        
        if not kline_data:
            raise HTTPException(status_code=404, detail="未找到股票数据")
        
        # 按时间正序排列
        kline_data = sorted(kline_data, key=lambda x: x["trade_date"])
        
        # 计算量价关系指标
        volume_price_indicators = []
        
        for i in range(1, len(kline_data)):
            current = kline_data[i]
            previous = kline_data[i-1]
            
            price_change = current["close"] - previous["close"]
            volume_change = current["vol"] - previous["vol"]
            
            # 量价关系类型
            if price_change > 0 and volume_change > 0:
                vp_type = "价涨量增"
                vp_signal = "强势上涨"
            elif price_change > 0 and volume_change <= 0:
                vp_type = "价涨量缩"
                vp_signal = "上涨乏力"
            elif price_change <= 0 and volume_change > 0:
                vp_type = "价跌量增"
                vp_signal = "杀跌明显"
            else:
                vp_type = "价跌量缩"
                vp_signal = "下跌放缓"
            
            volume_price_indicators.append({
                "trade_date": current["trade_date"],
                "close": current["close"],
                "volume": current["vol"],
                "price_change": round(price_change, 2),
                "volume_change": round(volume_change, 2),
                "pct_change": current.get("pct_chg", 0),
                "vp_type": vp_type,
                "vp_signal": vp_signal
            })
        
        # 统计量价关系分布
        vp_distribution = {
            "价涨量增": len([item for item in volume_price_indicators if item["vp_type"] == "价涨量增"]),
            "价涨量缩": len([item for item in volume_price_indicators if item["vp_type"] == "价涨量缩"]),
            "价跌量增": len([item for item in volume_price_indicators if item["vp_type"] == "价跌量增"]),
            "价跌量缩": len([item for item in volume_price_indicators if item["vp_type"] == "价跌量缩"])
        }
        
        # 计算量价相关性
        prices = [item["close"] for item in kline_data[1:]]
        volumes = [item["vol"] for item in kline_data[1:]]
        
        if len(prices) > 0:
            vp_correlation = calculate_correlation(prices, volumes)
        else:
            vp_correlation = 0
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "analysis_period": f"{days}天",
                "volume_price_data": volume_price_indicators,
                "vp_distribution": vp_distribution,
                "vp_correlation": round(vp_correlation, 4),
                "latest_signal": volume_price_indicators[-1]["vp_signal"] if volume_price_indicators else "无数据",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"量价关系分析失败: {str(e)}")