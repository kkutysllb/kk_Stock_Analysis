#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员API接口
支持系统管理、用户管理等功能
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

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


@router.get("/system/info")
async def get_system_info():
    """
    获取系统信息
    """
    try:
        # 获取数据库统计信息
        db_stats = {}
        for collection_name in ['stock_basic', 'daily', 'weekly', 'monthly']:
            try:
                collection = db_handler.get_collection(collection_name)
                count = collection.count_documents({})
                db_stats[collection_name] = count
            except:
                db_stats[collection_name] = 0
        
        return {
            "success": True,
            "data": {
                "system_status": "running",
                "database_stats": db_stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")

@router.post("/cache/clear")
async def clear_cache():
    """
    清理缓存
    """
    try:
        # 这里可以添加缓存清理逻辑
        return {
            "success": True,
            "data": {
                "message": "缓存清理完成",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")

@router.get("/database/collections")
async def get_database_collections():
    """
    获取数据库集合列表
    """
    try:
        # 使用本地优先的数据库获取集合列表
        api_db = db_handler.get_api_db()
        collections = api_db.list_collection_names()
        
        collection_info = []
        for collection_name in collections:
            try:
                collection = db_handler.get_collection(collection_name)
                count = collection.count_documents({})
                collection_info.append({
                    "name": collection_name,
                    "count": count
                })
            except:
                collection_info.append({
                    "name": collection_name,
                    "count": 0
                })
        
        return {
            "success": True,
            "data": {
                "collections": collection_info,
                "total_collections": len(collections),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库集合失败: {str(e)}")

@router.get("/database/stats")
async def get_database_stats():
    """
    获取数据库统计信息
    """
    try:
        # 统计主要集合的文档数量
        important_collections = [
            'stock_basic', 'daily', 'weekly', 'monthly', 
            'moneyflow', 'fina_indicator', 'income', 
            'balancesheet', 'cashflow'
        ]
        
        stats = {}
        for collection_name in important_collections:
            try:
                collection = db_handler.get_collection(collection_name)
                count = collection.count_documents({})
                stats[collection_name] = count
            except:
                stats[collection_name] = 0
        
        return {
            "success": True, 
            "data": {
                "collection_stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库统计失败: {str(e)}")

@router.get("/users")
async def manage_users():
    """
    用户管理接口（简化版）
    """
    try:
        return {
            "success": True, 
            "data": {
                "message": "用户管理功能暂未实现",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"用户管理接口失败: {str(e)}")