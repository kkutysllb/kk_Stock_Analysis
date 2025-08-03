#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
太上老君策略配置文件
定义策略的全局配置参数
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DatabaseConfig:
    """
    数据库配置
    """
    host: str = "127.0.0.1"
    port: int = 27017
    database: str = "quant_analysis"
    username: str = "root"
    password: str = "example"
    auth_source: str = "admin"
    
    # 集合名称 - 基于实际数据库结构
    factor_collection: str = "stock_factor_pro"  # 主要因子数据集合
    basic_collection: str = "infrastructure_stock_basic"        # 股票基本信息集合
    
    # 财务数据集合
    financial_indicator_collection: str = "stock_fina_indicator"  # 财务指标数据
    balance_sheet_collection: str = "stock_balance_sheet"         # 资产负债表数据
    income_statement_collection: str = "stock_income"             # 利润表数据
    cash_flow_collection: str = "stock_cash_flow"                 # 现金流量表数据
    
    # 连接配置
    connect_timeout: int = 30000
    server_selection_timeout: int = 30000
    max_pool_size: int = 100
    
    # 字段映射配置
    field_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        """初始化字段映射"""
        if self.field_mapping is None:
            self.field_mapping = {
                # 基础字段映射
                'stock_code': 'ts_code',
                'trade_date': 'trade_date',
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'vol',
                'amount': 'amount',
                
                # 技术指标字段映射 - 修正为实际数据库字段
                'turnover_rate': 'turnover_rate',
                'turnover_rate_f': 'turnover_rate_f',
                'volume_ratio': 'volume_ratio',
                
                # 移动平均线 - 修正为实际字段名
                'ma5': 'ma_bfq_5',
                'ma10': 'ma_bfq_10',
                'ma20': 'ma_bfq_20',
                'ma30': 'ma_bfq_30',
                'ma60': 'ma_bfq_60',
                'ma90': 'ma_bfq_90',
                'ma120': 'ma_bfq_120',
                'ma250': 'ma_bfq_250',
                
                # EMA指标
                'ema5': 'ema_bfq_5',
                'ema10': 'ema_bfq_10',
                'ema20': 'ema_bfq_20',
                'ema30': 'ema_bfq_30',
                'ema60': 'ema_bfq_60',
                'ema90': 'ema_bfq_90',
                'ema250': 'ema_bfq_250',
                
                # RSI指标
                'rsi6': 'rsi_bfq_6',
                'rsi12': 'rsi_bfq_12',
                'rsi24': 'rsi_bfq_24',
                
                # MACD指标 - 修正字段名
                'macd_dif': 'macd_dif_bfq',
                'macd_dea': 'macd_dea_bfq', 
                'macd_macd': 'macd_bfq',
                
                # 布林带指标
                'boll_upper': 'boll_upper_bfq',
                'boll_mid': 'boll_mid_bfq',
                'boll_lower': 'boll_lower_bfq',
                
                # KDJ指标
                'kdj_k': 'kdj_k_bfq',
                'kdj_d': 'kdj_d_bfq',
                'kdj_j': 'kdj_bfq',
                
                # 威廉指标
                'wr1': 'wr1_bfq',
                'wr2': 'wr_bfq',
                
                # 其他技术指标
                'bias1': 'bias1_bfq',
                'bias2': 'bias2_bfq', 
                'bias3': 'bias3_bfq',
                'cci': 'cci_bfq',
                'atr': 'atr_bfq',
                'roc': 'roc_bfq',
                'mtm': 'mtm_bfq',
                'psy': 'psy_bfq',
                'obv': 'obv_bfq',
                'emv': 'emv_bfq',
                'mfi': 'mfi_bfq',
                'vr': 'vr_bfq',
                'mass': 'mass_bfq',
                'cr': 'cr_bfq',
                
                # DMI指标
                'dmi_pdi': 'dmi_pdi_bfq',
                'dmi_mdi': 'dmi_mdi_bfq',
                'dmi_adx': 'dmi_adx_bfq',
                'dmi_adxr': 'dmi_adxr_bfq',
                
                # BRAR指标
                'brar_ar': 'brar_ar_bfq',
                'brar_br': 'brar_br_bfq',
                
                # 其他复合指标
                'asi': 'asi_bfq',
                'asit': 'asit_bfq',
                'trix': 'trix_bfq',
                'dpo': 'dpo_bfq',
                
                # 财务指标字段映射 (来自stock_fina_indicator集合)
                'eps': 'eps',                          # 每股收益
                'bvps': 'bps',                         # 每股净资产 (Book Value Per Share)
                'roe': 'roe',                          # 净资产收益率 (Return on Equity)
                'roa': 'roa_yearly',                   # 资产收益率 (Return on Assets)
                'debt_to_assets': 'debt_to_assets',    # 资产负债率
                'debt_to_equity': 'debt_to_eqt',       # 负债股东权益比
                'current_ratio': 'current_ratio',      # 流动比率
                'quick_ratio': 'quick_ratio',          # 速动比率
                'gross_margin': 'grossprofit_margin',  # 毛利率
                'net_margin': 'netprofit_margin',      # 净利率
                'assets_turnover': 'assets_turn',      # 资产周转率
                'equity_turnover': 'equity_turn',      # 股东权益周转率
                'cfps': 'cfps',                        # 每股现金流
                'ocfps': 'ocfps',                      # 每股经营现金流
                'revenue_ps': 'revenue_ps',            # 每股营收
                'retained_earnings': 'retained_earnings',  # 留存收益
                'total_assets': 'total_assets',        # 总资产
                'total_equity': 'total_hldr_eqy_exc_min_int',  # 股东权益合计
                'revenue_yoy': 'or_yoy',               # 营收同比增长率
                'profit_yoy': 'netprofit_yoy',         # 净利润同比增长率
                'eps_yoy': 'basic_eps_yoy',            # 每股收益同比增长率
                'roe_yoy': 'roe_yoy',                  # ROE同比变化
                'assets_yoy': 'assets_yoy',            # 资产同比增长率
                'equity_yoy': 'equity_yoy',            # 股东权益同比增长率
                
                # PE PB PS 估值指标
                'pe_ttm': 'pe_ttm',                    # 市盈率TTM
                'pb': 'pb',                            # 市净率
                'ps_ttm': 'ps_ttm',                    # 市销率TTM
                'pcf_ratio': 'pcf_ratio',              # 市现率
                
                # 市值相关
                'market_cap': 'circ_mv',               # 流通市值(万元)
                'total_market_cap': 'total_mv',        # 总市值(万元)
                'free_share': 'free_share',            # 自由流通股本
                'total_share': 'total_share',          # 总股本
                
                # 前收盘价和成交量
                'pre_close': 'pre_close',              # 前收盘价
                'volume_ma20': 'vol_ma20'              # 20日成交量均值
            }


