"""
量化策略配置管理器

统一管理三个量化策略的参数配置，避免重复和硬编码
"""

from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StrategyConfig:
    """策略配置基类"""
    name: str
    display_name: str
    version: str
    description: str
    max_positions: int
    max_single_weight: float
    rebalance_frequency: str
    risk_control: Dict[str, float]
    default_allocated_cash: float


class StrategyConfigManager:
    """策略配置管理器"""
    
    def __init__(self):
        self._configs = self._initialize_strategy_configs()
    
    def _initialize_strategy_configs(self) -> Dict[str, StrategyConfig]:
        """初始化所有策略配置"""
        configs = {
            'taishang_1': StrategyConfig(
                name='taishang_1',
                display_name='太上老君1号',
                version='1.0.0',
                description='多趋势共振策略 - 基于MACD、KDJ、成交量等多重指标共振识别投资机会',
                max_positions=8,
                max_single_weight=0.12,
                rebalance_frequency='daily',  # 每日检查
                risk_control={
                    'stop_loss': 0.06,      # 6%止损
                    'take_profit': 0.12,    # 12%止盈
                    'min_resonance_score': 6  # 最小共振得分
                },
                default_allocated_cash=300000
            ),
            
            'taishang_2': StrategyConfig(
                name='taishang_2',
                display_name='太上老君2号',
                version='1.0.0',
                description='好奇布偶猫BOLL策略 - 基于布林带指标的小市值股票择时策略',
                max_positions=10,
                max_single_weight=0.20,
                rebalance_frequency='daily',  # 每日检查
                risk_control={
                    'stop_loss': 0.10,      # 10%止损
                    'take_profit': 0.15,    # 15%止盈
                    'max_position_value': 200000  # 单股最大20万
                },
                default_allocated_cash=400000
            ),
            
            'taishang_3': StrategyConfig(
                name='taishang_3',
                display_name='太上老君3号',
                version='3.4.0',
                description='小市值动量策略 - 基于RSI择时+多因子评分+WR指标+事件驱动调仓',
                max_positions=10,
                max_single_weight=0.12,
                rebalance_frequency='event_driven',  # 事件驱动，每5日调仓
                risk_control={
                    'stop_loss': 0.06,      # 6%止损
                    'take_profit': 0.15,    # 15%止盈
                    'min_total_score': 0.65  # 最低综合得分
                },
                default_allocated_cash=500000
            )
        }
        return configs
    
    def get_strategy_config(self, strategy_name: str) -> StrategyConfig:
        """获取策略配置"""
        if strategy_name not in self._configs:
            raise ValueError(f"不支持的策略: {strategy_name}")
        return self._configs[strategy_name]
    
    def get_all_strategies(self) -> Dict[str, StrategyConfig]:
        """获取所有策略配置"""
        return self._configs.copy()
    
    def get_strategy_adapter_class_name(self, strategy_name: str) -> str:
        """获取策略适配器类名"""
        adapter_mapping = {
            'taishang_1': 'MultiTrendResonanceStrategyAdapter',
            'taishang_2': 'CuriousRagdollBollStrategyAdapter',
            'taishang_3': 'TaiShang3FactorStrategyAdapter'
        }
        return adapter_mapping.get(strategy_name)
    
    def get_strategy_module_path(self, strategy_name: str) -> str:
        """获取策略模块路径"""
        module_mapping = {
            'taishang_1': 'multi_trend_strategy_adapter',
            'taishang_2': 'curious_ragdoll_boll_strategy_adapter',
            'taishang_3': 'taishang_3_factor_strategy_adapter'
        }
        return module_mapping.get(strategy_name)
    
    def validate_strategy_params(self, strategy_name: str, custom_params: Dict[str, Any]) -> Dict[str, Any]:
        """验证和处理自定义策略参数"""
        config = self.get_strategy_config(strategy_name)
        
        # 基本参数验证
        validated_params = {}
        
        # 分配资金验证
        allocated_cash = custom_params.get('allocated_cash', config.default_allocated_cash)
        if allocated_cash <= 0 or allocated_cash > 10000000:
            raise ValueError(f"分配资金必须在0-1000万之间，当前: {allocated_cash}")
        validated_params['allocated_cash'] = allocated_cash
        
        # 持仓数量验证
        max_positions = custom_params.get('max_positions', config.max_positions)
        if max_positions <= 0 or max_positions > 20:
            raise ValueError(f"最大持仓数量必须在1-20之间，当前: {max_positions}")
        validated_params['max_positions'] = max_positions
        
        # 单股权重验证
        max_single_weight = custom_params.get('max_single_weight', config.max_single_weight)
        if max_single_weight <= 0 or max_single_weight > 0.5:
            raise ValueError(f"单股最大权重必须在0-50%之间，当前: {max_single_weight}")
        validated_params['max_single_weight'] = max_single_weight
        
        return validated_params
    
    def get_strategy_display_info(self, strategy_name: str) -> Dict[str, Any]:
        """获取策略展示信息"""
        config = self.get_strategy_config(strategy_name)
        
        return {
            'name': config.name,
            'display_name': config.display_name,
            'version': config.version,
            'description': config.description,
            'max_positions': config.max_positions,
            'max_single_weight': f"{config.max_single_weight:.1%}",
            'rebalance_frequency': self._get_frequency_description(config.rebalance_frequency),
            'risk_control': self._format_risk_control(config.risk_control),
            'default_allocated_cash': f"{config.default_allocated_cash:,}元",
            'suitable_funds': self._get_suitable_funds_range(strategy_name)
        }
    
    def _get_frequency_description(self, frequency: str) -> str:
        """获取调仓频率描述"""
        descriptions = {
            'daily': '每日检查',
            'event_driven': '事件驱动',
            'weekly': '每周调仓',
            'monthly': '每月调仓'
        }
        return descriptions.get(frequency, frequency)
    
    def _format_risk_control(self, risk_control: Dict[str, float]) -> str:
        """格式化风险控制信息"""
        parts = []
        if 'stop_loss' in risk_control:
            parts.append(f"{risk_control['stop_loss']:.0%}止损")
        if 'take_profit' in risk_control:
            parts.append(f"{risk_control['take_profit']:.0%}止盈")
        return "/".join(parts) if parts else "无"
    
    def _get_suitable_funds_range(self, strategy_name: str) -> str:
        """获取策略适合的资金范围"""
        ranges = {
            'taishang_1': '30万-300万',
            'taishang_2': '40万-500万',
            'taishang_3': '50万-1000万'
        }
        return ranges.get(strategy_name, '未知')


# 创建全局配置管理器实例
strategy_config_manager = StrategyConfigManager()