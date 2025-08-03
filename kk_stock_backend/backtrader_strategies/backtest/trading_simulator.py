#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股交易规则模拟器
模拟真实A股市场的交易规则、限制和费用计算
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    """订单类型"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"      # 待处理
    EXECUTED = "executed"    # 已执行
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"    # 已拒绝
    PARTIAL = "partial"      # 部分成交


@dataclass
class Order:
    """订单数据类"""
    order_id: str
    stock_code: str
    order_type: OrderType
    quantity: int
    price: float
    timestamp: datetime
    status: OrderStatus = OrderStatus.PENDING
    executed_quantity: int = 0
    executed_price: float = 0.0
    commission: float = 0.0
    stamp_tax: float = 0.0
    total_cost: float = 0.0
    reject_reason: str = ""


@dataclass
class TradingRule:
    """交易规则配置"""
    # 涨跌停限制
    limit_up_pct: float = 0.10      # 涨停10%
    limit_down_pct: float = -0.10   # 跌停10%
    st_limit_pct: float = 0.05      # ST股票5%
    
    # 交易时间
    morning_start: time = time(9, 30)
    morning_end: time = time(11, 30)
    afternoon_start: time = time(13, 0)
    afternoon_end: time = time(15, 0)
    
    # 买卖单位
    min_buy_unit: int = 100         # 最小买入单位（手）
    sell_unit: int = 1              # 卖出可以是任意股数
    
    # 费用设置
    commission_rate: float = 0.0001  # 万一手续费
    min_commission: float = 5.0      # 最低手续费5元
    stamp_tax_rate: float = 0.001    # 千一印花税（仅卖出）
    transfer_fee_rate: float = 0.00002  # 过户费（沪市）
    
    # 滑点设置
    slippage_rate: float = 0.001     # 千一滑点


class TradingSimulator:
    """
    A股交易规则模拟器
    负责处理所有与A股交易规则相关的逻辑
    """
    
    def __init__(self, trading_rule: Optional[TradingRule] = None):
        """
        初始化交易模拟器
        
        Args:
            trading_rule: 交易规则配置，如果为None则使用默认配置
        """
        self.trading_rule = trading_rule or TradingRule()
        self.trading_calendar = self._load_trading_calendar()
        
    def _load_trading_calendar(self) -> List[str]:
        """
        加载交易日历
        这里简化处理，实际应该从数据库加载真实交易日历
        """
        # 简化：生成2020-2025年的交易日（排除周末）
        date_range = pd.date_range('2020-01-01', '2025-12-31', freq='D')
        trading_days = []
        
        for date in date_range:
            # 排除周末
            if date.weekday() < 5:  # 0-4是周一到周五
                trading_days.append(date.strftime('%Y-%m-%d'))
        
        return trading_days
    
    def is_trading_day(self, date: str) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期字符串 'YYYY-MM-DD'
            
        Returns:
            是否为交易日
        """
        return date in self.trading_calendar
    
    def is_trading_time(self, timestamp: datetime) -> bool:
        """
        判断是否在交易时间内
        
        Args:
            timestamp: 时间戳
            
        Returns:
            是否在交易时间内
        """
        current_time = timestamp.time()
        
        # 上午交易时间
        if (self.trading_rule.morning_start <= current_time <= self.trading_rule.morning_end):
            return True
        
        # 下午交易时间
        if (self.trading_rule.afternoon_start <= current_time <= self.trading_rule.afternoon_end):
            return True
        
        return False
    
    def calculate_limit_price(self, prev_close: float, is_st: bool = False) -> Tuple[float, float]:
        """
        计算涨跌停价格
        
        Args:
            prev_close: 昨日收盘价
            is_st: 是否为ST股票
            
        Returns:
            (涨停价, 跌停价)
        """
        if is_st:
            limit_pct = self.trading_rule.st_limit_pct
        else:
            limit_pct = self.trading_rule.limit_up_pct
        
        limit_up = prev_close * (1 + limit_pct)
        limit_down = prev_close * (1 + self.trading_rule.limit_down_pct)
        
        # A股价格精度为分
        limit_up = round(limit_up, 2)
        limit_down = round(limit_down, 2)
        
        return limit_up, limit_down
    
    def validate_order(self, order: Order, market_data: Dict) -> Tuple[bool, str]:
        """
        验证订单是否符合交易规则
        
        Args:
            order: 订单对象
            market_data: 当日市场数据
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查交易日
        trade_date = order.timestamp.strftime('%Y-%m-%d')
        if not self.is_trading_day(trade_date):
            return False, "非交易日"
        
        # 检查交易时间（回测中可以放宽）
        # if not self.is_trading_time(order.timestamp):
        #     return False, "非交易时间"
        
        # 检查股票代码
        if order.stock_code not in market_data:
            return False, f"股票代码 {order.stock_code} 不存在"
        
        stock_data = market_data[order.stock_code]
        
        # 检查停牌
        if stock_data.get('suspended', False):
            return False, "股票停牌"
        
        # 检查涨跌停
        current_price = stock_data['close']
        prev_close = stock_data.get('prev_close', current_price)
        is_st = 'ST' in order.stock_code
        
        limit_up, limit_down = self.calculate_limit_price(prev_close, is_st)
        
        if order.order_type == OrderType.BUY:
            # 买入订单验证
            if order.quantity % self.trading_rule.min_buy_unit != 0:
                return False, f"买入数量必须是{self.trading_rule.min_buy_unit}股的整数倍"
            
            if order.quantity <= 0:
                return False, "买入数量必须大于0"
            
            # 检查涨停（简化：如果当前价格已经涨停，则不能买入）
            if current_price >= limit_up * 0.999:  # 允许小幅误差
                return False, "股票涨停，无法买入"
        
        elif order.order_type == OrderType.SELL:
            # 卖出订单验证
            if order.quantity <= 0:
                return False, "卖出数量必须大于0"
            
            # 检查跌停（简化：如果当前价格已经跌停，则不能卖出）
            if current_price <= limit_down * 1.001:  # 允许小幅误差
                return False, "股票跌停，无法卖出"
        
        return True, ""
    
    def calculate_fees(self, order: Order, executed_value: float) -> Tuple[float, float, float]:
        """
        计算交易费用
        
        Args:
            order: 订单对象
            executed_value: 成交金额
            
        Returns:
            (手续费, 印花税, 过户费)
        """
        # 手续费计算
        commission = executed_value * self.trading_rule.commission_rate
        commission = max(commission, self.trading_rule.min_commission)
        
        # 印花税（仅卖出收取）
        stamp_tax = 0.0
        if order.order_type == OrderType.SELL:
            stamp_tax = executed_value * self.trading_rule.stamp_tax_rate
        
        # 过户费（沪市收取，深市不收）
        transfer_fee = 0.0
        if order.stock_code.endswith('.SH'):
            transfer_fee = executed_value * self.trading_rule.transfer_fee_rate
            transfer_fee = max(transfer_fee, 1.0)  # 最低1元
        
        return commission, stamp_tax, transfer_fee
    
    def apply_slippage(self, price: float, order_type: OrderType) -> float:
        """
        应用滑点
        
        Args:
            price: 原始价格
            order_type: 订单类型
            
        Returns:
            应用滑点后的价格
        """
        if order_type == OrderType.BUY:
            # 买入时价格向上滑点
            slipped_price = price * (1 + self.trading_rule.slippage_rate)
        else:
            # 卖出时价格向下滑点
            slipped_price = price * (1 - self.trading_rule.slippage_rate)
        
        return round(slipped_price, 2)
    
    def execute_order(self, order: Order, market_data: Dict) -> Order:
        """
        执行订单
        
        Args:
            order: 待执行的订单
            market_data: 市场数据
            
        Returns:
            执行后的订单
        """
        # 验证订单
        is_valid, error_msg = self.validate_order(order, market_data)
        if not is_valid:
            order.status = OrderStatus.REJECTED
            order.reject_reason = error_msg
            return order
        
        # 获取执行价格
        stock_data = market_data[order.stock_code]
        
        # 简化处理：使用收盘价作为执行价格
        execution_price = stock_data['close']
        
        # 应用滑点
        execution_price = self.apply_slippage(execution_price, order.order_type)
        
        # 执行订单
        order.executed_quantity = order.quantity
        order.executed_price = execution_price
        order.status = OrderStatus.EXECUTED
        
        # 计算费用
        executed_value = order.executed_quantity * order.executed_price
        commission, stamp_tax, transfer_fee = self.calculate_fees(order, executed_value)
        
        order.commission = commission
        order.stamp_tax = stamp_tax
        
        # 计算总成本
        if order.order_type == OrderType.BUY:
            order.total_cost = executed_value + commission + transfer_fee
        else:
            order.total_cost = executed_value - commission - stamp_tax - transfer_fee
        
        return order
    
    def get_trading_info(self) -> Dict:
        """
        获取交易规则信息
        
        Returns:
            交易规则信息字典
        """
        return {
            'limit_up_pct': self.trading_rule.limit_up_pct,
            'limit_down_pct': self.trading_rule.limit_down_pct,
            'st_limit_pct': self.trading_rule.st_limit_pct,
            'min_buy_unit': self.trading_rule.min_buy_unit,
            'commission_rate': self.trading_rule.commission_rate,
            'min_commission': self.trading_rule.min_commission,
            'stamp_tax_rate': self.trading_rule.stamp_tax_rate,
            'transfer_fee_rate': self.trading_rule.transfer_fee_rate,
            'slippage_rate': self.trading_rule.slippage_rate,
            'trading_days_count': len(self.trading_calendar)
        }


if __name__ == "__main__":
    # 测试交易模拟器
    print("🚀 测试A股交易规则模拟器...")
    
    simulator = TradingSimulator()
    
    # 测试交易日判断
    print(f"2024-01-01是否为交易日: {simulator.is_trading_day('2024-01-01')}")
    print(f"2024-01-02是否为交易日: {simulator.is_trading_day('2024-01-02')}")
    
    # 测试涨跌停计算
    limit_up, limit_down = simulator.calculate_limit_price(10.0)
    print(f"昨收10元，涨停价: {limit_up}, 跌停价: {limit_down}")
    
    # 测试ST股票涨跌停
    st_limit_up, st_limit_down = simulator.calculate_limit_price(10.0, is_st=True)
    print(f"ST股票昨收10元，涨停价: {st_limit_up}, 跌停价: {st_limit_down}")
    
    # 测试费用计算
    test_order = Order(
        order_id="test_001",
        stock_code="000001.SZ",
        order_type=OrderType.BUY,
        quantity=1000,
        price=10.0,
        timestamp=datetime.now()
    )
    
    commission, stamp_tax, transfer_fee = simulator.calculate_fees(test_order, 10000)
    print(f"买入1万元费用 - 手续费: {commission:.2f}, 印花税: {stamp_tax:.2f}, 过户费: {transfer_fee:.2f}")
    
    test_order.order_type = OrderType.SELL
    commission, stamp_tax, transfer_fee = simulator.calculate_fees(test_order, 10000)
    print(f"卖出1万元费用 - 手续费: {commission:.2f}, 印花税: {stamp_tax:.2f}, 过户费: {transfer_fee:.2f}")
    
    print("✅ 交易模拟器测试完成")