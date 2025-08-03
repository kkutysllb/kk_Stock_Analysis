#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为管理员用户创建默认股票池
"""

import sys
import os
from datetime import datetime
from bson import ObjectId

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.cloud_db_handler import CloudDBHandler

def create_default_stock_pools():
    """为超级管理员创建默认股票池"""
    db_handler = CloudDBHandler()
    
    # 超级管理员用户ID
    admin_user_id = "946c1533-e852-45ca-abe2-54b9864b63b8"
    
    # 检查是否已有股票池
    stock_pools_collection = db_handler.db["user_stock_pools"]
    existing_pools = list(stock_pools_collection.find({"user_id": admin_user_id}))
    
    if existing_pools:
        print(f"用户 {admin_user_id} 已有 {len(existing_pools)} 个股票池：")
        for pool in existing_pools:
            print(f"  - {pool['pool_name']} ({len(pool.get('stocks', []))}只股票)")
        return
    
    # 创建默认股票池数据
    default_pools = [
        {
            "user_id": admin_user_id,
            "pool_name": "我的自选股",
            "description": "个人精选股票池",
            "pool_type": "default",
            "is_default": True,
            "is_public": False,
            "is_deletable": False,
            "share_code": None,
            "tags": ["自选股", "默认"],
            "stocks": [
                {
                    "ts_code": "300750.SZ",
                    "name": "宁德时代",
                    "industry": "电气设备",
                    "market": "深圳",
                    "add_time": datetime.utcnow(),
                    "add_reason": "新能源龙头股",
                    "tags": ["新能源", "电池", "龙头股"]
                },
                {
                    "ts_code": "002594.SZ",
                    "name": "比亚迪",
                    "industry": "汽车整车",
                    "market": "深圳",
                    "add_time": datetime.utcnow(),
                    "add_reason": "新能源汽车领军企业",
                    "tags": ["新能源", "汽车", "龙头股"]
                },
                {
                    "ts_code": "600519.SH",
                    "name": "贵州茅台",
                    "industry": "酿酒行业",
                    "market": "上海",
                    "add_time": datetime.utcnow(),
                    "add_reason": "白酒行业龙头",
                    "tags": ["白酒", "消费", "蓝筹股"]
                }
            ],
            "create_time": datetime.utcnow(),
            "update_time": datetime.utcnow()
        },
        {
            "user_id": admin_user_id,
            "pool_name": "科技成长股",
            "description": "科技行业高成长股票",
            "pool_type": "custom",
            "is_default": False,
            "is_public": False,
            "is_deletable": True,
            "share_code": None,
            "tags": ["科技股", "成长股"],
            "stocks": [
                {
                    "ts_code": "002415.SZ",
                    "name": "海康威视",
                    "industry": "电子",
                    "market": "深圳",
                    "add_time": datetime.utcnow(),
                    "add_reason": "安防监控行业龙头",
                    "tags": ["安防", "电子", "科技"]
                },
                {
                    "ts_code": "300059.SZ",
                    "name": "东方财富",
                    "industry": "软件服务",
                    "market": "深圳",
                    "add_time": datetime.utcnow(),
                    "add_reason": "金融科技平台",
                    "tags": ["金融科技", "软件", "互联网"]
                }
            ],
            "create_time": datetime.utcnow(),
            "update_time": datetime.utcnow()
        },
        {
            "user_id": admin_user_id,
            "pool_name": "蓝筹价值股",
            "description": "稳健的蓝筹价值股票",
            "pool_type": "custom",
            "is_default": False,
            "is_public": True,
            "is_deletable": True,
            "share_code": "ABC12345",
            "tags": ["蓝筹股", "价值股", "稳健"],
            "stocks": [
                {
                    "ts_code": "600036.SH",
                    "name": "招商银行",
                    "industry": "银行",
                    "market": "上海",
                    "add_time": datetime.utcnow(),
                    "add_reason": "优质银行股",
                    "tags": ["银行", "金融", "蓝筹股"]
                },
                {
                    "ts_code": "000858.SZ",
                    "name": "五粮液",
                    "industry": "酿酒行业",
                    "market": "深圳",
                    "add_time": datetime.utcnow(),
                    "add_reason": "白酒行业优质企业",
                    "tags": ["白酒", "消费", "蓝筹股"]
                }
            ],
            "create_time": datetime.utcnow(),
            "update_time": datetime.utcnow()
        }
    ]
    
    # 插入股票池数据
    inserted_pools = []
    for pool_data in default_pools:
        result = stock_pools_collection.insert_one(pool_data)
        pool_data["_id"] = result.inserted_id
        inserted_pools.append(pool_data)
        print(f"✓ 创建股票池: {pool_data['pool_name']} ({len(pool_data['stocks'])}只股票)")
    
    print(f"\n成功为用户 {admin_user_id} 创建了 {len(inserted_pools)} 个股票池")
    
    return inserted_pools

if __name__ == "__main__":
    create_default_stock_pools()