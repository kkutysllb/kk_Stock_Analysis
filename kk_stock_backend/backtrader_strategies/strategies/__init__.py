#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略实现模块
基于8大策略适配器的完整交易策略实现
"""

__version__ = "1.0.0"
__author__ = "KK量化团队"

from .value_investment_strategy import ValueInvestmentStrategy

__all__ = [
    'ValueInvestmentStrategy'
]