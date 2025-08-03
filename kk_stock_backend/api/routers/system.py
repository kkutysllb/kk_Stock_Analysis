#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统API接口
支持健康检查、性能监控等功能
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import time

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


@cache_endpoint(data_type='system_health', ttl=300)  # 缓存5分钟
@router.get("/health")
async def health_check():
    """
    系统健康检查
    """
    try:
        start_time = time.time()
        
        # 检查数据库连接
        collection = db_handler.get_collection('stock_basic')
        db_status = collection.find_one({}, {"_id": 1}) is not None
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "database": "connected" if db_status else "disconnected",
                "response_time_ms": response_time,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "data": {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        }

@cache_endpoint(data_type='system_metrics', ttl=600)  # 缓存10分钟
@router.get("/metrics")
async def get_system_metrics():
    """
    获取系统性能指标
    """
    try:
        # 获取数据库统计
        stats = {}
        for collection_name in ['stock_basic', 'daily', 'weekly', 'monthly']:
            try:
                collection = db_handler.get_collection(collection_name)
                count = collection.count_documents({})
                stats[collection_name] = count
            except:
                stats[collection_name] = 0
        
        return {
            "success": True,
            "data": {
                "database_stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")

@cache_endpoint(data_type='system_status', ttl=300)  # 缓存5分钟
@router.get("/status")
async def get_system_status():
    """
    获取系统运行状态
    """
    try:
        return {
            "success": True,
            "data": {
                "status": "running",
                "uptime": "unknown",
                "services": {
                    "api": "running",
                    "database": "connected"
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")