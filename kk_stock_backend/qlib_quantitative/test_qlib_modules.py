#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Qlib模块的基本功能
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
        
        # 测试股票列表获取
        stocks = adapter.get_stock_list("CSI500")
        logger.info(f"获取到{len(stocks)}只股票")
        
        # 测试数据格式转换
        test_code = "000001"
        qlib_format = adapter._convert_to_qlib_format(test_code)
        back_format = adapter._convert_from_qlib_format(qlib_format)
        
        logger.info(f"格式转换测试: {test_code} -> {qlib_format} -> {back_format}")
        
        # 测试小市值股票筛选
        small_cap_stocks = adapter.filter_small_cap_stocks("2023-12-31", count=10)
        logger.info(f"筛选出{len(small_cap_stocks)}只小市值股票")
        
        logger.info("数据适配器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"数据适配器测试失败: {e}")
        return False

def test_strategy_base():
    """测试策略基类"""
    try:
        from core.strategy_base_qlib import QlibStrategyBase, QlibSimpleStrategy
        from core.data_adapter import QlibDataAdapter
        
        logger.info("测试策略基类...")
        
        # 创建数据适配器
        adapter = QlibDataAdapter()
        
        # 创建简单策略
        config = {
            'initial_capital': 1000000,
            'commission': 0.0015
        }
        
        strategy = QlibSimpleStrategy(
            name="测试策略",
            data_adapter=adapter,
            config=config
        )
        
        logger.info(f"策略创建成功: {strategy.name}")
        logger.info(f"策略已初始化: {strategy.is_initialized}")
        
        logger.info("策略基类测试通过")
        return True
        
    except Exception as e:
        logger.error(f"策略基类测试失败: {e}")
        return False

def test_backtest_engine():
    """测试回测引擎"""
    try:
        from core.backtest_engine_qlib import QlibBacktestEngine
        from core.data_adapter import QlibDataAdapter
        
        logger.info("测试回测引擎...")
        
        # 创建数据适配器
        adapter = QlibDataAdapter()
        
        # 创建回测引擎
        config = {
            'initial_capital': 1000000,
            'commission': 0.0015,
            'benchmark': 'SH000905'
        }
        
        engine = QlibBacktestEngine(adapter, config)
        
        logger.info(f"回测引擎创建成功")
        logger.info(f"初始资金: {engine.initial_capital}")
        logger.info(f"手续费: {engine.commission}")
        logger.info(f"基准: {engine.benchmark_symbol}")
        
        logger.info("回测引擎测试通过")
        return True
        
    except Exception as e:
        logger.error(f"回测引擎测试失败: {e}")
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
        logger.info(f"可用现金: {manager.available_cash}")
        logger.info(f"总资产: {manager.total_value}")
        
        # 测试仓位计算
        position_size = manager.calculate_position_size("SH600000", 10.0, 1.0)
        logger.info(f"仓位计算结果: {position_size} 股")
        
        logger.info("投资组合管理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"投资组合管理器测试失败: {e}")
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

def main():
    """主函数"""
    logger.info("开始测试Qlib模块...")
    
    test_results = {
        "数据适配器": test_data_adapter(),
        "策略基类": test_strategy_base(),
        "回测引擎": test_backtest_engine(),
        "投资组合管理器": test_portfolio_manager(),
        "BOLL策略": test_boll_strategy()
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
        logger.info("所有模块测试通过! 可以进行完整回测。")
        return True
    else:
        logger.error("部分模块测试失败，请检查相关代码。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)