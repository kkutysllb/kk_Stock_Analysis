#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试情绪分析接口资金流计算修复
验证兼容net_amount和net_mf_amount字段的修复是否正确
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
sys.path.append(project_root)

# 添加api目录到路径
api_dir = os.path.join(project_root, 'api')
sys.path.append(api_dir)

from db_handler import DBHandler

def test_sentiment_money_flow_calculation():
    """
    测试情绪分析中的资金流计算
    """
    try:
        # 初始化数据库连接
        db_handler = DBHandler()
        print("数据库连接成功")
        
        # 测试日期范围
        end_date = "20250709"
        start_date = "20250703"  # 测试最近一周
        
        print(f"\n测试日期范围: {start_date} - {end_date}")
        
        # 获取资金流向数据集合
        money_flow_collection = db_handler.get_collection('stock_money_flow')
        
        # 模拟情绪分析接口的资金流计算逻辑
        pipeline = [
            {
                "$match": {
                    "trade_date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$trade_date",
                    "total_net_amount": {
                        "$sum": {
                            "$ifNull": ["$net_amount", "$net_mf_amount"]
                        }
                    },
                    "total_main_net": {
                        "$sum": {
                            "$add": [
                                {"$subtract": ["$buy_lg_amount", "$sell_lg_amount"]},
                                {"$subtract": ["$buy_elg_amount", "$sell_elg_amount"]}
                            ]
                        }
                    },
                    "data_count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        daily_flow = list(money_flow_collection.aggregate(pipeline))
        
        print(f"\n找到 {len(daily_flow)} 个交易日的数据:")
        
        flow_values = []
        for flow in daily_flow:
            trade_date = flow["_id"]
            total_net = flow.get("total_net_amount", 0)
            main_net = flow.get("total_main_net", 0)
            data_count = flow.get("data_count", 0)
            
            # 主力资金净流入(千元转亿元)
            main_net_flow = main_net / 100000
            flow_values.append(main_net_flow)
            
            print(f"  {trade_date}: 总净流入={total_net/100000:.1f}亿, 主力净流入={main_net_flow:.1f}亿, 数据量={data_count}")
        
        if flow_values:
            # 计算指标
            current_value = round(sum(flow_values) / len(flow_values), 1)
            period_end_value = round(flow_values[-1], 1)
            period_start_value = round(flow_values[0], 1)
            change = round(period_end_value - period_start_value, 1)
            
            # 判断情绪等级
            if current_value > 100:
                level = "bullish"
            elif current_value < -100:
                level = "bearish"
            else:
                level = "neutral"
            
            print(f"\n情绪指标计算结果:")
            print(f"  期初值: {period_start_value}亿")
            print(f"  期末值: {period_end_value}亿")
            print(f"  平均值: {current_value}亿")
            print(f"  变化: {change}亿")
            print(f"  情绪等级: {level}")
        else:
            print("\n未找到有效的资金流数据")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sentiment_money_flow_calculation()