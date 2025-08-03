#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的持仓日收益计算逻辑
基于股价变化计算真实的持仓收益
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
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

async def test_new_daily_return_calculation():
    """测试新的日收益计算逻辑"""
    print("=== 测试新的持仓日收益计算逻辑 ===")
    
    try:
        # 目标用户（手机号对应的UUID）
        db_handler = get_db_handler()
        users_col = db_handler.get_collection("users")
        user_record = users_col.find_one({"phone": "+8613609247807"})
        
        if not user_record:
            print("❌ 未找到目标用户")
            return
        
        user_id = user_record["user_id"]
        print(f"目标用户ID: {user_id}")
        
        # 1. 获取用户持仓
        print("\n1. 获取用户持仓...")
        positions = simulation_db.get_user_positions(user_id)
        print(f"   持仓数量: {len(positions)}")
        
        for pos in positions:
            print(f"   - {pos['stock_name']} ({pos['stock_code']}): {pos['total_quantity']:,}股")
        
        # 2. 手动计算日收益（使用新逻辑）
        print("\n2. 手动计算持仓日收益...")
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # 转换为数据库格式
        today_str = today.strftime("%Y%m%d")
        yesterday_str = yesterday.strftime("%Y%m%d")
        
        print(f"   今日: {today} ({today_str})")
        print(f"   昨日: {yesterday} ({yesterday_str})")
        
        total_daily_return = 0.0
        total_previous_value = 0.0
        
        for position in positions:
            stock_code = position["stock_code"]
            stock_name = position["stock_name"]
            quantity = position["total_quantity"]
            
            # 获取价格
            today_price = await simulation_service._get_stock_price_by_date(stock_code, today_str)
            yesterday_price = await simulation_service._get_stock_price_by_date(stock_code, yesterday_str)
            
            if today_price is not None and yesterday_price is not None:
                # 计算收益
                today_value = quantity * today_price
                yesterday_value = quantity * yesterday_price
                stock_return = today_value - yesterday_value
                price_change = today_price - yesterday_price
                price_change_pct = (price_change / yesterday_price * 100) if yesterday_price > 0 else 0
                
                total_daily_return += stock_return
                total_previous_value += yesterday_value
                
                print(f"   📊 {stock_name} ({stock_code}):")
                print(f"      持仓: {quantity:,}股")
                print(f"      昨日价格: {yesterday_price:.4f}")
                print(f"      今日价格: {today_price:.4f}")
                print(f"      价格变化: {price_change:+.4f} ({price_change_pct:+.2f}%)")
                print(f"      昨日市值: {yesterday_value:,.2f}")
                print(f"      今日市值: {today_value:,.2f}")
                print(f"      持仓收益: {stock_return:+,.2f}")
                print()
            else:
                print(f"   ❌ {stock_name} ({stock_code}): 价格数据缺失")
                print(f"      今日价格: {today_price}")
                print(f"      昨日价格: {yesterday_price}")
                print()
        
        # 计算总收益
        daily_return_rate = total_daily_return / total_previous_value if total_previous_value > 0 else 0
        
        print(f"🎯 持仓收益汇总:")
        print(f"   昨日持仓总市值: {total_previous_value:,.2f}")
        print(f"   持仓日收益: {total_daily_return:+,.2f}")
        print(f"   持仓收益率: {daily_return_rate:+.4f} ({daily_return_rate*100:+.2f}%)")
        
        # 3. 使用新的系统逻辑计算
        print("\n3. 使用新系统逻辑计算...")
        await simulation_scheduler.update_daily_returns()
        
        # 获取更新后的账户信息
        account = simulation_db.get_simulation_account(user_id)
        if account:
            system_return = account.get('daily_return', 0)
            system_rate = account.get('daily_return_rate', 0)
            
            print(f"   系统计算日收益: {system_return:+,.2f}")
            print(f"   系统计算收益率: {system_rate:+.4f} ({system_rate*100:+.2f}%)")
            
            # 验证一致性
            return_diff = abs(total_daily_return - system_return)
            rate_diff = abs(daily_return_rate - system_rate)
            
            print(f"\n4. 一致性验证:")
            print(f"   收益差异: {return_diff:.2f}")
            print(f"   收益率差异: {rate_diff:.6f}")
            
            if return_diff < 0.01 and rate_diff < 0.000001:
                print("   ✅ 计算结果一致！")
            else:
                print("   ⚠️  计算结果不一致")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        logger.exception("测试过程中发生异常")
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_new_daily_return_calculation())