#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制迁移持仓数据到正确的用户ID
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
collector_dir = os.path.join(os.path.dirname(current_dir), 'kk_stock_collector')
sys.path.insert(0, collector_dir)

from db_handler import DBHandler
from api.simulation.database import simulation_db

def force_migrate_positions():
    """强制迁移持仓数据"""
    try:
        # 用户ID
        old_user_id = "686b903968a1e145a3e69bac"  # _id
        new_user_id = "946c1533-e852-45ca-abe2-54b9864b63b8"  # user_id
        
        print(f"强制迁移数据:")
        print(f"  从: {old_user_id}")
        print(f"  到: {new_user_id}")
        
        # 获取旧数据
        old_account = simulation_db.get_simulation_account(old_user_id)
        old_positions = simulation_db.get_user_positions(old_user_id)
        
        if not old_account or not old_positions:
            print("❌ 没有找到源数据")
            return False
        
        print(f"\\n📊 找到源数据:")
        print(f"  账户总资产: ¥{old_account['total_assets']:,.2f}")
        print(f"  持仓数量: {len(old_positions)}只股票")
        
        # 获取数据库集合
        accounts_col = simulation_db.db[simulation_db.ACCOUNTS_COLLECTION]
        positions_col = simulation_db.db[simulation_db.POSITIONS_COLLECTION]
        trades_col = simulation_db.db[simulation_db.TRADES_COLLECTION]
        
        # 1. 更新账户数据
        print("\\n🔄 更新账户数据...")
        account_update = {
            'available_cash': old_account['available_cash'],
            'total_assets': old_account['total_assets'],
            'total_market_value': old_account['total_market_value'],
            'total_return': old_account['total_return'],
            'total_return_rate': old_account['total_return_rate'],
            'trade_count': old_account['trade_count']
        }
        
        result = accounts_col.update_one(
            {"user_id": new_user_id},
            {"$set": account_update}
        )
        
        if result.modified_count > 0:
            print("✅ 账户数据更新成功")
        else:
            print("⚠️  账户数据未更新")
        
        # 2. 删除新用户ID的现有持仓（如果有）
        positions_col.delete_many({"user_id": new_user_id})
        print("🗑️  清空现有持仓")
        
        # 3. 复制持仓数据
        print("\\n🔄 复制持仓数据...")
        for position in old_positions:
            new_position = position.copy()
            new_position['user_id'] = new_user_id
            if '_id' in new_position:
                del new_position['_id']
            positions_col.insert_one(new_position)
            print(f"  ✅ {position['stock_name']}: {position['total_quantity']:,}股")
        
        # 4. 删除新用户ID的现有交易记录
        trades_col.delete_many({"user_id": new_user_id})
        
        # 5. 复制交易记录
        print("\\n🔄 复制交易记录...")
        old_trades = list(trades_col.find({"user_id": old_user_id}))
        for trade in old_trades:
            new_trade = trade.copy()
            new_trade['user_id'] = new_user_id
            if '_id' in new_trade:
                del new_trade['_id']
            trades_col.insert_one(new_trade)
        print(f"  ✅ 复制了{len(old_trades)}笔交易记录")
        
        # 6. 验证结果
        print("\\n🔍 验证迁移结果...")
        new_account = simulation_db.get_simulation_account(new_user_id)
        new_positions = simulation_db.get_user_positions(new_user_id)
        
        if new_account and new_positions:
            print("\\n🎉 迁移成功！")
            print(f"  总资产: ¥{new_account['total_assets']:,.2f}")
            print(f"  可用现金: ¥{new_account['available_cash']:,.2f}")
            print(f"  持仓市值: ¥{new_account['total_market_value']:,.2f}")
            print(f"  持仓数量: {len(new_positions)}只股票")
            
            total_market_value = 0
            for pos in new_positions:
                market_value = pos['total_quantity'] * pos['current_price']
                total_market_value += market_value
                print(f"    {pos['stock_name']}: {pos['total_quantity']:,}股 = ¥{market_value:,.2f}")
            
            print(f"\\n💰 计算验证: 总市值 ¥{total_market_value:,.2f}")
            return True
        else:
            print("❌ 迁移验证失败")
            return False
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    force_migrate_positions()