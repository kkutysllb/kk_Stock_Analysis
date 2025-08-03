#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共回测引擎模块
支持多策略、真实数据、A股交易规则的专业回测系统
"""

__version__ = "1.0.0"
__author__ = "KK股票量化团队"

from .backtest_engine import BacktestEngine
from .trading_simulator import TradingSimulator
from .data_manager import DataManager
from .portfolio_manager import PortfolioManager
from .performance_analyzer import PerformanceAnalyzer
from .order_manager import OrderManager

__all__ = [
    'BacktestEngine',
    'TradingSimulator', 
    'DataManager',
    'PortfolioManager',
    'PerformanceAnalyzer',
    'OrderManager'
]