#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtrader量化策略模块
基于太上老君三大策略的完整回测系统
"""

import sys
import os

# 添加项目根目录到路径，确保所有模块都能正确导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

__version__ = "1.0.0"
__author__ = "KK Stock Backend"

# 导入配置类
from .config import Config

# 导入策略相关模块
from .strategies import *
from .data_feed import *
from .utils import *

# 导入回测引擎（如果存在）
try:
    from .backtest.backtest_engine import StrategyInterface
except ImportError:
    # 如果backtest模块不存在，创建一个基础接口
    class StrategyInterface:
        """策略接口基类"""
        def initialize(self, context):
            pass
        
        def generate_signals(self, current_date, market_data, portfolio_info):
            return []

# 导入策略适配器
try:
    from .multi_trend_strategy_adapter import MultiTrendResonanceStrategyAdapter
except ImportError:
    MultiTrendResonanceStrategyAdapter = None

try:
    from .curious_ragdoll_boll_strategy_adapter import CuriousRagdollBollStrategyAdapter
except ImportError:
    CuriousRagdollBollStrategyAdapter = None

try:
    from .taishang_3_factor_strategy_adapter import TaiShang3FactorStrategyAdapter
except ImportError:
    TaiShang3FactorStrategyAdapter = None

# 导出主要类和函数
__all__ = [
    'Config',
    'StrategyInterface',
    'MultiTrendResonanceStrategyAdapter',
    'CuriousRagdollBollStrategyAdapter', 
    'TaiShang3FactorStrategyAdapter'
]