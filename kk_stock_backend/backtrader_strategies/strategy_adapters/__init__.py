#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略适配器子模块
Strategy Adapters Submodule

本模块包含所有策略适配器，用于从API接口层分离出核心选股逻辑。
该架构调整将策略核心逻辑集中管理，API层只负责接口功能。

包含策略：
1. 太上老君1号 - 价值动量策略 (multi_trend_strategy_adapter.py)
2. 太上老君2号 - BOLL择时策略 (curious_ragdoll_boll_strategy_adapter.py)
3. 太上老君3号 - 小市值动量策略 (taishang_3_factor_strategy_adapter.py)
4. 价值投资策略 (value_investment_adapter.py)
5. 成长股策略 (growth_stock_adapter.py)
6. 动量突破策略 (momentum_breakthrough_adapter.py)
7. 高股息策略 (high_dividend_adapter.py)
8. 技术突破策略 (technical_breakthrough_adapter.py)
9. 超跌反弹策略 (oversold_rebound_adapter.py)
10. 连板龙头策略 (limit_up_leader_adapter.py)
11. 资金追踪策略 (fund_flow_tracking_adapter.py)
"""

# 导入策略适配器
from .multi_trend_strategy_adapter import MultiTrendResonanceStrategyAdapter
from .curious_ragdoll_boll_strategy_adapter import CuriousRagdollBollStrategyAdapter
from .taishang_3_factor_strategy_adapter import TaiShang3FactorStrategyAdapter
from .value_investment_adapter import ValueInvestmentAdapter
from .growth_stock_adapter import GrowthStockAdapter
from .momentum_breakthrough_adapter import MomentumBreakthroughAdapter
from .high_dividend_adapter import HighDividendAdapter
from .technical_breakthrough_adapter import TechnicalBreakthroughAdapter
from .oversold_rebound_adapter_simple import OversoldReboundAdapter
from .limit_up_leader_adapter_simple import LimitUpLeaderAdapter
from .fund_flow_tracking_adapter import FundFlowTrackingAdapter

# 策略适配器注册表
STRATEGY_ADAPTERS = {
    # 太上老君系列策略
    "multi_trend_strategy_adapter": MultiTrendResonanceStrategyAdapter,
    "curious_ragdoll_boll_strategy_adapter": CuriousRagdollBollStrategyAdapter,
    "taishang_3_factor_strategy_adapter": TaiShang3FactorStrategyAdapter,
    
    # API策略模版适配器
    "value_investment_adapter": ValueInvestmentAdapter,
    "growth_stock_adapter": GrowthStockAdapter,
    "momentum_breakthrough_adapter": MomentumBreakthroughAdapter,
    "high_dividend_adapter": HighDividendAdapter,
    "technical_breakthrough_adapter": TechnicalBreakthroughAdapter,
    "oversold_rebound_adapter": OversoldReboundAdapter,
    "limit_up_leader_adapter": LimitUpLeaderAdapter,
    "fund_flow_tracking_adapter": FundFlowTrackingAdapter,
}

# 策略类型分类
STRATEGY_TYPES = {
    "value": ["multi_trend_strategy_adapter", "value_investment_adapter"],
    "growth": ["growth_stock_adapter"],
    "momentum": ["momentum_breakthrough_adapter"],
    "dividend": ["high_dividend_adapter"],
    "technical": ["technical_breakthrough_adapter"],
    "rebound": ["oversold_rebound_adapter"],
    "limit_up": ["limit_up_leader_adapter"],
    "fund_flow": ["fund_flow_tracking_adapter"],
    "timing": ["curious_ragdoll_boll_strategy_adapter"],
    "factor": ["taishang_3_factor_strategy_adapter"]
}

def get_strategy_adapter(name: str):
    """
    获取策略适配器类
    
    Args:
        name: 策略适配器名称
        
    Returns:
        策略适配器类，如果未找到则返回None
    """
    return STRATEGY_ADAPTERS.get(name)

def get_all_strategies():
    """
    获取所有策略适配器
    
    Returns:
        策略适配器字典
    """
    return STRATEGY_ADAPTERS.copy()

def get_strategies_by_type(strategy_type: str):
    """
    根据策略类型获取策略适配器
    
    Args:
        strategy_type: 策略类型
        
    Returns:
        该类型的策略适配器名称列表
    """
    return STRATEGY_TYPES.get(strategy_type, [])

def list_all_strategy_names():
    """
    列出所有策略适配器名称
    
    Returns:
        策略适配器名称列表
    """
    return list(STRATEGY_ADAPTERS.keys())

def list_all_strategy_types():
    """
    列出所有策略类型
    
    Returns:
        策略类型列表
    """
    return list(STRATEGY_TYPES.keys())

# 导出的公共接口
__all__ = [
    # 策略适配器类
    'MultiTrendResonanceStrategyAdapter',
    'CuriousRagdollBollStrategyAdapter', 
    'TaiShang3FactorStrategyAdapter',
    'ValueInvestmentAdapter',
    'GrowthStockAdapter',
    'MomentumBreakthroughAdapter',
    'HighDividendAdapter',
    'TechnicalBreakthroughAdapter',
    'OversoldReboundAdapter',
    'LimitUpLeaderAdapter',
    'FundFlowTrackingAdapter',
    
    # 注册表和工具函数
    'STRATEGY_ADAPTERS',
    'STRATEGY_TYPES',
    'get_strategy_adapter',
    'get_all_strategies',
    'get_strategies_by_type',
    'list_all_strategy_names',
    'list_all_strategy_types'
]