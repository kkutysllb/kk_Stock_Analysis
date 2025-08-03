#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建历史账户快照数据，以便计算每日收益
"""

import sys
import os
import asyncio
from datetime import date, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.simulation.service import simulation_service
from api.db_handler import get_db_handler

async def create_historical_snapshots():
    """为所有用户创建最近几天的历史快照数据"""
    print("开始创建历史账户快照...")
    
    db_handler = get_db_handler()
    
    # 获取所有模拟账户用户
    accounts_col = db_handler.get_collection("simulation_accounts")
    accounts = list(accounts_col.find({"status": 1}))
    
    # 创建最近7天的快照
    today = date.today()
    dates_to_create = [today - timedelta(days=i) for i in range(7)]
    
    print(f"将为 {len(accounts)} 个账户创建 {len(dates_to_create)} 天的快照")
    
    for account in accounts:
        user_id = account["user_id"]
        print(f"处理用户: {user_id}")
        
        # 获取当前账户信息作为基准
        current_account = await simulation_service.get_account_info(user_id)
        if not current_account:
            print(f"  跳过：无法获取账户信息")
            continue
            
        for snapshot_date in dates_to_create:
            try:
                # 为了模拟历史数据，我们稍微调整总资产
                # 这样可以计算出有意义的每日收益
                days_ago = (today - snapshot_date).days
                
                # 创建历史快照（稍微调整总资产）
                historical_account = current_account.copy()
                if days_ago > 0:
                    # 模拟轻微的资产变化
                    variation_factor = 1 + (days_ago * 0.001)  # 每天0.1%的变化
                    historical_account["total_assets"] = current_account["total_assets"] / variation_factor
                    historical_account["total_return"] = historical_account["total_assets"] - current_account.get("initial_capital", 3000000)
                    historical_account["total_return_rate"] = historical_account["total_return"] / current_account.get("initial_capital", 3000000)
                
                # 创建快照
                simulation_service.db.create_account_snapshot(user_id, snapshot_date, historical_account)
                print(f"  创建快照: {snapshot_date} - 资产: ¥{historical_account['total_assets']:,.2f}")
                
            except Exception as e:
                print(f"  创建快照失败 {snapshot_date}: {e}")
    
    print("历史快照创建完成!")

if __name__ == "__main__":
    asyncio.run(create_historical_snapshots())