@dataclass
class BacktestConfig:
    """
    回测配置
    """
    # 基本配置
    initial_cash: float = 1000000.0  # 初始资金100万
    start_date: str = "2020-01-01"
    end_date: str = "2023-12-31"
    
    # 交易费用
    commission_rate: float = 0.0001  # 万一手续费
    stamp_tax_rate: float = 0.001    # 千一印花税（仅卖出）
    min_commission: float = 5.0      # 最低手续费5元
    
    # 滑点设置
    slippage_rate: float = 0.001     # 千一滑点
    
    # 数据配置
    data_frequency: str = "daily"     # daily, minute, tick
    benchmark: str = "000300.SH"      # 沪深300作为基准
    
    # 输出配置
    output_dir: str = "./results"
    save_trades: bool = True
    save_positions: bool = True
    save_performance: bool = True
    
    # 并行配置
    max_workers: int = 4
    enable_multiprocessing: bool = False


@dataclass
class StrategyConfig:
    """
    策略通用配置
    """
    # 基本参数
    max_positions: int = 20          # 最大持仓数量
    rebalance_frequency: int = 5     # 调仓频率（交易日）
    min_position_value: float = 10000.0  # 最小持仓价值
    
    # 风险控制
    max_single_position: float = 0.1     # 单只股票最大权重10%
    max_sector_weight: float = 0.3       # 单个行业最大权重30%
    stop_loss_pct: float = -0.06         # 止损比例-6%
    take_profit_pct: float = 0.12        # 止盈比例12%
    max_drawdown_limit: float = -0.20    # 最大回撤限制-20%
    
    # 选股过滤
    min_market_cap: float = 50e8         # 最小市值50亿
    max_market_cap: float = 5000e8       # 最大市值5000亿
    min_turnover: float = 0.01           # 最小换手率1%
    max_turnover: float = 0.20           # 最大换手率20%
    min_price: float = 5.0               # 最小股价5元
    max_price: float = 200.0             # 最大股价200元
    
    # 排除条件
    exclude_st: bool = True              # 排除ST股票
    exclude_new_stock_days: int = 60     # 排除上市60天内新股
    exclude_suspended: bool = True       # 排除停牌股票
    
    # 行业配置
    allowed_industries: List[str] = None # 允许的行业，None表示不限制
    excluded_industries: List[str] = None # 排除的行业


