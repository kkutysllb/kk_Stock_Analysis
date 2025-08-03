#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加真实账户持仓数据的脚本
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 添加数据收集器目录
collector_dir = os.path.join(os.path.dirname(current_dir), 'kk_stock_collector')
sys.path.insert(0, collector_dir)

from api.db_handler import get_db_handler

def get_current_price(stock_code: str, db_handler) -> float:
    """获取股票当前价格"""
    try:
        # 从数据库获取真实价格
        kline_col = db_handler.get_collection('stock_kline_daily')
        latest_kline = kline_col.find_one(
            {'ts_code': stock_code},
            sort=[('trade_date', -1)]
        )
        
        if latest_kline:
            return float(latest_kline['close'])
        else:
            # 如果数据库中没有数据，使用备用价格
            price_map = {
                "300750.SZ": 282.8,   # 宁德时代最新价格
                "601318.SH": 58.08,   # 中国平安最新价格
                "601899.SH": 19.85    # 紫金矿业最新价格
            }
            return price_map.get(stock_code, 0.0)
    except Exception as e:
        print(f"获取 {stock_code} 价格失败: {e}")
        return 0.0

def determine_board_type(stock_code: str) -> str:
    """判断板块类型"""
    if stock_code.startswith("688"):
        return "STAR"  # 科创板
    elif stock_code.startswith("300"):
        return "GEM"   # 创业板
    else:
        return "MAIN"  # 主板

def determine_market(stock_code: str) -> str:
    """判断市场"""
    if stock_code.endswith(".SH"):
        return "SH"
    elif stock_code.endswith(".SZ"):
        return "SZ"
    else:
        return "SH"  # 默认上海

