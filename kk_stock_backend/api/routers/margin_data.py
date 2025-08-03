#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融资融券API接口
支持融资融券汇总、明细数据查询
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


@router.get("/summary")
async def get_margin_summary(
    trade_date: Optional[str] = Query(default=None, description="交易日期 YYYYMMDD"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取融资融券汇总数据
    """
    try:
        collection = db_handler.get_collection('margin')
        
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
                "margin_summary": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取融资融券汇总失败: {str(e)}")

@router.get("/detail/{ts_code}")
async def get_margin_detail(
    ts_code: str,
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYYMMDD"),
    limit: int = Query(default=100, description="返回条数")
):
    """
    获取个股融资融券明细
    """
    try:
        collection = db_handler.get_collection('margin_detail')
        
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
                "margin_detail": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取个股融资融券明细失败: {str(e)}")