@dataclass
class MultiTrendConfig:
    """
    多趋势共振策略配置
    """
    # 均线参数
    sma_short: int = 5
    sma_medium: int = 20
    sma_long: int = 60
    ema_period: int = 12
    
    # RSI参数
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    
    # MACD参数
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    # 成交量参数
    volume_ma_period: int = 20
    volume_ratio_threshold: float = 1.5
    
    # 波动率参数
    volatility_period: int = 20
    volatility_threshold: float = 0.02
    
    # 得分权重
    trend_weight: float = 0.3
    momentum_weight: float = 0.25
    volume_weight: float = 0.2
    technical_weight: float = 0.25
    
    # 选股阈值
    min_score: float = 0.6
    top_n_stocks: int = 50


@dataclass
class BollConfig:
    """
    布林带策略配置
    """
    # 布林带参数
    boll_period: int = 20
    boll_std: float = 2.0
    
    # RSI参数
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    
    # 成交量参数
    volume_ma_period: int = 20
    volume_ratio_threshold: float = 1.2
    
    # 波动率参数
    volatility_period: int = 10
    volatility_threshold: float = 0.015
    
    # 趋势过滤
    trend_ma_period: int = 50
    enable_trend_filter: bool = True
    
    # 买卖信号阈值
    buy_threshold: float = 0.7
    sell_threshold: float = 0.3
    
    # 持仓管理
    max_hold_days: int = 30
    profit_target: float = 0.15


@dataclass
class SmallCapMomentumConfig:
    """
    小市值动量策略配置
    """
    # 市值范围
    min_market_cap: float = 20e8         # 最小市值20亿
    max_market_cap: float = 200e8        # 最大市值200亿
    
    # 动量参数
    momentum_period: int = 20
    momentum_threshold: float = 0.05
    
    # RSI参数
    rsi_period: int = 14
    rsi_min: float = 30.0
    rsi_max: float = 80.0
    
    # 成交量参数
    volume_ma_period: int = 20
    volume_ratio_min: float = 1.0
    volume_ratio_max: float = 5.0
    
    # 价格参数
    price_min: float = 5.0
    price_max: float = 50.0
    
    # 波动率参数
    volatility_period: int = 20
    volatility_min: float = 0.01
    volatility_max: float = 0.05
    
    # 趋势参数
    trend_ma_short: int = 10
    trend_ma_long: int = 30
    
    # 得分权重
    momentum_weight: float = 0.25
    technical_weight: float = 0.2
    volume_weight: float = 0.2
    volatility_weight: float = 0.15
    price_pattern_weight: float = 0.2
    
    # 选股参数
    min_score: float = 0.65
    top_n_stocks: int = 30


@dataclass
class RIMStrategyConfig:
    """
    RIM剩余收益模型策略配置（太上老君3号）
    """
    # RIM估值模型参数
    rim_discount_rate: float = 0.12        # 权益资本成本12%
    rim_terminal_growth: float = 0.03      # 永续增长率3%
    rim_forecast_years: int = 5            # 预测期5年
    rim_book_value_threshold: float = 0.1  # 净资产门槛值
    rim_roe_convergence_rate: float = 0.20 # ROE收敛率20%
    rim_long_term_roe: float = 0.12        # 长期ROE均值12%
    rim_dividend_payout: float = 0.5       # 分红率50%
    
    # RIM估值权重和技术指标权重
    rim_weight: float = 0.60               # RIM估值权重60%
    technical_weight: float = 0.40         # 技术指标权重40%
    
    # 事件驱动交易参数（参考太上老君2号）
    price_rebound_threshold: float = 0.02   # 价格反弹确认阈值2%
    volume_confirm_ratio: float = 1.2       # 成交量确认倍数1.2倍
    volume_selloff_ratio: float = 2.0       # 成交量异常放大卖出倍数2倍
    oversold_ma_threshold: float = 0.90     # 超跌阈值（相对MA20的90%）
    
    # 止盈止损参数
    profit_take_threshold: float = 0.20     # 止盈阈值20%
    profit_pullback_threshold: float = 0.06 # 盈利回撤阈值6%
    stop_loss_threshold: float = 0.12       # 止损阈值12%
    rim_overvaluation_threshold: float = 1.3 # RIM估值高估阈值（价格超过RIM估值30%）
    
    # 买入触发条件参数
    rim_discount_threshold: float = 0.15    # RIM估值折价阈值15%
    min_roe_threshold: float = 0.05         # 最低ROE要求5%
    max_debt_ratio: float = 0.70           # 最高资产负债率70%
    
    # 财务质量过滤参数
    min_eps_threshold: float = 0.01        # 最低EPS阈值
    min_bvps_threshold: float = 1.0        # 最低每股净资产阈值
    max_pe_threshold: float = 100.0        # 最高市盈率阈值（过滤异常值）
    min_revenue_growth: float = -0.30      # 最低营收增长率-30%（允许一定程度下滑）
    
    # 技术指标参数
    ma_period: int = 20                    # 移动平均周期20日
    volatility_period: int = 20            # 波动率计算周期
    momentum_period: int = 10              # 动量指标周期
    volume_ma_period: int = 20             # 成交量均线周期
    
    # 选股和持仓参数
    max_positions: int = 25                # 最大持仓25只
    max_single_weight: float = 0.04        # 单股最大权重4%
    stock_pool_size: int = 50              # 股票池大小50只
    max_position_value: float = 40000      # 单股最大金额4万（100万/25只）
    cash_reserve_ratio: float = 0.05       # 现金储备比例5%
    
    # 风险控制参数
    max_daily_trades: int = 3              # 每日最大交易股票数
    min_holding_days: int = 5              # 最短持有天数
    max_portfolio_turnover: float = 2.0    # 最大组合换手率200%
    
    # 过滤条件
    exclude_st: bool = True                # 排除ST股票
    exclude_suspended: bool = True         # 排除停牌股票
    exclude_new_listed_days: int = 60      # 排除上市60天内新股
    min_market_cap: float = 10e8           # 最小市值10亿
    max_market_cap: float = 1000e8         # 最大市值1000亿（中证1000范围）
    min_price: float = 2.0                 # 最低股价2元


