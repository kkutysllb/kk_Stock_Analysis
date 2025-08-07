#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子挖掘可视化模块
提供因子分析结果的可视化和报告生成功能
"""

try:
    from .factor_reporter import FactorReporter
    from .visualization_engine import VisualizationEngine
except ImportError as e:
    # 如果导入失败，定义一个占位符类
    class FactorReporter:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"FactorReporter 导入失败: {e}")
    
    class VisualizationEngine:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"VisualizationEngine 导入失败: {e}")

__version__ = "1.0.0"
__author__ = "KK Stock Analysis Team"

__all__ = [
    "FactorReporter",
    "VisualizationEngine"
]