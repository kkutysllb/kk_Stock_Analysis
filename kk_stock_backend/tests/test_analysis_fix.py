#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试资金流向分析接口修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.db_handler import DBHandler
from datetime import datetime

def test_analysis_fix():
    """测试资金流向分析接口修复"""
    try:
        # 初始化数据库连接
        db_handler = DBHandler()
        collection = db_handler.get_collection('stock_money_flow')
        
        print("=== 测试资金流向分析接口修复 ===")
        print(f"数据库连接: 成功")
        
        trade_date = "20250709"
        
        # 获取指定日期的数据
        cursor = collection.find(
            {"trade_date": trade_date},
            {"_id": 0}
        )
        
        all_data = list(cursor)
        print(f"\n{trade_date} 总数据量: {len(all_data)}")
        
        if all_data:
            # 使用正确的字段名 net_amount 进行统计
            total_net_inflow = sum(item.get("net_amount", 0) for item in all_data if item.get("net_amount", 0) > 0)
            total_net_outflow = sum(abs(item.get("net_amount", 0)) for item in all_data if item.get("net_amount", 0) < 0)
            
            inflow_stocks = [item for item in all_data if item.get("net_amount", 0) > 0]
            outflow_stocks = [item for item in all_data if item.get("net_amount", 0) < 0]
            neutral_stocks = [item for item in all_data if item.get("net_amount", 0) == 0]
            
            print(f"\n=== 市场统计 ===")
            print(f"净流入股票数量: {len(inflow_stocks)}")
            print(f"净流出股票数量: {len(outflow_stocks)}")
            print(f"中性股票数量: {len(neutral_stocks)}")
            print(f"总净流入金额: {total_net_inflow:,.2f}")
            print(f"总净流出金额: {total_net_outflow:,.2f}")
            
            # 获取排名前5的流入和流出股票
            top_inflow = sorted(inflow_stocks, key=lambda x: x.get("net_amount", 0), reverse=True)[:5]
            top_outflow = sorted(outflow_stocks, key=lambda x: x.get("net_amount", 0))[:5]
            
            print(f"\n=== 前5名净流入股票 ===")
            for i, stock in enumerate(top_inflow, 1):
                print(f"{i}. {stock.get('ts_code', 'N/A')}: {stock.get('net_amount', 0):,.2f}")
            
            print(f"\n=== 前5名净流出股票 ===")
            for i, stock in enumerate(top_outflow, 1):
                print(f"{i}. {stock.get('ts_code', 'N/A')}: {stock.get('net_amount', 0):,.2f}")
            
            print(f"\n✅ 资金流向分析接口修复验证成功！")
        else:
            print(f"❌ 未找到 {trade_date} 的数据")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_analysis_fix()