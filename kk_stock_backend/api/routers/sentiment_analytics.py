#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场情绪汇总计算API接口
基于现有数据计算市场情绪指标，为Dashboard情绪面板提供数据支持
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import numpy as np

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


@router.get("/dashboard-summary")
async def get_dashboard_sentiment_summary(
    days: int = Query(30, description="分析天数", ge=7, le=90),
    trade_date: Optional[str] = Query(None, description="指定交易日期(YYYYMMDD)")
):
    """
    获取Dashboard市场情绪面板汇总数据
    计算多空比、恐慌指数、资金流向、基差水平等核心指标
    """
    try:
        # 确定分析日期范围
        if not trade_date:
            # 获取最新交易日期 - 修正集合名称
            daily_collection = db_handler.get_collection('stock_kline_daily')
            latest_record = daily_collection.find_one(
                {},
                {"trade_date": 1},
                sort=[('trade_date', -1)]
            )
            trade_date = latest_record["trade_date"] if latest_record else datetime.now().strftime("%Y%m%d")
        
        # 确保trade_date是字符串类型，处理FastAPI Query对象
        if hasattr(trade_date, 'annotation'):
            # 这是一个FastAPI Query对象，获取默认值
            trade_date = datetime.now().strftime("%Y%m%d")
        elif not isinstance(trade_date, str):
            trade_date = str(trade_date)
            
        # 确保days是整数类型
        if hasattr(days, 'annotation'):
            days = 30  # 默认值
        elif not isinstance(days, int):
            days = int(days)
            
        end_date = trade_date
        start_date = (datetime.strptime(trade_date, "%Y%m%d") - timedelta(days=days-1)).strftime("%Y%m%d")
        
        # 并行计算各项指标
        tasks = [
            calculate_bull_bear_ratio(start_date, end_date),
            calculate_fear_greed_index(start_date, end_date),
            calculate_money_flow_indicator(start_date, end_date),
            calculate_basis_level(start_date, end_date),
            calculate_overall_sentiment(start_date, end_date)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        bull_bear_data = results[0] if not isinstance(results[0], Exception) else None
        fear_greed_data = results[1] if not isinstance(results[1], Exception) else None
        money_flow_data = results[2] if not isinstance(results[2], Exception) else None
        basis_data = results[3] if not isinstance(results[3], Exception) else None
        overall_data = results[4] if not isinstance(results[4], Exception) else None
        
        # 添加调试信息
        print(f"DEBUG - 多空比数据: {bull_bear_data is not None}")
        print(f"DEBUG - 恐慌指数数据: {fear_greed_data is not None}")
        print(f"DEBUG - 资金流向数据: {money_flow_data is not None}")
        print(f"DEBUG - 基差水平数据: {basis_data is not None}")
        print(f"DEBUG - 综合情绪数据: {overall_data is not None}")
        
        # 打印异常信息
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                indicator_names = ["多空比", "恐慌指数", "资金流向", "基差水平", "综合情绪"]
                print(f"DEBUG - {indicator_names[i]}计算异常: {result}")
        
        # 构建响应数据
        sentiment_indicators = []
        
        # 多空比指标
        if bull_bear_data:
            sentiment_indicators.append({
                "name": "多空比",
                "value": bull_bear_data["current_value"],
                "unit": "",
                "change": bull_bear_data["change"],
                "level": bull_bear_data["level"],
                "description": "多头持仓与空头持仓的比值，反映市场多空力量对比",
                "data": bull_bear_data["historical_data"]
            })
        
        # 恐慌指数
        if fear_greed_data:
            sentiment_indicators.append({
                "name": "恐慌指数",
                "value": fear_greed_data["current_value"],
                "unit": "",
                "change": fear_greed_data["change"],
                "level": fear_greed_data["level"],
                "description": "基于市场波动率和情绪计算的恐慌指数，数值越高表示市场恐慌程度越高",
                "data": fear_greed_data["historical_data"]
            })
        
        # 资金流向
        if money_flow_data:
            sentiment_indicators.append({
                "name": "资金流向",
                "value": money_flow_data["current_value"],
                "unit": "亿",
                "change": money_flow_data["change"],
                "level": money_flow_data["level"],
                "description": "主力资金净流入流出情况，正值表示净流入",
                "data": money_flow_data["historical_data"]
            })
        
        # 基差水平
        if basis_data:
            sentiment_indicators.append({
                "name": "基差水平",
                "value": basis_data["current_value"],
                "unit": "点",
                "change": basis_data["change"],
                "level": basis_data["level"],
                "description": "期货价格与现货价格的差值，反映市场预期",
                "data": basis_data["historical_data"]
            })
        
        # 综合情绪指数
        overall_sentiment = {
            "index": overall_data["index"] if overall_data else 50,
            "level": overall_data["level"] if overall_data else "中性",
            "factors": overall_data["factors"] if overall_data else ["数据计算中"]
        }
        
        return {
            "success": True,
            "data": {
                "analysis_period": f"{days}天",
                "latest_date": trade_date,
                "sentiment_indicators": sentiment_indicators,
                "overall_sentiment": overall_sentiment,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"市场情绪汇总计算失败: {str(e)}")


async def calculate_bull_bear_ratio(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    计算多空比指标
    基于股票涨跌比例计算市场多空力量对比
    """
    try:
        # 修正集合名称
        daily_collection = db_handler.get_collection('stock_kline_daily')
        
        # 获取指定日期范围的股票数据
        pipeline = [
            {
                "$match": {
                    "trade_date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$trade_date",
                    "total_stocks": {"$sum": 1},
                    "rising_stocks": {
                        "$sum": {
                            "$cond": [{"$gt": ["$pct_change", 0]}, 1, 0]
                        }
                    },
                    "falling_stocks": {
                        "$sum": {
                            "$cond": [{"$lt": ["$pct_change", 0]}, 1, 0]
                        }
                    }
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        daily_stats = list(daily_collection.aggregate(pipeline))
        
        if not daily_stats:
            return None
        
        # 计算多空比历史数据
        historical_data = []
        bull_bear_ratios = []
        
        for stat in daily_stats:
            total = stat["total_stocks"]
            rising = stat["rising_stocks"]
            falling = stat["falling_stocks"]
            
            if falling > 0:
                ratio = rising / falling
            else:
                ratio = rising if rising > 0 else 0
            
            bull_bear_ratios.append(ratio)
            historical_data.append([stat["_id"], round(ratio, 2)])
        
        # 计算当前值和变化
        # current_value是时间范围内的均值
        current_value = round(sum(bull_bear_ratios) / len(bull_bear_ratios), 2) if bull_bear_ratios else 0
        
        # change是期末相对于期初的变化
        period_end_value = round(bull_bear_ratios[-1], 2) if len(bull_bear_ratios) > 0 else 0
        period_start_value = round(bull_bear_ratios[0], 2) if len(bull_bear_ratios) > 0 else 0
        change = round(period_end_value - period_start_value, 2)
        
        # print(f"DEBUG - 多空比计算: 数据点={len(bull_bear_ratios)}, 期初={period_start_value}, 期末={period_end_value}, 均值={current_value}, 变化={change}")
        
        # 判断情绪等级（基于均值）
        if current_value > 1.5:
            level = "bullish"
        elif current_value < 0.7:
            level = "bearish"
        else:
            level = "neutral"
        
        return {
            "current_value": current_value,
            "change": change,
            "level": level,
            "historical_data": historical_data
        }
        
    except Exception as e:
        # print(f"计算多空比失败: {e}")
        return None


async def calculate_fear_greed_index(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    计算恐慌贪婪指数
    基于市场波动率、涨跌幅分布等计算
    """
    try:
        # 修正集合名称
        daily_collection = db_handler.get_collection('stock_kline_daily')
        
        # 获取市场整体数据
        pipeline = [
            {
                "$match": {
                    "trade_date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$trade_date",
                    "avg_pct_chg": {"$avg": "$pct_change"},
                    "std_pct_chg": {"$stdDevPop": "$pct_change"},
                    "total_amount": {"$sum": "$amount"},
                    "strong_rising": {
                        "$sum": {
                            "$cond": [{"$gt": ["$pct_change", 5]}, 1, 0]
                        }
                    },
                    "strong_falling": {
                        "$sum": {
                            "$cond": [{"$lt": ["$pct_change", -5]}, 1, 0]
                        }
                    },
                    "total_stocks": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        daily_stats = list(daily_collection.aggregate(pipeline))
        
        if not daily_stats:
            return None
        
        # 计算恐慌指数历史数据
        historical_data = []
        fear_indices = []
        
        for stat in daily_stats:
            # 恐慌指数计算逻辑
            volatility = stat.get("std_pct_chg", 0)
            avg_change = stat.get("avg_pct_chg", 0)
            strong_ratio = (stat.get("strong_falling", 0) - stat.get("strong_rising", 0)) / max(stat.get("total_stocks", 1), 1)
            
            # 综合计算恐慌指数 (0-100, 数值越高越恐慌)
            fear_index = min(100, max(0, 
                50 +  # 基准值
                volatility * 10 +  # 波动率影响
                (-avg_change) * 5 +  # 平均跌幅影响
                strong_ratio * 30  # 强势下跌比例影响
            ))
            
            fear_indices.append(fear_index)
            historical_data.append([stat["_id"], round(fear_index, 1)])
        
        # 计算当前值和变化
        # current_value是时间范围内的均值
        current_value = round(sum(fear_indices) / len(fear_indices), 1) if fear_indices else 50
        
        # change是期末相对于期初的变化
        period_end_value = round(fear_indices[-1], 1) if len(fear_indices) > 0 else 50
        period_start_value = round(fear_indices[0], 1) if len(fear_indices) > 0 else 50
        change = round(period_end_value - period_start_value, 1)
        
        # print(f"DEBUG - 恐慌指数计算: 数据点={len(fear_indices)}, 期初={period_start_value}, 期末={period_end_value}, 均值={current_value}, 变化={change}")
        
        # 判断情绪等级（基于均值）
        if current_value > 70:
            level = "bearish"  # 高恐慌
        elif current_value < 30:
            level = "bullish"  # 低恐慌(贪婪)
        else:
            level = "neutral"
        
        return {
            "current_value": current_value,
            "change": change,
            "level": level,
            "historical_data": historical_data
        }
        
    except Exception as e:
        # print(f"计算恐慌指数失败: {e}")
        return None


async def calculate_money_flow_indicator(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    计算资金流向指标
    基于个股资金流向数据汇总计算
    """
    try:
        # 使用正确的集合名称
        money_flow_collection = db_handler.get_collection('stock_money_flow')
        
        # 获取资金流向汇总数据 - 兼容net_amount和net_mf_amount字段
        pipeline = [
            {
                "$match": {
                    "trade_date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$trade_date",
                    "total_net_amount": {
                        "$sum": {
                            "$ifNull": ["$net_amount", "$net_mf_amount"]
                        }
                    },
                    "total_main_net": {
                        "$sum": {
                            "$add": [
                                {"$subtract": ["$buy_lg_amount", "$sell_lg_amount"]},
                                {"$subtract": ["$buy_elg_amount", "$sell_elg_amount"]}
                            ]
                        }
                    }
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        daily_flow = list(money_flow_collection.aggregate(pipeline))
        
        if not daily_flow:
            return None
        
        # 计算资金流向历史数据(转换为亿元)
        historical_data = []
        flow_values = []
        
        for flow in daily_flow:
            # 主力资金净流入(千元转亿元)
            main_net_flow = flow.get("total_main_net", 0) / 100000
            flow_values.append(main_net_flow)
            historical_data.append([flow["_id"], round(main_net_flow, 1)])
        
        # 计算当前值和变化
        # current_value是时间范围内的均值
        current_value = round(sum(flow_values) / len(flow_values), 1) if flow_values else 0
        
        # change是期末相对于期初的变化
        period_end_value = round(flow_values[-1], 1) if len(flow_values) > 0 else 0
        period_start_value = round(flow_values[0], 1) if len(flow_values) > 0 else 0
        change = round(period_end_value - period_start_value, 1)
        
        # print(f"DEBUG - 资金流向计算: 数据点={len(flow_values)}, 期初={period_start_value}, 期末={period_end_value}, 均值={current_value}, 变化={change}")
        
        # 判断情绪等级（基于均值）
        if current_value > 100:
            level = "bullish"  # 大幅净流入
        elif current_value < -100:
            level = "bearish"  # 大幅净流出
        else:
            level = "neutral"
        
        return {
            "current_value": current_value,
            "change": change,
            "level": level,
            "historical_data": historical_data
        }
        
    except Exception as e:
        print(f"计算资金流向指标失败: {e}")
        return None


async def calculate_basis_level(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    计算基差水平指标
    基于期货和现货价格差异计算
    """
    try:
        # 修正集合名称
        futures_collection = db_handler.get_collection('fut_daily')
        index_collection = db_handler.get_collection('index_daily')
        
        # 主要股指期货代码
        main_futures = ['IF.CFX', 'IC.CFX', 'IH.CFX', 'IM.CFX']
        # 对应的现货指数
        spot_indices = {
            'IF.CFX': '000300.SH',  # 沪深300
            'IC.CFX': '000905.SH',  # 中证500
            'IH.CFX': '000016.SH',  # 上证50
            'IM.CFX': '000852.SH'   # 中证1000
        }
        
        # 计算基差数据
        historical_data = []
        basis_values = []
        
        # 获取交易日期列表
        trade_dates = futures_collection.distinct('trade_date', {
            'trade_date': {'$gte': start_date, '$lte': end_date}
        })
        trade_dates.sort()
        
        for trade_date in trade_dates:
            daily_basis = []
            
            for future_code in main_futures:
                spot_code = spot_indices.get(future_code)
                if not spot_code:
                    continue
                
                # 获取期货价格
                future_data = futures_collection.find_one({
                    'ts_code': future_code,
                    'trade_date': trade_date
                })
                
                # 获取现货价格
                spot_data = index_collection.find_one({
                    'ts_code': spot_code,
                    'trade_date': trade_date
                })
                
                if future_data and spot_data:
                    future_price = future_data.get('close', 0)
                    spot_price = spot_data.get('close', 0)
                    
                    if spot_price > 0:
                        basis = future_price - spot_price
                        daily_basis.append(basis)
            
            # 计算当日平均基差
            if daily_basis:
                avg_basis = sum(daily_basis) / len(daily_basis)
                basis_values.append(avg_basis)
                historical_data.append([trade_date, round(avg_basis, 1)])
        
        if not basis_values:
            return None
        
        # 计算当前值和变化
        # current_value是时间范围内的均值
        current_value = round(sum(basis_values) / len(basis_values), 1) if basis_values else 0
        
        # change是期末相对于期初的变化
        period_end_value = round(basis_values[-1], 1) if len(basis_values) > 0 else 0
        period_start_value = round(basis_values[0], 1) if len(basis_values) > 0 else 0
        change = round(period_end_value - period_start_value, 1)
        
        # print(f"DEBUG - 基差水平计算: 数据点={len(basis_values)}, 期初={period_start_value}, 期末={period_end_value}, 均值={current_value}, 变化={change}")
        
        # 判断情绪等级（基于均值）
        if current_value > 20:
            level = "bullish"  # 期货升水较多
        elif current_value < -20:
            level = "bearish"  # 期货贴水较多
        else:
            level = "neutral"
        
        return {
            "current_value": current_value,
            "change": change,
            "level": level,
            "historical_data": historical_data
        }
        
    except Exception as e:
        print(f"计算基差水平失败: {e}")
        return None


async def calculate_overall_sentiment(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    计算综合情绪指数
    综合多个指标计算整体市场情绪
    """
    try:
        # 获取各项指标数据
        bull_bear_data = await calculate_bull_bear_ratio(start_date, end_date)
        fear_data = await calculate_fear_greed_index(start_date, end_date)
        money_flow_data = await calculate_money_flow_indicator(start_date, end_date)
        
        # 计算综合指数
        sentiment_scores = []
        
        # 多空比贡献 (30%权重)
        if bull_bear_data:
            ratio = bull_bear_data["current_value"]
            if ratio > 1.5:
                score = 70
            elif ratio > 1.2:
                score = 60
            elif ratio > 0.8:
                score = 50
            elif ratio > 0.5:
                score = 40
            else:
                score = 30
            sentiment_scores.append((score, 0.3))
        
        # 恐慌指数贡献 (25%权重，需要反转)
        if fear_data:
            fear_index = fear_data["current_value"]
            sentiment_score = 100 - fear_index  # 恐慌指数反转
            sentiment_scores.append((sentiment_score, 0.25))
        
        # 资金流向贡献 (25%权重)
        if money_flow_data:
            flow = money_flow_data["current_value"]
            if flow > 200:
                score = 80
            elif flow > 50:
                score = 65
            elif flow > -50:
                score = 50
            elif flow > -200:
                score = 35
            else:
                score = 20
            sentiment_scores.append((score, 0.25))
        
        # 计算加权平均
        if sentiment_scores:
            total_weight = sum(weight for _, weight in sentiment_scores)
            weighted_sum = sum(score * weight for score, weight in sentiment_scores)
            overall_index = round(weighted_sum / total_weight) if total_weight > 0 else 50
        else:
            overall_index = 50
        
        # 确定情绪等级
        if overall_index >= 70:
            level = "极度乐观"
        elif overall_index >= 60:
            level = "乐观"
        elif overall_index >= 40:
            level = "中性"
        elif overall_index >= 30:
            level = "悲观"
        else:
            level = "极度悲观"
        
        # 生成影响因素
        factors = []
        if bull_bear_data:
            factors.append(f"多空比: {bull_bear_data['current_value']:.2f}")
        if fear_data:
            factors.append(f"恐慌指数: {fear_data['current_value']:.1f}")
        if money_flow_data:
            factors.append(f"资金流向: {money_flow_data['current_value']:.1f}亿")
        
        return {
            "index": overall_index,
            "level": level,
            "factors": factors if factors else ["数据计算中"]
        }
        
    except Exception as e:
        print(f"计算综合情绪指数失败: {e}")
        return {
            "index": 50,
            "level": "中性",
            "factors": ["数据计算中"]
        }


@router.get("/indicators/{indicator_name}")
async def get_sentiment_indicator_detail(
    indicator_name: str,
    days: int = Query(30, description="分析天数", ge=7, le=90),
    trade_date: Optional[str] = Query(None, description="指定交易日期(YYYYMMDD)")
):
    """
    获取单个情绪指标的详细数据
    支持的指标: bull_bear_ratio, fear_greed_index, money_flow, basis_level
    """
    try:
        # 确定分析日期范围
        if not trade_date:
            daily_collection = db_handler.get_collection('stock_kline_daily')
            latest_record = daily_collection.find_one({}, {"trade_date": 1}, sort=[('trade_date', -1)])
            trade_date = latest_record["trade_date"] if latest_record else datetime.now().strftime("%Y%m%d")
        
        end_date = trade_date
        start_date = (datetime.strptime(trade_date, "%Y%m%d") - timedelta(days=days-1)).strftime("%Y%m%d")
        
        # 根据指标名称调用相应的计算函数
        if indicator_name == "bull_bear_ratio":
            result = await calculate_bull_bear_ratio(start_date, end_date)
        elif indicator_name == "fear_greed_index":
            result = await calculate_fear_greed_index(start_date, end_date)
        elif indicator_name == "money_flow":
            result = await calculate_money_flow_indicator(start_date, end_date)
        elif indicator_name == "basis_level":
            result = await calculate_basis_level(start_date, end_date)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的指标名称: {indicator_name}")
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"无法计算指标 {indicator_name} 的数据")
        
        return {
            "success": True,
            "data": {
                "indicator_name": indicator_name,
                "analysis_period": f"{days}天",
                "latest_date": trade_date,
                "indicator_data": result,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标详情失败: {str(e)}")