def add_real_positions():
    """添加真实持仓数据"""
    try:
        # 连接数据库
        db_handler = get_db_handler()
        
        # 查找用户（使用现有的超级管理员）
        users_col = db_handler.get_collection('users')
        user = users_col.find_one({'nickname': '超级管理员'})
        
        if not user:
            print("错误：未找到超级管理员用户")
            return
        
        user_id = str(user['_id'])
        print(f"找到用户: {user['nickname']} (ID: {user_id})")
        print(f"手机号: {user['phone']}")
        print(f"邮箱: {user['email']}")
        
        # 获取模拟交易数据库处理器
        from api.simulation.database import simulation_db
        sim_db = simulation_db
        
        # 持仓数据
        positions_data = [
            {
                "stock_code": "300750.SZ",
                "stock_name": "宁德时代",
                "quantity": 20000,
                "cost_price": 11.08
            },
            {
                "stock_code": "601318.SH", 
                "stock_name": "中国平安",
                "quantity": 15000,
                "cost_price": 50.36
            },
            {
                "stock_code": "601899.SH",
                "stock_name": "紫金矿业", 
                "quantity": 20000,
                "cost_price": 15.12
            }
        ]
        
        # 先检查账户是否存在，如果不存在则创建
        account = sim_db.get_simulation_account(user_id)
        
        if not account:
            print("创建模拟账户...")
            account = sim_db.create_simulation_account(user_id, 3000000.0, "模拟账户")
            if account:
                print("✅ 账户创建成功")
            else:
                print("❌ 账户创建失败")
                return
        
        # 删除现有持仓和交易记录（如果有）
        positions_col = sim_db.db[sim_db.POSITIONS_COLLECTION]
        trades_col = sim_db.db[sim_db.TRADES_COLLECTION]
        
        positions_col.delete_many({"user_id": user_id})
        trades_col.delete_many({"user_id": user_id})
        print("清理现有数据...")
        
        total_cost_value = 0.0
        total_market_value = 0.0
        
        # 添加持仓和交易记录
        for i, pos_data in enumerate(positions_data):
            stock_code = pos_data["stock_code"]
            stock_name = pos_data["stock_name"]
            quantity = pos_data["quantity"]
            cost_price = pos_data["cost_price"]
            current_price = get_current_price(stock_code, db_handler)
            
            # 计算成本和市值
            cost_value = quantity * cost_price
            market_value = quantity * current_price
            total_cost_value += cost_value
            total_market_value += market_value
            
            # 计算盈亏
            unrealized_pnl = market_value - cost_value
            unrealized_pnl_rate = unrealized_pnl / cost_value if cost_value > 0 else 0.0
            
            # 创建持仓记录
            position_data = {
                "user_id": user_id,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "market": determine_market(stock_code),
                "board_type": determine_board_type(stock_code),
                "total_quantity": quantity,
                "available_quantity": quantity,  # 1年前买入，T+1已过
                "frozen_quantity": 0,
                "avg_cost": cost_price,
                "current_price": current_price,
                "market_value": market_value,
                "cost_value": cost_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_rate": unrealized_pnl_rate,
                "last_price_update": datetime.now(),
                "position_date": "2024-07-26",  # 1年前
                "update_time": datetime.now()
            }
            
            positions_col.insert_one(position_data)
            print(f"✅ 添加持仓：{stock_name} {quantity}股，成本价{cost_price}，现价{current_price}")
            
            # 创建对应的买入交易记录
            trade_amount = quantity * cost_price
            commission = max(trade_amount * 0.0001, 5.0)  # 万1手续费，最低5元
            stamp_tax = 0.0  # 买入不收印花税
            transfer_fee = trade_amount * 0.00002  # 万0.2过户费
            slippage = trade_amount * 0.001  # 千1滑点
            total_cost = trade_amount + commission + stamp_tax + transfer_fee + slippage
            
            trade_data = {
                "user_id": user_id,
                "trade_id": f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{i:03d}",
                "stock_code": stock_code,
                "stock_name": stock_name,
                "trade_type": "BUY",
                "order_type": "MARKET",
                "quantity": quantity,
                "price": cost_price,
                "amount": trade_amount,
                "commission": commission,
                "stamp_tax": stamp_tax,
                "transfer_fee": transfer_fee,
                "slippage": slippage,
                "total_cost": total_cost,
                "trade_source": "MANUAL",
                "strategy_name": None,
                "trade_time": datetime(2024, 7, 26, 9, 30, 0),  # 1年前交易时间
                "settlement_date": "2024-07-29",  # T+1交割
                "status": "FILLED",
                "remarks": "历史真实持仓数据"
            }
            
            trades_col.insert_one(trade_data)
            print(f"✅ 添加交易记录：买入{stock_name}")
        
        # 更新账户信息
        initial_capital = 3000000.0
        total_return = total_market_value - total_cost_value
        total_return_rate = total_return / initial_capital if initial_capital > 0 else 0.0  # 修复：用初始资金作为分母
        available_cash = initial_capital - total_cost_value  # 初始资金减去投入成本
        total_assets = available_cash + total_market_value
        
        account_update = {
            "available_cash": available_cash,
            "total_assets": total_assets,
            "total_market_value": total_market_value,
            "total_return": total_return,
            "total_return_rate": total_return_rate,
            "trade_count": 3  # 3笔买入交易
        }
        
        sim_db.update_simulation_account(user_id, account_update)
        
        print(f"\n📊 账户摘要：")
        print(f"初始资金：¥{3000000.0:,.2f}")
        print(f"投入成本：¥{total_cost_value:,.2f}")
        print(f"当前市值：¥{total_market_value:,.2f}")
        print(f"可用现金：¥{available_cash:,.2f}")
        print(f"总资产：¥{total_assets:,.2f}")
        print(f"总收益：¥{total_return:,.2f}")
        print(f"收益率：{total_return_rate:.2%}")
        print(f"\n✅ 真实持仓数据添加完成！")
        
    except Exception as e:
        print(f"❌ 添加持仓数据失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_real_positions()