@dataclass
class LoggingConfig:
    """
    日志配置
    """
    log_level: str = "INFO"
    log_dir: str = "./logs"
    max_log_files: int = 30
    enable_file_logging: bool = True
    enable_console_logging: bool = True
    
    # 性能日志
    log_performance_interval: int = 10   # 每10次记录一次性能
    log_trade_details: bool = True
    log_signal_details: bool = True
    
    # 导出配置
    export_format: str = "csv"           # csv, json
    auto_export_interval: int = 100      # 自动导出间隔


class Config:
    """
    主配置类
    整合所有配置项
    """
    
    def __init__(self):
        # 基础配置
        self.strategy_name = "策略"  # 默认策略名称
        self.strategy_type = ""  # 策略类型
        self.database = DatabaseConfig()
        self.backtest = BacktestConfig()
        self.strategy = StrategyConfig()
        self.logging = LoggingConfig()
        
        # 策略特定配置
        self.multi_trend = MultiTrendConfig()
        self.boll = BollConfig()
        self.small_cap_momentum = SmallCapMomentumConfig()
        self.rim_strategy = RIMStrategyConfig()  # 太上老君3号RIM策略配置
        
        # 从环境变量加载配置
        self._load_from_env()
    
    def _load_from_env(self):
        """
        从环境变量加载配置
        """
        # 数据库配置
        if os.getenv('MONGO_HOST'):
            self.database.host = os.getenv('MONGO_HOST')
        if os.getenv('MONGO_PORT'):
            self.database.port = int(os.getenv('MONGO_PORT'))
        if os.getenv('MONGO_DATABASE'):
            self.database.database = os.getenv('MONGO_DATABASE')
        if os.getenv('MONGO_USERNAME'):
            self.database.username = os.getenv('MONGO_USERNAME')
        if os.getenv('MONGO_PASSWORD'):
            self.database.password = os.getenv('MONGO_PASSWORD')
        
        # 回测配置
        if os.getenv('INITIAL_CASH'):
            self.backtest.initial_cash = float(os.getenv('INITIAL_CASH'))
        if os.getenv('START_DATE'):
            self.backtest.start_date = os.getenv('START_DATE')
        if os.getenv('END_DATE'):
            self.backtest.end_date = os.getenv('END_DATE')
        
        # 日志配置
        if os.getenv('LOG_LEVEL'):
            self.logging.log_level = os.getenv('LOG_LEVEL')
        if os.getenv('LOG_DIR'):
            self.logging.log_dir = os.getenv('LOG_DIR')
    
    def get_strategy_config(self, strategy_name: str) -> Any:
        """
        获取特定策略的配置
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            策略配置对象
        """
        strategy_configs = {
            'multi_trend': self.multi_trend,
            'boll': self.boll,
            'small_cap_momentum': self.small_cap_momentum,
            'rim_strategy': self.rim_strategy,
            'taishang_3': self.rim_strategy  # 太上老君3号策略别名
        }
        
        return strategy_configs.get(strategy_name.lower())
    
    def update_config(self, config_dict: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config_dict: 配置字典
        """
        for section, values in config_dict.items():
            if hasattr(self, section):
                config_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            配置字典
        """
        return {
            'database': self.database.__dict__,
            'backtest': self.backtest.__dict__,
            'strategy': self.strategy.__dict__,
            'logging': self.logging.__dict__,
            'multi_trend': self.multi_trend.__dict__,
            'boll': self.boll.__dict__,
            'small_cap_momentum': self.small_cap_momentum.__dict__,
            'rim_strategy': self.rim_strategy.__dict__
        }
    
    def validate(self) -> List[str]:
        """
        验证配置的有效性
        
        Returns:
            错误信息列表
        """
        errors = []
        
        # 验证回测配置
        try:
            start_date = datetime.strptime(self.backtest.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(self.backtest.end_date, '%Y-%m-%d')
            if start_date >= end_date:
                errors.append("开始日期必须早于结束日期")
        except ValueError:
            errors.append("日期格式错误，应为YYYY-MM-DD")
        
        # 验证资金配置
        if self.backtest.initial_cash <= 0:
            errors.append("初始资金必须大于0")
        
        # 验证策略配置
        if self.strategy.max_positions <= 0:
            errors.append("最大持仓数量必须大于0")
        
        if self.strategy.max_single_position <= 0 or self.strategy.max_single_position > 1:
            errors.append("单只股票最大权重必须在0-1之间")
        
        # 验证风险参数
        if self.strategy.stop_loss_pct >= 0:
            errors.append("止损比例必须为负数")
        
        if self.strategy.take_profit_pct <= 0:
            errors.append("止盈比例必须为正数")
        
        return errors


# 全局配置实例
config = Config()


# 预定义配置模板
CONFIG_TEMPLATES = {
    'conservative': {
        'strategy': {
            'max_positions': 15,
            'stop_loss_pct': -0.10,
            'take_profit_pct': 0.20,
            'max_single_position': 0.08
        },
        'multi_trend': {
            'min_score': 0.7,
            'top_n_stocks': 30
        }
    },
    'aggressive': {
        'strategy': {
            'max_positions': 30,
            'stop_loss_pct': -0.20,
            'take_profit_pct': 0.40,
            'max_single_position': 0.15
        },
        'multi_trend': {
            'min_score': 0.5,
            'top_n_stocks': 80
        }
    },
    'balanced': {
        'strategy': {
            'max_positions': 20,
            'stop_loss_pct': -0.06,
            'take_profit_pct': 0.12,
            'max_single_position': 0.10
        },
        'multi_trend': {
            'min_score': 0.6,
            'top_n_stocks': 50
        }
    }
}


def load_config_template(template_name: str) -> Config:
    """
    加载配置模板
    
    Args:
        template_name: 模板名称 ('conservative', 'aggressive', 'balanced')
        
    Returns:
        配置对象
    """
    if template_name not in CONFIG_TEMPLATES:
        raise ValueError(f"未知的配置模板: {template_name}")
    
    new_config = Config()
    new_config.update_config(CONFIG_TEMPLATES[template_name])
    
    return new_config


def main():
    """
    主函数：演示配置的使用
    """
    # 创建默认配置
    cfg = Config()
    
    # 验证配置
    errors = cfg.validate()
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("配置验证通过")
    
    # 显示配置信息
    print(f"\n数据库配置:")
    print(f"  主机: {cfg.database.host}:{cfg.database.port}")
    print(f"  数据库: {cfg.database.database}")
    
    print(f"\n回测配置:")
    print(f"  初始资金: {cfg.backtest.initial_cash:,.0f}")
    print(f"  回测期间: {cfg.backtest.start_date} 至 {cfg.backtest.end_date}")
    print(f"  手续费率: {cfg.backtest.commission_rate:.4f}")
    
    print(f"\n策略配置:")
    print(f"  最大持仓: {cfg.strategy.max_positions}")
    print(f"  调仓频率: {cfg.strategy.rebalance_frequency}天")
    print(f"  止损比例: {cfg.strategy.stop_loss_pct:.1%}")
    print(f"  止盈比例: {cfg.strategy.take_profit_pct:.1%}")
    
    # 测试配置模板
    print("\n测试保守型配置模板:")
    conservative_config = load_config_template('conservative')
    print(f"  最大持仓: {conservative_config.strategy.max_positions}")
    print(f"  最小得分: {conservative_config.multi_trend.min_score}")


if __name__ == '__main__':
    main()