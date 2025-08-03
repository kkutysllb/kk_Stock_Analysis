#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测接口兼容性模块
该文件重新导向到统一的回测接口
"""

# 重新导出统一接口的所有内容，保持向后兼容性
from .backtest_unified import (
    router,
    active_tasks,
    BacktestConfig,
    BacktestTask, 
    BacktestResult,
    StrategyInfo,
    get_current_user,
    run_backtest_task,
    update_task_realtime_data
)

# 兼容性别名
get_current_user_sse = get_current_user

__all__ = [
    'router',
    'active_tasks', 
    'BacktestConfig',
    'BacktestTask',
    'BacktestResult', 
    'StrategyInfo',
    'get_current_user',
    'get_current_user_sse',
    'run_backtest_task',
    'update_task_realtime_data'
]