#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时回测引擎包装器
在原有回测引擎基础上添加实时数据收集和推送功能
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, date
import json
import numpy as np

from .backtest_engine import BacktestEngine
from .data_manager import DataManager


class RealtimeBacktestEngine:
    """实时回测引擎包装器"""
    
    def __init__(self, strategy, config, task_id: str, progress_callback: Optional[Callable] = None):
        """
        初始化实时回测引擎
        
        Args:
            strategy: 策略对象
            config: 配置对象
            task_id: 任务ID
            progress_callback: 进度回调函数
        """
        self.task_id = task_id
        self.progress_callback = progress_callback
        
        # 初始化原始回测引擎
        self.engine = BacktestEngine(strategy, config)
        
        # 实时数据收集
        self.daily_history = []
        self.realtime_metrics = {}
        self.current_positions = []
        self.recent_trades = []
        self.portfolio_series = []
        self.return_series = []
        self.drawdown_series = []
        self.date_series = []
        
        # 状态跟踪
        self.current_date = None
        self.total_days = 0
        self.completed_days = 0
        self.initial_cash = 0
        self.current_portfolio_value = 0
        self.peak_value = 0
        
    async def run_with_realtime_updates(self):
        """运行回测并提供实时更新"""
        try:
            # 初始化
            await self._update_progress(0.05, "初始化数据管理器...")
            self.engine.data_manager = DataManager()
            
            await self._update_progress(0.1, "加载策略和数据...")
            
            # 获取股票池和日期范围
            stock_pool = await self._get_stock_pool()
            date_range = self._get_date_range()
            self.total_days = len(date_range)
            
            await self._update_progress(0.15, f"开始回测，总计{self.total_days}个交易日...")
            
            # 初始化组合
            self.initial_cash = self.engine.config.backtest.initial_cash
            self.current_portfolio_value = self.initial_cash
            self.peak_value = self.initial_cash
            
            # 逐日执行回测
            for i, current_date in enumerate(date_range):
                self.current_date = current_date.strftime('%Y-%m-%d')
                self.completed_days = i + 1
                
                # 执行单日回测
                daily_result = await self._process_single_day(current_date, stock_pool)
                
                # 收集实时数据
                await self._collect_daily_data(daily_result)
                
                # 更新进度（15% - 85%）
                progress = 0.15 + (i / self.total_days) * 0.7
                message = f"回测进行中... {self.current_date} ({i+1}/{self.total_days})"
                await self._update_progress(progress, message)
                
                # 如果需要，可以在这里添加延时来模拟真实回测速度
                # await asyncio.sleep(0.01)
            
            await self._update_progress(0.9, "生成回测报告...")
            
            # 生成最终结果
            final_result = await self._generate_final_result()
            
            await self._update_progress(1.0, "回测完成!")
            
            return final_result
            
        except Exception as e:
            await self._update_progress(-1, f"回测失败: {str(e)}")
            raise
    
    async def _get_stock_pool(self) -> List[str]:
        """获取股票池"""
        # 这里应该从数据管理器获取股票池
        # 暂时返回模拟数据
        return ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH']
    
    def _get_date_range(self) -> List[date]:
        """获取交易日期范围"""
        start_date = datetime.strptime(self.engine.config.backtest.start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(self.engine.config.backtest.end_date, '%Y-%m-%d').date()
        
        # 生成交易日列表（简化实现，实际应该排除节假日）
        date_list = []
        current = start_date
        while current <= end_date:
            # 排除周末（简化实现）
            if current.weekday() < 5:
                date_list.append(current)
            current += datetime.timedelta(days=1)
        
        return date_list
    
    async def _process_single_day(self, current_date: date, stock_pool: List[str]) -> Dict[str, Any]:
        """处理单日回测逻辑"""
        try:
            # 模拟单日回测逻辑
            # 实际实现中应该调用原始回测引擎的相应方法
            
            # 获取当日市场数据
            market_data = await self._get_market_data(current_date, stock_pool)
            
            # 生成交易信号
            signals = self._generate_signals(current_date, market_data)
            
            # 执行交易
            trades = self._execute_trades(signals, market_data)
            
            # 更新组合状态
            portfolio_update = self._update_portfolio(current_date, market_data, trades)
            
            return {
                'date': current_date.strftime('%Y-%m-%d'),
                'market_data': market_data,
                'signals': signals,
                'trades': trades,
                'portfolio': portfolio_update
            }
            
        except Exception as e:
            return {
                'date': current_date.strftime('%Y-%m-%d'),
                'error': str(e),
                'portfolio': {'total_value': self.current_portfolio_value}
            }
    
    async def _get_market_data(self, current_date: date, stock_pool: List[str]) -> Dict[str, Dict]:
        """获取市场数据（模拟）"""
        market_data = {}
        
        for stock_code in stock_pool:
            # 模拟股价数据
            base_price = 10 + hash(stock_code) % 20
            random_factor = (hash(f"{stock_code}{current_date}") % 100) / 1000
            
            market_data[stock_code] = {
                'close': base_price * (1 + random_factor),
                'open': base_price * (1 + random_factor * 0.8),
                'high': base_price * (1 + random_factor * 1.2),
                'low': base_price * (1 + random_factor * 0.6),
                'volume': 1000000 + (hash(f"{stock_code}{current_date}") % 500000),
                'amount': base_price * 1000000,
                'turnover_rate': 2.5 + (hash(f"{stock_code}{current_date}") % 50) / 10,
                'pe_ratio': 15 + (hash(f"{stock_code}{current_date}") % 20)
            }
        
        return market_data
    
    def _generate_signals(self, current_date: date, market_data: Dict[str, Dict]) -> List[Dict]:
        """生成交易信号（模拟）"""
        signals = []
        
        # 简单的模拟信号生成逻辑
        for stock_code, data in market_data.items():
            signal_strength = (hash(f"{stock_code}{current_date}signal") % 100) / 100
            
            if signal_strength > 0.7:
                signals.append({
                    'symbol': stock_code,
                    'action': 'buy',
                    'quantity': 100,
                    'price': data['close'],
                    'confidence': signal_strength
                })
            elif signal_strength < 0.3:
                # 检查是否持有该股票
                if any(pos['symbol'] == stock_code for pos in self.current_positions):
                    signals.append({
                        'symbol': stock_code,
                        'action': 'sell',
                        'quantity': 100,
                        'price': data['close'],
                        'confidence': 1 - signal_strength
                    })
        
        return signals
    
    def _execute_trades(self, signals: List[Dict], market_data: Dict[str, Dict]) -> List[Dict]:
        """执行交易（模拟）"""
        executed_trades = []
        
        for signal in signals:
            # 模拟交易执行
            trade = {
                'date': self.current_date,
                'symbol': signal['symbol'],
                'action': signal['action'],
                'quantity': signal['quantity'],
                'price': signal['price'],
                'amount': signal['quantity'] * signal['price'],
                'commission': signal['quantity'] * signal['price'] * 0.0003,
                'stamp_tax': signal['quantity'] * signal['price'] * 0.001 if signal['action'] == 'sell' else 0,
                'trade_id': f"{self.task_id}_{len(executed_trades)}"
            }
            
            executed_trades.append(trade)
            
            # 更新持仓
            self._update_positions(trade)
        
        # 保存最近的交易记录
        self.recent_trades.extend(executed_trades[-5:])  # 保存最近5笔交易
        if len(self.recent_trades) > 20:
            self.recent_trades = self.recent_trades[-20:]  # 只保留最近20笔
        
        return executed_trades
    
    def _update_positions(self, trade: Dict):
        """更新持仓信息"""
        symbol = trade['symbol']
        
        # 查找现有持仓
        existing_pos = None
        for pos in self.current_positions:
            if pos['symbol'] == symbol:
                existing_pos = pos
                break
        
        if trade['action'] == 'buy':
            if existing_pos:
                # 增加持仓
                total_cost = existing_pos['quantity'] * existing_pos['avg_price'] + trade['amount']
                total_quantity = existing_pos['quantity'] + trade['quantity']
                existing_pos['quantity'] = total_quantity
                existing_pos['avg_price'] = total_cost / total_quantity
            else:
                # 新建持仓
                self.current_positions.append({
                    'symbol': symbol,
                    'quantity': trade['quantity'],
                    'avg_price': trade['price'],
                    'market_value': trade['amount'],
                    'pnl': 0,
                    'pnl_pct': 0
                })
        
        elif trade['action'] == 'sell' and existing_pos:
            # 减少持仓
            existing_pos['quantity'] -= trade['quantity']
            if existing_pos['quantity'] <= 0:
                self.current_positions.remove(existing_pos)
    
    def _update_portfolio(self, current_date: date, market_data: Dict[str, Dict], trades: List[Dict]) -> Dict:
        """更新组合状态"""
        # 计算持仓市值
        positions_value = 0
        for pos in self.current_positions:
            current_price = market_data.get(pos['symbol'], {}).get('close', pos['avg_price'])
            pos['market_value'] = pos['quantity'] * current_price
            pos['pnl'] = pos['market_value'] - pos['quantity'] * pos['avg_price']
            pos['pnl_pct'] = pos['pnl'] / (pos['quantity'] * pos['avg_price']) if pos['avg_price'] > 0 else 0
            positions_value += pos['market_value']
        
        # 计算现金（简化计算）
        cash = self.initial_cash
        for trade in trades:
            if trade['action'] == 'buy':
                cash -= trade['amount'] + trade['commission'] + trade['stamp_tax']
            else:
                cash += trade['amount'] - trade['commission'] - trade['stamp_tax']
        
        # 更新组合总价值
        self.current_portfolio_value = cash + positions_value
        
        # 更新最高价值
        if self.current_portfolio_value > self.peak_value:
            self.peak_value = self.current_portfolio_value
        
        # 计算收益率
        total_return = (self.current_portfolio_value - self.initial_cash) / self.initial_cash
        daily_return = 0  # 简化实现
        drawdown = (self.current_portfolio_value - self.peak_value) / self.peak_value if self.peak_value > 0 else 0
        
        portfolio_state = {
            'date': current_date.strftime('%Y-%m-%d'),
            'total_value': self.current_portfolio_value,
            'cash': cash,
            'positions_value': positions_value,
            'positions': self.current_positions.copy(),
            'total_return': total_return,
            'daily_return': daily_return,
            'drawdown': drawdown,
            'positions_count': len(self.current_positions)
        }
        
        return portfolio_state
    
    async def _collect_daily_data(self, daily_result: Dict[str, Any]):
        """收集每日数据"""
        self.daily_history.append(daily_result)
        
        # 更新时间序列数据
        if 'portfolio' in daily_result:
            portfolio = daily_result['portfolio']
            self.date_series.append(daily_result['date'])
            self.portfolio_series.append(portfolio.get('total_value', 0))
            self.return_series.append(portfolio.get('total_return', 0))
            self.drawdown_series.append(portfolio.get('drawdown', 0))
        
        # 更新实时指标
        self._update_realtime_metrics()
    
    def _update_realtime_metrics(self):
        """更新实时指标"""
        if not self.portfolio_series:
            return
        
        # 计算基本指标
        returns = np.array(self.return_series)
        portfolio_values = np.array(self.portfolio_series)
        
        self.realtime_metrics = {
            'total_return': returns[-1] if len(returns) > 0 else 0,
            'annual_return': returns[-1] * (252 / max(len(returns), 1)) if len(returns) > 0 else 0,
            'max_drawdown': min(self.drawdown_series) if self.drawdown_series else 0,
            'volatility': np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0,
            'sharpe_ratio': (np.mean(returns) * 252) / (np.std(returns) * np.sqrt(252)) if len(returns) > 1 and np.std(returns) > 0 else 0,
            'current_positions_count': len(self.current_positions),
            'total_trades': len(self.recent_trades),
            'win_rate': self._calculate_win_rate()
        }
    
    def _calculate_win_rate(self) -> float:
        """计算胜率"""
        if not self.recent_trades:
            return 0.0
        
        # 简化的胜率计算（基于交易方向）
        profitable_trades = sum(1 for trade in self.recent_trades if trade['action'] == 'sell')
        return profitable_trades / len(self.recent_trades) if self.recent_trades else 0.0
    
    async def _generate_final_result(self) -> Dict[str, Any]:
        """生成最终回测结果"""
        return {
            'task_id': self.task_id,
            'strategy_name': self.engine.strategy.name if hasattr(self.engine.strategy, 'name') else 'Unknown',
            'performance_metrics': self.realtime_metrics,
            'daily_history': self.daily_history,
            'portfolio_series': self.portfolio_series,
            'return_series': self.return_series,
            'drawdown_series': self.drawdown_series,
            'date_series': self.date_series,
            'recent_trades': self.recent_trades,
            'final_positions': self.current_positions,
            'initial_cash': self.initial_cash,
            'final_value': self.current_portfolio_value,
            'completed_at': datetime.now().isoformat()
        }
    
    async def _update_progress(self, progress: float, message: str):
        """更新进度并回调"""
        if self.progress_callback:
            await self.progress_callback(self.task_id, {
                'progress': progress,
                'message': message,
                'current_date': self.current_date,
                'total_days': self.total_days,
                'completed_days': self.completed_days,
                'current_portfolio_value': self.current_portfolio_value,
                'total_return': self.realtime_metrics.get('total_return', 0),
                'daily_return': 0,  # 简化实现
                'current_positions': self.current_positions.copy(),
                'recent_trades': self.recent_trades.copy(),
                'date_series': self.date_series.copy(),
                'portfolio_series': self.portfolio_series.copy(),
                'return_series': self.return_series.copy(),
                'drawdown_series': self.drawdown_series.copy(),
                **self.realtime_metrics
            })