#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建昨天的账户快照，用于测试每日收益计算
"""

import sys
import os
import asyncio
from datetime import date, datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.db_handler import get_db_handler
from api.simulation.service import simulation_service

async def create_yesterday_snapshot():
    """创建昨天的账户快照（基于股票的历史价格）"""
    print("创建昨天的账户快照...")
    
    db_handler = get_db_handler()
    
    # 计算昨天日期（找最近的交易日）
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 从交易日历找到最近的交易日
    from api.simulation.scheduler import SimulationScheduler
    scheduler = SimulationScheduler()
    latest_trading_date, previous_trading_date = scheduler.get_latest_trading_date_and_previous(today)
    
    print(f"今日: {today}")
    print(f"最近交易日: {latest_trading_date}")
    print(f"上一交易日: {previous_trading_date}")
    
    # 使用上一交易日作为"昨天"
    target_date = previous_trading_date
    
    # 获取所有模拟账户
    accounts_col = db_handler.get_collection("simulation_accounts")
    accounts = list(accounts_col.find({"status": 1}))
    
    success_count = 0
    
    for account in accounts:
        try:
            user_id = account["user_id"]
            print(f"\n处理用户: {user_id}")
            
            # 获取用户当前持仓
            positions_col = db_handler.get_collection("simulation_positions")
            positions = list(positions_col.find({"user_id": user_id}))
            
            if not positions:
                print(f"  用户无持仓，使用现金账户数据")
                # 无持仓用户，直接使用当前账户数据
                current_account = await simulation_service.get_account_info(user_id)
                if current_account:
                    simulation_service.db.create_account_snapshot(user_id, target_date, current_account)
                    success_count += 1
                continue
            
            # 计算昨天的持仓市值（基于股票历史价格）
            total_yesterday_market_value = 0
            
            stock_kline_col = db_handler.get_collection("stock_kline_daily")
            
            for position in positions:
                stock_code = position["stock_code"]
                quantity = position["total_quantity"]
                
                # 查找股票在目标日期的收盘价
                target_date_str = target_date.strftime("%Y%m%d")
                
                # 尝试找到目标日期的K线数据
                kline_data = stock_kline_col.find_one({
                    "ts_code": stock_code,
                    "trade_date": target_date_str
                })
                
                if kline_data:
                    yesterday_price = kline_data["close"]
                    position_value = quantity * yesterday_price
                    total_yesterday_market_value += position_value
                    print(f"  {stock_code}: {quantity}股 × ¥{yesterday_price:.2f} = ¥{position_value:,.2f}")
                else:
                    # 如果找不到历史数据，使用当前价格
                    current_price = position.get("current_price", 0)
                    position_value = quantity * current_price
                    total_yesterday_market_value += position_value
                    print(f"  {stock_code}: 无历史数据，使用当前价格 ¥{current_price:.2f}")
            
            # 构建昨天的账户数据
            current_account = await simulation_service.get_account_info(user_id)
            if current_account:
                yesterday_account = current_account.copy()
                
                # 更新昨天的市值数据
                yesterday_account["total_market_value"] = total_yesterday_market_value
                yesterday_account["total_assets"] = yesterday_account["available_cash"] + total_yesterday_market_value
                
                # 重新计算总收益
                initial_capital = yesterday_account.get("initial_capital", 3000000)
                yesterday_account["total_return"] = yesterday_account["total_assets"] - initial_capital
                yesterday_account["total_return_rate"] = yesterday_account["total_return"] / initial_capital if initial_capital > 0 else 0
                
                print(f"  昨日总资产: ¥{yesterday_account['total_assets']:,.2f}")
                print(f"  昨日市值: ¥{total_yesterday_market_value:,.2f}")
                
                # 创建昨天的快照
                simulation_service.db.create_account_snapshot(user_id, target_date, yesterday_account)
                success_count += 1
                
        except Exception as e:
            print(f"  处理失败: {e}")
    
    print(f"\n昨日快照创建完成: {success_count}/{len(accounts)}")
    
    # 现在运行每日收益更新
    print("\n运行每日收益更新...")
    await scheduler.update_daily_returns()
    
    print("\n每日收益计算完成！现在前端应该显示正确的日收益数据。")

if __name__ == "__main__":
    asyncio.run(create_yesterday_snapshot())