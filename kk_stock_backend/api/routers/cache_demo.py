#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存演示路由
展示如何在API路由中使用Redis缓存
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(api_dir)
sys.path.insert(0, project_root)

from cache_manager import get_cache_manager
from cache_config import get_ttl_for_data_type, get_cache_key_prefix
from api.cache_middleware import cache_endpoint
from api.global_db import db_handler

router = APIRouter()


# 缓存依赖函数
def get_cache():
    """获取缓存管理器依赖"""
    return get_cache_manager()

@router.get("/cached-stock-list")
@cache_endpoint(data_type='stock_list', ttl=1800)  # 30分钟缓存
async def get_cached_stock_list(
    market: Optional[str] = Query(default=None, description="市场类型"),
    limit: int = Query(default=50, description="返回数量限制")
):
    """
    获取股票列表（带缓存）
    演示使用装饰器进行缓存
    """
    try:
        collection = db_handler.get_collection('stock_basic')
        
        # 构建查询条件
        query = {"list_status": "L"}  # 只查询上市股票
        if market:
            query["market"] = market
        
        # 查询数据
        cursor = collection.find(query, {"_id": 0}).limit(limit)
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "market": market,
                "count": len(results),
                "stocks": results,
                "cached": True,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")

@router.get("/manual-cache-demo")
async def manual_cache_demo(
    symbol: str = Query(..., description="股票代码"),
    cache_manager = Depends(get_cache)
):
    """
    手动缓存演示
    展示如何手动控制缓存逻辑
    """
    try:
        # 生成缓存键
        cache_key = f"stock:detail:{symbol}"
        
        # 尝试从缓存获取
        cached_data = None
        if cache_manager and cache_manager.is_available():
            cached_data = await cache_manager.async_get(cache_key)
            
        if cached_data:
            # 缓存命中
            return {
                "success": True,
                "data": cached_data,
                "cache_hit": True,
                "timestamp": datetime.now().isoformat()
            }
        
        # 缓存未命中，从数据库查询
        collection = db_handler.get_collection('stock_basic')
        stock_info = collection.find_one({"ts_code": symbol}, {"_id": 0})
        
        if not stock_info:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 获取最新行情
        daily_collection = db_handler.get_collection('stock_daily')
        latest_daily = daily_collection.find_one(
            {"ts_code": symbol},
            {"_id": 0},
            sort=[("trade_date", -1)]
        )
        
        # 组合数据
        result_data = {
            "basic_info": stock_info,
            "latest_quote": latest_daily,
            "query_time": datetime.now().isoformat()
        }
        
        # 存储到缓存
        if cache_manager and cache_manager.is_available():
            ttl = get_ttl_for_data_type('stock_basic')
            await cache_manager.async_set(cache_key, result_data, ttl)
        
        return {
            "success": True,
            "data": result_data,
            "cache_hit": False,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.get("/cache-stats")
async def get_cache_stats(cache_manager = Depends(get_cache)):
    """
    获取缓存统计信息
    """
    try:
        if not cache_manager:
            return {
                "success": False,
                "message": "缓存未启用",
                "timestamp": datetime.now().isoformat()
            }
        
        stats = cache_manager.get_stats()
        
        return {
            "success": True,
            "data": {
                "cache_stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")

@router.delete("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(default=None, description="清除模式，如 stock:*"),
    cache_manager = Depends(get_cache)
):
    """
    清除缓存
    """
    try:
        if not cache_manager:
            return {
                "success": False,
                "message": "缓存未启用",
                "timestamp": datetime.now().isoformat()
            }
        
        if pattern:
            # 清除匹配模式的缓存
            deleted_count = cache_manager.clear_pattern(f"*{pattern}*")
            message = f"已清除 {deleted_count} 个匹配 '{pattern}' 的缓存项"
        else:
            # 清除所有API缓存
            deleted_count = cache_manager.clear_pattern("stock_api:*")
            message = f"已清除 {deleted_count} 个API缓存项"
        
        return {
            "success": True,
            "data": {
                "deleted_count": deleted_count,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")

@router.get("/performance-test")
async def performance_test(
    iterations: int = Query(default=10, description="测试迭代次数"),
    use_cache: bool = Query(default=True, description="是否使用缓存"),
    cache_manager = Depends(get_cache)
):
    """
    性能测试
    比较有缓存和无缓存的查询性能
    """
    try:
        import time
        
        # 测试查询
        test_symbols = ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH', '000858.SZ']
        
        results = []
        
        for i in range(iterations):
            symbol = test_symbols[i % len(test_symbols)]
            
            start_time = time.time()
            
            if use_cache and cache_manager and cache_manager.is_available():
                # 使用缓存的查询
                cache_key = f"perf_test:{symbol}"
                cached_data = await cache_manager.async_get(cache_key)
                
                if not cached_data:
                    # 缓存未命中，查询数据库
                    collection = db_handler.get_collection('stock_basic')
                    data = collection.find_one({"ts_code": symbol}, {"_id": 0})
                    
                    if data:
                        await cache_manager.async_set(cache_key, data, 300)  # 5分钟缓存
                    
                    cache_hit = False
                else:
                    data = cached_data
                    cache_hit = True
            else:
                # 直接查询数据库
                collection = db_handler.get_collection('stock_basic')
                data = collection.find_one({"ts_code": symbol}, {"_id": 0})
                cache_hit = False
            
            end_time = time.time()
            query_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            results.append({
                "iteration": i + 1,
                "symbol": symbol,
                "query_time_ms": round(query_time, 2),
                "cache_hit": cache_hit,
                "data_found": data is not None
            })
        
        # 计算统计信息
        total_time = sum(r["query_time_ms"] for r in results)
        avg_time = total_time / len(results)
        cache_hits = sum(1 for r in results if r["cache_hit"])
        hit_rate = (cache_hits / len(results)) * 100
        
        return {
            "success": True,
            "data": {
                "test_config": {
                    "iterations": iterations,
                    "use_cache": use_cache,
                    "test_symbols": test_symbols
                },
                "results": results,
                "statistics": {
                    "total_time_ms": round(total_time, 2),
                    "average_time_ms": round(avg_time, 2),
                    "cache_hits": cache_hits,
                    "hit_rate_percent": round(hit_rate, 2)
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"性能测试失败: {str(e)}")

@router.get("/cache-warmup")
async def cache_warmup(
    data_type: str = Query(default="stock_basic", description="预热的数据类型"),
    limit: int = Query(default=100, description="预热数据数量"),
    cache_manager = Depends(get_cache)
):
    """
    缓存预热
    预先加载常用数据到缓存中
    """
    try:
        if not cache_manager or not cache_manager.is_available():
            return {
                "success": False,
                "message": "缓存未启用",
                "timestamp": datetime.now().isoformat()
            }
        
        warmed_count = 0
        
        if data_type == "stock_basic":
            # 预热股票基本信息
            collection = db_handler.get_collection('stock_basic')
            cursor = collection.find(
                {"list_status": "L"},  # 只预热上市股票
                {"_id": 0}
            ).limit(limit)
            
            for stock in cursor:
                cache_key = f"stock:basic:{stock['ts_code']}"
                ttl = get_ttl_for_data_type('stock_basic')
                await cache_manager.async_set(cache_key, stock, ttl)
                warmed_count += 1
        
        elif data_type == "market_indices":
            # 预热主要指数数据
            major_indices = [
                '000001.SH', '399001.SZ', '399006.SZ', '000688.SH', 
                '000300.SH', '000905.SH', '000852.SH'
            ]
            
            collection = db_handler.get_collection('index_daily')
            
            for ts_code in major_indices:
                latest_data = collection.find_one(
                    {"ts_code": ts_code},
                    {"_id": 0},
                    sort=[("trade_date", -1)]
                )
                
                if latest_data:
                    cache_key = f"index:latest:{ts_code}"
                    ttl = get_ttl_for_data_type('index_daily')
                    await cache_manager.async_set(cache_key, latest_data, ttl)
                    warmed_count += 1
        
        return {
            "success": True,
            "data": {
                "data_type": data_type,
                "warmed_count": warmed_count,
                "message": f"已预热 {warmed_count} 个 {data_type} 缓存项",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"缓存预热失败: {str(e)}")