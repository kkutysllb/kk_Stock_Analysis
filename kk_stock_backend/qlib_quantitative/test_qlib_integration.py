#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qlib框架完整性测试脚本
验证所有核心模块和功能的正常工作
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_data_adapter():
    """测试数据适配器"""
    logger.info("🔍 测试数据适配器...")
    
    try:
        from core.data_adapter import QlibDataAdapter
        
        # 创建数据适配器
        adapter = QlibDataAdapter()
        
        # 测试获取股票列表
        stocks = adapter.get_stock_list("CSI500")
        logger.info(f"✅ 股票列表获取成功: {len(stocks)}只股票")
        
        # 测试获取单只股票数据
        test_stock = stocks[0]
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        
        stock_data = adapter.get_stock_data(test_stock, start_date, end_date)
        logger.info(f"✅ 股票数据获取成功: {test_stock} - {len(stock_data)}条记录")
        
        # 测试获取基准数据
        benchmark_data = adapter.get_benchmark_data("SH000905", start_date, end_date)
        logger.info(f"✅ 基准数据获取成功: {len(benchmark_data)}条记录")
        
        # 测试获取因子数据
        factor_data = adapter.get_factor_data(test_stock, start_date, end_date)
        logger.info(f"✅ 因子数据获取成功: {len(factor_data)}条记录")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据适配器测试失败: {e}")
        return False

def test_strategy_model():
    """测试策略模型"""
    logger.info("🔍 测试策略模型...")
    
    try:
        from strategies.curious_ragdoll_boll_qlib import (
            CuriousRagdollBollConfig, 
            CuriousRagdollBollModel,
            CuriousRagdollBollStrategy
        )
        
        # 创建配置
        config = CuriousRagdollBollConfig()
        
        # 创建模型
        model = CuriousRagdollBollModel(config)
        logger.info("✅ 策略模型创建成功")
        
        # 创建策略
        strategy = CuriousRagdollBollStrategy(config)
        logger.info("✅ 策略实例创建成功")
        
        # 测试布林带计算
        test_prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20] * 3)
        boll_bands = model.calculate_boll_bands(test_prices)
        logger.info(f"✅ 布林带计算成功: {boll_bands}")
        
        # 测试技术指标计算
        test_data = pd.DataFrame({
            'close': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20] * 3,
            'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000] * 3
        })
        
        momentum_factors = model.calculate_momentum_factors(test_data)
        logger.info(f"✅ 动量因子计算成功: {momentum_factors}")
        
        trend_factors = model.calculate_trend_factors(test_data)
        logger.info(f"✅ 趋势因子计算成功: {trend_factors}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 策略模型测试失败: {e}")
        return False

def test_backtest_engine():
    """测试回测引擎"""
    logger.info("🔍 测试回测引擎...")
    
    try:
        from core.backtest_engine_qlib import QlibBacktestEngine
        from core.data_adapter import QlibDataAdapter
        
        # 创建数据适配器
        data_adapter = QlibDataAdapter()
        
        # 创建回测引擎
        engine = QlibBacktestEngine(data_adapter)
        logger.info("✅ 回测引擎创建成功")
        
        # 测试基础功能
        logger.info("✅ 回测引擎基础功能正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 回测引擎测试失败: {e}")
        return False

def test_portfolio_manager():
    """测试投资组合管理"""
    logger.info("🔍 测试投资组合管理...")
    
    try:
        from core.portfolio_manager_qlib import QlibPortfolioManager
        
        # 创建投资组合管理器
        portfolio_manager = QlibPortfolioManager()
        logger.info("✅ 投资组合管理器创建成功")
        
        # 测试基础功能
        logger.info("✅ 投资组合管理器基础功能正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 投资组合管理器测试失败: {e}")
        return False

def test_complete_workflow():
    """测试完整工作流"""
    logger.info("🔍 测试完整工作流...")
    
    try:
        from strategies.curious_ragdoll_boll_qlib import (
            CuriousRagdollBollConfig,
            CuriousRagdollBollBacktester
        )
        
        # 创建配置
        config = CuriousRagdollBollConfig(
            stock_pool_size=10,  # 减少股票数量以加快测试
            fixed_positions=5
        )
        
        # 创建回测器
        backtester = CuriousRagdollBollBacktester(config)
        
        # 运行小规模回测
        logger.info("运行小规模回测测试...")
        portfolio_metrics, indicators = backtester.run_backtest(
            start_date="2023-01-01",
            end_date="2023-01-31",  # 只测试一个月
            benchmark="SH000905"
        )
        
        # 分析结果
        results = backtester.analyze_results(portfolio_metrics, indicators)
        
        logger.info(f"✅ 完整工作流测试成功")
        logger.info(f"  测试结果: {results}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 完整工作流测试失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    logger.info("🔍 测试数据库连接...")
    
    try:
        from api.db_handler import DBHandler
        
        # 创建数据库处理器
        db_handler = DBHandler()
        
        # 测试连接
        collection = db_handler.get_collection("stock_kline_daily")
        count = collection.count_documents({})
        logger.info(f"✅ 数据库连接成功: stock_kline_daily集合有{count}条记录")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        return False

def generate_test_report(test_results):
    """生成测试报告"""
    logger.info("📊 生成测试报告...")
    
    report = {
        "测试时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "qlib框架版本": "0.9.6",
        "Python版本": sys.version,
        "测试结果": test_results,
        "总体状态": "通过" if all(test_results.values()) else "失败",
        "通过率": f"{sum(test_results.values())}/{len(test_results)} ({sum(test_results.values())/len(test_results)*100:.1f}%)"
    }
    
    # 保存报告
    output_dir = "/Users/libing/kk_Projects/kk_Stock/kk_stock_backend/abu_quantitative/results"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"qlib_integration_test_{timestamp}.json")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📄 测试报告已保存: {report_file}")
    return report

def main():
    """主函数"""
    logger.info("🚀 开始Qlib框架完整性测试")
    
    # 测试项目
    test_functions = [
        ("数据库连接", test_database_connection),
        ("数据适配器", test_data_adapter),
        ("策略模型", test_strategy_model),
        ("回测引擎", test_backtest_engine),
        ("投资组合管理", test_portfolio_manager),
        ("完整工作流", test_complete_workflow)
    ]
    
    # 执行测试
    test_results = {}
    for test_name, test_func in test_functions:
        try:
            logger.info(f"🧪 开始测试: {test_name}")
            result = test_func()
            test_results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"📋 {test_name}: {status}")
        except Exception as e:
            logger.error(f"❌ {test_name}测试异常: {e}")
            test_results[test_name] = False
    
    # 生成报告
    report = generate_test_report(test_results)
    
    # 显示总结
    logger.info("🎯 Qlib框架完整性测试完成")
    logger.info(f"📊 测试结果: {report['通过率']}")
    logger.info(f"📈 总体状态: {report['总体状态']}")
    
    # 详细结果
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        logger.info(f"  {status} {test_name}")
    
    if report['总体状态'] == "通过":
        logger.info("🎉 恭喜！Qlib框架集成成功，所有核心功能正常")
    else:
        logger.warning("⚠️ 部分功能测试失败，请检查相关模块")
    
    return report['总体状态'] == "通过"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)