#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局数据库处理器单例
解决连接泄露问题 - 所有路由文件共享同一个数据库处理器实例
"""

import logging
from api.db_handler import get_db_handler

logger = logging.getLogger(__name__)

# 全局数据库处理器单例实例
_global_db_handler = None

def get_global_db_handler():
    """获取全局数据库处理器单例 - 所有路由文件共享同一个实例"""
    global _global_db_handler
    
    if _global_db_handler is None:
        logger.info("🔧 初始化全局数据库处理器单例")
        _global_db_handler = get_db_handler()
        logger.info("✅ 全局数据库处理器单例创建成功")
    
    return _global_db_handler

# 向后兼容的全局变量
db_handler = get_global_db_handler()