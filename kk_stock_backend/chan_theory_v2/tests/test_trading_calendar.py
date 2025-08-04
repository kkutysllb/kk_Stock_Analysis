#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易日历功能测试脚本
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入交易日历功能
from chan_theory_v2.core.trading_calendar import (
    get_nearest_trading_date,
    is_trading_day,
    get_trading_dates,
    get_previous_n_trading_days,
    TradingCalendar
)

# 设置日志级别
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_get_nearest_trading_date():
    """
    测试获取最近交易日功能
    """
    logger.info("=== 测试获取最近交易日功能 ===")
    
    # 测试当前日期
    today = datetime.now()
    nearest_backward = get_nearest_trading_date(today, 'backward')
    nearest_forward = get_nearest_trading_date(today, 'forward')
    
    logger.info(f"当前日期: {today.strftime('%Y-%m-%d')}")
    logger.info(f"向前最近交易日: {nearest_backward.strftime('%Y-%m-%d') if nearest_backward else 'None'}")
    logger.info(f"向后最近交易日: {nearest_forward.strftime('%Y-%m-%d') if nearest_forward else 'None'}")
    
    # 测试字符串格式日期
    date_str = "20230101"  # 2023年1月1日
    nearest_backward = get_nearest_trading_date(date_str, 'backward')
    nearest_forward = get_nearest_trading_date(date_str, 'forward')
    
    logger.info(f"指定日期: {date_str}")
    logger.info(f"向前最近交易日: {nearest_backward.strftime('%Y-%m-%d') if nearest_backward else 'None'}")
    logger.info(f"向后最近交易日: {nearest_forward.strftime('%Y-%m-%d') if nearest_forward else 'None'}")
    
    # 测试带连字符的日期字符串
    date_str = "2023-02-01"  # 2023年2月1日
    nearest_backward = get_nearest_trading_date(date_str, 'backward')
    nearest_forward = get_nearest_trading_date(date_str, 'forward')
    
    logger.info(f"指定日期: {date_str}")
    logger.info(f"向前最近交易日: {nearest_backward.strftime('%Y-%m-%d') if nearest_backward else 'None'}")
    logger.info(f"向后最近交易日: {nearest_forward.strftime('%Y-%m-%d') if nearest_forward else 'None'}")


def test_is_trading_day():
    """
    测试判断是否为交易日功能
    """
    logger.info("\n=== 测试判断是否为交易日功能 ===")
    
    # 测试当前日期
    today = datetime.now()
    is_today_trading = is_trading_day(today)
    logger.info(f"当前日期 {today.strftime('%Y-%m-%d')} 是否为交易日: {is_today_trading}")
    
    # 测试周末日期
    # 找到最近的周六
    days_to_saturday = (5 - today.weekday()) % 7 + 1
    saturday = today + timedelta(days=days_to_saturday)
    is_saturday_trading = is_trading_day(saturday)
    logger.info(f"周六 {saturday.strftime('%Y-%m-%d')} 是否为交易日: {is_saturday_trading}")
    
    # 测试已知的交易日
    known_trading_day = "2023-01-03"  # 2023年1月3日，应该是交易日
    is_known_trading = is_trading_day(known_trading_day)
    logger.info(f"已知日期 {known_trading_day} 是否为交易日: {is_known_trading}")


def test_get_trading_dates():
    """
    测试获取交易日列表功能
    """
    logger.info("\n=== 测试获取交易日列表功能 ===")
    
    # 测试获取过去30天的交易日
    today = datetime.now()
    start_date = today - timedelta(days=30)
    trading_days = get_trading_dates(start_date, today)
    
    logger.info(f"过去30天 ({start_date.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}) 的交易日:")
    for i, day in enumerate(trading_days):
        logger.info(f"  {i+1}. {day.strftime('%Y-%m-%d')}")
    logger.info(f"共 {len(trading_days)} 个交易日")
    
    # 测试获取指定月份的交易日
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    trading_days = get_trading_dates(start_date, end_date)
    
    logger.info(f"2023年1月的交易日:")
    for i, day in enumerate(trading_days):
        logger.info(f"  {i+1}. {day.strftime('%Y-%m-%d')}")
    logger.info(f"共 {len(trading_days)} 个交易日")


def test_get_previous_n_trading_days():
    """
    测试获取前N个交易日功能
    """
    logger.info("\n=== 测试获取前N个交易日功能 ===")
    
    # 测试获取当前日期前5个交易日
    today = datetime.now()
    prev_days = get_previous_n_trading_days(today, 5)
    
    logger.info(f"当前日期 {today.strftime('%Y-%m-%d')} 前5个交易日:")
    for i, day in enumerate(prev_days):
        logger.info(f"  {i+1}. {day.strftime('%Y-%m-%d')}")
    
    # 测试获取指定日期前10个交易日
    specific_date = "2023-02-15"
    prev_days = get_previous_n_trading_days(specific_date, 10)
    
    logger.info(f"指定日期 {specific_date} 前10个交易日:")
    for i, day in enumerate(prev_days):
        logger.info(f"  {i+1}. {day.strftime('%Y-%m-%d')}")


def main():
    """
    主函数
    """
    logger.info("开始测试交易日历功能...")
    
    # 测试获取最近交易日功能
    test_get_nearest_trading_date()
    
    # 测试判断是否为交易日功能
    test_is_trading_day()
    
    # 测试获取交易日列表功能
    test_get_trading_dates()
    
    # 测试获取前N个交易日功能
    test_get_previous_n_trading_days()
    
    logger.info("交易日历功能测试完成!")


if __name__ == "__main__":
    main()