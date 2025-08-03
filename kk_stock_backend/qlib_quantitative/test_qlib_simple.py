#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的Qlib模块测试
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_adapter():
    """测试数据适配器"""
    try:
        from core.data_adapter import QlibDataAdapter
        
        logger.info("测试数据适配器...")
        
        # 创建数据适配器
        adapter = QlibDataAdapter()
        
        # 测试数据格式转换
        test_code = "000001"
        qlib_format = adapter._convert_to_qlib_format(test_code)
        back_format = adapter._convert_from_qlib_format(qlib_format)
        
        logger.info(f"格式转换测试: {test_code} -> {qlib_format} -> {back_format}")
        
        logger.info("数据适配器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"数据适配器测试失败: {e}")
        return False

def test_boll_strategy():
    """测试BOLL策略"""
    try:
        from strategies.curious_ragdoll_boll_qlib import CuriousRagdollBollConfig, CuriousRagdollBollModel
        
        logger.info("测试BOLL策略...")
        
        # 创建配置
        config = CuriousRagdollBollConfig(
            boll_period=20,
            boll_std=2.0,
            stock_pool_size=50,
            fixed_positions=10
        )
        
        logger.info(f"配置创建成功: 布林带周期{config.boll_period}, 标准差{config.boll_std}")
        
        # 创建模型
        model = CuriousRagdollBollModel(config)
        
        logger.info(f"模型创建成功")
        
        logger.info("BOLL策略测试通过")
        return True
        
    except Exception as e:
        logger.error(f"BOLL策略测试失败: {e}")
        return False

def test_portfolio_manager():
    """测试投资组合管理器"""
    try:
        from core.portfolio_manager_qlib import QlibPortfolioManager
        
        logger.info("测试投资组合管理器...")
        
        # 创建投资组合管理器
        config = {
            'max_position_ratio': 0.1,
            'max_total_position': 0.95,
            'min_cash_ratio': 0.05,
            'topk': 10,
            'n_drop': 2
        }
        
        manager = QlibPortfolioManager(1000000, config)
        
        logger.info(f"投资组合管理器创建成功")
        logger.info(f"初始资金: {manager.initial_capital}")
        
        # 测试仓位计算
        position_size = manager.calculate_position_size("SH600000", 10.0, 1.0)
        logger.info(f"仓位计算结果: {position_size} 股")
        
        logger.info("投资组合管理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"投资组合管理器测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始简化测试...")
    
    test_results = {
        "数据适配器": test_data_adapter(),
        "BOLL策略": test_boll_strategy(),
        "投资组合管理器": test_portfolio_manager()
    }
    
    logger.info("\n" + "="*50)
    logger.info("测试结果汇总:")
    logger.info("="*50)
    
    success_count = 0
    for module_name, result in test_results.items():
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{module_name}: {status}")
        if result:
            success_count += 1
    
    logger.info(f"\n总计: {success_count}/{len(test_results)} 模块测试通过")
    
    if success_count == len(test_results):
        logger.info("核心模块测试通过! 基本功能可用。")
        return True
    else:
        logger.error("部分模块测试失败，请检查相关代码。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)