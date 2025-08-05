#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单管理和执行系统
负责订单的创建、验证、执行和管理
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
import pandas as pd

from .trading_simulator import Order, OrderType, OrderStatus, TradingSimulator


@dataclass
class Position:
    """持仓数据类"""
    stock_code: str
    quantity: int
    avg_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    entry_date: datetime
    last_update: datetime


@dataclass 
class Trade:
    """交易记录数据类"""
    trade_id: str
    stock_code: str
    order_type: OrderType
    quantity: int
    price: float
    commission: float
    stamp_tax: float
    net_amount: float
    trade_date: datetime


class OrderManager:
    """
    订单管理器
    负责订单的生命周期管理
    """
    
    def __init__(self, trading_simulator: TradingSimulator):
        """
        初始化订单管理器
        
        Args:
            trading_simulator: 交易模拟器
        """
        self.trading_simulator = trading_simulator
        self.orders = {}  # 所有订单：{order_id: Order}
        self.pending_orders = {}  # 待处理订单：{order_id: Order}
        self.executed_orders = {}  # 已执行订单：{order_id: Order}
        self.trades = {}  # 交易记录：{trade_id: Trade}
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
    def create_order(self, 
                    stock_code: str,
                    order_type: OrderType,
                    quantity: int,
                    price: float,
                    timestamp: datetime) -> str:
        """
        创建订单
        
        Args:
            stock_code: 股票代码
            order_type: 订单类型
            quantity: 数量
            price: 价格
            timestamp: 时间戳
            
        Returns:
            订单ID
        """
        # 检查是否存在重复的待处理订单（同一股票、同一类型、同一数量）
        for existing_order in self.pending_orders.values():
            if (existing_order.stock_code == stock_code and 
                existing_order.order_type == order_type and
                existing_order.quantity == quantity and
                abs(existing_order.price - price) < 0.01):  # 价格差异小于0.01认为是重复
                self.logger.warning(f"检测到重复订单，跳过创建: {stock_code} {order_type.value} {quantity}股")
                return existing_order.order_id
        
        order_id = str(uuid.uuid4())[:8]
        
        order = Order(
            order_id=order_id,
            stock_code=stock_code,
            order_type=order_type,
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            status=OrderStatus.PENDING
        )
        
        # 保存订单
        self.orders[order_id] = order
        self.pending_orders[order_id] = order
        
        self.logger.info(f"创建订单: {order_id} - {order_type.value} {stock_code} {quantity}股 @{price:.2f}")
        
        return order_id
    
    def execute_pending_orders(self, current_date: str, market_data: Dict[str, Dict]) -> List[Trade]:
        """
        执行所有待处理订单
        
        Args:
            current_date: 当前日期
            market_data: 市场数据 {stock_code: daily_data}
            
        Returns:
            执行的交易列表
        """
        executed_trades = []
        
        # 处理所有待执行订单
        for order_id in list(self.pending_orders.keys()):
            order = self.pending_orders[order_id]
            
            # 检查股票是否有数据
            if order.stock_code not in market_data:
                self.logger.warning(f"股票 {order.stock_code} 无市场数据，订单 {order_id} 取消")
                self._cancel_order(order_id, "无市场数据")
                continue
            
            # 执行订单
            executed_order = self.trading_simulator.execute_order(order, market_data)
            
            # 更新订单状态
            self.orders[order_id] = executed_order
            
            if executed_order.status == OrderStatus.EXECUTED:
                # 订单执行成功
                self.executed_orders[order_id] = executed_order
                del self.pending_orders[order_id]
                
                # 创建交易记录
                trade = self._create_trade_record(executed_order, current_date)
                executed_trades.append(trade)
                
                self.logger.info(f"订单执行成功: {order_id} - {executed_order.order_type.value} "
                               f"{executed_order.stock_code} {executed_order.executed_quantity}股 "
                               f"@{executed_order.executed_price:.2f}")
                
            elif executed_order.status == OrderStatus.REJECTED:
                # 订单被拒绝
                del self.pending_orders[order_id]
                self.logger.warning(f"订单被拒绝: {order_id} - {executed_order.reject_reason}")
                
            elif executed_order.status == OrderStatus.CANCELLED:
                # 订单被取消
                del self.pending_orders[order_id]
                self.logger.info(f"订单被取消: {order_id}")
        
        return executed_trades
    
    def _create_trade_record(self, order: Order, trade_date: str) -> Trade:
        """
        创建交易记录
        
        Args:
            order: 已执行的订单
            trade_date: 交易日期
            
        Returns:
            交易记录
        """
        trade_id = str(uuid.uuid4())[:8]
        
        # 计算净金额（现金流变化）
        if order.order_type == OrderType.BUY:
            # 买入：现金减少（股票价值 + 手续费），印花税买入时为0
            net_amount = -(order.executed_quantity * order.executed_price + order.commission)
        else:
            # 卖出：现金增加（股票价值 - 手续费 - 印花税）
            net_amount = (order.executed_quantity * order.executed_price - 
                         order.commission - order.stamp_tax)
        
        trade = Trade(
            trade_id=trade_id,
            stock_code=order.stock_code,
            order_type=order.order_type,
            quantity=order.executed_quantity,
            price=order.executed_price,
            commission=order.commission,
            stamp_tax=order.stamp_tax,
            net_amount=net_amount,
            trade_date=pd.to_datetime(trade_date)
        )
        
        self.trades[trade_id] = trade
        return trade
    
    def _cancel_order(self, order_id: str, reason: str = ""):
        """
        取消订单
        
        Args:
            order_id: 订单ID
            reason: 取消原因
        """
        if order_id in self.pending_orders:
            order = self.pending_orders[order_id]
            order.status = OrderStatus.CANCELLED
            order.reject_reason = reason
            
            self.orders[order_id] = order
            del self.pending_orders[order_id]
    
    def cancel_all_pending_orders(self):
        """取消所有待处理订单"""
        for order_id in list(self.pending_orders.keys()):
            self._cancel_order(order_id, "批量取消")
        
        self.logger.info("已取消所有待处理订单")
    
    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """
        获取订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单状态
        """
        if order_id in self.orders:
            return self.orders[order_id].status
        return None
    
    def get_order_details(self, order_id: str) -> Optional[Dict]:
        """
        获取订单详情
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单详情字典
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            return asdict(order)
        return None
    
    def get_trades_by_stock(self, stock_code: str) -> List[Trade]:
        """
        获取指定股票的所有交易记录
        
        Args:
            stock_code: 股票代码
            
        Returns:
            交易记录列表
        """
        return [trade for trade in self.trades.values() 
                if trade.stock_code == stock_code]
    
    def get_trades_by_date_range(self, start_date: str, end_date: str) -> List[Trade]:
        """
        获取指定日期范围的交易记录
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易记录列表
        """
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        return [trade for trade in self.trades.values() 
                if start_dt <= trade.trade_date <= end_dt]
    
    def get_trading_summary(self) -> Dict:
        """
        获取交易统计摘要
        
        Returns:
            交易统计字典
        """
        total_orders = len(self.orders)
        executed_orders = len(self.executed_orders)
        pending_orders = len(self.pending_orders)
        cancelled_orders = len([o for o in self.orders.values() 
                               if o.status == OrderStatus.CANCELLED])
        rejected_orders = len([o for o in self.orders.values() 
                              if o.status == OrderStatus.REJECTED])
        
        total_trades = len(self.trades)
        buy_trades = len([t for t in self.trades.values() 
                         if t.order_type == OrderType.BUY])
        sell_trades = len([t for t in self.trades.values() 
                          if t.order_type == OrderType.SELL])
        
        total_commission = sum(t.commission for t in self.trades.values())
        total_stamp_tax = sum(t.stamp_tax for t in self.trades.values())
        total_fees = total_commission + total_stamp_tax
        
        return {
            'orders': {
                'total': total_orders,
                'executed': executed_orders,
                'pending': pending_orders,
                'cancelled': cancelled_orders,
                'rejected': rejected_orders
            },
            'trades': {
                'total': total_trades,
                'buy_trades': buy_trades,
                'sell_trades': sell_trades
            },
            'fees': {
                'total_commission': total_commission,
                'total_stamp_tax': total_stamp_tax,
                'total_fees': total_fees
            }
        }
    
    def get_trades_dataframe(self) -> pd.DataFrame:
        """
        获取交易记录DataFrame
        
        Returns:
            交易记录DataFrame
        """
        if not self.trades:
            return pd.DataFrame()
        
        trades_data = []
        for trade in self.trades.values():
            trade_dict = asdict(trade)
            trade_dict['order_type'] = trade_dict['order_type'].value
            trades_data.append(trade_dict)
        
        df = pd.DataFrame(trades_data)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date')
        
        return df
    
    def export_trades_to_csv(self, filename: str):
        """
        导出交易记录到CSV文件
        
        Args:
            filename: 文件名
        """
        df = self.get_trades_dataframe()
        if not df.empty:
            df.to_csv(filename, index=False, encoding='utf-8')
            self.logger.info(f"交易记录已导出到: {filename}")
        else:
            self.logger.warning("没有交易记录可导出")
    
    def get_executed_trades(self) -> List[Trade]:
        """
        获取所有已执行的交易记录列表
        
        Returns:
            已执行的交易记录列表
        """
        return list(self.trades.values())
    
    def clear_history(self):
        """清理历史数据"""
        self.orders.clear()
        self.pending_orders.clear()
        self.executed_orders.clear()
        self.trades.clear()
        
        self.logger.info("订单和交易历史已清理")


if __name__ == "__main__":
    # 测试订单管理器
    print("🚀 测试订单管理器...")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建交易模拟器和订单管理器
    trading_simulator = TradingSimulator()
    order_manager = OrderManager(trading_simulator)
    
    # 创建测试订单
    current_time = datetime.now()
    
    # 买入订单
    buy_order_id = order_manager.create_order(
        stock_code="000001.SZ",
        order_type=OrderType.BUY,
        quantity=1000,
        price=10.0,
        timestamp=current_time
    )
    
    # 卖出订单
    sell_order_id = order_manager.create_order(
        stock_code="000002.SZ",
        order_type=OrderType.SELL,
        quantity=500,
        price=20.0,
        timestamp=current_time
    )
    
    # 模拟市场数据
    market_data = {
        "000001.SZ": {
            "open": 9.8,
            "high": 10.2,
            "low": 9.7,
            "close": 10.0,
            "volume": 1000000,
            "prev_close": 9.9
        },
        "000002.SZ": {
            "open": 19.8,
            "high": 20.2,
            "low": 19.7,
            "close": 20.0,
            "volume": 500000,
            "prev_close": 19.9
        }
    }
    
    # 执行订单
    executed_trades = order_manager.execute_pending_orders("2024-01-15", market_data)
    
    print(f"\n执行的交易数量: {len(executed_trades)}")
    for trade in executed_trades:
        print(f"交易: {trade.order_type.value} {trade.stock_code} "
              f"{trade.quantity}股 @{trade.price:.2f}, 净金额: {trade.net_amount:.2f}")
    
    # 获取交易统计
    summary = order_manager.get_trading_summary()
    print(f"\n交易统计: {summary}")
    
    # 获取交易记录DataFrame
    trades_df = order_manager.get_trades_dataframe()
    if not trades_df.empty:
        print(f"\n交易记录DataFrame:")
        print(trades_df)
    
    print("✅ 订单管理器测试完成")