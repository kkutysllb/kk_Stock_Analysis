#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试交易日历逻辑
"""

import sys
import os
from datetime import date, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.cloud_db_handler import CloudDBHandler

def get_previous_trading_date(db_handler, current_date: date) -> date:
    """获取指定日期的上一个交易日"""
    try:
        trading_calendar_col = db_handler.get_collection("infrastructure_trading_calendar")
        current_date_str = current_date.strftime("%Y%m%d")
        
        # 查找当前日期或之前最近的交易日
        trading_record = trading_calendar_col.find_one({
            "cal_date": {"$lte": current_date_str},
            "exchange": "SSE",
            "is_open": 1
        }, sort=[("cal_date", -1)])
        
        if trading_record and "pretrade_date" in trading_record:
            pretrade_date_str = trading_record["pretrade_date"]
            print(f"找到交易记录: {trading_record}")
            # 解析pretrade_date: "20240726" -> date(2024, 7, 26)
            year = int(pretrade_date_str[:4])
            month = int(pretrade_date_str[4:6])
            day = int(pretrade_date_str[6:8])
            return date(year, month, day)
        else:
            # 如果没有找到，回退到自然日计算（减1天）
            print(f"未找到 {current_date} 的交易日信息，使用自然日计算")
            return current_date - timedelta(days=1)
            
    except Exception as e:
        print(f"获取上一交易日失败: {e}")
        # 出错时回退到自然日计算
        return current_date - timedelta(days=1)

def test_trading_calendar():
    """测试交易日历功能"""
    db_handler = CloudDBHandler()
    
    # 测试几个日期
    test_dates = [
        date(2024, 7, 26),  # 周五
        date(2024, 7, 27),  # 周六（应该回到周五）
        date(2024, 7, 28),  # 周日（应该回到周五）
        date(2024, 7, 29),  # 周一
        date.today()        # 今天
    ]
    
    for test_date in test_dates:
        prev_trading_date = get_previous_trading_date(db_handler, test_date)
        print(f"日期: {test_date} ({test_date.strftime('%A')}) => 上一交易日: {prev_trading_date} ({prev_trading_date.strftime('%A')})")
        print("-" * 60)

if __name__ == "__main__":
    test_trading_calendar()