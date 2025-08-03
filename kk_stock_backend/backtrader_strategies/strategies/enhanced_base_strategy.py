#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强基础策略类
为所有策略提供通用功能和接口
"""

import backtrader as bt
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtrader_strategies.config import Config


class EnhancedBaseStrategy(bt.Strategy):
    """
    增强基础策略类
    提供通用的策略功能和接口
    """
    
    params = (
        # 基础参数
        ('max_positions', 20),
        ('rebalance_frequency', 5),
        ('min_position_value', 10000.0),
        
        # 风险控制参数
        ('stop_loss_pct', -0.06),
        ('take_profit_pct', 0.12),
        ('max_single_position', 0.1),
        ('max_drawdown_limit', -0.20),
        
        # 选股过滤参数
        ('min_market_cap', 50e8),
        ('max_market_cap', 5000e8),
        ('min_turnover', 0.01),
        ('max_turnover', 0.20),
        ('min_price', 5.0),
        ('max_price', 200.0),
        
        # 调试参数
        ('debug', True),
        ('log_trades', True),
    )
    
    def __init__(self):
        """初始化策略"""
        # 策略状态
        self.rebalance_counter = 0
        self.positions_info = {}  # 持仓信息
        self.trade_records = []   # 交易记录
        self.performance_metrics = {}  # 性能指标
        
        # 数据引用字典
        self.data_dict = {}
        
        # 为每个数据源创建引用
        for i, data in enumerate(self.datas):
            if hasattr(data, '_name'):
                stock_code = data._name
            else:
                stock_code = f"stock_{i}"
            
            self.data_dict[stock_code] = data
            
            # 为每个数据源添加技术指标（如果数据中没有）
            if not hasattr(data, 'ma5'):
                data.ma5 = bt.indicators.SimpleMovingAverage(data.close, period=5)
            if not hasattr(data, 'ma20'):
                data.ma20 = bt.indicators.SimpleMovingAverage(data.close, period=20)
            if not hasattr(data, 'ma60'):
                data.ma60 = bt.indicators.SimpleMovingAverage(data.close, period=60)
            if not hasattr(data, 'rsi'):
                data.rsi = bt.indicators.RSI(data.close, period=14)
            if not hasattr(data, 'macd'):
                data.macd = bt.indicators.MACD(data.close)
        
        self.log(f"🚀 策略初始化完成，数据源数量: {len(self.datas)}")
    
    def log(self, txt, dt=None):
        """日志记录"""
        dt = dt or self.datas[0].datetime.date(0)
        if self.p.debug:
            print(f'[{dt.isoformat()}] {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: {order.data._name}, 价格: {order.executed.price:.2f}, '
                        f'数量: {order.executed.size}, 成本: {order.executed.value:.2f}')
                
                # 记录持仓信息
                stock_code = order.data._name
                self.positions_info[stock_code] = {
                    'entry_price': order.executed.price,
                    'entry_date': self.datas[0].datetime.date(0),
                    'size': order.executed.size,
                    'entry_value': order.executed.value
                }
                
            elif order.issell():
                self.log(f'卖出执行: {order.data._name}, 价格: {order.executed.price:.2f}, '
                        f'数量: {order.executed.size}, 收入: {order.executed.value:.2f}')
                
                # 计算收益并记录交易
                stock_code = order.data._name
                if stock_code in self.positions_info:
                    pos_info = self.positions_info[stock_code]
                    pnl = order.executed.value - pos_info['entry_value']
                    pnl_pct = pnl / pos_info['entry_value']
                    
                    trade_record = {
                        'stock_code': stock_code,
                        'entry_date': pos_info['entry_date'],
                        'exit_date': self.datas[0].datetime.date(0),
                        'entry_price': pos_info['entry_price'],
                        'exit_price': order.executed.price,
                        'size': order.executed.size,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'hold_days': (self.datas[0].datetime.date(0) - pos_info['entry_date']).days
                    }
                    
                    self.trade_records.append(trade_record)
                    
                    # 移除持仓信息
                    del self.positions_info[stock_code]
                    
                    self.log(f'交易完成: {stock_code}, 收益: {pnl:.2f} ({pnl_pct:.2%})')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败: {order.data._name}, 状态: {order.getstatusname()}')
    
    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return
        
        self.log(f'交易关闭: {trade.data._name}, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')
    
    def get_price_data(self, stock_code: str, field: str = 'close') -> Optional[float]:
        """
        获取指定股票的价格数据
        
        Args:
            stock_code: 股票代码
            field: 数据字段 ('open', 'high', 'low', 'close', 'volume')
            
        Returns:
            价格数据，如果不存在返回None
        """
        if stock_code in self.data_dict:
            data = self.data_dict[stock_code]
            if hasattr(data, field):
                return getattr(data, field)[0]
        return None
    
    def get_indicator_data(self, stock_code: str, indicator: str) -> Optional[float]:
        """
        获取指定股票的技术指标数据
        
        Args:
            stock_code: 股票代码
            indicator: 指标名称 ('ma5', 'ma20', 'ma60', 'rsi', 'macd')
            
        Returns:
            指标数据，如果不存在返回None
        """
        if stock_code in self.data_dict:
            data = self.data_dict[stock_code]
            if hasattr(data, indicator):
                indicator_obj = getattr(data, indicator)
                if hasattr(indicator_obj, '__getitem__'):
                    return indicator_obj[0]
                else:
                    return float(indicator_obj)
        return None
    
    def calculate_position_size(self, stock_code: str, target_value: float) -> int:
        """
        计算持仓数量
        
        Args:
            stock_code: 股票代码
            target_value: 目标持仓价值
            
        Returns:
            持仓数量（手数）
        """
        current_price = self.get_price_data(stock_code, 'close')
        if current_price is None or current_price <= 0:
            return 0
        
        # 计算股数（向下取整到100的倍数）
        shares = int(target_value / current_price / 100) * 100
        
        # 确保最小持仓
        if shares < 100:
            shares = 100 if target_value >= current_price * 100 else 0
        
        return shares
    
    def get_portfolio_value(self) -> float:
        """获取组合总价值"""
        return self.broker.getvalue()
    
    def get_available_cash(self) -> float:
        """获取可用现金"""
        return self.broker.getcash()
    
    def get_current_positions(self) -> Dict[str, Dict]:
        """
        获取当前持仓信息
        
        Returns:
            持仓信息字典
        """
        current_positions = {}
        
        for stock_code, data in self.data_dict.items():
            position = self.getposition(data)
            if position.size > 0:
                current_price = self.get_price_data(stock_code, 'close')
                current_value = position.size * current_price if current_price else 0
                
                current_positions[stock_code] = {
                    'size': position.size,
                    'price': position.price,
                    'current_price': current_price,
                    'value': current_value,
                    'pnl': (current_price - position.price) * position.size if current_price else 0,
                    'pnl_pct': (current_price - position.price) / position.price if current_price and position.price else 0
                }
        
        return current_positions
    
    def should_rebalance(self) -> bool:
        """判断是否应该调仓"""
        self.rebalance_counter += 1
        return self.rebalance_counter >= self.p.rebalance_frequency
    
    def reset_rebalance_counter(self):
        """重置调仓计数器"""
        self.rebalance_counter = 0
    
    def apply_risk_management(self, stock_code: str) -> bool:
        """
        应用风险管理规则
        
        Args:
            stock_code: 股票代码
            
        Returns:
            是否应该卖出
        """
        if stock_code not in self.positions_info:
            return False
        
        current_price = self.get_price_data(stock_code, 'close')
        if current_price is None:
            return False
        
        pos_info = self.positions_info[stock_code]
        entry_price = pos_info['entry_price']
        
        # 计算收益率
        pnl_pct = (current_price - entry_price) / entry_price
        
        # 止损检查
        if pnl_pct <= self.p.stop_loss_pct:
            self.log(f'触发止损: {stock_code}, 收益率: {pnl_pct:.2%}')
            return True
        
        # 止盈检查
        if pnl_pct >= self.p.take_profit_pct:
            self.log(f'触发止盈: {stock_code}, 收益率: {pnl_pct:.2%}')
            return True
        
        return False
    
    def filter_stocks(self, stock_codes: List[str]) -> List[str]:
        """
        股票过滤器
        
        Args:
            stock_codes: 待过滤的股票代码列表
            
        Returns:
            过滤后的股票代码列表
        """
        filtered_stocks = []
        
        for stock_code in stock_codes:
            # 基础数据检查
            current_price = self.get_price_data(stock_code, 'close')
            volume = self.get_price_data(stock_code, 'volume')
            
            if current_price is None or volume is None:
                continue
            
            # 价格过滤
            if current_price < self.p.min_price or current_price > self.p.max_price:
                continue
            
            # 成交量过滤（避免流动性不足的股票）
            if volume < 1000000:  # 最小成交量100万股
                continue
            
            filtered_stocks.append(stock_code)
        
        return filtered_stocks
    
    def next(self):
        """策略主逻辑 - 子类需要重写此方法"""
        # 基础的风险管理
        for stock_code in list(self.positions_info.keys()):
            if self.apply_risk_management(stock_code):
                if stock_code in self.data_dict:
                    data = self.data_dict[stock_code]
                    self.sell(data=data)
        
        # 调仓逻辑由子类实现
        if self.should_rebalance():
            self.rebalance()
            self.reset_rebalance_counter()
    
    def rebalance(self):
        """调仓逻辑 - 子类需要重写此方法"""
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略信息
        
        Returns:
            策略信息字典
        """
        current_positions = self.get_current_positions()
        
        return {
            'strategy_name': self.__class__.__name__,
            'total_positions': len(current_positions),
            'max_positions': self.p.max_positions,
            'portfolio_value': self.get_portfolio_value(),
            'available_cash': self.get_available_cash(),
            'positions_info': current_positions,
            'trade_count': len(self.trade_records),
            'rebalance_counter': self.rebalance_counter
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取策略性能摘要
        
        Returns:
            性能摘要字典
        """
        if not self.trade_records:
            return {'total_trades': 0}
        
        trades_df = pd.DataFrame(self.trade_records)
        
        # 基础统计
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        
        # 收益统计
        total_pnl = trades_df['pnl'].sum()
        avg_pnl = trades_df['pnl'].mean()
        avg_pnl_pct = trades_df['pnl_pct'].mean()
        
        # 胜率统计
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # 持仓时间统计
        avg_hold_days = trades_df['hold_days'].mean()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'avg_pnl_pct': avg_pnl_pct,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else float('inf'),
            'avg_hold_days': avg_hold_days
        }