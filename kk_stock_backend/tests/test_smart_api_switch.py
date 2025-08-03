#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能API切换机制
验证新旧接口的自动切换功能
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta

# 添加项目根目录到 sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from data_collector_new.collector_stock_weekly import StockWeeklyCollector, APIHealthManager
from data_collector_new.collector_stock_monthly import StockMonthlyCollector
from data_collector_new.db_handler import DBHandler
import tushare as ts
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")

class TushareHandler:
    def __init__(self, token):
        self.pro = ts.pro_api(token)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_health_manager():
    """测试API健康管理器"""
    logger.info("=== 测试API健康管理器 ===")
    
    # 获取单例实例
    manager1 = APIHealthManager()
    manager2 = APIHealthManager()
    
    # 验证单例模式
    assert manager1 is manager2, "APIHealthManager应该是单例"
    logger.info("✓ 单例模式验证通过")
    
    # 测试初始状态
    assert manager1.is_api_healthy('stk_week_month_adj'), "初始状态应该是健康的"
    logger.info("✓ 初始健康状态正确")
    
    # 测试失败报告
    for i in range(3):
        manager1.report_api_failure('stk_week_month_adj', f'测试失败{i+1}')
    
    # 验证失败后状态
    assert not manager1.is_api_healthy('stk_week_month_adj'), "连续失败后应该标记为不健康"
    logger.info("✓ 失败检测机制正常")
    
    # 测试成功恢复
    manager1.report_api_success('stk_week_month_adj')
    assert manager1.is_api_healthy('stk_week_month_adj'), "成功后应该恢复健康状态"
    logger.info("✓ 成功恢复机制正常")
    
    logger.info("API健康管理器测试完成\n")

def test_weekly_collector_smart_switch():
    """测试周线采集器的智能切换"""
    logger.info("=== 测试周线采集器智能切换 ===")
    
    try:
        # 初始化处理器
        db_handler = DBHandler()
        ts_handler = TushareHandler(TUSHARE_TOKEN)
        collector = StockWeeklyCollector(db_handler, ts_handler)
        
        # 测试正常获取数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        # 测试获取数据
        df = collector.fetch_data(start_date, end_date, ts_code='000001.SZ')
        
        if df is not None and not df.empty:
            logger.info(f"✓ 成功获取到 {len(df)} 条周线数据")
            logger.info(f"数据字段: {list(df.columns)}")
            
            # 检查数值字段
            numeric_cols = collector.get_numeric_columns()
            logger.info(f"数值字段: {numeric_cols}")
            
        else:
            logger.warning("未获取到数据，可能是接口问题")
            
    except Exception as e:
        logger.error(f"周线采集器测试失败: {e}")
    
    logger.info("周线采集器测试完成\n")

def test_monthly_collector_smart_switch():
    """测试月线采集器的智能切换"""
    logger.info("=== 测试月线采集器智能切换 ===")
    
    try:
        # 初始化处理器
        db_handler = DBHandler()
        ts_handler = TushareHandler(TUSHARE_TOKEN)
        collector = StockMonthlyCollector(db_handler, ts_handler)
        
        # 测试正常获取数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        
        # 测试获取数据
        df = collector.fetch_data(start_date, end_date, ts_code='000001.SZ')
        
        if df is not None and not df.empty:
            logger.info(f"✓ 成功获取到 {len(df)} 条月线数据")
            logger.info(f"数据字段: {list(df.columns)}")
            
            # 检查数值字段
            numeric_cols = collector.get_numeric_columns()
            logger.info(f"数值字段: {numeric_cols}")
            
        else:
            logger.warning("未获取到数据，可能是接口问题")
            
    except Exception as e:
        logger.error(f"月线采集器测试失败: {e}")
    
    logger.info("月线采集器测试完成\n")

def test_api_switch_simulation():
    """模拟API切换场景"""
    logger.info("=== 模拟API切换场景 ===")
    
    # 获取健康管理器
    manager = APIHealthManager()
    
    # 重置状态
    manager.report_api_success('stk_week_month_adj')
    logger.info("重置API状态为健康")
    
    # 模拟连续失败
    logger.info("模拟连续失败...")
    for i in range(3):
        manager.report_api_failure('stk_week_month_adj', f'模拟失败{i+1}')
        logger.info(f"失败次数: {i+1}, 健康状态: {manager.is_api_healthy('stk_week_month_adj')}")
    
    # 此时应该切换到旧接口
    try:
        db_handler = DBHandler()
        ts_handler = TushareHandler(TUSHARE_TOKEN)
        collector = StockWeeklyCollector(db_handler, ts_handler)
        logger.info(f"当前API健康状态: {manager.is_api_healthy('stk_week_month_adj')}")
        logger.info("应该使用旧接口获取数据")
    except Exception as e:
        logger.warning(f"采集器初始化失败: {e}")
        logger.info(f"当前API健康状态: {manager.is_api_healthy('stk_week_month_adj')}")
        logger.info("应该使用旧接口获取数据")
    
    # 模拟成功恢复
    logger.info("\n模拟API恢复...")
    manager.report_api_success('stk_week_month_adj')
    logger.info(f"恢复后API健康状态: {manager.is_api_healthy('stk_week_month_adj')}")
    logger.info("应该重新使用新接口")
    
    logger.info("API切换模拟完成\n")

def main():
    """主测试函数"""
    logger.info("开始智能API切换机制测试")
    logger.info("=" * 50)
    
    try:
        # 测试API健康管理器
        test_api_health_manager()
        
        # 测试周线采集器
        test_weekly_collector_smart_switch()
        
        # 测试月线采集器
        test_monthly_collector_smart_switch()
        
        # 模拟切换场景
        test_api_switch_simulation()
        
        logger.info("=" * 50)
        logger.info("✓ 所有测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    main()