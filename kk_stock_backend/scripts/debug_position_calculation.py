#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from api.simulation.service import SimulationTradingService
from api.simulation.database import SimulationDatabase
from api.db_handler import DBHandler, get_db_handler
import asyncio

async def debug_position_calculation():
    """调试持仓收益计算问题"""
    try:
        service = SimulationTradingService()
        db = SimulationDatabase()
        
        user_id = '946c1533-e852-45ca-abe2-54b9864b63b8'
        
        # 0. 检查用户账户是否存在
        print('=== 检查用户账户 ===')
        account = await service.get_account_info(user_id)
        if account:
            print(f'用户账户存在:')
            print(f'  总资产: {account.get("total_assets", 0):.2f}')
            print(f'  现金: {account.get("cash", 0):.2f}')
            print(f'  持仓市值: {account.get("total_market_value", 0):.2f}')
            print(f'  总收益: {account.get("total_return", 0):.2f}')
            print(f'  总收益率: {account.get("total_return_rate", 0):.2%}')
        else:
            print('用户账户不存在，尝试创建...')
            account = await service.init_user_account(user_id, 3000000.0)
            if account:
                print('账户创建成功')
            else:
                print('账户创建失败')
                return
        
        # 1. 获取原始持仓数据（不经过service层处理）
        print('\n=== 原始持仓数据（数据库层） ===')
        raw_positions = db.get_user_positions(user_id)
        if not raw_positions:
            print('没有找到持仓数据')
        else:
            for pos in raw_positions:
                print(f'\n股票: {pos.get("stock_name", "未知")}({pos.get("stock_code", "未知")})')
                print(f'  数量: {pos.get("total_quantity", 0)}')
                print(f'  平均成本: {pos.get("avg_cost", 0):.2f}')
                print(f'  成本总值: {pos.get("cost_value", 0):.2f}')
                print(f'  当前价格: {pos.get("current_price", 0):.2f}')
                print(f'  市值: {pos.get("market_value", 0):.2f}')
                print(f'  未实现盈亏: {pos.get("unrealized_pnl", 0):.2f}')
                print(f'  未实现收益率: {pos.get("unrealized_pnl_rate", 0):.2%}')
                
                # 验证计算
                quantity = pos.get("total_quantity", 0)
                avg_cost = pos.get("avg_cost", 0)
                current_price = pos.get("current_price", 0)
                cost_value = pos.get("cost_value", 0)
                
                calculated_cost_value = quantity * avg_cost
                calculated_market_value = quantity * current_price
                calculated_pnl = calculated_market_value - calculated_cost_value
                calculated_pnl_rate = calculated_pnl / calculated_cost_value if calculated_cost_value > 0 else 0
                
                print(f'  --- 验证计算 ---')
                print(f'  计算成本总值: {calculated_cost_value:.2f} (数据库: {cost_value:.2f})')
                print(f'  计算市值: {calculated_market_value:.2f}')
                print(f'  计算盈亏: {calculated_pnl:.2f}')
                print(f'  计算收益率: {calculated_pnl_rate:.2%}')
                
                if abs(cost_value - calculated_cost_value) > 0.01:
                    print(f'  ⚠️  成本总值不匹配！数据库值可能有误')
        
        # 2. 获取service层处理后的持仓数据
        print('\n=== Service层处理后的持仓数据 ===')
        service_positions = await service.get_user_positions(user_id)
        if not service_positions:
            print('没有找到持仓数据')
        else:
            for pos in service_positions:
                print(f'\n股票: {pos.get("stock_name", "未知")}({pos.get("stock_code", "未知")})')
                print(f'  数量: {pos.get("total_quantity", 0)}')
                print(f'  平均成本: {pos.get("avg_cost", 0):.2f}')
                print(f'  成本总值: {pos.get("cost_value", 0):.2f}')
                print(f'  当前价格: {pos.get("current_price", 0):.2f}')
                print(f'  市值: {pos.get("market_value", 0):.2f}')
                print(f'  未实现盈亏: {pos.get("unrealized_pnl", 0):.2f}')
                print(f'  未实现收益率: {pos.get("unrealized_pnl_rate", 0):.2%}')
        
        # 3. 检查交易记录，验证成本计算
        print('\n=== 交易记录验证 ===')
        all_trades, total_count = await service.get_trade_history(user_id, page=1, page_size=100)
        print(f'总交易记录数: {total_count}')
        
        if total_count == 0:
            print('没有找到任何交易记录')
            
            # 检查数据库中是否有其他用户的数据
            print('\n=== 检查数据库中的所有用户 ===')
            db_handler = get_db_handler()
            accounts_col = db_handler.get_collection('simulation_accounts')
            all_accounts = list(accounts_col.find({}, {'user_id': 1, 'total_assets': 1, 'initial_capital': 1}))
            
            print(f'数据库中共有 {len(all_accounts)} 个账户:')
            for acc in all_accounts:
                print(f'  用户ID: {acc.get("user_id", "未知")}, 总资产: {acc.get("total_assets", 0):.2f}, 初始资金: {acc.get("initial_capital", 0):.2f}')
            
            # 检查持仓表
            positions_col = db_handler.get_collection('simulation_positions')
            all_positions = list(positions_col.find({}, {'user_id': 1, 'stock_code': 1, 'stock_name': 1, 'total_quantity': 1}))
            print(f'\n数据库中共有 {len(all_positions)} 条持仓记录:')
            for pos in all_positions:
                print(f'  用户ID: {pos.get("user_id", "未知")}, 股票: {pos.get("stock_name", "未知")}({pos.get("stock_code", "未知")}), 数量: {pos.get("total_quantity", 0)}')
            
            # 检查交易记录表
            trades_col = db_handler.get_collection('simulation_trades')
            all_trades_db = list(trades_col.find({}, {'user_id': 1, 'stock_code': 1, 'trade_type': 1, 'quantity': 1}).limit(10))
            print(f'\n数据库中的交易记录样本 (前10条):')
            for trade in all_trades_db:
                print(f'  用户ID: {trade.get("user_id", "未知")}, 股票: {trade.get("stock_code", "未知")}, 类型: {trade.get("trade_type", "未知")}, 数量: {trade.get("quantity", 0)}')
        else:
            # 分析交易记录
            target_stocks = ['300750.SZ', '601318.SH', '601899.SH']
            for stock_code in target_stocks:
                print(f'\n--- {stock_code} 交易记录 ---')
                trades, _ = await service.get_trade_history(user_id, page=1, page_size=100, stock_code=stock_code)
                
                total_buy_quantity = 0
                total_buy_amount = 0
                total_sell_quantity = 0
                
                for trade in trades:
                    trade_type = trade.get('trade_type', '')
                    quantity = trade.get('quantity', 0)
                    price = trade.get('price', 0)
                    amount = trade.get('amount', 0)
                    total_cost = trade.get('total_cost', 0)
                    
                    print(f'  {trade_type}: {quantity}股 @ {price:.2f}, 金额: {amount:.2f}, 总成本: {total_cost:.2f}')
                    
                    if trade_type == 'buy':
                        total_buy_quantity += quantity
                        total_buy_amount += total_cost  # 使用total_cost包含手续费
                    elif trade_type == 'sell':
                        total_sell_quantity += quantity
                
                current_quantity = total_buy_quantity - total_sell_quantity
                if current_quantity > 0:
                    avg_cost_from_trades = total_buy_amount / total_buy_quantity if total_buy_quantity > 0 else 0
                    current_cost_value = avg_cost_from_trades * current_quantity
                    
                    print(f'  总买入: {total_buy_quantity}股, 总成本: {total_buy_amount:.2f}')
                    print(f'  总卖出: {total_sell_quantity}股')
                    print(f'  当前持仓: {current_quantity}股')
                    print(f'  从交易记录计算的平均成本: {avg_cost_from_trades:.2f}')
                    print(f'  从交易记录计算的成本总值: {current_cost_value:.2f}')
                    
                    # 对比数据库中的持仓数据
                    db_position = db.get_position(user_id, stock_code)
                    if db_position:
                        db_avg_cost = db_position.get('avg_cost', 0)
                        db_cost_value = db_position.get('cost_value', 0)
                        print(f'  数据库中的平均成本: {db_avg_cost:.2f}')
                        print(f'  数据库中的成本总值: {db_cost_value:.2f}')
                        
                        if abs(db_avg_cost - avg_cost_from_trades) > 0.01:
                            print(f'  ⚠️  平均成本不匹配！')
                        if abs(db_cost_value - current_cost_value) > 0.01:
                            print(f'  ⚠️  成本总值不匹配！')
                            
    except Exception as e:
        print(f'调试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(debug_position_calculation())