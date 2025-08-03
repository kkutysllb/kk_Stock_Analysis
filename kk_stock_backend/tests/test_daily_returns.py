#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试每日收益更新
"""

import sys
import os
import asyncio
from datetime import date

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.simulation.scheduler import SimulationScheduler
from api.db_handler import get_db_handler

async def test_daily_returns_update():
    """测试每日收益更新"""
    print("开始测试每日收益更新...")
    
    # 创建调度器实例
    scheduler = SimulationScheduler()
    
    # 测试获取交易日功能
    today = date.today()
    latest_trading_date, prev_trading_date = scheduler.get_latest_trading_date_and_previous(today)
    print(f"今日: {today}, 最近交易日: {latest_trading_date}, 上一交易日: {prev_trading_date}")
    print(f"每日收益计算: {latest_trading_date} vs {prev_trading_date}")
    
    # 手动运行每日收益更新
    await scheduler.update_daily_returns()
    
    print("每日收益更新测试完成!")

if __name__ == "__main__":
    asyncio.run(test_daily_returns_update())