#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙虎榜API接口
支持龙虎榜统计、机构交易数据查询
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
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


@router.get("/stats")
async def get_dragon_tiger_stats(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取龙虎榜统计数据
    """
    try:
        collection = db_handler.get_collection('top_list')
        
        # 构建查询条件
        query = {}
        if trade_date:
            query["trade_date"] = trade_date
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("trade_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "dragon_tiger_stats": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取龙虎榜统计失败: {str(e)}")

@router.get("/institutions")
async def get_institution_trades(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    limit: int = Query(default=50, description="返回条数")
):
    """
    获取机构交易数据
    """
    try:
        collection = db_handler.get_collection('top_inst')
        
        # 构建查询条件
        query = {}
        if trade_date:
            query["trade_date"] = trade_date
        
        cursor = collection.find(
            query,
            {"_id": 0}
        ).sort("trade_date", -1).limit(limit)
        
        results = list(cursor)
        
        return {
            "success": True,
            "data": {
                "institution_trades": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取机构交易数据失败: {str(e)}")