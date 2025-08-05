#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组合管理和风险控制系统
负责持仓管理、风险控制、资金分配等
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging

from .order_manager import Trade, OrderType, Position


@dataclass
class PortfolioSnapshot:
    """组合快照数据类"""
    date: datetime
    total_value: float
    cash: float
    positions_value: float
    total_positions: int
    daily_return: float
    cumulative_return: float
    drawdown: float
    positions: Dict[str, Position]


class PortfolioManager:
    """
    组合管理器
    负责持仓管理、资金分配、风险控制
    """
    
    def __init__(self, initial_cash: float = 1000000.0):
        """
        初始化组合管理器
        
        Args:
            initial_cash: 初始资金
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}  # 当前持仓：{stock_code: Position}
        self.portfolio_history = []  # 组合历史快照
        
        # 风险控制参数
        self.max_single_position_pct = 0.1  # 单股最大仓位10%
        self.max_total_positions = 20  # 最大持仓数量
        self.stop_loss_pct = 0.06  # 止损比例6%
        self.take_profit_pct = 0.12  # 止盈比例12%
        self.max_drawdown_limit = 0.20  # 最大回撤限制20%
        self.min_holding_trading_days = 0  # 最小持仓交易日天数（默认0天，即无限制）
        
        # 交易日历缓存
        self.trading_dates_cache = []  # 用于计算交易日持仓天数
        
        # 统计变量
        self.max_portfolio_value = initial_cash
        self.max_drawdown = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
    def update_portfolio_config(self, config: Dict[str, Any]):
        """
        更新组合配置
        
        Args:
            config: 配置字典
        """
        if 'max_single_position' in config:
            self.max_single_position_pct = config['max_single_position']
        if 'max_positions' in config:
            self.max_total_positions = config['max_positions']
        if 'stop_loss_pct' in config:
            self.stop_loss_pct = config['stop_loss_pct']
        if 'take_profit_pct' in config:
            self.take_profit_pct = config['take_profit_pct']
        if 'max_drawdown_limit' in config:
            self.max_drawdown_limit = config['max_drawdown_limit']
        if 'min_holding_trading_days' in config:
            self.min_holding_trading_days = config['min_holding_trading_days']
            
        self.logger.info(f"组合配置已更新: {config}")
    
    def process_trade(self, trade: Trade):
        """
        处理交易，更新持仓
        
        Args:
            trade: 交易记录
        """
        stock_code = trade.stock_code
        
        if trade.order_type == OrderType.BUY:
            self._process_buy_trade(trade)
        elif trade.order_type == OrderType.SELL:
            self._process_sell_trade(trade)
        
        # 更新现金
        self.cash += trade.net_amount
        
        self.total_trades += 1
        self.logger.info(f"处理交易: {trade.order_type.value} {stock_code} "
                        f"{trade.quantity}股 @{trade.price:.2f}, 现金余额: {self.cash:.2f}")
    
    def _process_buy_trade(self, trade: Trade):
        """
        处理买入交易
        
        Args:
            trade: 买入交易记录
        """
        stock_code = trade.stock_code
        
        if stock_code in self.positions:
            # 加仓：更新平均成本
            position = self.positions[stock_code]
            total_cost = (position.quantity * position.avg_price + 
                         trade.quantity * trade.price)
            total_quantity = position.quantity + trade.quantity
            
            position.quantity = total_quantity
            position.avg_price = total_cost / total_quantity
            position.last_update = trade.trade_date
            
        else:
            # 建仓：创建新持仓
            position = Position(
                stock_code=stock_code,
                quantity=trade.quantity,
                avg_price=trade.price,
                market_value=trade.quantity * trade.price,
                unrealized_pnl=0.0,
                unrealized_pnl_pct=0.0,
                entry_date=trade.trade_date,
                last_update=trade.trade_date
            )
            self.positions[stock_code] = position
    
    def _process_sell_trade(self, trade: Trade):
        """
        处理卖出交易
        
        Args:
            trade: 卖出交易记录
        """
        stock_code = trade.stock_code
        
        if stock_code not in self.positions:
            self.logger.error(f"尝试卖出未持有的股票: {stock_code}")
            return
        
        position = self.positions[stock_code]
        
        if trade.quantity >= position.quantity:
            # 全部卖出：移除持仓
            realized_pnl = (trade.price - position.avg_price) * position.quantity
            if realized_pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            del self.positions[stock_code]
            self.logger.info(f"平仓 {stock_code}, 实现盈亏: {realized_pnl:.2f}")
            
        else:
            # 部分卖出：减少持仓
            position.quantity -= trade.quantity
            position.last_update = trade.trade_date
            
            realized_pnl = (trade.price - position.avg_price) * trade.quantity
            if realized_pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            self.logger.info(f"减仓 {stock_code}, 剩余: {position.quantity}股, "
                           f"实现盈亏: {realized_pnl:.2f}")
    
    def update_positions_value(self, market_data: Dict[str, Dict], current_date: str):
        """
        更新持仓市值和盈亏
        
        Args:
            market_data: 市场数据
            current_date: 当前日期
        """
        for stock_code, position in self.positions.items():
            if stock_code in market_data:
                current_price = market_data[stock_code]['close']
                
                # 更新市值
                position.market_value = position.quantity * current_price
                
                # 更新未实现盈亏
                position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                if position.avg_price > 0:
                    position.unrealized_pnl_pct = position.unrealized_pnl / (position.avg_price * position.quantity)
                else:
                    position.unrealized_pnl_pct = 0.0
                
                position.last_update = pd.to_datetime(current_date)
    
    def take_snapshot(self, current_date: str) -> PortfolioSnapshot:
        """
        创建组合快照
        
        Args:
            current_date: 当前日期
            
        Returns:
            组合快照
        """
        # 计算持仓总市值
        positions_value = sum(pos.market_value for pos in self.positions.values())
        total_value = self.cash + positions_value
        
        # 计算收益率
        cumulative_return = (total_value - self.initial_cash) / self.initial_cash
        
        # 计算日收益率
        daily_return = 0.0
        if len(self.portfolio_history) > 0:
            prev_value = self.portfolio_history[-1].total_value
            if prev_value > 0:
                daily_return = (total_value - prev_value) / prev_value
        
        # 更新最大组合价值和回撤
        if total_value > self.max_portfolio_value:
            self.max_portfolio_value = total_value
        
        current_drawdown = (total_value - self.max_portfolio_value) / self.max_portfolio_value
        if current_drawdown < self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # 创建快照
        snapshot = PortfolioSnapshot(
            date=pd.to_datetime(current_date),
            total_value=total_value,
            cash=self.cash,
            positions_value=positions_value,
            total_positions=len(self.positions),
            daily_return=daily_return,
            cumulative_return=cumulative_return,
            drawdown=current_drawdown,
            positions=self.positions.copy()
        )
        
        # 保存快照
        self.portfolio_history.append(snapshot)
        
        return snapshot
    
    def check_risk_limits(self, market_data: Dict[str, Dict], current_date: str = None) -> List[Tuple[str, str]]:
        """
        检查风险限制
        
        Args:
            market_data: 市场数据
            current_date: 当前日期（用于计算持仓天数）
            
        Returns:
            违反风险限制的股票列表 [(stock_code, reason)]
        """
        violations = []
        total_value = self.get_total_value()
        
        # 更新交易日历缓存
        if current_date and current_date not in self.trading_dates_cache:
            self.trading_dates_cache.append(current_date)
        
        for stock_code, position in self.positions.items():
            if stock_code not in market_data:
                continue
            
            current_price = market_data[stock_code]['close']
            
            # 检查最小持仓天数
            if self.min_holding_trading_days > 0 and current_date:
                holding_days = self._calculate_holding_trading_days(position, current_date)
                
                if holding_days < self.min_holding_trading_days:
                    # 检查是否为严重亏损（可以提前止损）
                    if position.avg_price > 0:
                        pnl_pct = (current_price - position.avg_price) / position.avg_price
                        if pnl_pct <= -self.stop_loss_pct * 1.5:  # 亏损超过1.5倍止损线才允许提前卖出
                            violations.append((stock_code, f"严重亏损提前止损: {pnl_pct:.2%} (持仓{holding_days}个交易日)"))
                    # 其他情况不允许卖出（跳过后续风控检查）
                    continue
            
            # 检查止损止盈
            if position.avg_price > 0:
                pnl_pct = (current_price - position.avg_price) / position.avg_price
                
                if pnl_pct <= -self.stop_loss_pct:
                    violations.append((stock_code, f"触发止损: {pnl_pct:.2%}"))
                
                elif pnl_pct >= self.take_profit_pct:
                    violations.append((stock_code, f"触发止盈: {pnl_pct:.2%}"))
            
            # 检查单股仓位限制
            if total_value > 0:
                position_pct = position.market_value / total_value
                if position_pct > self.max_single_position_pct:
                    violations.append((stock_code, f"超过单股仓位限制: {position_pct:.2%}"))
        
        # 检查最大回撤
        if abs(self.max_drawdown) > self.max_drawdown_limit:
            violations.append(("PORTFOLIO", f"超过最大回撤限制: {self.max_drawdown:.2%}"))
        
        return violations
    
    def _calculate_holding_trading_days(self, position: Position, current_date: str) -> int:
        """
        计算持仓交易日天数
        
        Args:
            position: 持仓对象
            current_date: 当前日期
            
        Returns:
            持仓交易日天数
        """
        try:
            entry_date = position.entry_date.strftime('%Y-%m-%d') if hasattr(position.entry_date, 'strftime') else str(position.entry_date)
            
            # 确保当前日期在缓存中
            if current_date not in self.trading_dates_cache:
                self.trading_dates_cache.append(current_date)
            
            # 使用交易日历计算
            try:
                entry_index = self.trading_dates_cache.index(entry_date)
                current_index = self.trading_dates_cache.index(current_date)
                return max(0, current_index - entry_index)
            except ValueError:
                # 如果日期不在缓存中，使用自然日粗略估算
                from datetime import datetime
                entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
                current_dt = datetime.strptime(current_date, '%Y-%m-%d')
                total_days = (current_dt - entry_dt).days
                # 粗略估算：5个工作日约等于7个自然日
                return max(0, int(total_days * 5 / 7))
                
        except Exception as e:
            self.logger.warning(f"计算持仓天数失败: {e}")
            return 0
    
    def calculate_position_size(self, 
                               stock_code: str, 
                               target_weight: float, 
                               current_price: float) -> int:
        """
        计算建仓数量
        
        Args:
            stock_code: 股票代码
            target_weight: 目标权重
            current_price: 当前价格
            
        Returns:
            建仓数量（股）
        """
        total_value = self.get_total_value()
        target_value = total_value * target_weight
        
        # 考虑交易费用的影响
        estimated_commission = target_value * 0.0003
        available_value = target_value - estimated_commission
        
        if available_value <= 0 or current_price <= 0:
            return 0
        
        # 计算股数（向下取整到100的倍数）
        shares = int(available_value / current_price / 100) * 100
        
        return max(0, shares)
    
    def get_available_cash_for_new_position(self) -> float:
        """
        获取可用于新建仓的现金
        
        Returns:
            可用现金金额
        """
        # 预留一定比例的现金作为缓冲
        cash_buffer_pct = 0.05  # 5%缓冲
        available_cash = self.cash * (1 - cash_buffer_pct)
        
        return max(0, available_cash)
    
    def can_open_new_position(self) -> bool:
        """
        检查是否可以开新仓
        
        Returns:
            是否可以开新仓
        """
        # 检查持仓数量限制
        if len(self.positions) >= self.max_total_positions:
            return False
        
        # 检查可用现金
        available_cash = self.get_available_cash_for_new_position()
        min_position_value = 10000  # 最小建仓金额1万元
        
        if available_cash < min_position_value:
            return False
        
        return True
    
    def get_total_value(self) -> float:
        """
        获取组合总价值
        
        Returns:
            组合总价值
        """
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value
    
    def get_position_info(self, stock_code: str) -> Optional[Position]:
        """
        获取指定股票的持仓信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            持仓信息
        """
        return self.positions.get(stock_code)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """
        获取所有持仓
        
        Returns:
            所有持仓字典
        """
        return self.positions.copy()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        获取组合摘要
        
        Returns:
            组合摘要字典
        """
        total_value = self.get_total_value()
        positions_value = sum(pos.market_value for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        # 计算胜率
        total_closed_trades = self.winning_trades + self.losing_trades
        win_rate = self.winning_trades / total_closed_trades if total_closed_trades > 0 else 0
        
        return {
            'total_value': total_value,
            'cash': self.cash,
            'positions_value': positions_value,
            'cash_ratio': self.cash / total_value if total_value > 0 else 1.0,
            'total_positions': len(self.positions),
            'total_unrealized_pnl': total_unrealized_pnl,
            'cumulative_return': (total_value - self.initial_cash) / self.initial_cash,
            'max_drawdown': self.max_drawdown,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate
        }
    
    def get_portfolio_dataframe(self) -> pd.DataFrame:
        """
        获取组合历史DataFrame
        
        Returns:
            组合历史DataFrame
        """
        if not self.portfolio_history:
            return pd.DataFrame()
        
        data = []
        for snapshot in self.portfolio_history:
            data.append({
                'date': snapshot.date,
                'total_value': snapshot.total_value,
                'cash': snapshot.cash,
                'positions_value': snapshot.positions_value,
                'total_positions': snapshot.total_positions,
                'daily_return': snapshot.daily_return,
                'cumulative_return': snapshot.cumulative_return,
                'drawdown': snapshot.drawdown
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return df
    
    def export_portfolio_to_csv(self, filename: str):
        """
        导出组合历史到CSV文件
        
        Args:
            filename: 文件名
        """
        df = self.get_portfolio_dataframe()
        if not df.empty:
            df.to_csv(filename, index=False, encoding='utf-8')
            self.logger.info(f"组合历史已导出到: {filename}")
        else:
            self.logger.warning("没有组合历史可导出")
    
    def reset_portfolio(self):
        """重置组合"""
        self.cash = self.initial_cash
        self.positions.clear()
        self.portfolio_history.clear()
        self.max_portfolio_value = self.initial_cash
        self.max_drawdown = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        self.logger.info("组合已重置")


if __name__ == "__main__":
    # 测试组合管理器
    print("🚀 测试组合管理器...")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建组合管理器
    portfolio_manager = PortfolioManager(initial_cash=1000000.0)
    
    # 创建模拟交易
    from datetime import datetime
    
    current_date = datetime.now()
    
    # 模拟买入交易
    buy_trade = Trade(
        trade_id="trade_001",
        stock_code="000001.SZ",
        order_type=OrderType.BUY,
        quantity=1000,
        price=10.0,
        commission=30.0,
        stamp_tax=0.0,
        net_amount=-10030.0,
        trade_date=current_date
    )
    
    portfolio_manager.process_trade(buy_trade)
    
    # 模拟市场数据更新
    market_data = {
        "000001.SZ": {
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000
        }
    }
    
    portfolio_manager.update_positions_value(market_data, "2024-01-15")
    
    # 创建组合快照
    snapshot = portfolio_manager.take_snapshot("2024-01-15")
    
    print(f"\n组合快照:")
    print(f"总价值: {snapshot.total_value:.2f}")
    print(f"现金: {snapshot.cash:.2f}")
    print(f"持仓市值: {snapshot.positions_value:.2f}")
    print(f"累计收益率: {snapshot.cumulative_return:.2%}")
    
    # 获取组合摘要
    summary = portfolio_manager.get_portfolio_summary()
    print(f"\n组合摘要: {summary}")
    
    # 检查风险限制
    violations = portfolio_manager.check_risk_limits(market_data)
    print(f"\n风险检查: {violations}")
    
    print("✅ 组合管理器测试完成")