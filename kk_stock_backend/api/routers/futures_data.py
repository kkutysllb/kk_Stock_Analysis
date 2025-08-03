# -*- coding: utf-8 -*-
"""
期货数据API接口
支持期货基本信息、期货行情数据、持仓数据等高并发查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel
import math

import sys
import os

# 添加项目根目录到sys.path以便导入数据库管理器
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(api_dir)
sys.path.insert(0, project_root)


sys.path.insert(0, project_root)
from api.cache_middleware import cache_endpoint
from api.global_db import db_handler

router = APIRouter()


# 股指期货与现货指数映射关系
FUTURES_SPOT_MAPPING = {
    'IF': '000300.SH',  # 沪深300期货 -> 沪深300指数
    'IC': '000905.SH',  # 中证500期货 -> 中证500指数
    'IH': '000016.SH',  # 上证50期货 -> 上证50指数
    'IM': '000852.SH'   # 中证1000期货 -> 中证1000指数
}

# 数据模型
class FuturesBasicInfo(BaseModel):
    ts_code: str
    symbol: str
    name: str
    fut_code: str
    multiplier: float
    trade_unit: str
    per_unit: float
    quote_unit: str
    d_mode_desc: str
    list_date: str
    delist_date: str

class FuturesKlineData(BaseModel):
    ts_code: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    settle: float
    vol: float
    amount: float
    oi: float

# 贴升水分析数据模型
class ContractAnalysis(BaseModel):
    ts_code: str
    contract_name: str
    futures_price: float
    spot_price: float
    basis: float
    basis_rate: float
    is_contango: bool
    days_to_expiry: Optional[int]
    trade_date: str

class ContangoAnalysisData(BaseModel):
    symbol: str
    spot_index_code: str
    spot_index_name: str
    trade_date: str
    spot_price: float
    contracts: List[ContractAnalysis]
    term_structure: Dict[str, float]
    market_sentiment: str
    analysis_summary: str

# ==================== 期货基本信息 ====================

@cache_endpoint(data_type="futures_basic", ttl=3600)
@router.get("/basic/list")
async def get_futures_list(
    exchange: Optional[str] = Query(default=None, description="交易所代码"),
    fut_type: Optional[str] = Query(default=None, description="期货类型"),
    limit: int = Query(default=100, description="返回数量限制")
):
    """
    获取期货基本信息列表
    支持按交易所、期货类型筛选
    """
    try:
        collection = db_handler.get_collection('infrastructure_fut_basic')
        
        # 构建查询条件
        query = {}
        
        if exchange:
            query["exchange"] = exchange
        
        if fut_type:
            query["fut_type"] = fut_type
        
        # 异步查询数据
        cursor = collection.find(
            query,
            {"_id": 0}
        ).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "futures_list": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期货列表失败: {str(e)}")

@router.get("/basic/{ts_code}")
async def get_futures_info(
    ts_code: str
):
    """
    获取单个期货的基本信息
    """
    try:
        collection = db_handler.get_collection('infrastructure_fut_basic')
        
        result = collection.find_one(
            {"ts_code": ts_code},
            {"_id": 0}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail=f"期货代码 {ts_code} 不存在")
        
        return {
            "success": True,
            "data": {
                "futures_info": result,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期货信息失败: {str(e)}")

# ==================== 期货行情数据 ====================

@cache_endpoint(data_type="futures_daily", ttl=1800)
@router.get("/daily/{ts_code}")
async def get_futures_daily(
    ts_code: str,
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取期货日线数据
    """
    try:
        collection = db_handler.get_collection('fut_daily')
        
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
        raise HTTPException(status_code=500, detail=f"获取期货日线数据失败: {str(e)}")

# ==================== 期货持仓数据 ====================

