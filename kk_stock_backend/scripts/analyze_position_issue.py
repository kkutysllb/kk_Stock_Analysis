#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析模拟交易系统中持仓收益计算问题
专门针对UUID用户的持仓数据进行详细分析
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.simulation.database import SimulationDatabase
from api.simulation.service import SimulationTradingService
from decimal import Decimal
from datetime import datetime

async def analyze_position_calculation():
    """
    分析持仓收益计算问题
    """
    print("=" * 60)
    print("📊 模拟交易系统持仓收益计算分析")
    print("=" * 60)
    
    # 初始化数据库和服务
    db = SimulationDatabase()
    service = SimulationTradingService()
    
    # 使用正确的UUID用户ID
    user_id = "946c1533-e852-45ca-abe2-54b9864b63b8"
    
    print(f"\n🔍 分析用户: {user_id}")
    
    # 1. 获取账户信息
    print("\n1️⃣ 账户信息:")
    account = db.get_simulation_account(user_id)
    if account:
        print(f"   总资产: {account['total_assets']:,.2f}")
        print(f"   可用资金: {account['available_cash']:,.2f}")
        print(f"   持仓市值: {account['total_market_value']:,.2f}")
        print(f"   总收益: {account['total_return']:,.2f}")
        print(f"   总收益率: {account['total_return_rate']:.2%}")
    else:
        print("   ❌ 账户不存在")
        return
    
    # 2. 获取原始持仓数据（数据库层）
    print("\n2️⃣ 原始持仓数据（数据库层）:")
    raw_positions = db.get_user_positions(user_id)
    for pos in raw_positions:
        print(f"   📈 {pos['stock_name']}({pos['stock_code']})")
        print(f"      总数量: {pos['total_quantity']:,}")
        print(f"      可用数量: {pos['available_quantity']:,}")
        print(f"      平均成本: {pos['avg_cost']:.4f}")
        print(f"      成本价值: {pos['cost_value']:,.2f}")
        print(f"      当前价格: {pos.get('current_price', 'N/A')}")
        print(f"      市值: {pos.get('market_value', 'N/A')}")
        print(f"      未实现盈亏: {pos.get('unrealized_pnl', 'N/A')}")
        print(f"      未实现盈亏率: {pos.get('unrealized_pnl_rate', 'N/A')}")
        print()
    
    # 3. 获取Service层处理后的持仓数据
    print("3️⃣ Service层处理后的持仓数据:")
    service_positions = await service.get_user_positions(user_id)
    for pos in service_positions:
        print(f"   📈 {pos['stock_name']}({pos['stock_code']})")
        print(f"      总数量: {pos['total_quantity']:,}")
        print(f"      可用数量: {pos['available_quantity']:,}")
        print(f"      平均成本: {pos['avg_cost']:.4f}")
        print(f"      成本价值: {pos['cost_value']:,.2f}")
        print(f"      当前价格: {pos.get('current_price', 'N/A')}")
        print(f"      市值: {pos.get('market_value', 'N/A')}")
        print(f"      未实现盈亏: {pos.get('unrealized_pnl', 'N/A')}")
        print(f"      未实现盈亏率: {pos.get('unrealized_pnl_rate', 'N/A')}")
        print()
    
    # 4. 获取交易记录并重新计算成本
    print("4️⃣ 交易记录分析:")
    trades, total_count = db.get_user_trades(user_id, limit=1000)  # 获取更多记录
    print(f"   总交易记录数: {total_count}")
    print(f"   获取到的记录数: {len(trades)}")
    
    # 按股票分组分析交易记录
    stock_trades = {}
    for trade in trades:
        stock_code = trade['stock_code']
        if stock_code not in stock_trades:
            stock_trades[stock_code] = []
        stock_trades[stock_code].append(trade)
    
    print("\n   📊 按股票分组的交易分析:")
    for stock_code, stock_trade_list in stock_trades.items():
        print(f"\n   🏷️  {stock_code}:")
        
        total_buy_quantity = 0
        total_buy_amount = 0
        total_sell_quantity = 0
        total_sell_amount = 0
        
        for trade in sorted(stock_trade_list, key=lambda x: x['trade_time']):
            trade_type = trade['trade_type']
            quantity = trade['quantity']
            price = trade['trade_price']
            amount = trade['trade_amount']
            
            print(f"      {trade['trade_time'].strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"{trade_type} | 数量: {quantity:,} | 价格: {price:.4f} | 金额: {amount:,.2f}")
            
            if trade_type == 'BUY':
                total_buy_quantity += quantity
                total_buy_amount += amount
            elif trade_type == 'SELL':
                total_sell_quantity += quantity
                total_sell_amount += amount
        
        # 计算当前持仓
        current_quantity = total_buy_quantity - total_sell_quantity
        if current_quantity > 0:
            avg_cost = total_buy_amount / total_buy_quantity if total_buy_quantity > 0 else 0
            cost_value = current_quantity * avg_cost
            
            print(f"      \n      📊 计算结果:")
            print(f"         买入总数量: {total_buy_quantity:,}")
            print(f"         买入总金额: {total_buy_amount:,.2f}")
            print(f"         卖出总数量: {total_sell_quantity:,}")
            print(f"         卖出总金额: {total_sell_amount:,.2f}")
            print(f"         当前持仓: {current_quantity:,}")
            print(f"         平均成本: {avg_cost:.4f}")
            print(f"         成本价值: {cost_value:,.2f}")
            
            # 与数据库中的持仓数据对比
            db_position = next((p for p in raw_positions if p['stock_code'] == stock_code), None)
            if db_position:
                print(f"         \n      🔍 与数据库对比:")
                print(f"         数据库持仓数量: {db_position['total_quantity']:,}")
                print(f"         数据库平均成本: {db_position['avg_cost']:.4f}")
                print(f"         数据库成本价值: {db_position['cost_value']:,.2f}")
                
                # 检查是否一致
                quantity_match = current_quantity == db_position['total_quantity']
                cost_match = abs(avg_cost - db_position['avg_cost']) < 0.0001
                value_match = abs(cost_value - db_position['cost_value']) < 0.01
                
                print(f"         \n      ✅ 一致性检查:")
                print(f"         持仓数量一致: {'✅' if quantity_match else '❌'}")
                print(f"         平均成本一致: {'✅' if cost_match else '❌'}")
                print(f"         成本价值一致: {'✅' if value_match else '❌'}")
                
                if not (quantity_match and cost_match and value_match):
                    print(f"         \n      ⚠️  发现不一致！")
    
    # 5. 检查账户总资产计算
    print("\n5️⃣ 账户总资产计算验证:")
    total_cost_value = sum(pos['cost_value'] for pos in raw_positions)
    total_market_value = sum(pos.get('market_value', 0) for pos in service_positions if pos.get('market_value'))
    calculated_total_assets = account['available_cash'] + total_market_value
    
    print(f"   可用资金: {account['available_cash']:,.2f}")
    print(f"   持仓总成本: {total_cost_value:,.2f}")
    print(f"   持仓总市值: {total_market_value:,.2f}")
    print(f"   计算的总资产: {calculated_total_assets:,.2f}")
    print(f"   数据库总资产: {account['total_assets']:,.2f}")
    print(f"   总资产一致: {'✅' if abs(calculated_total_assets - account['total_assets']) < 0.01 else '❌'}")
    
    print("\n" + "=" * 60)
    print("📋 分析完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(analyze_position_calculation())