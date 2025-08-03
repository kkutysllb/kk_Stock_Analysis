#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金流向API接口
支持个股、行业、大盘资金流向数据查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime

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


# ==================== 个股资金流向 ====================

@router.get("/stock/{ts_code}")
async def get_stock_money_flow(
    ts_code: str,
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取个股资金流向数据
    """
    try:
        collection = db_handler.get_collection('stock_money_flow')
        
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
                "money_flow": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取个股资金流向失败: {str(e)}")

# ==================== 行业资金流向 ====================

@router.get("/industry")
async def get_industry_money_flow(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    limit: int = Query(default=50, description="返回条数")
):
    """
    获取行业资金流向数据
    """
    try:
        collection = db_handler.get_collection('money_flow_industry')
        
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
        else:
            # 处理日期格式转换：YYYY-MM-DD -> YYYYMMDD
            if '-' in trade_date:
                trade_date = trade_date.replace('-', '')
        
        # 获取所有数据用于统计
        all_cursor = collection.find({"trade_date": trade_date}, {"_id": 0})
        all_results = list(all_cursor)
        
        # 统计正负值数量
        positive_count = len([item for item in all_results if item.get('net_amount', 0) > 0])
        negative_count = len([item for item in all_results if item.get('net_amount', 0) < 0])
        zero_count = len([item for item in all_results if item.get('net_amount', 0) == 0])
        
        print(f"行业数据统计 - 总数: {len(all_results)}, 净流入: {positive_count}, 净流出: {negative_count}, 零值: {zero_count}")
        
        # 返回所有数据，不限制limit，让前端处理
        cursor = collection.find({"trade_date": trade_date}, {"_id": 0}).sort("net_amount", -1)
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "industry_flows": results,
                "count": len(results),
                "positive_count": positive_count,
                "negative_count": negative_count,
                "zero_count": zero_count,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行业资金流向失败: {str(e)}")

# ==================== 大盘资金流向 ====================

@router.get("/market")
async def get_market_money_flow(
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=30, description="返回条数")
):
    """
    获取大盘资金流向数据
    """
    try:
        collection = db_handler.get_collection('money_flow_market')
        
        # 构建查询条件
        query = {}
        
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
        
        # 计算汇总统计
        if results:
            total_net = sum(item.get("net_amount", 0) for item in results)
            total_buy = sum(item.get("buy_amount", 0) for item in results)
            total_sell = sum(item.get("sell_amount", 0) for item in results)
            
            summary = {
                "total_net_amount": total_net,
                "total_buy_amount": total_buy,
                "total_sell_amount": total_sell,
                "average_net_amount": total_net / len(results) if results else 0,
                "inflow_days": sum(1 for item in results if item.get("net_amount", 0) > 0),
                "outflow_days": sum(1 for item in results if item.get("net_amount", 0) < 0)
            }
        else:
            summary = {}
        
        return {
            "success": True,
            "data": {
                "market_flows": results,
                "summary_statistics": summary,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取大盘资金流向失败: {str(e)}")

# ==================== 资金流向排行榜 ====================

@router.get("/rankings/inflow")
async def get_money_flow_inflow_ranking(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    limit: int = Query(default=50, description="返回数量")
):
    """
    获取资金净流入排行榜
    """
    try:
        collection = db_handler.get_collection('stock_money_flow')
        
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
        
        cursor = collection.find(
            {"trade_date": trade_date, "net_amount": {"$gt": 0}},
            {"_id": 0}
        ).sort("net_amount", -1).limit(limit)
        
        results = list(cursor)
        
        # 添加股票基本信息和涨跌幅
        if results:
            ts_codes = [item["ts_code"] for item in results]
            
            # 获取股票基本信息
            stock_basic = db_handler.get_collection('infrastructure_stock_basic')
            basic_info = {
                item["ts_code"]: item 
                for item in stock_basic.find(
                    {"ts_code": {"$in": ts_codes}},
                    {"_id": 0, "ts_code": 1, "name": 1, "industry": 1}
                )
            }
            
            # 获取当日K线数据（涨跌幅）
            kline_collection = db_handler.get_collection('stock_kline_daily')
            kline_info = {
                item["ts_code"]: item 
                for item in kline_collection.find(
                    {"ts_code": {"$in": ts_codes}, "trade_date": trade_date},
                    {"_id": 0, "ts_code": 1, "pct_change": 1}
                )
            }
            
            for item in results:
                if item["ts_code"] in basic_info:
                    item.update(basic_info[item["ts_code"]])
                if item["ts_code"] in kline_info:
                    item["pct_change"] = kline_info[item["ts_code"]].get("pct_change", 0)
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "type": "inflow",
                "rankings": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资金流入排行榜失败: {str(e)}")

@router.get("/rankings/outflow")
async def get_money_flow_outflow_ranking(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    limit: int = Query(default=50, description="返回数量")
):
    """
    获取资金净流出排行榜
    """
    try:
        collection = db_handler.get_collection('stock_money_flow')
        
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
        
        cursor = collection.find(
            {"trade_date": trade_date, "net_amount": {"$lt": 0}},
            {"_id": 0}
        ).sort("net_amount", 1).limit(limit)
        
        results = list(cursor)
        
        # 添加股票基本信息和涨跌幅
        if results:
            ts_codes = [item["ts_code"] for item in results]
            
            # 获取股票基本信息
            stock_basic = db_handler.get_collection('infrastructure_stock_basic')
            basic_info = {
                item["ts_code"]: item 
                for item in stock_basic.find(
                    {"ts_code": {"$in": ts_codes}},
                    {"_id": 0, "ts_code": 1, "name": 1, "industry": 1}
                )
            }
            
            # 获取当日K线数据（涨跌幅）
            kline_collection = db_handler.get_collection('stock_kline_daily')
            kline_info = {
                item["ts_code"]: item 
                for item in kline_collection.find(
                    {"ts_code": {"$in": ts_codes}, "trade_date": trade_date},
                    {"_id": 0, "ts_code": 1, "pct_change": 1}
                )
            }
            
            for item in results:
                if item["ts_code"] in basic_info:
                    item.update(basic_info[item["ts_code"]])
                if item["ts_code"] in kline_info:
                    item["pct_change"] = kline_info[item["ts_code"]].get("pct_change", 0)
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "type": "outflow",
                "rankings": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资金流出排行榜失败: {str(e)}")

# ==================== 综合分析 ====================

@router.get("/analysis")
async def get_money_flow_analysis(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    days: int = Query(default=10, description="分析天数")
):
    """
    获取资金流向综合分析
    """
    try:
        collection = db_handler.get_collection('stock_money_flow')
        
        # 获取最近的交易日期列表
        all_dates = collection.distinct('trade_date')
        all_dates.sort(reverse=True)
        
        if not trade_date:
            trade_date = all_dates[0] if all_dates else datetime.now().strftime('%Y%m%d')
        
        # 获取近N个交易日的数据用于图表
        recent_dates = all_dates[:days]
        
        # 获取历史数据用于图表
        historical_data = []
        for date in recent_dates:
            daily_cursor = collection.find(
                {"trade_date": date},
                {"_id": 0, "trade_date": 1, "net_amount": 1, "net_mf_amount": 1}
            )
            daily_data = list(daily_cursor)
            
            if daily_data:
                # 兼容两种字段名：net_amount 和 net_mf_amount
                daily_inflow = 0
                daily_outflow = 0
                for item in daily_data:
                    net_value = item.get("net_amount", 0) or item.get("net_mf_amount", 0)
                    if net_value > 0:
                        daily_inflow += net_value
                    elif net_value < 0:
                        daily_outflow += abs(net_value)
                
                historical_data.append({
                    "trade_date": date,
                    "net_inflow": daily_inflow,
                    "net_outflow": daily_outflow,
                    "net_amount": daily_inflow - daily_outflow
                })
        
        # 获取指定交易日的详细数据进行统计
        cursor = collection.find(
            {"trade_date": trade_date},
            {"_id": 0}
        )
        
        all_data = list(cursor)
        
        if not all_data:
            raise HTTPException(status_code=404, detail="未找到该交易日的资金流向数据")
        
        # 计算市场整体统计（兼容两种字段名）
        total_net_inflow = 0
        total_net_outflow = 0
        inflow_stocks = []
        outflow_stocks = []
        neutral_stocks = []
        
        for item in all_data:
            net_value = item.get("net_amount", 0) or item.get("net_mf_amount", 0)
            if net_value > 0:
                total_net_inflow += net_value
                inflow_stocks.append(item)
            elif net_value < 0:
                total_net_outflow += abs(net_value)
                outflow_stocks.append(item)
            else:
                neutral_stocks.append(item)
        
        # 计算超大单、大单、中单、小单统计（兼容两种字段名）
        super_large_net = sum(item.get("net_mf_vol", 0) for item in all_data)
        large_net = sum(item.get("net_amount", 0) or item.get("net_mf_amount", 0) for item in all_data)
        
        market_analysis = {
            "trade_date": trade_date,
            "total_stocks": len(all_data),
            "inflow_stocks": len(inflow_stocks),
            "outflow_stocks": len(outflow_stocks),
            "neutral_stocks": len(neutral_stocks),
            "total_net_inflow": total_net_inflow,
            "total_net_outflow": total_net_outflow,
            "net_inflow_ratio": round(len(inflow_stocks) / len(all_data) * 100, 2) if all_data else 0,
            "market_sentiment": "积极" if total_net_inflow > total_net_outflow else "消极" if total_net_outflow > total_net_inflow else "中性"
        }
        
        # 获取排名前10的流入和流出股票（兼容两种字段名）
        top_inflow = sorted(inflow_stocks, key=lambda x: x.get("net_amount", 0) or x.get("net_mf_amount", 0), reverse=True)[:10]
        top_outflow = sorted(outflow_stocks, key=lambda x: x.get("net_amount", 0) or x.get("net_mf_amount", 0))[:10]
        
        return {
            "success": True,
            "data": {
                "market_analysis": market_analysis,
                "top_inflow_stocks": top_inflow,
                "top_outflow_stocks": top_outflow,
                "historical_data": historical_data,
                "analysis_period": f"{days}天",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"获取资金流向分析失败: {str(e)}")