@cache_endpoint(data_type="futures_holdings", ttl=1800)
@router.get("/holding/summary")
async def get_futures_holding_summary(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD，默认最新交易日"),
    symbols: Optional[str] = Query(default="IF,IC,IH,IM", description="期货品种代码，逗号分隔")
):
    """
    获取股指期货机构持仓汇总数据
    返回指定品种前20大机构的持仓汇总信息，用于Dashboard概览面板
    """
    try:
        collection = db_handler.get_collection('fut_holding')
        
        # 处理品种列表
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        if not symbol_list:
            symbol_list = ['IF', 'IC', 'IH', 'IM']
        
        # 日期处理逻辑
        original_date = trade_date  # 保存原始请求日期
        
        # 如果没有指定日期，获取最新交易日
        if not trade_date:
            # 构建查询条件，匹配任意一个品种的合约
            symbol_regex_list = [{"symbol": {"$regex": f"^{symbol}\\d+$"}} for symbol in symbol_list]
            latest_doc = collection.find_one(
                {"$or": symbol_regex_list},
                {"trade_date": 1},
                sort=[("trade_date", -1)]
            )
            if latest_doc:
                trade_date = latest_doc['trade_date']
            else:
                raise HTTPException(status_code=404, detail="未找到持仓数据")
        
        # 汇总结果
        summary_data = {}
        
        for symbol in symbol_list:
            # 查询该品种在指定日期的前20大机构持仓数据
            # 使用正则表达式匹配品种代码（如IC匹配IC2001, IC2002等）
            # 分两步：1.先获取前20大机构 2.再按中信期货和其他分类统计
            # 第一步：获取前20大机构列表
            top20_pipeline = [
                {
                    "$match": {
                        "symbol": {"$regex": f"^{symbol}\\d+$"},
                        "trade_date": trade_date
                    }
                },
                {
                    "$group": {
                        "_id": "$broker",
                        "total_long": {"$sum": "$long_hld"},
                        "total_short": {"$sum": "$short_hld"},
                        "total_long_chg": {"$sum": "$long_chg"},
                        "total_short_chg": {"$sum": "$short_chg"},
                        "total_vol": {"$sum": "$vol"},
                        "total_vol_chg": {"$sum": "$vol_chg"}
                    }
                },
                {
                    "$sort": {"total_long": -1}
                },
                {
                    "$limit": 20
                }
            ]
            
            top20_result = list(collection.aggregate(top20_pipeline))
            
            if not top20_result:
                # 如果没有数据，添加空数据并继续处理下一个品种
                summary_data[symbol] = {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "total_long": 0,
                    "total_short": 0,
                    "net_position": 0,
                    "total_long_chg": 0,
                    "total_short_chg": 0,
                    "net_position_chg": 0,
                    "total_vol": 0,
                    "total_vol_chg": 0,
                    "institution_count": 0,
                    "broker_breakdown": {
                        "citic": {"total_long": 0, "total_short": 0, "net_position": 0, "total_long_chg": 0, "total_short_chg": 0, "net_position_chg": 0, "total_vol": 0, "total_vol_chg": 0, "institution_count": 0},
                        "others": {"total_long": 0, "total_short": 0, "net_position": 0, "total_long_chg": 0, "total_short_chg": 0, "net_position_chg": 0, "total_vol": 0, "total_vol_chg": 0, "institution_count": 0}
                    }
                }
                continue
                
            # 获取前20大机构名单
            top20_brokers = [item["_id"] for item in top20_result]
            
            # 第二步：基于前20大机构进行分类统计
            pipeline = [
                {
                    "$match": {
                        "symbol": {"$regex": f"^{symbol}\\d+$"},
                        "trade_date": trade_date,
                        "broker": {"$in": top20_brokers}  # 只统计前20大机构
                    }
                },
                {
                    "$addFields": {
                        "broker_group": {
                            "$cond": {
                                "if": {"$regexMatch": {"input": "$broker", "regex": "中信期货"}},  
                                "then": "中信期货",
                                "else": "其他"
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$broker_group",
                        "total_long": {"$sum": "$long_hld"},
                        "total_short": {"$sum": "$short_hld"},
                        "total_long_chg": {"$sum": "$long_chg"},
                        "total_short_chg": {"$sum": "$short_chg"},
                        "total_vol": {"$sum": "$vol"},
                        "total_vol_chg": {"$sum": "$vol_chg"},
                        "brokers": {"$addToSet": "$broker"}  # 记录机构名单
                    }
                }
            ]
            
            result = list(collection.aggregate(pipeline))
            
            if result:
                # 初始化数据结构
                citic_data = {"total_long": 0, "total_short": 0, "total_long_chg": 0, "total_short_chg": 0, "total_vol": 0, "total_vol_chg": 0, "institution_count": 0}
                other_data = {"total_long": 0, "total_short": 0, "total_long_chg": 0, "total_short_chg": 0, "total_vol": 0, "total_vol_chg": 0, "institution_count": 0}
                
                # 处理分组数据
                for item in result:
                    broker_group = item['_id']
                    brokers_list = item['brokers']  # 获取该组的机构列表
                    
                    if broker_group == '中信期货':
                        citic_data = {
                            "total_long": item['total_long'],
                            "total_short": item['total_short'],
                            "total_long_chg": item['total_long_chg'],
                            "total_short_chg": item['total_short_chg'],
                            "total_vol": item['total_vol'],
                            "total_vol_chg": item['total_vol_chg'],
                            "institution_count": len(brokers_list)  # 使用实际机构数量
                        }
                    else:
                        other_data = {
                            "total_long": item['total_long'],
                            "total_short": item['total_short'],
                            "total_long_chg": item['total_long_chg'],
                            "total_short_chg": item['total_short_chg'],
                            "total_vol": item['total_vol'],
                            "total_vol_chg": item['total_vol_chg'],
                            "institution_count": len(brokers_list)  # 使用实际机构数量
                        }
                
                # 计算当前品种的总数据
                total_data = {
                    "total_long": citic_data['total_long'] + other_data['total_long'],
                    "total_short": citic_data['total_short'] + other_data['total_short'],
                    "total_long_chg": citic_data['total_long_chg'] + other_data['total_long_chg'],
                    "total_short_chg": citic_data['total_short_chg'] + other_data['total_short_chg'],
                    "total_vol": citic_data['total_vol'] + other_data['total_vol'],
                    "total_vol_chg": citic_data['total_vol_chg'] + other_data['total_vol_chg'],
                    "institution_count": 20  # 固定为20，因为我们明确取的是前20大机构
                }
                
                # 计算净持仓
                total_net_position = total_data['total_long'] - total_data['total_short']
                total_net_position_chg = total_data['total_long_chg'] - total_data['total_short_chg']
                citic_net_position = citic_data['total_long'] - citic_data['total_short']
                citic_net_position_chg = citic_data['total_long_chg'] - citic_data['total_short_chg']
                other_net_position = other_data['total_long'] - other_data['total_short']
                other_net_position_chg = other_data['total_long_chg'] - other_data['total_short_chg']
                
                summary_data[symbol] = {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "total_long": total_data['total_long'],
                    "total_short": total_data['total_short'],
                    "net_position": total_net_position,
                    "total_long_chg": total_data['total_long_chg'],
                    "total_short_chg": total_data['total_short_chg'],
                    "net_position_chg": total_net_position_chg,
                    "total_vol": total_data['total_vol'],
                    "total_vol_chg": total_data['total_vol_chg'],
                    "institution_count": total_data['institution_count'],
                    "broker_breakdown": {
                        "citic": {
                            "total_long": citic_data['total_long'],
                            "total_short": citic_data['total_short'],
                            "net_position": citic_net_position,
                            "total_long_chg": citic_data['total_long_chg'],
                            "total_short_chg": citic_data['total_short_chg'],
                            "net_position_chg": citic_net_position_chg,
                            "total_vol": citic_data['total_vol'],
                            "total_vol_chg": citic_data['total_vol_chg'],
                            "institution_count": citic_data['institution_count']
                        },
                        "others": {
                            "total_long": other_data['total_long'],
                            "total_short": other_data['total_short'],
                            "net_position": other_net_position,
                            "total_long_chg": other_data['total_long_chg'],
                            "total_short_chg": other_data['total_short_chg'],
                            "net_position_chg": other_net_position_chg,
                            "total_vol": other_data['total_vol'],
                            "total_vol_chg": other_data['total_vol_chg'],
                            "institution_count": other_data['institution_count']
                        }
                    }
                }
            else:
                # 如果没有数据，返回空值
                summary_data[symbol] = {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "total_long": 0,
                    "total_short": 0,
                    "net_position": 0,
                    "total_long_chg": 0,
                    "total_short_chg": 0,
                    "net_position_chg": 0,
                    "total_vol": 0,
                    "total_vol_chg": 0,
                    "institution_count": 0,
                    "broker_breakdown": {
                        "citic": {"total_long": 0, "total_short": 0, "net_position": 0, "total_long_chg": 0, "total_short_chg": 0, "net_position_chg": 0, "total_vol": 0, "total_vol_chg": 0, "institution_count": 0},
                        "others": {"total_long": 0, "total_short": 0, "net_position": 0, "total_long_chg": 0, "total_short_chg": 0, "net_position_chg": 0, "total_vol": 0, "total_vol_chg": 0, "institution_count": 0}
                    }
                }
        
        return {
            "success": True,
            "data": {
                "summary": summary_data,
                "trade_date": trade_date,
                "symbols": symbol_list,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期货持仓汇总失败: {str(e)}")

@cache_endpoint(data_type="futures_top20", ttl=1800)
@router.get("/holding/top20")
async def get_futures_top20_holdings(
    symbols: Optional[str] = Query(default="IF,IC,IH,IM", description="期货品种代码，逗号分隔"),
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD，默认最新交易日"),
    days: int = Query(default=7, description="获取历史趋势数据的天数")
):
    """
    获取期货前20机构持仓详细数据
    返回各品种前20大机构的详细持仓排名和历史趋势数据，用于图表化展示
    """
    try:
        collection = db_handler.get_collection('fut_holding')
        
        # 处理品种列表
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        if not symbol_list:
            symbol_list = ['IF', 'IC', 'IH', 'IM']
        
        # 如果没有指定日期，获取最新交易日
        if not trade_date:
            symbol_regex_list = [{"symbol": {"$regex": f"^{symbol}\\d+$"}} for symbol in symbol_list]
            latest_doc = collection.find_one(
                {"$or": symbol_regex_list},
                {"trade_date": 1},
                sort=[("trade_date", -1)]
            )
            if latest_doc:
                trade_date = latest_doc['trade_date']
            else:
                raise HTTPException(status_code=404, detail="未找到持仓数据")
        
        # 获取历史日期列表（包含指定日期）
        from datetime import datetime, timedelta
        trade_date_obj = datetime.strptime(trade_date, '%Y%m%d')
        date_list = []
        for i in range(days):
            date_obj = trade_date_obj - timedelta(days=i)
            date_str = date_obj.strftime('%Y%m%d')
            date_list.append(date_str)
        
        holdings_by_symbol = {}
        
        for symbol in symbol_list:
            # 获取该品种在指定日期的前20大机构持仓数据
            pipeline = [
                {
                    "$match": {
                        "symbol": {"$regex": f"^{symbol}\\d+$"},
                        "trade_date": trade_date
                    }
                },
                {
                    "$group": {
                        "_id": "$broker",
                        "long_hld": {"$sum": "$long_hld"},
                        "short_hld": {"$sum": "$short_hld"},
                        "long_chg": {"$sum": "$long_chg"},
                        "short_chg": {"$sum": "$short_chg"},
                        "vol": {"$sum": "$vol"},
                        "vol_chg": {"$sum": "$vol_chg"}
                    }
                },
                {
                    "$addFields": {
                        "net_position": {"$subtract": ["$long_hld", "$short_hld"]},
                        "net_chg": {"$subtract": ["$long_chg", "$short_chg"]}
                    }
                },
                {
                    "$sort": {"long_hld": -1}  # 按多头持仓量排序
                },
                {
                    "$limit": 20  # 取前20大机构
                }
            ]
            
            result = list(collection.aggregate(pipeline))
            
            # 为机构数据添加排名
            top20_institutions = []
            for rank, item in enumerate(result, 1):
                top20_institutions.append({
                    "rank": rank,
                    "broker": item["_id"],
                    "long_hld": item["long_hld"],
                    "short_hld": item["short_hld"],
                    "net_position": item["net_position"],
                    "long_chg": item["long_chg"],
                    "short_chg": item["short_chg"],
                    "net_chg": item["net_chg"],
                    "vol": item["vol"],
                    "vol_chg": item["vol_chg"]
                })
            
            # 获取历史趋势数据
            daily_trends = []
            for date_str in reversed(date_list):  # 按时间正序
                trend_pipeline = [
                    {
                        "$match": {
                            "symbol": {"$regex": f"^{symbol}\\d+$"},
                            "trade_date": date_str
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total_long": {"$sum": "$long_hld"},
                            "total_short": {"$sum": "$short_hld"},
                            "total_long_chg": {"$sum": "$long_chg"},
                            "total_short_chg": {"$sum": "$short_chg"},
                            "institution_count": {"$sum": 1}
                        }
                    }
                ]
                
                trend_result = list(collection.aggregate(trend_pipeline))
                if trend_result:
                    data = trend_result[0]
                    daily_trends.append({
                        "trade_date": date_str,
                        "total_long": data["total_long"],
                        "total_short": data["total_short"],
                        "net_position": data["total_long"] - data["total_short"],
                        "total_long_chg": data["total_long_chg"],
                        "total_short_chg": data["total_short_chg"],
                        "net_position_chg": data["total_long_chg"] - data["total_short_chg"],
                        "institution_count": data["institution_count"]
                    })
                else:
                    # 如果某天没有数据，添加空数据点
                    daily_trends.append({
                        "trade_date": date_str,
                        "total_long": 0,
                        "total_short": 0,
                        "net_position": 0,
                        "total_long_chg": 0,
                        "total_short_chg": 0,
                        "net_position_chg": 0,
                        "institution_count": 0
                    })
            
            holdings_by_symbol[symbol] = {
                "symbol": symbol,
                "trade_date": trade_date,
                "top20_institutions": top20_institutions,
                "daily_trends": daily_trends
            }
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "symbols": symbol_list,
                "holdings_by_symbol": holdings_by_symbol,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取前20机构持仓数据失败: {str(e)}")

@router.get("/holding/{ts_code}")
async def get_futures_holding(
    ts_code: str,
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=50, description="返回条数")
):
    """
    获取期货持仓数据
    """
    try:
        collection = db_handler.get_collection('fut_holding')
        
        # 构建查询条件
        query = {"symbol": ts_code.split('.')[0]}  # 期货持仓数据使用symbol字段
        
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
                "holding_data": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期货持仓数据失败: {str(e)}")

# ==================== 期货仓单数据 ====================

@router.get("/warehouse/{symbol}")
async def get_futures_warehouse(
    symbol: str,
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=50, description="返回条数")
):
    """
    获取期货仓单数据
    """
    try:
        collection = db_handler.get_collection('fut_wm')
        
        # 构建查询条件
        query = {"symbol": symbol}
        
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
                "symbol": symbol,
                "warehouse_data": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期货仓单数据失败: {str(e)}")

# ==================== 批量查询接口（支持并发） ====================

@router.post("/batch/daily")
async def get_batch_futures_daily(
    request_data: Dict[str, Any]
):
    """
    批量获取期货日线数据（支持并发查询）
    
    请求格式:
    {
        "ts_codes": ["RB2501.SHF", "HC2501.SHF"],
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
            raise HTTPException(status_code=400, detail="批量查询最多支持50个期货代码")
        
        # 异步并发查询
        async def fetch_single_futures_data(ts_code: str):
            try:
                collection = db_handler.get_collection('fut_daily')
                
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
        tasks = [fetch_single_futures_data(ts_code) for ts_code in ts_codes]
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
        raise HTTPException(status_code=500, detail=f"批量查询期货数据失败: {str(e)}")

# ==================== 活跃期货合约统计汇总 ====================

@router.get("/active/summary")
async def get_active_futures_summary(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD，默认最新交易日"),
    symbols: Optional[str] = Query(default="IH,IF,IC,IM", description="期货品种代码，逗号分隔")
):
    """
    获取活跃期货合约统计汇总
    直接从fut_holding集合中获取IH、IF、IC、IM开头的活跃合约信息并进行统计汇总
    """
    try:
        # 处理品种列表
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        if not symbol_list:
            symbol_list = ['IH', 'IF', 'IC', 'IM']
        
        holding_collection = db_handler.get_collection('fut_holding')
        
        # 如果没有指定日期，获取最新交易日
        if not trade_date:
            # 构建查询条件，匹配任意一个品种的合约
            symbol_regex_list = [{"symbol": {"$regex": f"^{symbol}\\d+$"}} for symbol in symbol_list]
            latest_doc = holding_collection.find_one(
                {"$or": symbol_regex_list},
                {"trade_date": 1},
                sort=[("trade_date", -1)]
            )
            if latest_doc:
                trade_date = latest_doc['trade_date']
            else:
                raise HTTPException(status_code=404, detail="未找到持仓数据")
        
        summary_data = {}
        
        for symbol in symbol_list:
            # 获取该品种的持仓数据并进行统计汇总
            pipeline = [
                {
                    "$match": {
                        "symbol": {"$regex": f"^{symbol}\\d+$"},
                        "trade_date": trade_date
                    }
                },
                {
                    "$group": {
                        "_id": "$symbol",
                        "total_long": {"$sum": "$long_hld"},
                        "total_short": {"$sum": "$short_hld"},
                        "total_long_chg": {"$sum": "$long_chg"},
                        "total_short_chg": {"$sum": "$short_chg"},
                        "total_vol": {"$sum": "$vol"},
                        "total_vol_chg": {"$sum": "$vol_chg"},
                        "institution_count": {"$sum": 1},
                        "contracts": {"$addToSet": "$symbol"}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_long": {"$sum": "$total_long"},
                        "total_short": {"$sum": "$total_short"},
                        "total_long_chg": {"$sum": "$total_long_chg"},
                        "total_short_chg": {"$sum": "$total_short_chg"},
                        "total_vol": {"$sum": "$total_vol"},
                        "total_vol_chg": {"$sum": "$total_vol_chg"},
                        "institution_count": {"$sum": "$institution_count"},
                        "active_contracts": {"$push": "$contracts"},
                        "contract_details": {
                            "$push": {
                                "contracts": "$contracts",
                                "total_long": "$total_long",
                                "total_short": "$total_short",
                                "total_vol": "$total_vol"
                            }
                        }
                    }
                }
            ]
            
            result = list(holding_collection.aggregate(pipeline))
            
            if result:
                data = result[0]
                
                # 展平活跃合约列表
                active_contracts = []
                for contract_list in data.get('active_contracts', []):
                    active_contracts.extend(contract_list)
                active_contracts = list(set(active_contracts))  # 去重
                
                # 找出主力合约（持仓量最大的合约）
                main_contract = None
                max_volume = 0
                for contract_detail in data.get('contract_details', []):
                    for contract in contract_detail.get('contracts', []):
                        total_vol = contract_detail.get('total_vol', 0)
                        if total_vol > max_volume:
                            max_volume = total_vol
                            main_contract = {
                                "symbol": contract,
                                "total_volume": total_vol,
                                "total_long": contract_detail.get('total_long', 0),
                                "total_short": contract_detail.get('total_short', 0)
                            }
                
                summary_data[symbol] = {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "active_contracts_count": len(active_contracts),
                    "active_contracts": active_contracts,
                    "total_long": data.get('total_long', 0),
                    "total_short": data.get('total_short', 0),
                    "net_position": data.get('total_long', 0) - data.get('total_short', 0),
                    "total_long_chg": data.get('total_long_chg', 0),
                    "total_short_chg": data.get('total_short_chg', 0),
                    "net_position_chg": data.get('total_long_chg', 0) - data.get('total_short_chg', 0),
                    "total_vol": data.get('total_vol', 0),
                    "total_vol_chg": data.get('total_vol_chg', 0),
                    "institution_count": data.get('institution_count', 0),
                    "main_contract": main_contract
                }
            else:
                # 如果没有数据，返回空值
                summary_data[symbol] = {
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "active_contracts_count": 0,
                    "active_contracts": [],
                    "total_long": 0,
                    "total_short": 0,
                    "net_position": 0,
                    "total_long_chg": 0,
                    "total_short_chg": 0,
                    "net_position_chg": 0,
                    "total_vol": 0,
                    "total_vol_chg": 0,
                    "institution_count": 0,
                    "main_contract": None
                }
        
        # 计算总体统计
        total_stats = {
            "total_active_contracts": sum(data['active_contracts_count'] for data in summary_data.values()),
            "total_long": sum(data['total_long'] for data in summary_data.values()),
            "total_short": sum(data['total_short'] for data in summary_data.values()),
            "total_net_position": sum(data['net_position'] for data in summary_data.values()),
            "total_vol": sum(data['total_vol'] for data in summary_data.values()),
            "total_institutions": sum(data['institution_count'] for data in summary_data.values())
        }
        
        return {
            "success": True,
            "data": {
                "summary_by_symbol": summary_data,
                "total_stats": total_stats,
                "trade_date": trade_date,
                "symbols": symbol_list,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃期货合约汇总失败: {str(e)}")

# ==================== 期货交易日历 ====================

@router.get("/calendar")
async def get_futures_calendar(
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    exchange: Optional[str] = Query(default=None, description="交易所代码")
):
    """
    获取期货交易日历
    """
    try:
        collection = db_handler.get_collection('fut_trade_cal')
        
        # 构建查询条件
        query = {}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["cal_date"] = date_query
        
        if exchange:
            query["exchange"] = exchange
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("cal_date", 1)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "calendar": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期货交易日历失败: {str(e)}")

# ==================== 贴升水分析 ====================

@router.get("/contango-analysis", response_model=Dict[str, Any])
async def get_contango_analysis(
    symbols: Optional[str] = Query(default="IF,IC,IH,IM", description="期货品种，多个用逗号分隔"),
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    days: int = Query(default=30, description="历史数据天数")
):
    """
    获取股指期货贴升水分析
    计算基差、基差率、期限结构等指标
    """
    try:
        # 解析品种列表
        symbol_list = [s.strip() for s in symbols.split(',')]
        
        # 获取最新交易日期
        if not trade_date:
            fut_daily_collection = db_handler.get_collection('fut_daily')
            latest_record = fut_daily_collection.find_one(
                sort=[('trade_date', -1)],
                projection={'trade_date': 1}
            )
            if not latest_record:
                raise HTTPException(status_code=404, detail="未找到期货数据")
            trade_date = latest_record['trade_date']
        
        analysis_results = []
        
        for symbol in symbol_list:
            if symbol not in FUTURES_SPOT_MAPPING:
                continue
                
            spot_index_code = FUTURES_SPOT_MAPPING[symbol]
            
            # 获取现货指数数据
            index_collection = db_handler.get_collection('index_daily')
            spot_data = index_collection.find_one({
                'ts_code': spot_index_code,
                'trade_date': trade_date
            })
            
            if not spot_data:
                continue
                
            spot_price = float(spot_data.get('close', 0))
            
            # 获取该品种的期货合约数据
            fut_daily_collection = db_handler.get_collection('fut_daily')
            futures_cursor = fut_daily_collection.find({
                'ts_code': {'$regex': f'^{symbol}'},
                'trade_date': trade_date
            })
            
            contracts = []
            term_structure = {}
            
            for fut_data in futures_cursor:
                ts_code = fut_data['ts_code']
                futures_price = float(fut_data.get('close', 0))
                settle_price = float(fut_data.get('settle', futures_price))
                
                if futures_price <= 0 or spot_price <= 0:
                    continue
                    
                # 计算基差和基差率
                basis = settle_price - spot_price
                basis_rate = (basis / spot_price) * 100
                is_contango = basis > 0
                
                # 提取合约月份用于期限结构
                contract_month = ts_code.split('.')[0][-4:]
                term_structure[contract_month] = basis_rate
                
                contracts.append(ContractAnalysis(
                    ts_code=ts_code,
                    contract_name=fut_data.get('name', ts_code),
                    futures_price=settle_price,
                    spot_price=spot_price,
                    basis=round(basis, 2),
                    basis_rate=round(basis_rate, 4),
                    is_contango=is_contango,
                    days_to_expiry=None,  # 可后续计算
                    trade_date=trade_date
                ))
            
            if contracts:
                # 分析市场情绪
                avg_basis_rate = sum(c.basis_rate for c in contracts) / len(contracts)
                if avg_basis_rate > 1:
                    sentiment = "强升水"
                elif avg_basis_rate > 0:
                    sentiment = "升水"
                elif avg_basis_rate > -1:
                    sentiment = "贴水"
                else:
                    sentiment = "强贴水"
                
                # 生成分析摘要
                contango_count = sum(1 for c in contracts if c.is_contango)
                total_contracts = len(contracts)
                summary = f"{symbol}品种共{total_contracts}个合约，其中{contango_count}个升水，{total_contracts-contango_count}个贴水，平均基差率{avg_basis_rate:.2f}%"
                
                analysis_results.append(ContangoAnalysisData(
                    symbol=symbol,
                    spot_index_code=spot_index_code,
                    spot_index_name=spot_data.get('name', spot_index_code),
                    trade_date=trade_date,
                    spot_price=spot_price,
                    contracts=contracts,
                    term_structure=term_structure,
                    market_sentiment=sentiment,
                    analysis_summary=summary
                ))
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "analysis_results": [result.dict() for result in analysis_results],
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"贴升水分析失败: {str(e)}")

@router.get("/contango-analysis/{symbol}", response_model=Dict[str, Any])
async def get_symbol_contango_analysis(
    symbol: str,
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=30, description="返回数据条数")
):
    """
    获取单个品种的贴升水历史分析
    """
    try:
        if symbol not in FUTURES_SPOT_MAPPING:
            raise HTTPException(status_code=400, detail=f"不支持的期货品种: {symbol}")
            
        spot_index_code = FUTURES_SPOT_MAPPING[symbol]
        
        # 构建日期查询条件
        date_query = {}
        if start_date:
            date_query['$gte'] = start_date
        if end_date:
            date_query['$lte'] = end_date
            
        query_condition = {}
        if date_query:
            query_condition['trade_date'] = date_query
            
        # 获取期货数据
        fut_daily_collection = db_handler.get_collection('fut_daily')
        futures_cursor = fut_daily_collection.find({
            'ts_code': {'$regex': f'^{symbol}'},
            **query_condition
        }).sort('trade_date', -1).limit(limit * 10)  # 多取一些数据用于分析
        
        # 获取对应的现货指数数据
        index_collection = db_handler.get_collection('index_daily')
        index_cursor = index_collection.find({
            'ts_code': spot_index_code,
            **query_condition
        }).sort('trade_date', -1).limit(limit)
        
        # 构建现货价格字典
        spot_prices = {}
        for spot_data in index_cursor:
            spot_prices[spot_data['trade_date']] = float(spot_data.get('close', 0))
        
        # 分析期货数据
        daily_analysis = {}
        for fut_data in futures_cursor:
            trade_date = fut_data['trade_date']
            if trade_date not in spot_prices:
                continue
                
            spot_price = spot_prices[trade_date]
            if spot_price <= 0:
                continue
                
            if trade_date not in daily_analysis:
                daily_analysis[trade_date] = {
                    'trade_date': trade_date,
                    'spot_price': spot_price,
                    'contracts': [],
                    'avg_basis': 0,
                    'avg_basis_rate': 0
                }
            
            ts_code = fut_data['ts_code']
            futures_price = float(fut_data.get('close', 0))
            settle_price = float(fut_data.get('settle', futures_price))
            
            if settle_price > 0:
                basis = settle_price - spot_price
                basis_rate = (basis / spot_price) * 100
                
                daily_analysis[trade_date]['contracts'].append({
                    'ts_code': ts_code,
                    'futures_price': settle_price,
                    'basis': round(basis, 2),
                    'basis_rate': round(basis_rate, 4),
                    'is_contango': basis > 0
                })
        
        # 计算每日平均基差
        for date_data in daily_analysis.values():
            if date_data['contracts']:
                date_data['avg_basis'] = round(sum(c['basis'] for c in date_data['contracts']) / len(date_data['contracts']), 2)
                date_data['avg_basis_rate'] = round(sum(c['basis_rate'] for c in date_data['contracts']) / len(date_data['contracts']), 4)
        
        # 按日期排序并限制返回数量
        sorted_analysis = sorted(daily_analysis.values(), key=lambda x: x['trade_date'], reverse=True)[:limit]
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "spot_index_code": spot_index_code,
                "analysis_period": len(sorted_analysis),
                "historical_analysis": sorted_analysis,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取{symbol}贴升水分析失败: {str(e)}")