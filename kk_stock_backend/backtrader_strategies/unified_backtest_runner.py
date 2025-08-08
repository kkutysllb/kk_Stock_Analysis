#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一回测器脚本
支持8大策略的统一回测框架，提供完整的策略选择和参数配置功能
"""

import sys
import os
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# 导入回测引擎核心模块
from backtrader_strategies.backtest.backtest_engine import BacktestEngine
from backtrader_strategies.config import Config
from backtrader_strategies.strategy_adapters import STRATEGY_ADAPTERS, STRATEGY_TYPES

# 导入量化策略实现（根据分层架构，只导入4个量化策略）
# TODO: 按优先级顺序实现4个量化策略
# from backtrader_strategies.strategies.technical_breakthrough_strategy import TechnicalBreakthroughStrategy
# from backtrader_strategies.strategies.momentum_breakthrough_strategy import MomentumBreakthroughStrategy
# from backtrader_strategies.strategies.oversold_rebound_strategy import OversoldReboundStrategy
# from backtrader_strategies.strategies.limit_up_leader_strategy import LimitUpLeaderStrategy


class UnifiedBacktestRunner:
    """
    量化策略统一回测器
    支持4大量化策略的统一回测框架
    
    量化策略列表（按适用性排序）:
    1. 技术突破策略 (95% 量化适用性)
    2. 动量突破策略 (90% 量化适用性) 
    3. 超跌反弹策略 (85% 量化适用性)
    4. 连板龙头策略 (80% 量化适用性)
    """
    
    def __init__(self):
        """初始化统一回测器"""
        self.logger = logging.getLogger(__name__)
        self.config = None
        self.backtest_engine = None
        self.strategy = None
        
        # 量化策略实现映射（仅包含4个量化策略）
        self.strategy_implementations = {
            # 按量化适用性排序，优先实现
            # 'technical_breakthrough_adapter': TechnicalBreakthroughStrategy,      # 95% 量化适用性 - 优先级1
            # 'momentum_breakthrough_adapter': MomentumBreakthroughStrategy,        # 90% 量化适用性 - 优先级2
            # 'oversold_rebound_adapter': OversoldReboundStrategy,                  # 85% 量化适用性 - 优先级3
            # 'limit_up_leader_adapter': LimitUpLeaderStrategy,                     # 80% 量化适用性 - 优先级4
        }
        
        # 4大量化策略序号映射（按量化适用性排序）
        self.strategy_order = [
            'technical_breakthrough_adapter',# 1. 技术突破策略 (95% 量化适用性)
            'momentum_breakthrough_adapter', # 2. 动量突破策略 (90% 量化适用性)
            'oversold_rebound_adapter',      # 3. 超跌反弹策略 (85% 量化适用性)
            'limit_up_leader_adapter',       # 4. 连板龙头策略 (80% 量化适用性)
        ]
        
        # 量化策略友好名称映射
        self.strategy_display_names = {
            'technical_breakthrough_adapter': '技术突破策略',
            'momentum_breakthrough_adapter': '动量突破策略',
            'oversold_rebound_adapter': '超跌反弹策略',
            'limit_up_leader_adapter': '连板龙头策略',
        }
        
        # 序号到策略的映射
        self.strategy_by_number = {
            str(i+1): strategy for i, strategy in enumerate(self.strategy_order)
        }
        
        # 基准指数映射
        self.benchmark_indices = {
            '上证指数': '000001.SH',
            '沪深300': '000300.SH', 
            '中证500': '000905.SH',
            '中证1000': '000852.SH',
            '创业板指': '399006.SZ',
            '科创50': '000688.SH',
            '深证成指': '399001.SZ',
            '中小板指': '399005.SZ'
        }
        
        # 基准指数序号映射
        self.benchmark_order = [
            '上证指数',   # 1
            '沪深300',    # 2  
            '中证500',    # 3
            '中证1000',   # 4
            '创业板指',   # 5
            '科创50',     # 6
            '深证成指',   # 7
            '中小板指'    # 8
        ]
        
        self.benchmark_by_number = {
            str(i+1): self.benchmark_indices[name] for i, name in enumerate(self.benchmark_order)
        }
    
    def setup_logging(self, log_level: str = "INFO", log_file: str = None):
        """
        设置日志配置
        
        Args:
            log_level: 日志级别
            log_file: 日志文件路径（可选）
        """
        # 创建results目录
        results_dir = os.path.join(current_dir, "results")
        os.makedirs(results_dir, exist_ok=True)
        
        # 默认日志文件
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(results_dir, f"unified_backtest_{timestamp}.log")
        
        # 配置日志格式
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file, encoding='utf-8')
            ]
        )
        
        self.logger.info(f"📝 日志系统初始化完成，日志文件: {log_file}")
    
    def create_backtest_config(self,
                             strategy_type: str,
                             start_date: str,
                             end_date: str,
                             initial_cash: float = 1000000.0,
                             **kwargs) -> Config:
        """
        创建回测配置
        
        Args:
            strategy_type: 策略类型
            start_date: 回测开始日期 (YYYY-MM-DD)
            end_date: 回测结束日期 (YYYY-MM-DD)
            initial_cash: 初始资金
            **kwargs: 其他配置参数
            
        Returns:
            配置对象
        """
        config = Config()
        
        # 回测基本配置
        config.backtest.initial_cash = initial_cash
        config.backtest.start_date = start_date
        config.backtest.end_date = end_date
        config.backtest.commission_rate = kwargs.get('commission_rate', 0.0001)  # 万三手续费
        config.backtest.stamp_tax_rate = kwargs.get('stamp_tax_rate', 0.001)     # 千一印花税
        config.backtest.slippage_rate = kwargs.get('slippage_rate', 0.001)       # 千一滑点
        config.backtest.min_commission = kwargs.get('min_commission', 5.0)       # 最低5元手续费
        
        # 策略配置
        config.strategy.max_positions = kwargs.get('max_positions', 10)
        config.strategy.max_single_position = kwargs.get('max_single_position', 0.08)
        config.strategy.stop_loss_pct = kwargs.get('stop_loss_pct', -0.15)
        config.strategy.take_profit_pct = kwargs.get('take_profit_pct', 0.30)
        config.strategy.max_drawdown_limit = kwargs.get('max_drawdown_limit', -0.25)
        
        # 策略特定配置
        config.strategy_type = strategy_type
        config.strategy_name = self.strategy_display_names.get(strategy_type, strategy_type)
        
        # 输出配置
        config.backtest.output_dir = os.path.join(current_dir, "results")
        config.backtest.save_trades = True
        config.backtest.save_positions = True
        config.backtest.save_performance = True
        
        # 基准配置 - 解析基准输入
        benchmark_input = kwargs.get('benchmark', '1')  # 默认上证指数（序号1）
        config.backtest.benchmark = self.resolve_benchmark(benchmark_input)
        
        # 数据配置
        config.backtest.data_source = kwargs.get('data_source', 'mongodb')
        
        # 获取基准名称用于显示
        benchmark_name = None
        for name, code in self.benchmark_indices.items():
            if code == config.backtest.benchmark:
                benchmark_name = name
                break
        benchmark_display = f"{benchmark_name}({config.backtest.benchmark})" if benchmark_name else config.backtest.benchmark
        
        self.logger.info(f"📋 回测配置创建完成:")
        self.logger.info(f"   策略类型: {strategy_type}")
        self.logger.info(f"   回测时间: {start_date} 至 {end_date}")
        self.logger.info(f"   初始资金: {initial_cash:,.0f}元")
        self.logger.info(f"   最大持仓: {config.strategy.max_positions}只")
        self.logger.info(f"   单股仓位: {config.strategy.max_single_position:.1%}")
        self.logger.info(f"   基准指数: {benchmark_display}")
        
        return config
    
    def resolve_strategy_type(self, strategy_input: str) -> str:
        """
        解析策略类型输入，支持序号和策略名称
        
        Args:
            strategy_input: 策略输入（序号1-8或策略名称）
            
        Returns:
            策略类型名称
        """
        # 如果是数字，转换为策略名称
        if strategy_input.isdigit():
            strategy_name = self.strategy_by_number.get(strategy_input)
            if strategy_name is None:
                valid_numbers = list(self.strategy_by_number.keys())
                raise ValueError(f"不支持的策略序号: {strategy_input}，可用序号: {valid_numbers}")
            return strategy_name
        
        # 如果是策略名称，直接验证
        if strategy_input in self.strategy_display_names:
            return strategy_input
        
        # 检查是否是中文显示名称
        for strategy_type, display_name in self.strategy_display_names.items():
            if strategy_input == display_name:
                return strategy_type
        
        # 都不匹配
        available = list(self.strategy_display_names.keys())
        raise ValueError(f"不支持的策略类型: {strategy_input}，可用策略: {available}")
    
    def resolve_benchmark(self, benchmark_input: str) -> str:
        """
        解析基准指数输入，支持序号、中文名称和指数代码
        
        Args:
            benchmark_input: 基准输入（序号1-8、中文名称或指数代码）
            
        Returns:
            基准指数代码
        """
        # 如果是数字，转换为指数代码
        if benchmark_input.isdigit():
            benchmark_code = self.benchmark_by_number.get(benchmark_input)
            if benchmark_code is None:
                valid_numbers = list(self.benchmark_by_number.keys())
                raise ValueError(f"不支持的基准序号: {benchmark_input}，可用序号: {valid_numbers}")
            return benchmark_code
        
        # 如果是中文名称，转换为指数代码
        if benchmark_input in self.benchmark_indices:
            return self.benchmark_indices[benchmark_input]
        
        # 如果已经是指数代码，直接返回
        if benchmark_input in self.benchmark_indices.values():
            return benchmark_input
        
        # 都不匹配，使用默认值
        self.logger.warning(f"无法识别基准: {benchmark_input}，使用默认基准: 沪深300")
        return self.benchmark_indices['沪深300']
    
    def list_available_strategies(self) -> Dict[str, Any]:
        """
        列出所有可用的策略
        
        Returns:
            策略信息字典
        """
        strategies_info = {}
        
        # 按序号顺序排列策略
        for i, strategy_type in enumerate(self.strategy_order):
            strategy_class = self.strategy_implementations.get(strategy_type)
            display_name = self.strategy_display_names.get(strategy_type, strategy_type)
            adapter_class = STRATEGY_ADAPTERS.get(strategy_type)
            
            strategies_info[strategy_type] = {
                'number': i + 1,
                'display_name': display_name,
                'implementation_class': strategy_class.__name__ if strategy_class else None,
                'adapter_class': adapter_class.__name__ if adapter_class else None,
                'implemented': strategy_class is not None,
                'description': self._get_strategy_description(strategy_type)
            }
        
        return strategies_info
    
    def _get_strategy_description(self, strategy_type: str) -> str:
        """获取量化策略描述"""
        descriptions = {
            'technical_breakthrough_adapter': '基于多种技术指标的综合突破形态识别，95%量化适用性',
            'momentum_breakthrough_adapter': '捕捉技术指标突破信号，追踪趋势动量，90%量化适用性',
            'oversold_rebound_adapter': '捕捉超跌股票的反弹机会，短期交易策略，85%量化适用性',
            'limit_up_leader_adapter': '追踪涨停板龙头股票，捕捉强势行情，80%量化适用性',
        }
        return descriptions.get(strategy_type, '暂无描述')
    
    def resolve_strategy_type(self, strategy_input: str) -> str:
        """
        解析策略输入（支持序号或策略名称）
        
        Args:
            strategy_input: 策略输入（序号或策略名称）
            
        Returns:
            策略类型
        """
        # 如果是数字，从序号映射中获取
        if strategy_input.isdigit():
            strategy_type = self.strategy_by_number.get(strategy_input)
            if strategy_type is None:
                available_numbers = list(self.strategy_by_number.keys())
                raise ValueError(f"不支持的策略序号: {strategy_input}，可用序号: {available_numbers}")
            return strategy_type
        
        # 如果是策略名称
        if strategy_input in self.strategy_order:
            return strategy_input
        
        # 如果都不匹配
        available_strategies = [f"{i+1}. {self.strategy_display_names[s]}" for i, s in enumerate(self.strategy_order)]
        raise ValueError(f"不支持的策略: {strategy_input}，可用策略:\n" + "\n".join(available_strategies))
    
    def resolve_benchmark(self, benchmark_input: str) -> str:
        """
        解析基准指数输入（支持序号、中文名称或指数代码）
        
        Args:
            benchmark_input: 基准输入（序号、中文名称或指数代码）
            
        Returns:
            基准指数代码
        """
        # 如果是数字，从序号映射中获取
        if benchmark_input.isdigit():
            benchmark_code = self.benchmark_by_number.get(benchmark_input)
            if benchmark_code is None:
                available_numbers = list(self.benchmark_by_number.keys())
                raise ValueError(f"不支持的基准序号: {benchmark_input}，可用序号: {available_numbers}")
            return benchmark_code
        
        # 如果是中文名称
        if benchmark_input in self.benchmark_indices:
            return self.benchmark_indices[benchmark_input]
        
        # 如果是指数代码（包含.）
        if '.' in benchmark_input:
            # 验证是否为有效的指数代码格式
            valid_codes = list(self.benchmark_indices.values())
            if benchmark_input in valid_codes:
                return benchmark_input
            else:
                self.logger.warning(f"未知的指数代码: {benchmark_input}，将直接使用")
                return benchmark_input
        
        # 如果都不匹配
        available_benchmarks = [f"{i+1}. {name}" for i, name in enumerate(self.benchmark_order)]
        raise ValueError(f"不支持的基准: {benchmark_input}，可用基准:\n" + "\n".join(available_benchmarks))
    
    def list_available_benchmarks(self) -> Dict[str, str]:
        """
        列出所有可用的基准指数
        
        Returns:
            基准指数映射字典
        """
        return {
            'benchmarks': [
                {
                    'number': i + 1,
                    'name': name,
                    'code': self.benchmark_indices[name],
                    'description': self._get_benchmark_description(name)
                }
                for i, name in enumerate(self.benchmark_order)
            ]
        }
    
    def _get_benchmark_description(self, benchmark_name: str) -> str:
        """获取基准指数描述"""
        descriptions = {
            '上证指数': '上海证券交易所综合股价指数，反映A股整体表现',
            '沪深300': '沪深两市市值最大的300只股票，代表大盘蓝筹',
            '中证500': '中等市值股票代表，排除沪深300后的500只股票',
            '中证1000': '小盘股代表，排除沪深300和中证500后的1000只股票',
            '创业板指': '创业板市场代表性指数，反映成长股表现',
            '科创50': '科创板最具代表性的50只股票',
            '深证成指': '深圳证券交易所成份股指数',
            '中小板指': '中小板块代表性指数'
        }
        return descriptions.get(benchmark_name, '暂无描述')
    
    def create_strategy(self, strategy_input: str) -> Any:
        """
        创建策略实例
        
        Args:
            strategy_input: 策略输入（序号或策略名称）
            
        Returns:
            策略实例
        """
        # 解析策略类型
        strategy_type = self.resolve_strategy_type(strategy_input)
        
        if strategy_type not in self.strategy_implementations:
            available_strategies = list(self.strategy_implementations.keys())
            raise ValueError(f"不支持的策略类型: {strategy_type}，可用策略: {available_strategies}")
        
        strategy_class = self.strategy_implementations[strategy_type]
        if strategy_class is None:
            raise NotImplementedError(f"策略 {strategy_type} 尚未实现")
        
        strategy = strategy_class()
        display_name = self.strategy_display_names.get(strategy_type, strategy_type)
        
        self.logger.info(f"🎯 策略创建完成: {display_name}")
        return strategy
    
    def run_backtest(self,
                    strategy_type: str,
                    start_date: str,
                    end_date: str,
                    initial_cash: float = 1000000.0,
                    **kwargs) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            strategy_type: 策略类型
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_cash: 初始资金
            **kwargs: 其他配置参数
            
        Returns:
            回测结果
        """
        try:
            # 1. 解析策略类型（将序号转换为策略名称）
            resolved_strategy_type = self.resolve_strategy_type(strategy_type)
            
            # 2. 创建配置
            self.config = self.create_backtest_config(
                strategy_type=resolved_strategy_type,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                **kwargs
            )
            
            # 3. 创建策略  
            self.strategy = self.create_strategy(resolved_strategy_type)
            
            # 4. 创建回测引擎
            self.backtest_engine = BacktestEngine(self.config)
            self.logger.info(f"🚀 回测引擎初始化完成")
            
            # 5. 设置策略
            self.backtest_engine.set_strategy(self.strategy)
            self.logger.info(f"🎯 策略设置完成")
            
            # 5.1 从策略参数更新配置
            strategy_info = self.strategy.get_strategy_info()
            if 'max_single_position' in strategy_info:
                self.config.strategy.max_single_position = strategy_info['max_single_position']
                self.logger.info(f"📊 从策略更新配置: max_single_position = {strategy_info['max_single_position']:.1%}")
            if 'max_positions' in strategy_info:
                self.config.strategy.max_positions = strategy_info['max_positions']
                self.logger.info(f"📊 从策略更新配置: max_positions = {strategy_info['max_positions']}")
            
            # 6. 加载数据（策略适配器选股 + 数据加载）
            self.logger.info(f"📊 开始加载数据和选股...")
            self.backtest_engine.load_data(
                stock_codes=kwargs.get('stock_codes', None),
                max_stocks=kwargs.get('max_stocks', 50)
            )
            self.logger.info(f"📊 数据加载和选股完成")
            
            # 6. 运行回测
            self.logger.info(f"🔄 开始运行回测...")
            start_time = datetime.now()
            
            # 检查是否是异步方法
            backtest_result = self.backtest_engine.run_backtest()
            if hasattr(backtest_result, '__await__'):
                # 如果是协程，需要异步运行
                import asyncio
                result = asyncio.run(backtest_result)
            else:
                result = backtest_result
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"✅ 回测完成，耗时: {duration:.2f}秒")
            
            # 7. 添加执行统计信息
            result['execution_stats'] = {
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration_seconds': duration,
                'strategy_type': resolved_strategy_type,
                'strategy_display_name': self.strategy_display_names.get(resolved_strategy_type, resolved_strategy_type)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 回测执行失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def print_backtest_summary(self, result: Dict[str, Any]):
        """
        打印回测结果摘要
        
        Args:
            result: 回测结果
        """
        print("\n" + "="*100)
        print("🎯 KK量化策略回测结果摘要")
        print("="*100)
        
        # 执行信息
        exec_stats = result.get('execution_stats', {})
        print(f"\n⚡ 执行信息:")
        print(f"   策略名称: {exec_stats.get('strategy_display_name', 'N/A')}")
        print(f"   开始时间: {exec_stats.get('start_time', 'N/A')}")
        print(f"   结束时间: {exec_stats.get('end_time', 'N/A')}")
        print(f"   执行耗时: {exec_stats.get('duration_seconds', 0):.2f}秒")
        
        # 基本信息
        config_info = result.get('backtest_config', {})
        print(f"\n📋 回测配置:")
        print(f"   初始资金: {config_info.get('initial_cash', 0):,.0f}元")
        print(f"   回测期间: {config_info.get('start_date', 'N/A')} 至 {config_info.get('end_date', 'N/A')}")
        print(f"   交易日数: {config_info.get('trading_days', 0)}天")
        print(f"   股票池: {config_info.get('total_stocks', 0)}只股票")
        
        # 策略信息
        strategy_info = result.get('strategy_info', {})
        print(f"\n🎯 策略信息:")
        print(f"   策略版本: {strategy_info.get('strategy_version', 'N/A')}")
        print(f"   最大持仓: {strategy_info.get('max_positions', 'N/A')}只")
        print(f"   单股仓位: {strategy_info.get('max_single_position', 0):.1%}")
        print(f"   买入信号: {strategy_info.get('buy_signals_count', 0)}次")
        print(f"   卖出信号: {strategy_info.get('sell_signals_count', 0)}次")
        
        # 绩效指标
        performance = result.get('performance_report', {}).get('basic_metrics', {})
        print(f"\n📊 核心绩效指标:")
        print(f"   总收益率: {performance.get('total_return', 0):.2%}")
        print(f"   年化收益率: {performance.get('annual_return', 0):.2%}")
        print(f"   年化波动率: {performance.get('volatility', 0):.2%}")
        print(f"   夏普比率: {performance.get('sharpe_ratio', 0):.3f}")
        print(f"   最大回撤: {performance.get('max_drawdown', 0):.2%}")
        print(f"   卡玛比率: {performance.get('calmar_ratio', 0):.3f}")
        
        # 高级指标
        advanced = result.get('performance_report', {}).get('advanced_metrics', {})
        if advanced:
            print(f"\n📈 高级绩效指标:")
            print(f"   索蒂诺比率: {advanced.get('sortino_ratio', 0):.3f}")
            print(f"   VaR(5%): {advanced.get('var_5', 0):.2%}")
            print(f"   CVaR(5%): {advanced.get('cvar_5', 0):.2%}")
            print(f"   盈利日占比: {advanced.get('winning_days_ratio', 0):.1%}")
            print(f"   最大连续亏损: {advanced.get('max_consecutive_losses', 0)}天")
            print(f"   盈亏比: {advanced.get('avg_win_loss_ratio', 0):.2f}")
        
        # 组合摘要
        portfolio = result.get('portfolio_summary', {})
        print(f"\n💰 组合摘要:")
        print(f"   最终价值: {portfolio.get('total_value', 0):,.0f}元")
        print(f"   现金余额: {portfolio.get('cash', 0):,.0f}元")
        print(f"   持仓市值: {portfolio.get('positions_value', 0):,.0f}元")
        print(f"   现金比例: {portfolio.get('cash_ratio', 0):.1%}")
        print(f"   累计收益率: {portfolio.get('cumulative_return', 0):.2%}")
        
        # 交易统计
        trading = result.get('trading_summary', {})
        print(f"\n🔄 交易统计:")
        print(f"   总交易次数: {trading.get('trades', {}).get('total', 0)}")
        print(f"   买入交易: {trading.get('trades', {}).get('buy_trades', 0)}")
        print(f"   卖出交易: {trading.get('trades', {}).get('sell_trades', 0)}")
        print(f"   盈利交易: {portfolio.get('winning_trades', 0)}")
        print(f"   亏损交易: {portfolio.get('losing_trades', 0)}")
        print(f"   胜率: {portfolio.get('win_rate', 0):.1%}")
        print(f"   总手续费: {trading.get('fees', {}).get('total_commission', 0):,.2f}元")
        print(f"   总印花税: {trading.get('fees', {}).get('total_stamp_tax', 0):,.2f}元")
        print(f"   总费用: {trading.get('fees', {}).get('total_fees', 0):,.2f}元")
        
        # 基准比较
        benchmark_data = result.get('benchmark_data', {})
        if benchmark_data:
            print(f"\n🏆 基准比较:")
            print(f"   基准指数: {benchmark_data.get('benchmark_code', 'N/A')}")
            print(f"   基准收益率: {benchmark_data.get('final_return', 0):.2%}")
            print(f"   超额收益: {performance.get('total_return', 0) - benchmark_data.get('final_return', 0):.2%}")
        
        # 当前持仓
        current_positions = result.get('current_positions', [])
        if current_positions:
            print(f"\n📈 当前持仓 (前10只):")
            for i, pos in enumerate(current_positions[:10]):
                print(f"   {i+1:2d}. {pos.get('symbol', 'N/A'):>10} | "
                      f"持仓: {pos.get('shares', 0):>6} | "
                      f"权重: {pos.get('weight', 0):>6.1%} | "
                      f"盈亏: {pos.get('unrealized_pnl', 0):>8.0f}元")
        
        print(f"\n📁 详细结果保存在: {config_info.get('output_dir', './results')} 目录")
        print("="*100)
    
    def analyze_performance(self, result: Dict[str, Any]):
        """
        分析策略性能并给出建议
        
        Args:
            result: 回测结果
        """
        print("\n🔍 策略性能分析与建议:")
        print("-" * 50)
        
        performance = result.get('performance_report', {}).get('basic_metrics', {})
        advanced = result.get('performance_report', {}).get('advanced_metrics', {})
        portfolio = result.get('portfolio_summary', {})
        
        # 收益分析
        total_return = performance.get('total_return', 0)
        annual_return = performance.get('annual_return', 0)
        
        if total_return > 0.30:
            print("✅ 策略收益表现优秀（>30%）")
        elif total_return > 0.15:
            print("✅ 策略收益表现良好（15%-30%）")
        elif total_return > 0.08:
            print("⚠️  策略收益一般（8%-15%）")
        else:
            print("❌ 策略收益偏低（<8%），需要优化")
        
        # 风险分析
        max_drawdown = performance.get('max_drawdown', 0)
        volatility = performance.get('volatility', 0)
        
        if abs(max_drawdown) < 0.10:
            print("✅ 回撤控制优秀（<10%）")
        elif abs(max_drawdown) < 0.20:
            print("⚠️  回撤控制一般（10%-20%）")
        else:
            print("❌ 回撤过大（>20%），风控需要加强")
        
        # 风险调整收益分析
        sharpe_ratio = performance.get('sharpe_ratio', 0)
        
        if sharpe_ratio > 2.0:
            print("✅ 风险调整收益优秀（夏普比率>2.0）")
        elif sharpe_ratio > 1.5:
            print("✅ 风险调整收益良好（夏普比率>1.5）")
        elif sharpe_ratio > 1.0:
            print("✅ 风险调整收益可接受（夏普比率>1.0）")
        else:
            print("⚠️  风险调整收益偏低（夏普比率<1.0）")
        
        # 胜率分析
        win_rate = portfolio.get('win_rate', 0)
        
        if win_rate > 0.6:
            print("✅ 交易胜率优秀（>60%）")
        elif win_rate > 0.5:
            print("✅ 交易胜率良好（50%-60%）")
        else:
            print("⚠️  交易胜率偏低（<50%）")
        
        # 基准比较
        benchmark_data = result.get('benchmark_data', {})
        if benchmark_data:
            benchmark_return = benchmark_data.get('final_return', 0)
            excess_return = total_return - benchmark_return
            
            if excess_return > 0.05:
                print("✅ 相对基准表现优秀（超额收益>5%）")
            elif excess_return > 0:
                print("✅ 相对基准表现良好（有正超额收益）")
            else:
                print("❌ 相对基准表现不佳（负超额收益）")
        
        print("-" * 50)


def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="KK量化策略统一回测器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用序号运行技术突破策略，对比上证指数基准
  python unified_backtest_runner.py --strategy 1 --benchmark 1 --start-date 2023-01-01 --end-date 2023-12-31
  
  # 使用策略代码和中文基准名称
  python unified_backtest_runner.py --strategy technical_breakthrough_adapter --benchmark 沪深300 --start-date 2024-01-01 --end-date 2024-12-31
  
  # 使用自定义参数运行动量突破策略
  python unified_backtest_runner.py --strategy 2 --benchmark 1 --start-date 2024-01-01 --end-date 2024-12-31 --initial-cash 2000000 --max-positions 15
  
  # 列出所有可用量化策略和基准
  python unified_backtest_runner.py --list-strategies
  python unified_backtest_runner.py --list-benchmarks
        """
    )
    
    parser.add_argument('--strategy', '-s', 
                       type=str,
                       help='选择量化策略类型（可以使用序号1-4或策略代码名称）')
    
    parser.add_argument('--start-date', '-sd',
                       type=str,
                       help='回测开始日期 (YYYY-MM-DD)')
    
    parser.add_argument('--end-date', '-ed',
                       type=str,
                       help='回测结束日期 (YYYY-MM-DD)')
    
    parser.add_argument('--initial-cash', '-c',
                       type=float,
                       default=1000000.0,
                       help='初始资金 (默认: 1000000)')
    
    parser.add_argument('--max-positions', '-mp',
                       type=int,
                       default=10,
                       help='最大持仓数量 (默认: 10)')
    
    parser.add_argument('--max-single-position', '-msp',
                       type=float,
                       default=0.08,
                       help='单股最大仓位比例 (默认: 0.08)')
    
    parser.add_argument('--stop-loss', '-sl',
                       type=float,
                       default=-0.15,
                       help='止损比例 (默认: -0.15)')
    
    parser.add_argument('--take-profit', '-tp',
                       type=float,
                       default=0.30,
                       help='止盈比例 (默认: 0.30)')
    
    parser.add_argument('--cash-reserve-ratio', '-crr',
                       type=float,
                       default=0.20,
                       help='现金储备比例 (默认: 0.20)')
    
    parser.add_argument('--benchmark', '-b',
                       type=str,
                       default='1',
                       help='基准指数 (可以使用序号1-8、中文名称或指数代码，默认: 1=上证指数)')
    
    parser.add_argument('--log-level',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='日志级别 (默认: INFO)')
    
    parser.add_argument('--list-strategies', '-ls',
                       action='store_true',
                       help='列出所有可用策略')
    
    parser.add_argument('--list-benchmarks', '-lb',
                       action='store_true',
                       help='列出所有可用基准指数')
    
    parser.add_argument('--max-stocks', '-ms',
                       type=int,
                       default=50,
                       help='最大股票数量 (默认: 50)')
    
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='静默模式，不打印详细结果')
    
    return parser


def main():
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 创建回测器实例
    runner = UnifiedBacktestRunner()
    
    # 设置日志
    runner.setup_logging(log_level=args.log_level)
    
    try:
        # 列出量化策略
        if args.list_strategies:
            print("\n🤖 4大量化策略列表:")
            print("=" * 80)
            strategies_info = runner.list_available_strategies()
            
            for strategy_type, info in strategies_info.items():
                status = "✅ 已实现" if info['implemented'] else "🚧 待实现"
                number = info['number']
                print(f"\n{number}. {info['display_name']}")
                print(f"   策略代码: {strategy_type}")
                print(f"   实现状态: {status}")
                print(f"   策略描述: {info['description']}")
                print("-" * 80)
            
            print(f"\n💡 使用方法:")
            print(f"   # 使用序号运行技术突破策略")
            print(f"   python unified_backtest_runner.py --strategy 1 --start-date 2024-01-01 --end-date 2024-12-31")
            print(f"   # 使用策略代码运行动量突破策略")
            print(f"   python unified_backtest_runner.py --strategy momentum_breakthrough_adapter --start-date 2024-01-01 --end-date 2024-12-31")
            print("=" * 80)
            
            return
        
        # 列出基准指数
        if args.list_benchmarks:
            print("\n📊 可用基准指数列表:")
            print("=" * 80)
            benchmarks_info = runner.list_available_benchmarks()
            
            for benchmark in benchmarks_info['benchmarks']:
                number = benchmark['number']
                name = benchmark['name']
                code = benchmark['code']
                description = benchmark['description']
                print(f"\n{number}. {name}")
                print(f"   指数代码: {code}")
                print(f"   指数描述: {description}")
                print("-" * 80)
            
            print(f"\n💡 使用方法:")
            print(f"   # 使用序号指定基准")
            print(f"   python unified_backtest_runner.py --strategy 1 --benchmark 2 --start-date 2024-01-01 --end-date 2024-12-31")
            print(f"   # 使用中文名称指定基准")
            print(f"   python unified_backtest_runner.py --strategy 1 --benchmark 沪深300 --start-date 2024-01-01 --end-date 2024-12-31")
            print(f"   # 使用指数代码指定基准")
            print(f"   python unified_backtest_runner.py --strategy 1 --benchmark 000300.SH --start-date 2024-01-01 --end-date 2024-12-31")
            print("=" * 80)
            
            return
        
        # 检查必需参数
        if not args.strategy:
            print("❌ 错误: 必须指定策略类型，使用 --list-strategies 查看可用策略")
            return
        
        if not args.start_date or not args.end_date:
            print("❌ 错误: 必须指定开始日期和结束日期")
            return
        
        # 验证日期格式
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
            
            if start_date >= end_date:
                print("❌ 错误: 开始日期必须早于结束日期")
                return
                
        except ValueError:
            print("❌ 错误: 日期格式不正确，请使用 YYYY-MM-DD 格式")
            return
        
        # 运行回测
        print(f"🚀 开始运行 {runner.strategy_display_names.get(args.strategy, args.strategy)} 回测...")
        print(f"📅 回测时间: {args.start_date} 至 {args.end_date}")
        print(f"💰 初始资金: {args.initial_cash:,.0f}元")
        
        result = runner.run_backtest(
            strategy_type=args.strategy,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_cash=args.initial_cash,
            max_positions=args.max_positions,
            max_single_position=args.max_single_position,
            stop_loss_pct=args.stop_loss,
            take_profit_pct=args.take_profit,
            cash_reserve_ratio=args.cash_reserve_ratio,
            benchmark=args.benchmark,
            max_stocks=args.max_stocks
        )
        
        # 输出结果
        if not args.quiet:
            runner.print_backtest_summary(result)
            runner.analyze_performance(result)
        
        print(f"\n🎉 回测完成!")
        print(f"💡 提示: 使用 --quiet 参数可以减少输出信息")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  用户中断了回测执行")
    except Exception as e:
        print(f"\n❌ 回测执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()