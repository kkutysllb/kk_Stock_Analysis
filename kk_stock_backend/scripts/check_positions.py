#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from api.simulation.service import SimulationTradingService
from api.db_handler import DBHandler, get_db_handler

# 初始化数据库处理器
db_handler = get_db_handler()

async def check_user_positions():
    """检查用户持仓信息"""
    try:
        service = SimulationTradingService()
        
        # 获取账户信息
        account = await service.get_account_info('admin')
        if not account:
            print('账户不存在，正在初始化...')
            account = await service.init_user_account('admin', 3000000.0)
            if not account:
                print('账户初始化失败')
                return
        
        print('=== 账户信息 ===')
        print(f'总资产: {account.get("total_assets", 0):.2f}')
        print(f'现金: {account.get("cash", 0):.2f}')
        print(f'持仓市值: {account.get("total_market_value", 0):.2f}')
        print(f'总收益: {account.get("total_return", 0):.2f}')
        print(f'总收益率: {account.get("total_return_rate", 0):.2%}')
        
        # 获取持仓详情
        positions = await service.get_user_positions('admin')
        print('\n=== 持仓详情 ===')
        if not positions:
            print('暂无持仓')
        else:
            for pos in positions:
                stock_name = pos.get('stock_name', '未知')
                stock_code = pos.get('stock_code', '未知')
                quantity = pos.get('quantity', 0)
                avg_cost = pos.get('avg_cost', 0)
                current_price = pos.get('current_price', 0)
                market_value = pos.get('market_value', 0)
                unrealized_pnl = pos.get('unrealized_pnl', 0)
                unrealized_return_rate = pos.get('unrealized_return_rate', 0)
                
                print(f'\n股票: {stock_name}({stock_code})')
                print(f'  数量: {quantity}')
                print(f'  成本价: {avg_cost:.2f}')
                print(f'  现价: {current_price:.2f}')
                print(f'  市值: {market_value:.2f}')
                print(f'  盈亏: {unrealized_pnl:.2f}')
                print(f'  收益率: {unrealized_return_rate:.2%}')
                
        # 检查特定股票的价格更新
        target_stocks = ['300750.SZ', '601318.SH', '601899.SH']  # 宁德时代、中国平安、紫金矿业
        print('\n=== 目标股票价格检查 ===')
        for stock_code in target_stocks:
            try:
                price = await service._get_current_stock_price(stock_code)
                print(f'{stock_code}: {price:.2f}')
            except Exception as e:
                print(f'{stock_code}: 获取价格失败 - {e}')
                
    except Exception as e:
        print(f'检查持仓失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import asyncio
    asyncio.run(check_user_positions())