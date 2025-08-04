#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎主类
整合所有组件，提供统一的回测接口
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
import json
from abc import ABC, abstractmethod

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .trading_simulator import TradingSimulator, OrderType
from .data_manager import DataManager
from .order_manager import OrderManager
from .portfolio_manager import PortfolioManager
from .performance_analyzer import PerformanceAnalyzer
from backtrader_strategies.config import Config


class StrategyInterface(ABC):
    """
    策略接口基类
    所有策略都需要实现这个接口
    """
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]):
        """
        策略初始化
        
        Args:
            context: 上下文信息，包含配置、数据等
        """
        pass
    
    @abstractmethod
    def generate_signals(self, 
                        current_date: str, 
                        market_data: Dict[str, Dict],
                        portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成交易信号
        
        Args:
            current_date: 当前日期
            market_data: 市场数据 {stock_code: daily_data}
            portfolio_info: 组合信息
            
        Returns:
            交易信号列表 [{'action': 'buy/sell', 'stock_code': str, 'quantity': int, 'price': float}]
        """
        pass
    
    @abstractmethod
    def on_trade_executed(self, trade_info: Dict[str, Any]):
        """
        交易执行后回调
        
        Args:
            trade_info: 交易信息
        """
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略信息
        
        Returns:
            策略信息字典
        """
        pass


class BacktestEngine:
    """
    回测引擎主类
    负责整个回测流程的协调和管理
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化回测引擎
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        self.config = config or Config()
        
        # 初始化各个组件
        # 创建交易规则配置
        from .trading_simulator import TradingRule
        trading_rule = TradingRule(
            commission_rate=self.config.backtest.commission_rate,
            stamp_tax_rate=self.config.backtest.stamp_tax_rate,
            min_commission=self.config.backtest.min_commission,
            slippage_rate=getattr(self.config.backtest, 'slippage_rate', 0.001)
        )
        
        self.trading_simulator = TradingSimulator(trading_rule)
        self.data_manager = DataManager(self.config.database)
        self.order_manager = OrderManager(self.trading_simulator)
        self.portfolio_manager = PortfolioManager(self.config.backtest.initial_cash)
        self.performance_analyzer = PerformanceAnalyzer()
        
        # 策略相关
        self.strategy = None
        self.strategy_context = {}
        
        # 回测状态
        self.is_running = False
        self.current_date = None
        self.trading_dates = []
        self.market_data = {}
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 实时数据回调
        self.realtime_callback = None
        
        # 创建输出目录
        os.makedirs(self.config.backtest.output_dir, exist_ok=True)
        
        self.logger.info(f"回测引擎初始化完成，初始资金: {self.config.backtest.initial_cash:,.0f}元")
    
    def set_strategy(self, strategy: StrategyInterface):
        """
        设置回测策略
        
        Args:
            strategy: 策略实例
        """
        self.strategy = strategy
        
        # 初始化策略
        self.strategy_context = {
            'config': self.config,
            'initial_cash': self.config.backtest.initial_cash,
            'start_date': self.config.backtest.start_date,
            'end_date': self.config.backtest.end_date
        }
        
        self.strategy.initialize(self.strategy_context)
        self.logger.info(f"策略设置完成: {strategy.__class__.__name__}")
    
    def set_realtime_callback(self, callback: Callable[[str, Dict[str, Any], List[Dict]], None]):
        """
        设置实时数据更新回调函数
        
        Args:
            callback: 回调函数，接收 (current_date, portfolio_data, trades_data) 参数
        """
        self.realtime_callback = callback
        self.logger.info("实时数据回调函数已设置")
    
    def load_data(self, stock_codes: Optional[List[str]] = None, max_stocks: int = 50):
        """
        加载回测数据
        
        Args:
            stock_codes: 股票代码列表，如果为None则自动加载股票池
            max_stocks: 最大股票数量
        """
        self.logger.info("开始加载回测数据...")
        
        # 获取股票池 - 根据策略指定的指数代码
        if stock_codes is None:
            # 检查策略是否指定了指数代码
            index_code = "000510.CSI"  # 默认中证A500
            if hasattr(self.strategy, 'get_index_code'):
                index_code = self.strategy.get_index_code()
                self.logger.info(f"策略指定使用指数: {index_code}")
            
            stock_codes = self.data_manager.load_stock_universe(index_code)
        
        # 加载市场数据 - 如果策略支持评分，使用策略评分选择股票
        strategy_scorer = None
        if hasattr(self.strategy, '_calculate_resonance_score'):
            strategy_scorer = self.strategy._calculate_resonance_score
            self.logger.info("检测到策略评分功能，将使用策略评分选择最优股票")
        
        self.market_data = self.data_manager.load_market_data(
            stock_codes=stock_codes,
            start_date=self.config.backtest.start_date,
            end_date=self.config.backtest.end_date,
            max_stocks=max_stocks,
            strategy_scorer=strategy_scorer
        )
        
        # 获取交易日历
        self.trading_dates = self.data_manager.get_trading_dates(
            self.config.backtest.start_date,
            self.config.backtest.end_date
        )
        
        # 数据质量检查
        data_quality = self.data_manager.validate_data_quality(self.market_data)
        
        self.logger.info(f"数据加载完成:")
        self.logger.info(f"  股票数量: {len(self.market_data)}")
        self.logger.info(f"  交易日数: {len(self.trading_dates)}")
        self.logger.info(f"  数据质量: {data_quality['overall_quality']} (平均得分: {data_quality['avg_quality_score']:.1f})")
        
        if data_quality['issues']:
            self.logger.warning("数据质量问题:")
            for issue in data_quality['issues'][:5]:  # 只显示前5个问题
                self.logger.warning(f"  {issue}")
    
    def run_backtest(self) -> Dict[str, Any]:
        """
        运行回测
        
        Returns:
            回测结果字典
        """
        if not self.strategy:
            raise ValueError("请先设置策略")
        
        if not self.market_data:
            raise ValueError("请先加载数据")
        
        self.logger.info("开始回测...")
        self.is_running = True
        
        # 更新组合配置
        self.portfolio_manager.update_portfolio_config({
            'max_single_position': self.config.strategy.max_single_position,
            'max_positions': self.config.strategy.max_positions,
            'stop_loss_pct': abs(self.config.strategy.stop_loss_pct),
            'take_profit_pct': self.config.strategy.take_profit_pct,
            'max_drawdown_limit': abs(self.config.strategy.max_drawdown_limit)
        })
        
        try:
            # 按日期循环回测
            for i, trade_date in enumerate(self.trading_dates):
                self.current_date = trade_date
                
                # 更新进度
                if (i + 1) % 50 == 0:
                    progress = (i + 1) / len(self.trading_dates) * 100
                    self.logger.info(f"回测进度: {progress:.1f}% ({i+1}/{len(self.trading_dates)})")
                
                # 执行单日回测
                self._process_single_day(trade_date)
            
            # 生成回测结果
            result = self._generate_backtest_result()
            
            self.logger.info("回测完成!")
            return result
            
        except Exception as e:
            self.logger.error(f"回测过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.is_running = False
    
    def _process_single_day(self, trade_date: str):
        """
        处理单日回测逻辑
        
        Args:
            trade_date: 交易日期
        """
        # 1. 获取当日市场数据
        daily_market_data = {}
        for stock_code, stock_df in self.market_data.items():
            stock_data = self.data_manager.get_stock_data_on_date(
                stock_code, trade_date, self.market_data
            )
            if stock_data:
                daily_market_data[stock_code] = stock_data
        
        # 2. 更新持仓市值
        self.portfolio_manager.update_positions_value(daily_market_data, trade_date)
        
        # 3. 检查风险控制
        risk_violations = self.portfolio_manager.check_risk_limits(daily_market_data)
        
        # 4. 处理风险违规（强制平仓）
        forced_sells = set()  # 记录强制卖出的股票，避免重复
        for stock_code, reason in risk_violations:
            if stock_code != "PORTFOLIO" and stock_code not in forced_sells:  # 跳过组合级别的风险和已处理的股票
                position = self.portfolio_manager.get_position_info(stock_code)
                if position and position.quantity > 0:
                    # 创建强制卖出订单
                    self.order_manager.create_order(
                        stock_code=stock_code,
                        order_type=OrderType.SELL,
                        quantity=position.quantity,
                        price=daily_market_data[stock_code]['close'],
                        timestamp=pd.to_datetime(trade_date)
                    )
                    forced_sells.add(stock_code)  # 记录已处理
                    self.logger.warning(f"风险控制平仓: {stock_code} - {reason}")
        
        # 5. 生成策略信号
        portfolio_info = self.portfolio_manager.get_portfolio_summary()
        signals = self.strategy.generate_signals(trade_date, daily_market_data, portfolio_info)
        
        # 6. 处理策略信号
        for signal in signals:
            self._process_signal(signal, trade_date)
        
        # 7. 执行所有待处理订单
        executed_trades = self.order_manager.execute_pending_orders(trade_date, daily_market_data)
        
        # 8. 更新组合
        for trade in executed_trades:
            self.portfolio_manager.process_trade(trade)
            # 通知策略交易执行
            self.strategy.on_trade_executed({
                'stock_code': trade.stock_code,
                'order_type': trade.order_type.value,
                'quantity': trade.quantity,
                'price': trade.price,
                'trade_date': trade_date
            })
        
        # 9. 创建组合快照
        self.portfolio_manager.take_snapshot(trade_date)
        
        # 10. 调用实时数据回调（如果设置了的话）- 每天都要调用
        if self.realtime_callback:
            try:
                # 获取当前组合数据
                portfolio_summary = self.portfolio_manager.get_portfolio_summary()
                positions_dict = self.portfolio_manager.get_all_positions()
                
                # 计算收益率和回撤
                current_value = portfolio_summary.get('total_value', 0.0)
                initial_cash = self.config.backtest.initial_cash
                
                # 计算累计收益率
                total_return = (current_value - initial_cash) / initial_cash if initial_cash > 0 else 0.0
                
                # 计算日收益率（需要获取前一日价值）
                daily_return = 0.0
                if hasattr(self.portfolio_manager, 'portfolio_history') and len(self.portfolio_manager.portfolio_history) > 1:
                    previous_value = self.portfolio_manager.portfolio_history[-2].total_value
                    if previous_value > 0:
                        daily_return = (current_value - previous_value) / previous_value
                
                # 计算回撤（需要计算历史最高点）
                max_value = initial_cash
                if hasattr(self.portfolio_manager, 'portfolio_history'):
                    max_value = max(max_value, max([snapshot.total_value for snapshot in self.portfolio_manager.portfolio_history] + [current_value]))
                drawdown = (current_value - max_value) / max_value if max_value > 0 else 0.0
                
                # 每天都记录调试日志，确保实时推送正常
                self.logger.info(f"📊 [{trade_date}] 计算指标: 当前价值={current_value:,.0f}, 初始资金={initial_cash:,.0f}, 最高价值={max_value:,.0f}")
                self.logger.info(f"📊 [{trade_date}] 计算结果: 累计收益率={total_return:.4f}({total_return*100:.2f}%), 回撤={drawdown:.4f}({drawdown*100:.2f}%)")
                
                # 构建组合数据
                portfolio_data = {
                    'total_value': current_value,
                    'cash': portfolio_summary.get('cash', 0.0),
                    'positions_value': current_value - portfolio_summary.get('cash', 0.0),
                    'positions': [
                        {
                            'symbol': pos.stock_code,
                            'name': pos.stock_code,  # 简化处理，可以后续优化
                            'shares': pos.quantity,
                            'value': pos.market_value
                        } for pos in positions_dict.values() if pos.quantity > 0
                    ],
                    'daily_return': daily_return,
                    'total_return': total_return,
                    'drawdown': drawdown
                }
                
                # 获取最近的交易数据
                all_trades = self.order_manager.get_executed_trades()
                recent_trades = [
                    {
                        'date': trade.trade_date.strftime('%Y-%m-%d') if hasattr(trade.trade_date, 'strftime') else str(trade.trade_date),
                        'symbol': trade.stock_code,
                        'type': 'buy' if trade.order_type.value == 'BUY' else 'sell',
                        'price': trade.price,
                        'quantity': trade.quantity,
                        'value': trade.price * trade.quantity
                    } for trade in all_trades
                ]
                
                # 调用回调函数
                self.realtime_callback(trade_date, portfolio_data, recent_trades)
                
                # 添加小的延迟，确保SSE有时间推送数据
                import time
                time.sleep(0.01)  # 10毫秒延迟，确保实时性
            except Exception as e:
                self.logger.error(f"实时回调调用失败: {e}")
    
    def _process_signal(self, signal: Dict[str, Any], trade_date: str):
        """
        处理交易信号
        
        Args:
            signal: 交易信号
            trade_date: 交易日期
        """
        try:
            action = signal['action'].lower()
            stock_code = signal['stock_code']
            
            if action == 'buy':
                # 检查是否可以开新仓
                if not self.portfolio_manager.can_open_new_position():
                    self.logger.debug(f"无法开新仓，跳过买入信号: {stock_code}")
                    return
                
                # 计算买入数量
                target_weight = signal.get('weight', self.config.strategy.max_single_position)
                current_price = signal['price']
                quantity = self.portfolio_manager.calculate_position_size(
                    stock_code, target_weight, current_price
                )
                
                if quantity > 0:
                    self.order_manager.create_order(
                        stock_code=stock_code,
                        order_type=OrderType.BUY,
                        quantity=quantity,
                        price=current_price,
                        timestamp=pd.to_datetime(trade_date)
                    )
            
            elif action == 'sell':
                # 检查是否有持仓
                position = self.portfolio_manager.get_position_info(stock_code)
                if position and position.quantity > 0:
                    quantity = signal.get('quantity', position.quantity)
                    quantity = min(quantity, position.quantity)  # 不能超过持仓数量
                    
                    if quantity > 0:
                        self.order_manager.create_order(
                            stock_code=stock_code,
                            order_type=OrderType.SELL,
                            quantity=quantity,
                            price=signal['price'],
                            timestamp=pd.to_datetime(trade_date)
                        )
                        
        except Exception as e:
            self.logger.error(f"处理交易信号失败: {signal}, 错误: {e}")
    
    def _generate_backtest_result(self) -> Dict[str, Any]:
        """
        生成回测结果
        
        Returns:
            回测结果字典
        """
        self.logger.info("生成回测报告...")
        
        # 获取组合历史和交易记录
        portfolio_history = self.portfolio_manager.portfolio_history
        trades_df = self.order_manager.get_trades_dataframe()
        
        # 生成绩效报告 - 优先使用配置中的策略名称
        strategy_name = getattr(self.config, 'strategy_name', None) or self.strategy.__class__.__name__ if self.strategy else "策略"
        performance_report = self.performance_analyzer.generate_performance_report(
            portfolio_history=portfolio_history,
            trades_df=trades_df,
            strategy_name=strategy_name
        )
        
        # 计算时间戳目录路径，保持一致性
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        strategy_dir = os.path.join(self.config.backtest.output_dir, strategy_name)
        timestamped_dir = os.path.join(strategy_dir, timestamp)
        
        # 确保输出目录存在
        os.makedirs(timestamped_dir, exist_ok=True)
        
        # 生成图表文件（保持向后兼容） - 临时注释掉，只返回数据给前端
        # chart_files = self.performance_analyzer.create_performance_charts(
        #     portfolio_history=portfolio_history,
        #     trades_df=trades_df,
        #     output_dir=timestamped_dir,
        #     strategy_name=strategy_name
        # )
        chart_files = []  # 不生成图片文件
        
        # 生成图表数据供前端使用（包含基准数据）
        chart_data = self.performance_analyzer.generate_chart_data(
            portfolio_history=portfolio_history,
            trades_df=trades_df,
            strategy_name=strategy_name,
            start_date=self.config.backtest.start_date,
            end_date=self.config.backtest.end_date,
            benchmark_code=self.config.backtest.benchmark
        )
        
        # 获取策略信息
        strategy_info = self.strategy.get_strategy_info() if self.strategy else {}
        
        # 组装完整结果
        result = {
            'backtest_config': {
                'initial_cash': self.config.backtest.initial_cash,
                'start_date': self.config.backtest.start_date,
                'end_date': self.config.backtest.end_date,
                'total_stocks': len(self.market_data),
                'trading_days': len(self.trading_dates),
                'strategy_type': getattr(self.config, 'strategy_type', '')
            },
            'strategy_info': strategy_info,
            'performance_report': performance_report,
            'portfolio_summary': self.portfolio_manager.get_portfolio_summary(),
            'trading_summary': self.order_manager.get_trading_summary(),
            'chart_files': chart_files,  # 保持向后兼容
            'chart_data': chart_data  # 新增：前端图表数据
        }
        
        # 如果图表数据中包含基准数据，将其提取到结果的顶层
        if chart_data and 'benchmark_data' in chart_data:
            result['benchmark_data'] = chart_data['benchmark_data']
        
        # 保存结果
        self._save_backtest_result(result, strategy_name, timestamped_dir, portfolio_history)
        
        return result
    
    def _save_backtest_result(self, result: Dict[str, Any], strategy_name: str, timestamped_dir: str, portfolio_history):
        """
        保存回测结果
        
        Args:
            result: 回测结果
            strategy_name: 策略名称
            timestamped_dir: 时间戳目录路径
            portfolio_history: 组合历史快照
        """
        
        # 保存JSON报告
        if self.config.backtest.save_performance:
            json_filename = os.path.join(timestamped_dir, f"{strategy_name}_backtest_result.json")
            self.performance_analyzer.export_report_to_json(result, json_filename)
        
        # 保存Markdown分析报告
        markdown_filename = os.path.join(timestamped_dir, f"{strategy_name}_comprehensive_analysis_report.md")
        self.performance_analyzer.export_comprehensive_markdown_report(result, markdown_filename, portfolio_history)
        
        # 保存交易记录
        if self.config.backtest.save_trades:
            trades_filename = os.path.join(timestamped_dir, f"{strategy_name}_trades.csv")
            self.order_manager.export_trades_to_csv(trades_filename)
        
        # 保存组合历史
        if self.config.backtest.save_positions:
            portfolio_filename = os.path.join(timestamped_dir, f"{strategy_name}_portfolio.csv")
            self.portfolio_manager.export_portfolio_to_csv(portfolio_filename)
        
        self.logger.info(f"回测结果已保存到: {timestamped_dir}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        获取当前回测状态
        
        Returns:
            状态信息字典
        """
        return {
            'is_running': self.is_running,
            'current_date': self.current_date,
            'total_trading_days': len(self.trading_dates),
            'current_day_index': self.trading_dates.index(self.current_date) + 1 if self.current_date in self.trading_dates else 0,
            'portfolio_value': self.portfolio_manager.get_total_value(),
            'cash': self.portfolio_manager.cash,
            'total_positions': len(self.portfolio_manager.positions),
            'total_trades': self.order_manager.get_trading_summary()['trades']['total']
        }
    
    def reset(self):
        """重置回测引擎"""
        self.is_running = False
        self.current_date = None
        self.portfolio_manager.reset_portfolio()
        self.order_manager.clear_history()
        
        self.logger.info("回测引擎已重置")


# 便利函数
def run_strategy_backtest(strategy: StrategyInterface, 
                         config: Optional[Config] = None,
                         stock_codes: Optional[List[str]] = None,
                         max_stocks: int = 50,
                         task_id: Optional[str] = None,
                         active_tasks: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    运行策略回测的便利函数
    
    Args:
        strategy: 策略实例
        config: 配置对象
        stock_codes: 股票代码列表
        max_stocks: 最大股票数量
        
    Returns:
        回测结果
    """
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建回测引擎
    engine = BacktestEngine(config)
    
    # 设置策略
    engine.set_strategy(strategy)
    
    # 加载数据
    engine.load_data(stock_codes, max_stocks)
    
    # 如果提供了任务ID和active_tasks，在引擎中设置实时更新回调
    if task_id and active_tasks:
        def update_realtime_callback(current_date: str, portfolio_data: Dict[str, Any], trades_data: List[Dict]):
            """回测过程中的实时数据更新回调"""
            try:
                # 首先检查任务是否存在
                if task_id not in active_tasks:
                    logging.error(f"   ❌ 任务ID {task_id} 不在 active_tasks 中！")
                    return
                
                # 构建实时数据更新
                update_data = {
                    'current_date': current_date,
                    'current_portfolio_value': portfolio_data.get('total_value', 0.0),
                    'current_cash': portfolio_data.get('cash', 0.0),
                    'current_positions_value': portfolio_data.get('positions_value', 0.0),
                    'current_positions': portfolio_data.get('positions', []),
                    'daily_return': portfolio_data.get('daily_return', 0.0),
                    'total_return': portfolio_data.get('total_return', 0.0),
                    'current_drawdown': portfolio_data.get('drawdown', 0.0),
                    'recent_trades': trades_data[-10:] if trades_data else [],
                    'total_trades': len(trades_data) if trades_data else 0
                }
                
                # 更新active_tasks
                active_tasks[task_id].update(update_data)
                
                # 更新或初始化时序数据
                if 'date_series' not in active_tasks[task_id]:
                    active_tasks[task_id]['date_series'] = []
                    active_tasks[task_id]['portfolio_series'] = []
                    active_tasks[task_id]['daily_return_series'] = []
                    active_tasks[task_id]['cumulative_return_series'] = []
                    active_tasks[task_id]['drawdown_series'] = []
                
                # 检查是否是新的日期数据点
                if current_date not in active_tasks[task_id]['date_series']:
                    active_tasks[task_id]['date_series'].append(current_date)
                    active_tasks[task_id]['portfolio_series'].append(portfolio_data.get('total_value', 0.0))
                    active_tasks[task_id]['daily_return_series'].append(portfolio_data.get('daily_return', 0.0))
                    active_tasks[task_id]['cumulative_return_series'].append(portfolio_data.get('total_return', 0.0))
                    active_tasks[task_id]['drawdown_series'].append(portfolio_data.get('drawdown', 0.0))
                else:
                    # 更新已存在的数据点
                    idx = active_tasks[task_id]['date_series'].index(current_date)
                    active_tasks[task_id]['portfolio_series'][idx] = portfolio_data.get('total_value', 0.0)
                    active_tasks[task_id]['daily_return_series'][idx] = portfolio_data.get('daily_return', 0.0)
                    active_tasks[task_id]['cumulative_return_series'][idx] = portfolio_data.get('total_return', 0.0)
                    active_tasks[task_id]['drawdown_series'][idx] = portfolio_data.get('drawdown', 0.0)
                
                # 标记数据已更新，用于SSE推送
                active_tasks[task_id]['last_update'] = current_date
                active_tasks[task_id]['data_updated'] = True
                
                # 详细的调试日志
                logging.info(f"🔄 [{current_date}] 实时数据推送详情:")
                logging.info(f"   📈 组合价值: {portfolio_data.get('total_value', 0.0):,.2f}")
                logging.info(f"   💰 现金: {portfolio_data.get('cash', 0.0):,.2f}") 
                logging.info(f"   📊 总收益率: {portfolio_data.get('total_return', 0.0):.4f} ({portfolio_data.get('total_return', 0.0)*100:.2f}%)")
                logging.info(f"   📉 日收益率: {portfolio_data.get('daily_return', 0.0):.4f} ({portfolio_data.get('daily_return', 0.0)*100:.2f}%)")
                logging.info(f"   ⬇️  回撤: {portfolio_data.get('drawdown', 0.0):.4f} ({portfolio_data.get('drawdown', 0.0)*100:.2f}%)")
                logging.info(f"   🔢 交易数: {len(trades_data) if trades_data else 0}")
                logging.info(f"   📋 持仓数: {len(portfolio_data.get('positions', []))}")
                
                # 确认数据已写入active_tasks
                series_len = len(active_tasks[task_id].get('date_series', []))
                logging.info(f"   ✅ 时序数据长度: {series_len}")
                
            except Exception as e:
                logging.error(f"更新实时数据失败: {e}")
        
        # 设置回调函数到引擎
        engine.set_realtime_callback(update_realtime_callback)
    
    # 运行回测
    result = engine.run_backtest()
    
    return result


if __name__ == "__main__":
    print("🚀 回测引擎测试...")
    
    # 这里可以添加测试代码
    # 由于需要具体的策略实现，暂时跳过测试
    
    print("✅ 回测引擎创建完成")