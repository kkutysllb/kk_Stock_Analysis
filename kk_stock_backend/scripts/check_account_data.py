#!/usr/bin/env python3
"""
检查模拟账户数据
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.db_handler import get_db_handler

async def check_account_data():
    db = get_db_handler()
    
    try:
        # 查找管理员用户
        admin_user = await db.find_one('users', {'role': 'admin', 'is_admin': True})
        if not admin_user:
            print('未找到管理员用户')
            return
        
        user_id = admin_user['_id']
        print(f'管理员用户ID: {user_id}')
        
        # 查找模拟账户
        account = await db.find_one('simulation_accounts', {'user_id': user_id})
        
        if account:
            print('\n模拟账户数据：')
            print(f'initial_capital: {account.get("initial_capital", "N/A")}')
            print(f'total_assets: {account.get("total_assets", "N/A")}')
            print(f'total_return: {account.get("total_return", "N/A")}')
            print(f'total_return_rate: {account.get("total_return_rate", "N/A")}')
            print(f'available_cash: {account.get("available_cash", "N/A")}')
            print(f'total_market_value: {account.get("total_market_value", "N/A")}')
            
            # 手动计算验证
            initial = account.get('initial_capital', 0)
            total_assets = account.get('total_assets', 0)
            total_return = account.get('total_return', 0)
            
            print('\n手动计算验证：')
            print(f'总资产 - 初始资金 = {total_assets} - {initial} = {total_assets - initial}')
            if initial > 0:
                calculated_rate = (total_assets - initial) / initial
                print(f'收益率应该是 = ({total_assets} - {initial}) / {initial} = {calculated_rate:.4f} = {calculated_rate * 100:.2f}%')
                print(f'数据库中的收益率 = {account.get("total_return_rate", 0):.4f}')
                
                # 分析问题
                db_rate = account.get("total_return_rate", 0)
                if abs(calculated_rate - db_rate) > 0.01:  # 差异超过1%
                    print(f'\n❌ 发现问题：数据库收益率与计算值不匹配!')
                    print(f'   计算值: {calculated_rate:.4f}')
                    print(f'   数据库值: {db_rate:.4f}')
                    print(f'   差异: {abs(calculated_rate - db_rate):.4f}')
                else:
                    print(f'\n✅ 收益率计算正确')
            else:
                print('收益率计算失败：初始资金为0')
        else:
            print('未找到管理员模拟账户')
    
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(check_account_data())