#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查交易记录数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.simulation.database import SimulationDatabase
from api.db_handler import get_db_handler

def check_trade_records():
    """
    检查交易记录数据
    """
    print("=" * 60)
    print("🔍 检查交易记录数据")
    print("=" * 60)
    
    # 初始化数据库
    db = SimulationDatabase()
    db_handler = get_db_handler()
    
    # 目标用户ID
    user_id = "946c1533-e852-45ca-abe2-54b9864b63b8"
    
    print(f"\n🎯 检查用户: {user_id}")
    
    # 1. 检查simulation_trades集合
    print("\n1️⃣ 检查simulation_trades集合:")
    trades_col = db_handler.get_collection('simulation_trades')
    
    # 查询该用户的所有交易记录
    user_trades = list(trades_col.find({"user_id": user_id}))
    print(f"   该用户的交易记录数: {len(user_trades)}")
    
    if user_trades:
        for trade in user_trades:
            print(f"   交易ID: {trade.get('trade_id', 'N/A')}")
            print(f"   股票代码: {trade.get('stock_code', 'N/A')}")
            print(f"   交易类型: {trade.get('trade_type', 'N/A')}")
            print(f"   数量: {trade.get('quantity', 'N/A')}")
            print(f"   价格: {trade.get('trade_price', 'N/A')}")
            print(f"   时间: {trade.get('trade_time', 'N/A')}")
            print()
    
    # 2. 检查所有交易记录
    print("2️⃣ 检查所有交易记录:")
    all_trades = list(trades_col.find({}).limit(10))
    print(f"   数据库中总交易记录数: {trades_col.count_documents({})}")
    print(f"   前10条交易记录:")
    
    for i, trade in enumerate(all_trades, 1):
        print(f"   {i}. 用户: {trade.get('user_id', 'N/A')[:20]}... | "
              f"股票: {trade.get('stock_code', 'N/A')} | "
              f"类型: {trade.get('trade_type', 'N/A')} | "
              f"数量: {trade.get('quantity', 'N/A')}")
    
    # 3. 检查持仓数据的创建时间
    print("\n3️⃣ 检查持仓数据:")
    positions_col = db_handler.get_collection('simulation_positions')
    user_positions = list(positions_col.find({"user_id": user_id}))
    
    print(f"   该用户的持仓记录数: {len(user_positions)}")
    for pos in user_positions:
        print(f"   股票: {pos.get('stock_code', 'N/A')} | "
              f"数量: {pos.get('total_quantity', 'N/A')} | "
              f"成本: {pos.get('avg_cost', 'N/A')} | "
              f"创建时间: {pos.get('create_time', 'N/A')} | "
              f"更新时间: {pos.get('last_update_time', 'N/A')}")
    
    # 4. 检查账户数据
    print("\n4️⃣ 检查账户数据:")
    accounts_col = db_handler.get_collection('simulation_accounts')
    user_account = accounts_col.find_one({"user_id": user_id})
    
    if user_account:
        print(f"   创建时间: {user_account.get('create_time', 'N/A')}")
        print(f"   最后更新: {user_account.get('last_update_time', 'N/A')}")
        print(f"   初始资金: {user_account.get('initial_capital', 'N/A'):,.2f}")
        print(f"   可用资金: {user_account.get('available_cash', 'N/A'):,.2f}")
        print(f"   总资产: {user_account.get('total_assets', 'N/A'):,.2f}")
        print(f"   交易次数: {user_account.get('trade_count', 'N/A')}")
    
    # 5. 检查是否有其他相关集合
    print("\n5️⃣ 检查数据库中的所有集合:")
    collections = db_handler.db.list_collection_names()
    trade_related_collections = [col for col in collections if 'trade' in col.lower() or 'transaction' in col.lower()]
    
    print(f"   所有集合: {collections}")
    print(f"   交易相关集合: {trade_related_collections}")
    
    # 6. 检查是否有其他用户ID格式的交易记录
    print("\n6️⃣ 检查其他可能的用户ID格式:")
    
    # 检查手机号格式
    phone_trades = list(trades_col.find({"user_id": "+8613609247807"}).limit(5))
    print(f"   手机号格式交易记录数: {len(phone_trades)}")
    
    # 检查其他可能的ID格式
    similar_id_trades = list(trades_col.find({"user_id": {"$regex": "946c1533"}}).limit(5))
    print(f"   相似ID格式交易记录数: {len(similar_id_trades)}")
    
    print("\n" + "=" * 60)
    print("🔍 检查完成")
    print("=" * 60)

if __name__ == "__main__":
    check_trade_records()