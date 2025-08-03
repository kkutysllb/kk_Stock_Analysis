#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动创建今天的账户快照
解决时序逻辑错误导致的收益不更新问题
"""

import asyncio
import sys
import os
from datetime import datetime, date
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.simulation.database import simulation_db
from api.simulation.service import simulation_service
from api.simulation.scheduler import simulation_scheduler
from api.db_handler import get_db_handler

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """手动创建今天的账户快照"""
    print("=== 手动创建今天的账户快照 ===")
    
    try:
        today = date.today()
        print(f"当前日期: {today}")
        
        # 获取数据库处理器
        db_handler = get_db_handler()
        
        # 1. 先更新所有持仓的价格
        print("\n1. 更新持仓价格...")
        try:
            await simulation_scheduler.update_position_prices()
            print("   ✅ 持仓价格更新完成")
        except Exception as e:
            print(f"   ❌ 持仓价格更新失败: {e}")
            logger.exception("持仓价格更新失败")
        
        # 2. 获取所有活跃用户
        print("\n2. 获取所有活跃用户...")
        users_col = db_handler.get_collection("users")
        users = list(users_col.find({"status": 1}, {"user_id": 1}))
        print(f"   找到 {len(users)} 个活跃用户")
        
        # 3. 为每个用户创建今日快照
        print("\n3. 创建今日快照...")
        success_count = 0
        failed_users = []
        
        for user in users:
            try:
                user_id = user["user_id"]
                
                # 更新账户资产（确保最新的持仓市值计算）
                await simulation_service._update_account_assets(user_id)
                
                # 创建快照
                await simulation_service.create_daily_snapshot(user_id)
                success_count += 1
                
                # 获取账户信息验证
                account = simulation_db.get_simulation_account(user_id)
                if account:
                    print(f"   ✅ {user_id}: 总资产 {account.get('total_assets', 0):,.2f}")
                
            except Exception as e:
                failed_users.append(user_id)
                print(f"   ❌ {user_id}: 快照创建失败 - {e}")
                logger.exception(f"用户 {user_id} 快照创建失败")
        
        print(f"\n快照创建完成: 成功 {success_count}/{len(users)}")
        if failed_users:
            print(f"失败的用户: {failed_users}")
        
        # 4. 验证特定用户的快照
        print("\n4. 验证特定用户快照...")
        # 查找手机号对应的用户ID
        user_record = users_col.find_one({"phone": "+8613609247807"})
        if user_record:
            user_id = user_record["user_id"]
            print(f"   目标用户ID: {user_id}")
            
            # 检查今日快照
            snapshots_col = db_handler.get_collection(simulation_db.SNAPSHOTS_COLLECTION)
            today_datetime = datetime.combine(today, datetime.min.time())
            
            today_snapshot = snapshots_col.find_one({
                "user_id": user_id,
                "snapshot_date": today_datetime
            })
            
            if today_snapshot:
                print(f"   ✅ 今日快照创建成功:")
                print(f"      总资产: {today_snapshot['total_assets']:,.2f}")
                print(f"      持仓市值: {today_snapshot['total_market_value']:,.2f}")
                print(f"      创建时间: {today_snapshot['create_time']}")
            else:
                print("   ❌ 今日快照未找到")
        else:
            print("   ❌ 目标用户未找到")
        
        # 5. 现在可以执行日收益更新
        print("\n5. 执行每日收益更新...")
        try:
            await simulation_scheduler.update_daily_returns()
            print("   ✅ 每日收益更新完成")
            
            # 再次验证目标用户的收益
            if user_record:
                account = simulation_db.get_simulation_account(user_record["user_id"])
                if account:
                    print(f"   用户最新收益信息:")
                    print(f"      日收益: {account.get('daily_return', 0):,.2f}")
                    print(f"      日收益率: {account.get('daily_return_rate', 0):.4f}")
                    print(f"      最后更新: {account.get('last_update_time', 'N/A')}")
            
        except Exception as e:
            print(f"   ❌ 每日收益更新失败: {e}")
            logger.exception("每日收益更新失败")
        
        print("\n=== 手动快照创建完成 ===")
        print("\n📝 后续操作:")
        print("1. 定时任务已修改为每日19:00创建快照，19:30更新收益")
        print("2. 明天开始将自动按新的时间执行")
        print("3. 可以重启后端服务以确保定时任务生效")
        
    except Exception as e:
        logger.exception("手动快照创建过程中发生异常")
        print(f"操作失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())