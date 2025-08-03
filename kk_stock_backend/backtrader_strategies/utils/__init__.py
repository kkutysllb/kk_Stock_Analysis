#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块
提供通用的辅助功能
"""

__version__ = "1.0.0"
__author__ = "太上老君量化团队"

# 导入工具类
from .visualization_config import init_visualization, get_chinese_font

# 自动初始化可视化配置
init_visualization()

__all__ = [
    'init_visualization',
    'get_chinese_font'
]