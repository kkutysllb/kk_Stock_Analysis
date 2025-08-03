#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图表数据修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.db_handler import DBHandler
from datetime import datetime

def test_chart_fix():
    """测试图表数据修复"""
    try:
        # 初始化数据库连接
        db_handler = DBHandler()
        collection = db_handler.get_collection('stock_money_flow')
        
        print("=== 测试图表数据修复 ===")
        print(f"数据库连接: 成功")
        
        # 获取最近5个交易日期
        all_dates = collection.distinct('trade_date')
        all_dates.sort(reverse=True)
        recent_dates = all_dates[:5]
        
        print(f"\n测试日期: {recent_dates}")
        
        # 模拟修复后的分析接口历史数据查询逻辑
        historical_data = []
        
        for date in recent_dates:
            daily_cursor = collection.find(
                {"trade_date": date},
                {"_id": 0, "trade_date": 1, "net_amount": 1, "net_mf_amount": 1}
            )
            daily_data = list(daily_cursor)
            
            if daily_data:
                # 兼容两种字段名：net_amount 和 net_mf_amount
                daily_inflow = 0
                daily_outflow = 0
                for item in daily_data:
                    net_value = item.get("net_amount", 0) or item.get("net_mf_amount", 0)
                    if net_value > 0:
                        daily_inflow += net_value
                    elif net_value < 0:
                        daily_outflow += abs(net_value)
                
                historical_data.append({
                    "trade_date": date,
                    "net_inflow": daily_inflow,
                    "net_outflow": daily_outflow,
                    "net_amount": daily_inflow - daily_outflow,
                    "data_count": len(daily_data)
                })
                
                print(f"日期 {date}: 流入={daily_inflow:,.2f}, 流出={daily_outflow:,.2f}, 净额={daily_inflow - daily_outflow:,.2f}, 数据量={len(daily_data)}")
            else:
                print(f"日期 {date}: 无数据")
        
        print(f"\n=== 修复后历史数据汇总 ===")
        for data in historical_data:
            print(f"{data['trade_date']}: 净流入={data['net_inflow']:,.2f}, 净流出={data['net_outflow']:,.2f}, 净额={data['net_amount']:,.2f}")
        
        # 检查是否所有日期都有数据
        zero_data_dates = [data['trade_date'] for data in historical_data if data['net_inflow'] == 0 and data['net_outflow'] == 0]
        
        if zero_data_dates:
            print(f"\n⚠️  仍有零数据的日期: {zero_data_dates}")
        else:
            print(f"\n✅ 所有日期都有正常的资金流向数据！")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_chart_fix()