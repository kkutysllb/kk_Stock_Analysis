"""
模拟交易系统初始化工具

用于为用户自动创建模拟账户
"""

import logging
from typing import List
from api.db_handler import get_db_handler
from .database import simulation_db


logger = logging.getLogger(__name__)


async def init_simulation_account_for_user(user_id: str) -> bool:
    """
    为用户初始化模拟账户
    
    Args:
        user_id: 用户ID
        
    Returns:
        初始化是否成功
    """
    try:
        # 检查用户是否已有模拟账户
        existing_account = simulation_db.get_simulation_account(user_id)
        if existing_account:
            logger.info(f"用户 {user_id} 已存在模拟账户，跳过初始化")
            return True
        
        # 创建模拟账户
        account = simulation_db.create_simulation_account(user_id, 3000000.0, "模拟账户")
        if account:
            logger.info(f"用户 {user_id} 模拟账户初始化成功")
            return True
        else:
            logger.error(f"用户 {user_id} 模拟账户初始化失败")
            return False
            
    except Exception as e:
        logger.error(f"用户 {user_id} 模拟账户初始化异常: {e}")
        return False


async def init_simulation_accounts_for_all_users() -> int:
    """
    为所有用户初始化模拟账户
    
    Returns:
        成功初始化的账户数量
    """
    try:
        db_handler = get_db_handler()
        users_col = db_handler.get_collection("users")
        
        # 获取所有用户
        users = list(users_col.find({"status": 1}, {"user_id": 1}))
        
        success_count = 0
        total_count = len(users)
        
        logger.info(f"开始为 {total_count} 个用户初始化模拟账户")
        
        for user in users:
            user_id = user["user_id"]
            if await init_simulation_account_for_user(user_id):
                success_count += 1
        
        logger.info(f"模拟账户初始化完成: {success_count}/{total_count} 成功")
        return success_count
        
    except Exception as e:
        logger.error(f"批量初始化模拟账户失败: {e}")
        return 0


def get_users_without_simulation_account() -> List[str]:
    """
    获取没有模拟账户的用户列表
    
    Returns:
        用户ID列表
    """
    try:
        db_handler = get_db_handler()
        users_col = db_handler.get_collection("users")
        accounts_col = db_handler.get_collection(simulation_db.ACCOUNTS_COLLECTION)
        
        # 获取所有活跃用户
        users = list(users_col.find({"status": 1}, {"user_id": 1}))
        all_user_ids = [user["user_id"] for user in users]
        
        # 获取已有模拟账户的用户
        existing_accounts = list(accounts_col.find({}, {"user_id": 1}))
        existing_user_ids = [acc["user_id"] for acc in existing_accounts]
        
        # 找出没有模拟账户的用户
        users_without_account = [user_id for user_id in all_user_ids if user_id not in existing_user_ids]
        
        logger.info(f"找到 {len(users_without_account)} 个用户没有模拟账户")
        return users_without_account
        
    except Exception as e:
        logger.error(f"获取无模拟账户用户列表失败: {e}")
        return []


async def check_and_init_missing_accounts() -> int:
    """
    检查并初始化缺失的模拟账户
    
    Returns:
        成功初始化的账户数量
    """
    try:
        missing_user_ids = get_users_without_simulation_account()
        
        if not missing_user_ids:
            logger.info("所有用户都已有模拟账户")
            return 0
        
        success_count = 0
        for user_id in missing_user_ids:
            if await init_simulation_account_for_user(user_id):
                success_count += 1
        
        logger.info(f"补充模拟账户完成: {success_count}/{len(missing_user_ids)} 成功")
        return success_count
        
    except Exception as e:
        logger.error(f"检查并初始化缺失账户失败: {e}")
        return 0