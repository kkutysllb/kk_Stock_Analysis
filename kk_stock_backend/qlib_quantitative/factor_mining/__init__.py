#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能因子挖掘系统
基于261个技术因子挖掘中证A500指数成分股的收益相关因子
"""

from .core.factor_analyzer import FactorAnalyzer
from .core.factor_selector import FactorSelector
from .core.model_trainer import ModelTrainer

__version__ = "1.0.0"
__author__ = "KK Stock Analysis Team"

__all__ = [
    "FactorAnalyzer",
    "FactorSelector", 
    "ModelTrainer"
]