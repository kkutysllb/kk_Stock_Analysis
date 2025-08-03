#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时回测接口兼容性模块
该文件重新导向到统一的回测接口
注意：此接口已合并到 backtest_unified.py 中
"""

# 重新导出统一接口中的实时相关内容
from .backtest_unified import (
    router,
    active_tasks,
    get_current_user_sse,
    sse_generator,
    update_task_realtime_data
)

# 向后兼容性警告
import warnings
from api.global_db import db_handler
warnings.warn(
    "backtest_realtime 模块已合并到 backtest_unified 中，建议更新导入路径",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    'router',
    'active_tasks',
    'get_current_user_sse', 
    'sse_generator',
    'update_task_realtime_data'
]