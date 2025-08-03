#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的资金流向接口
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from api.cloud_db_handler import CloudDBHandler

def test_money_flow_query():
    """测试资金流向查询逻辑"""
    db_handler = CloudDBHandler()
    collection = db_handler.get_collection('stock_money_flow')
    
    trade_date = "20250709"
    limit = 20
    
    print("=== 测试修复后的资金流向查询 ===")
    
    # 测试资金流出查询（修复后）
    print(f"\n1. 测试资金流出查询 (trade_date={trade_date}, limit={limit})")
    
    outflow_cursor = collection.find(
        {"trade_date": trade_date, "net_amount": {"$lt": 0}},
        {"_id": 0}
    ).sort("net_amount", 1).limit(limit)
    
    outflow_results = list(outflow_cursor)
    print(f"   查询到 {len(outflow_results)} 条流出数据")
    
    if outflow_results:
        print("   前3条流出数据:")
        for i, item in enumerate(outflow_results[:3]):
            print(f"     {i+1}. {item['ts_code']} ({item.get('name', 'N/A')}): net_amount={item['net_amount']}")
    
    # 测试资金流入查询（修复后）
    print(f"\n2. 测试资金流入查询 (trade_date={trade_date}, limit={limit})")
    
    inflow_cursor = collection.find(
        {"trade_date": trade_date, "net_amount": {"$gt": 0}},
        {"_id": 0}
    ).sort("net_amount", -1).limit(limit)
    
    inflow_results = list(inflow_cursor)
    print(f"   查询到 {len(inflow_results)} 条流入数据")
    
    if inflow_results:
        print("   前3条流入数据:")
        for i, item in enumerate(inflow_results[:3]):
            print(f"     {i+1}. {item['ts_code']} ({item.get('name', 'N/A')}): net_amount={item['net_amount']}")
    
    # 统计数据分布
    print(f"\n3. 数据分布统计 (trade_date={trade_date})")
    
    total_count = collection.count_documents({"trade_date": trade_date})
    outflow_count = collection.count_documents({"trade_date": trade_date, "net_amount": {"$lt": 0}})
    inflow_count = collection.count_documents({"trade_date": trade_date, "net_amount": {"$gt": 0}})
    zero_count = collection.count_documents({"trade_date": trade_date, "net_amount": 0})
    
    print(f"   总数据量: {total_count}")
    print(f"   净流出数量: {outflow_count} ({outflow_count/total_count*100:.1f}%)")
    print(f"   净流入数量: {inflow_count} ({inflow_count/total_count*100:.1f}%)")
    print(f"   零流量数量: {zero_count} ({zero_count/total_count*100:.1f}%)")
    
    return outflow_results, inflow_results

if __name__ == "__main__":
    test_money_flow_query()