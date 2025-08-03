#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HM数据API接口
支持hm_detail和hm_list自定义集合数据查询
"""

from fastapi import APIRouter, HTTPException, Query
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

from api.global_db import db_handler

router = APIRouter()


# 数据模型
class HMDetailInfo(BaseModel):
    """HM详细信息数据模型"""
    pass  # 根据实际数据结构定义字段

class HMListInfo(BaseModel):
    """HM列表信息数据模型"""
    pass  # 根据实际数据结构定义字段

# ==================== HM详细数据接口 ====================

@router.get("/detail/list")
async def get_hm_detail_list(
    limit: int = Query(default=100, description="返回数量限制", le=1000),
    skip: int = Query(default=0, description="跳过记录数", ge=0),
    sort_field: Optional[str] = Query(default=None, description="排序字段"),
    sort_order: int = Query(default=-1, description="排序方式：1升序，-1降序")
):
    """
    获取HM详细数据列表
    支持分页、排序功能
    """
    try:
        collection = db_handler.get_collection('hm_detail')
        
        # 构建排序条件
        sort_condition = []
        if sort_field:
            sort_condition.append((sort_field, sort_order))
        else:
            # 默认按_id排序
            sort_condition.append(("_id", -1))
        
        # 查询数据
        cursor = collection.find(
            {},
            {"_id": 0}
        ).sort(sort_condition).skip(skip).limit(limit)
        
        results = list(cursor)
        
        # 获取总数
        total_count = collection.count_documents({})
        
        return {
            "success": True,
            "data": {
                "hm_detail_list": results,
                "pagination": {
                    "total_count": total_count,
                    "returned_count": len(results),
                    "skip": skip,
                    "limit": limit,
                    "has_more": (skip + len(results)) < total_count
                },
                "sort_info": {
                    "field": sort_field,
                    "order": "desc" if sort_order == -1 else "asc"
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取HM详细数据失败: {str(e)}")

@router.get("/detail/search")
async def search_hm_detail(
    keyword: str = Query(..., description="搜索关键字"),
    search_fields: Optional[str] = Query(default=None, description="搜索字段，逗号分隔"),
    limit: int = Query(default=50, description="返回结果数量限制", le=500)
):
    """
    搜索HM详细数据
    支持多字段模糊搜索
    """
    try:
        collection = db_handler.get_collection('hm_detail')
        
        # 获取集合的一个样本文档来确定可搜索字段
        sample_doc = collection.find_one({}, {"_id": 0})
        if not sample_doc:
            raise HTTPException(status_code=404, detail="HM详细数据集合为空")
        
        # 确定搜索字段
        if search_fields:
            fields_to_search = [field.strip() for field in search_fields.split(",")]
            # 验证字段是否存在
            fields_to_search = [field for field in fields_to_search if field in sample_doc]
        else:
            # 默认搜索所有字符串类型字段
            fields_to_search = [key for key, value in sample_doc.items() 
                              if isinstance(value, str)]
        
        if not fields_to_search:
            raise HTTPException(status_code=400, detail="未找到可搜索的字段")
        
        # 构建搜索条件
        search_conditions = []
        for field in fields_to_search:
            search_conditions.append({
                field: {"$regex": keyword, "$options": "i"}
            })
        
        search_query = {"$or": search_conditions}
        
        # 执行搜索
        cursor = collection.find(
            search_query,
            {"_id": 0}
        ).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "keyword": keyword,
                "search_fields": fields_to_search,
                "results": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"搜索HM详细数据失败: {str(e)}")

@router.get("/detail/stats")
async def get_hm_detail_stats():
    """
    获取HM详细数据统计信息
    """
    try:
        collection = db_handler.get_collection('hm_detail')
        
        # 基础统计
        total_count = collection.count_documents({})
        
        if total_count == 0:
            return {
                "success": True,
                "data": {
                    "total_count": 0,
                    "message": "HM详细数据集合为空",
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # 获取样本数据分析字段结构
        sample_docs = list(collection.find({}, {"_id": 0}).limit(10))
        
        # 分析字段类型
        field_types = {}
        if sample_docs:
            for field, value in sample_docs[0].items():
                field_types[field] = type(value).__name__
        
        # 获取最新和最旧的记录（如果有时间字段）
        latest_record = collection.find_one({}, {"_id": 0}, sort=[("_id", -1)])
        oldest_record = collection.find_one({}, {"_id": 0}, sort=[("_id", 1)])
        
        return {
            "success": True,
            "data": {
                "total_count": total_count,
                "field_structure": field_types,
                "sample_data": sample_docs[0] if sample_docs else None,
                "data_range": {
                    "latest_record": latest_record,
                    "oldest_record": oldest_record
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取HM详细数据统计失败: {str(e)}")

# ==================== HM列表数据接口 ====================

@router.get("/list/all")
async def get_hm_list_all(
    limit: int = Query(default=109, description="返回数量限制", le=500),
    skip: int = Query(default=0, description="跳过记录数", ge=0)
):
    """
    获取HM列表数据
    由于数据量较小(109条)，支持一次性获取全部
    """
    try:
        collection = db_handler.get_collection('hm_list')
        
        # 查询数据
        cursor = collection.find(
            {},
            {"_id": 0}
        ).skip(skip).limit(limit)
        
        results = list(cursor)
        
        # 获取总数
        total_count = collection.count_documents({})
        
        return {
            "success": True,
            "data": {
                "hm_list": results,
                "pagination": {
                    "total_count": total_count,
                    "returned_count": len(results),
                    "skip": skip,
                    "limit": limit,
                    "has_more": (skip + len(results)) < total_count
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取HM列表数据失败: {str(e)}")

@router.get("/list/search")
async def search_hm_list(
    keyword: str = Query(..., description="搜索关键字"),
    limit: int = Query(default=50, description="返回结果数量限制", le=109)
):
    """
    搜索HM列表数据
    """
    try:
        collection = db_handler.get_collection('hm_list')
        
        # 获取集合的一个样本文档来确定可搜索字段
        sample_doc = collection.find_one({}, {"_id": 0})
        if not sample_doc:
            raise HTTPException(status_code=404, detail="HM列表数据集合为空")
        
        # 默认搜索所有字符串类型字段
        fields_to_search = [key for key, value in sample_doc.items() 
                          if isinstance(value, str)]
        
        if not fields_to_search:
            raise HTTPException(status_code=400, detail="未找到可搜索的字段")
        
        # 构建搜索条件
        search_conditions = []
        for field in fields_to_search:
            search_conditions.append({
                field: {"$regex": keyword, "$options": "i"}
            })
        
        search_query = {"$or": search_conditions}
        
        # 执行搜索
        cursor = collection.find(
            search_query,
            {"_id": 0}
        ).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "keyword": keyword,
                "search_fields": fields_to_search,
                "results": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"搜索HM列表数据失败: {str(e)}")

@router.get("/list/stats")
async def get_hm_list_stats():
    """
    获取HM列表数据统计信息
    """
    try:
        collection = db_handler.get_collection('hm_list')
        
        # 基础统计
        total_count = collection.count_documents({})
        
        if total_count == 0:
            return {
                "success": True,
                "data": {
                    "total_count": 0,
                    "message": "HM列表数据集合为空",
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # 获取所有数据进行分析（数据量小，可以全部加载）
        all_docs = list(collection.find({}, {"_id": 0}))
        
        # 分析字段类型
        field_types = {}
        if all_docs:
            for field, value in all_docs[0].items():
                field_types[field] = type(value).__name__
        
        return {
            "success": True,
            "data": {
                "total_count": total_count,
                "field_structure": field_types,
                "sample_data": all_docs[0] if all_docs else None,
                "data_summary": {
                    "first_record": all_docs[0] if all_docs else None,
                    "last_record": all_docs[-1] if all_docs else None
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取HM列表数据统计失败: {str(e)}")

# ==================== 批量查询接口 ====================

@router.post("/batch/query")
async def batch_query_hm_data(
    request_data: Dict[str, Any]
):
    """
    批量查询HM数据
    支持同时查询detail和list数据
    
    请求格式:
    {
        "collections": ["hm_detail", "hm_list"],
        "query_conditions": {
            "hm_detail": {...},
            "hm_list": {...}
        },
        "limits": {
            "hm_detail": 100,
            "hm_list": 50
        }
    }
    """
    try:
        collections = request_data.get("collections", ["hm_detail", "hm_list"])
        query_conditions = request_data.get("query_conditions", {})
        limits = request_data.get("limits", {"hm_detail": 100, "hm_list": 109})
        
        # 异步查询函数
        async def query_collection(collection_name: str):
            try:
                collection = db_handler.get_collection(collection_name)
                query = query_conditions.get(collection_name, {})
                limit = limits.get(collection_name, 100)
                
                cursor = collection.find(query, {"_id": 0}).limit(limit)
                results = list(cursor)
                
                return {
                    "collection": collection_name,
                    "success": True,
                    "data": results,
                    "count": len(results)
                }
                
            except Exception as e:
                return {
                    "collection": collection_name,
                    "success": False,
                    "error": str(e),
                    "data": []
                }
        
        # 并发执行查询
        tasks = [query_collection(col) for col in collections if col in ["hm_detail", "hm_list"]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        response_data = {}
        for result in results:
            if isinstance(result, dict):
                collection_name = result["collection"]
                response_data[collection_name] = result
        
        return {
            "success": True,
            "data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量查询HM数据失败: {str(e)}")

# ==================== 数据导出接口 ====================

@router.get("/export/summary")
async def get_hm_data_summary():
    """
    获取HM数据汇总信息
    用于数据导出和概览
    """
    try:
        # 获取两个集合的基本信息
        hm_detail_collection = db_handler.get_collection('hm_detail')
        hm_list_collection = db_handler.get_collection('hm_list')
        
        detail_count = hm_detail_collection.count_documents({})
        list_count = hm_list_collection.count_documents({})
        
        # 获取字段结构
        detail_sample = hm_detail_collection.find_one({}, {"_id": 0}) if detail_count > 0 else None
        list_sample = hm_list_collection.find_one({}, {"_id": 0}) if list_count > 0 else None
        
        return {
            "success": True,
            "data": {
                "collections_summary": {
                    "hm_detail": {
                        "count": detail_count,
                        "fields": list(detail_sample.keys()) if detail_sample else [],
                        "sample": detail_sample
                    },
                    "hm_list": {
                        "count": list_count,
                        "fields": list(list_sample.keys()) if list_sample else [],
                        "sample": list_sample
                    }
                },
                "total_records": detail_count + list_count,
                "last_updated": "20250627",  # 根据提供的信息
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取HM数据汇总失败: {str(e)}")

# ==================== 龙虎榜与游资交易数据交集分析接口 ====================

@router.get("/dragon-tiger/intersection")
async def analyze_dragon_tiger_hm_intersection(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    hm_name: Optional[str] = Query(default=None, description="游资名称"),
    ts_code: Optional[str] = Query(default=None, description="股票代码"),
    limit: int = Query(default=100, description="返回结果数量限制", le=500),
    match_type: str = Query(default="exact", description="匹配类型: exact(精确), fuzzy(模糊)")
):
    """
    龙虎榜与游资交易数据交集分析
    通过营业部字段关联，分析游资在龙虎榜中的交易情况
    """
    try:
        # 获取数据库集合
        top_inst_collection = db_handler.get_collection('top_inst')  # 龙虎榜机构数据
        hm_detail_collection = db_handler.get_collection('hm_detail')  # 游资详细交易数据
        hm_list_collection = db_handler.get_collection('hm_list')  # 游资列表数据
        
        # 构建查询条件
        base_query = {}
        if trade_date:
            base_query["trade_date"] = trade_date
        if ts_code:
            base_query["ts_code"] = ts_code
        
        # 获取游资营业部映射关系
        hm_org_mapping = {}
        hm_list_cursor = hm_list_collection.find({}, {"_id": 0, "name": 1, "orgs": 1})
        
        for hm_record in hm_list_cursor:
            hm_name_key = hm_record["name"]
            orgs_str = hm_record["orgs"]
            try:
                import ast
                orgs_list = ast.literal_eval(orgs_str) if orgs_str else []
                hm_org_mapping[hm_name_key] = orgs_list
            except:
                hm_org_mapping[hm_name_key] = []
        
        # 如果指定了游资名称，只分析该游资
        if hm_name:
            target_orgs = hm_org_mapping.get(hm_name, [])
            if not target_orgs:
                return {
                    "success": True,
                    "data": {
                        "message": f"未找到游资 '{hm_name}' 的营业部信息",
                        "intersection_results": [],
                        "count": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                }
        else:
            # 获取所有游资的营业部
            target_orgs = []
            for orgs_list in hm_org_mapping.values():
                target_orgs.extend(orgs_list)
            target_orgs = list(set(target_orgs))  # 去重
        
        if not target_orgs:
            return {
                "success": True,
                "data": {
                    "message": "未找到任何游资营业部信息",
                    "intersection_results": [],
                    "count": 0,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # 构建龙虎榜查询条件
        dragon_tiger_query = base_query.copy()
        
        if match_type == "exact":
            # 精确匹配
            dragon_tiger_query["exalter"] = {"$in": target_orgs}
        else:
            # 模糊匹配
            org_patterns = []
            for org in target_orgs:
                org_patterns.append({"exalter": {"$regex": org.replace("(", "\\(").replace(")", "\\)"), "$options": "i"}})
            if org_patterns:
                dragon_tiger_query["$or"] = org_patterns
        
        # 查询龙虎榜数据
        dragon_tiger_cursor = top_inst_collection.find(
            dragon_tiger_query,
            {"_id": 0}
        ).sort("trade_date", -1).limit(limit)
        
        dragon_tiger_results = list(dragon_tiger_cursor)
        
        # 为每条龙虎榜记录匹配对应的游资信息
        enriched_results = []
        for dt_record in dragon_tiger_results:
            exalter = dt_record["exalter"]
            
            # 查找对应的游资
            matched_hm_names = []
            for hm_name_key, orgs_list in hm_org_mapping.items():
                if match_type == "exact":
                    if exalter in orgs_list:
                        matched_hm_names.append(hm_name_key)
                else:
                    # 模糊匹配
                    for org in orgs_list:
                        if org in exalter or exalter in org:
                            matched_hm_names.append(hm_name_key)
                            break
            
            # 获取对应的游资详细交易数据
            hm_detail_query = {
                "trade_date": dt_record["trade_date"],
                "ts_code": dt_record["ts_code"]
            }
            
            if matched_hm_names:
                hm_detail_query["hm_name"] = {"$in": matched_hm_names}
            
            hm_detail_records = list(hm_detail_collection.find(
                hm_detail_query,
                {"_id": 0}
            ))
            
            # 组合结果
            enriched_record = {
                "dragon_tiger_data": dt_record,
                "matched_hm_names": matched_hm_names,
                "hm_detail_data": hm_detail_records,
                "intersection_type": match_type,
                "org_matched": exalter
            }
            
            enriched_results.append(enriched_record)
        
        # 统计分析
        stats = {
            "total_dragon_tiger_records": len(dragon_tiger_results),
            "records_with_hm_match": len([r for r in enriched_results if r["matched_hm_names"]]),
            "unique_hm_names": list(set([name for r in enriched_results for name in r["matched_hm_names"]])),
            "unique_stocks": list(set([r["dragon_tiger_data"]["ts_code"] for r in enriched_results])),
            "date_range": {
                "start_date": min([r["dragon_tiger_data"]["trade_date"] for r in enriched_results]) if enriched_results else None,
                "end_date": max([r["dragon_tiger_data"]["trade_date"] for r in enriched_results]) if enriched_results else None
            }
        }
        
        return {
            "success": True,
            "data": {
                "intersection_results": enriched_results,
                "statistics": stats,
                "query_params": {
                    "trade_date": trade_date,
                    "hm_name": hm_name,
                    "ts_code": ts_code,
                    "match_type": match_type,
                    "limit": limit
                },
                "count": len(enriched_results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"龙虎榜与游资交易数据交集分析失败: {str(e)}")

@router.get("/dragon-tiger/hm-summary")
async def get_hm_dragon_tiger_summary(
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    top_n: int = Query(default=20, description="返回前N名活跃游资", le=50)
):
    """
    获取游资在龙虎榜中的活跃度汇总统计
    分析哪些游资最活跃，交易金额最大等
    """
    try:
        # 获取数据库集合
        top_inst_collection = db_handler.get_collection('top_inst')
        hm_list_collection = db_handler.get_collection('hm_list')
        
        # 构建日期查询条件
        date_query = {}
        if start_date and end_date:
            date_query["trade_date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            date_query["trade_date"] = {"$gte": start_date}
        elif end_date:
            date_query["trade_date"] = {"$lte": end_date}
        
        # 获取游资营业部映射
        hm_org_mapping = {}
        org_to_hm_mapping = {}  # 反向映射：营业部 -> 游资名称
        
        hm_list_cursor = hm_list_collection.find({}, {"_id": 0, "name": 1, "orgs": 1, "desc": 1})
        
        for hm_record in hm_list_cursor:
            hm_name = hm_record["name"]
            orgs_str = hm_record["orgs"]
            desc = hm_record.get("desc", "")
            
            try:
                import ast
                orgs_list = ast.literal_eval(orgs_str) if orgs_str else []
                hm_org_mapping[hm_name] = {
                    "orgs": orgs_list,
                    "desc": desc
                }
                
                # 建立反向映射
                for org in orgs_list:
                    org_to_hm_mapping[org] = hm_name
                    
            except:
                hm_org_mapping[hm_name] = {"orgs": [], "desc": desc}
        
        # 获取所有游资相关的龙虎榜数据
        all_orgs = list(org_to_hm_mapping.keys())
        
        if not all_orgs:
            return {
                "success": True,
                "data": {
                    "message": "未找到游资营业部数据",
                    "hm_summary": [],
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # 查询龙虎榜数据
        dragon_tiger_query = date_query.copy()
        dragon_tiger_query["exalter"] = {"$in": all_orgs}
        
        dragon_tiger_cursor = top_inst_collection.find(
            dragon_tiger_query,
            {"_id": 0}
        )
        
        # 按游资统计数据
        hm_stats = {}
        
        for dt_record in dragon_tiger_cursor:
            exalter = dt_record["exalter"]
            hm_name = org_to_hm_mapping.get(exalter)
            
            if not hm_name:
                continue
                
            if hm_name not in hm_stats:
                hm_stats[hm_name] = {
                    "hm_name": hm_name,
                    "desc": hm_org_mapping[hm_name]["desc"],
                    "orgs": hm_org_mapping[hm_name]["orgs"],
                    "total_trades": 0,
                    "total_buy_amount": 0,
                    "total_sell_amount": 0,
                    "total_net_buy": 0,
                    "trade_dates": set(),
                    "stocks_traded": set(),
                    "avg_buy_rate": 0,
                    "avg_sell_rate": 0,
                    "recent_trades": []
                }
            
            stats = hm_stats[hm_name]
            stats["total_trades"] += 1
            stats["total_buy_amount"] += dt_record.get("buy", 0)
            stats["total_sell_amount"] += dt_record.get("sell", 0)
            stats["total_net_buy"] += dt_record.get("net_buy", 0)
            stats["trade_dates"].add(dt_record["trade_date"])
            stats["stocks_traded"].add(dt_record["ts_code"])
            
            # 保存最近的交易记录
            if len(stats["recent_trades"]) < 5:
                stats["recent_trades"].append({
                    "trade_date": dt_record["trade_date"],
                    "ts_code": dt_record["ts_code"],
                    "buy": dt_record.get("buy", 0),
                    "sell": dt_record.get("sell", 0),
                    "net_buy": dt_record.get("net_buy", 0)
                })
        
        # 转换集合为列表并计算平均值
        hm_summary = []
        for hm_name, stats in hm_stats.items():
            stats["trade_dates"] = sorted(list(stats["trade_dates"]))
            stats["stocks_traded"] = list(stats["stocks_traded"])
            stats["unique_trade_days"] = len(stats["trade_dates"])
            stats["unique_stocks_count"] = len(stats["stocks_traded"])
            
            # 计算活跃度评分（综合考虑交易次数、金额、股票数量）
            stats["activity_score"] = (
                stats["total_trades"] * 0.3 +
                abs(stats["total_net_buy"]) / 1000000 * 0.4 +  # 净买入金额（百万为单位）
                stats["unique_stocks_count"] * 0.3
            )
            
            hm_summary.append(stats)
        
        # 按活跃度评分排序
        hm_summary.sort(key=lambda x: x["activity_score"], reverse=True)
        
        # 只返回前N名
        hm_summary = hm_summary[:top_n]
        
        # 整体统计
        overall_stats = {
            "total_hm_count": len(hm_stats),
            "total_trades": sum(stats["total_trades"] for stats in hm_stats.values()),
            "total_buy_amount": sum(stats["total_buy_amount"] for stats in hm_stats.values()),
            "total_sell_amount": sum(stats["total_sell_amount"] for stats in hm_stats.values()),
            "total_net_buy": sum(stats["total_net_buy"] for stats in hm_stats.values()),
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
        return {
            "success": True,
            "data": {
                "hm_summary": hm_summary,
                "overall_stats": overall_stats,
                "query_params": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "top_n": top_n
                },
                "count": len(hm_summary),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取游资龙虎榜汇总统计失败: {str(e)}")
