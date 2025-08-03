#!/usr/bin/env python3
"""
调试模拟账户数据脚本
检查账户数据的准确性
"""

import asyncio
from api.simulation.database import simulation_db
from api.simulation.service import simulation_service
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_account_data():
    """调试账户数据"""
    
    # 获取所有账户
    try:
        db = simulation_db.db  
        accounts_col = db[simulation_db.ACCOUNTS_COLLECTION]
        accounts = list(accounts_col.find({}))
        
        logger.info(f"找到 {len(accounts)} 个模拟账户")
        
        for account in accounts:
            user_id = account['user_id']
            logger.info(f"\n=== 账户详情 - 用户ID: {user_id} ===")
            logger.info(f"初始资金: {account.get('initial_capital', 0):,.2f}")
            logger.info(f"可用现金: {account.get('available_cash', 0):,.2f}")
            logger.info(f"冻结现金: {account.get('frozen_cash', 0):,.2f}")
            logger.info(f"持仓市值: {account.get('total_market_value', 0):,.2f}")
            logger.info(f"总资产: {account.get('total_assets', 0):,.2f}")
            logger.info(f"总收益: {account.get('total_return', 0):,.2f}")
            logger.info(f"总收益率: {account.get('total_return_rate', 0):.2f}%")
            
            # 手动计算验证
            manual_total_assets = account.get('available_cash', 0) + account.get('frozen_cash', 0) + account.get('total_market_value', 0)
            manual_total_return = manual_total_assets - account.get('initial_capital', 0)
            manual_return_rate = (manual_total_return / account.get('initial_capital', 1)) * 100 if account.get('initial_capital', 0) > 0 else 0
            
            logger.info(f"--- 手动验证计算 ---")
            logger.info(f"手动计算总资产: {manual_total_assets:,.2f}")
            logger.info(f"手动计算总收益: {manual_total_return:,.2f}")
            logger.info(f"手动计算收益率: {manual_return_rate:.2f}%")
            
            # 检查持仓数据
            positions = simulation_db.get_user_positions(user_id)
            logger.info(f"持仓股票数量: {len(positions)}")
            total_position_value = 0
            for pos in positions:
                position_value = pos.get('market_value', 0)
                total_position_value += position_value
                logger.info(f"  {pos.get('stock_code')}: {pos.get('stock_name')} - 市值: {position_value:,.2f}")
            
            logger.info(f"持仓总市值(计算): {total_position_value:,.2f}")
            
            # 检查数据一致性
            if abs(manual_total_assets - account.get('total_assets', 0)) > 0.01:
                logger.warning(f"总资产数据不一致! 存储值: {account.get('total_assets', 0):,.2f}, 计算值: {manual_total_assets:,.2f}")
            
            if abs(total_position_value - account.get('total_market_value', 0)) > 0.01:
                logger.warning(f"持仓市值不一致! 存储值: {account.get('total_market_value', 0):,.2f}, 计算值: {total_position_value:,.2f}")
                
        logger.info("\n=== 调试完成 ===")
        
    except Exception as e:
        logger.error(f"调试失败: {e}")

if __name__ == "__main__":
    asyncio.run(debug_account_data())