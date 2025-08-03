#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复每日收益计算问题

问题分析：
1. 用户有持仓数据但没有交易记录（手动插入的真实数据）
2. 系统的每日收益计算依赖于账户快照数据
3. 需要确保定时任务正常运行，更新持仓价格和每日收益
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.simulation.database import simulation_db
from api.simulation.service import simulation_service
from api.simulation.scheduler import simulation_scheduler
from api.db_handler import DBHandler, get_db_handler

# 创建数据库处理器实例
db_handler = get_db_handler()

async def main():
    print("=== 修复每日收益计算问题 ===")
    
    # 测试用户ID
    user_id = "946c1533-e852-45ca-abe2-54b9864b63b8"
    
    print(f"\n1. 检查用户 {user_id} 的账户信息...")
    account = simulation_db.get_simulation_account(user_id)
    if account:
        print(f"   账户状态: {account.get('status')}")
        print(f"   总资产: {account.get('total_assets', 0):,.2f}")
        print(f"   可用资金: {account.get('available_cash', 0):,.2f}")
        print(f"   持仓市值: {account.get('total_market_value', 0):,.2f}")
        print(f"   日收益: {account.get('daily_return', 0):,.2f}")
        print(f"   日收益率: {account.get('daily_return_rate', 0):.4f}")
    else:
        print("   ❌ 账户不存在")
        return
    
    print(f"\n2. 检查用户持仓数据...")
    positions = simulation_db.get_user_positions(user_id)
    print(f"   持仓数量: {len(positions)}")
    for pos in positions:
        print(f"   - {pos['stock_name']} ({pos['stock_code']}): {pos['total_quantity']}股, 成本价: {pos['avg_cost']:.2f}, 当前价: {pos.get('current_price', 0):.2f}")
    
    print(f"\n3. 检查账户快照数据...")
    snapshots_col = db_handler.get_collection(simulation_db.SNAPSHOTS_COLLECTION)
    snapshots = list(snapshots_col.find({"user_id": user_id}).sort("snapshot_date", -1).limit(5))
    print(f"   快照数量: {len(snapshots)}")
    for snapshot in snapshots:
        snapshot_date = snapshot['snapshot_date']
        if isinstance(snapshot_date, datetime):
            date_str = snapshot_date.strftime('%Y-%m-%d')
        else:
            date_str = str(snapshot_date)
        print(f"   - {date_str}: 总资产 {snapshot['total_assets']:,.2f}")
    
    print(f"\n4. 手动更新持仓价格...")
    try:
        await simulation_scheduler.update_position_prices()
        print("   ✅ 持仓价格更新完成")
    except Exception as e:
        print(f"   ❌ 持仓价格更新失败: {e}")
    
    print(f"\n5. 手动更新账户资产...")
    try:
        await simulation_service._update_account_assets(user_id)
        print("   ✅ 账户资产更新完成")
    except Exception as e:
        print(f"   ❌ 账户资产更新失败: {e}")
    
    print(f"\n6. 创建今日快照...")
    try:
        await simulation_service.create_daily_snapshot(user_id)
        print("   ✅ 今日快照创建完成")
    except Exception as e:
        print(f"   ❌ 今日快照创建失败: {e}")
    
    print(f"\n7. 手动更新每日收益...")
    try:
        await simulation_scheduler.update_daily_returns()
        print("   ✅ 每日收益更新完成")
    except Exception as e:
        print(f"   ❌ 每日收益更新失败: {e}")
    
    print(f"\n8. 检查更新后的账户信息...")
    account = simulation_db.get_simulation_account(user_id)
    if account:
        print(f"   总资产: {account.get('total_assets', 0):,.2f}")
        print(f"   持仓市值: {account.get('total_market_value', 0):,.2f}")
        print(f"   日收益: {account.get('daily_return', 0):,.2f}")
        print(f"   日收益率: {account.get('daily_return_rate', 0):.4f}")
        print(f"   总收益: {account.get('total_return', 0):,.2f}")
        print(f"   总收益率: {account.get('total_return_rate', 0):.4f}")
    
    print(f"\n9. 检查更新后的持仓数据...")
    positions = simulation_db.get_user_positions(user_id)
    total_market_value = 0
    for pos in positions:
        market_value = pos.get('market_value', 0)
        total_market_value += market_value
        unrealized_pnl = pos.get('unrealized_pnl', 0)
        unrealized_pnl_rate = pos.get('unrealized_pnl_rate', 0)
        print(f"   - {pos['stock_name']} ({pos['stock_code']}):")
        print(f"     持仓: {pos['total_quantity']}股, 成本价: {pos['avg_cost']:.2f}, 当前价: {pos.get('current_price', 0):.2f}")
        print(f"     市值: {market_value:,.2f}, 盈亏: {unrealized_pnl:,.2f} ({unrealized_pnl_rate:.2%})")
    
    print(f"\n   计算的总市值: {total_market_value:,.2f}")
    
    print(f"\n10. 检查最新快照数据...")
    snapshots = list(snapshots_col.find({"user_id": user_id}).sort("snapshot_date", -1).limit(3))
    print(f"    最新快照数量: {len(snapshots)}")
    for snapshot in snapshots:
        snapshot_date = snapshot['snapshot_date']
        if isinstance(snapshot_date, datetime):
            date_str = snapshot_date.strftime('%Y-%m-%d')
        else:
            date_str = str(snapshot_date)
        print(f"    - {date_str}: 总资产 {snapshot['total_assets']:,.2f}")
    
    print("\n=== 修复完成 ===")
    print("\n总结:")
    print("1. 系统确实有定时任务来更新每日收益")
    print("2. 每日收益计算依赖于账户快照数据")
    print("3. 即使没有交易记录，系统也会基于持仓数据和最新价格计算收益")
    print("4. 建议设置定时任务定期运行这些更新操作")

if __name__ == "__main__":
    asyncio.run(main())