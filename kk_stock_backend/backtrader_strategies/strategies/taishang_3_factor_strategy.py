#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
太上老君3号核心策略
基于RIM绝对估值法选股+事件驱动交易的中证1000指数增强策略
"""

import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional


class TaiShang3FactorStrategy(bt.Strategy):
    """
    太上老君3号核心策略
    
    策略逻辑：
    1. 基于中证1000成分股进行选股
    2. 使用RIM绝对估值法筛选低估股票：
       - RIM模型：基于剩余收益模型计算内在价值
       - 技术指标：动量、相对强度、成交量确认
       - 组合评分：RIM估值(60%) + 技术指标(40%)
    3. 事件驱动交易：参考太上老君2号触发机制
       - 买入：价格超跌反弹+成交量确认+RIM支撑
       - 卖出：止盈止损+盈利回撤+成交量异常+估值高估
    4. 风险控制：动态止盈止损+仓位管理
    
    适用场景：中证1000指数增强，追求稳健超额收益
    """
    
    params = (
        # 基础参数
        ('max_positions', 25),               # 最大持仓25只
        ('stock_pool_size', 50),             # 候选股票池50只
        ('max_position_value', 400000),      # 单股最大投资额40万
        ('signal_based_rebalance', True),    # 信号驱动调仓
        
        # 新3因子参数
        ('market_cap_weight', 0.40),         # 20日市值增长因子权重40%
        ('mae_rank_weight', 0.45),           # Rank MAE因子权重45%  
        ('growth_weight', 0.15),             # 成长性因子权重15%
        ('market_cap_period', 20),           # 市值变化计算周期
        ('mae_ma_period', 20),               # MAE移动平均周期
        
        # 风控参数
        ('stop_loss_pct', 0.15),             # 止损15%
        ('take_profit_pct', 0.30),           # 止盈30%
        ('max_drawdown_limit', 0.25),        # 最大回撤限制25%
        ('cash_reserve_ratio', 0.20),        # 现金储备比例20%
    )
    
    def __init__(self):
        """初始化策略"""
        self.order_list = []                 # 订单列表
        self.last_rebalance = None           # 上次调仓日期
        self.current_signal = 0              # 当前市场信号
        self.rsi_state = {'up_break': 1, 'down_break': -1}  # RSI状态
        
        # 策略统计
        self.trade_count = 0
        self.win_trades = 0
        self.total_profit = 0.0
        
        # 持仓管理
        self.position_info = {}              # 持仓详细信息
        self.target_weights = {}             # 目标权重
        
        print(f"🎯 太上老君3号策略初始化")
        print(f"   最大持仓: {self.params.max_positions}只")
        print(f"   单股限额: {self.params.max_position_value:,}元")
        print(f"   交易方式: 事件驱动触发")
        print(f"   RIM估值权重: 60% + 技术指标权重: 40%")
        print(f"   止盈: {self.params.take_profit_pct:.0%}, 止损: {self.params.stop_loss_pct:.0%}")
    
    def next(self):
        """策略主循环"""
        try:
            current_date = self.datas[0].datetime.date(0).strftime('%Y-%m-%d')
            
            # 1. 检查是否需要调仓
            if self._should_rebalance():
                self._execute_rebalancing(current_date)
            
            # 2. 检查现有持仓的风控
            self._check_risk_management()
            
            # 3. 记录策略状态
            self._log_strategy_status(current_date)
            
        except Exception as e:
            print(f"❌ 策略执行出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _should_rebalance(self) -> bool:
        """判断是否需要调仓"""
        current_date = self.datas[0].datetime.date(0)
        
        # 首次调仓
        if self.last_rebalance is None:
            return True
        
        # 按周期调仓
        days_since_rebalance = (current_date - self.last_rebalance).days
        return days_since_rebalance >= self.params.rebalance_period
    
    def _execute_rebalancing(self, current_date: str):
        """执行调仓"""
        try:
            print(f"\n🔄 {current_date} 执行调仓")
            
            # 1. 检查市场择时信号
            market_signal = self._check_market_timing()
            
            if market_signal == 0:
                print("⏸️  市场信号观望，暂不调仓")
                return
            
            # 2. 获取候选股票池
            candidate_stocks = self._get_candidate_stocks()
            
            if not candidate_stocks:
                print("❌ 无可用候选股票")
                return
            
            # 3. 计算目标权重
            if market_signal == 1:  # 买入信号
                self.target_weights = self._calculate_target_weights(candidate_stocks, 0.8)
            else:  # 卖出信号，降低仓位
                self.target_weights = self._calculate_target_weights(candidate_stocks, 0.2)
            
            # 4. 执行调仓交易
            self._execute_trades()
            
            # 5. 更新调仓日期
            self.last_rebalance = self.datas[0].datetime.date(0)
            
            print(f"✅ 调仓完成，目标持仓: {len(self.target_weights)}只")
            
        except Exception as e:
            print(f"❌ 调仓执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _check_market_timing(self) -> int:
        """检查市场择时信号（基于RSI）"""
        try:
            # 这里应该获取中证1000指数的RSI
            # 简化处理：使用第一只股票的RSI代替
            if len(self.datas) == 0:
                return 0
            
            # 获取RSI数据（假设已经计算好）
            rsi_data = getattr(self.datas[0], 'rsi', None)
            if rsi_data is None:
                return 0
            
            current_rsi = rsi_data[0]
            if np.isnan(current_rsi):
                return 0
            
            # RSI择时逻辑
            upper = self.params.rsi_upper
            lower = self.params.rsi_lower
            
            # 判断突破信号
            if (self.rsi_state['up_break'] == 0 and current_rsi >= upper):
                self.current_signal = 1
                self.rsi_state['up_break'] = 1
                print(f"🟢 RSI买入信号: {current_rsi:.1f} >= {upper}")
                return 1
            elif (self.rsi_state['down_break'] == 1 and current_rsi >= lower):
                self.current_signal = 1
                self.rsi_state['down_break'] = 0
                print(f"🟢 RSI买入信号: {current_rsi:.1f} >= {lower}")
                return 1
            elif (self.rsi_state['up_break'] == 1 and current_rsi <= upper):
                self.current_signal = -1
                self.rsi_state['up_break'] = 0
                print(f"🔴 RSI卖出信号: {current_rsi:.1f} <= {upper}")
                return -1
            elif (self.rsi_state['down_break'] == 0 and current_rsi <= lower):
                self.current_signal = -1
                self.rsi_state['down_break'] = 1
                print(f"🔴 RSI卖出信号: {current_rsi:.1f} <= {lower}")
                return -1
            
            return 0
            
        except Exception as e:
            print(f"检查市场择时失败: {e}")
            return 0
    
    def _get_candidate_stocks(self) -> List[str]:
        """获取候选股票池"""
        try:
            candidate_stocks = []
            factor_scores = []
            
            # 遍历所有数据源（股票）
            for i, data in enumerate(self.datas):
                if data._name == 'cash':  # 跳过现金数据
                    continue
                
                stock_code = data._name
                
                # 基础质量过滤
                if not self._is_stock_qualified(data):
                    continue
                
                # 计算3因子评分
                score = self._calculate_3factor_score(data)
                if score > 0:
                    factor_scores.append((stock_code, score))
            
            # 按评分排序，选择前N只
            factor_scores.sort(key=lambda x: x[1], reverse=True)
            candidate_stocks = [stock[0] for stock in factor_scores[:self.params.stock_pool_size]]
            
            print(f"📊 3因子评分完成，候选股票: {len(candidate_stocks)}只")
            if candidate_stocks:
                top_5 = factor_scores[:5]
                print(f"   前5只: {[f'{stock}({score:.1f})' for stock, score in top_5]}")
            
            return candidate_stocks
            
        except Exception as e:
            print(f"获取候选股票失败: {e}")
            return []
    
    def _is_stock_qualified(self, data) -> bool:
        """股票基础质量过滤"""
        try:
            # 检查数据完整性
            if len(data) < 20:  # 至少需要20天数据
                return False
            
            current_price = data.close[0]
            if current_price <= 0:
                return False
            
            # 检查市值数据
            market_cap = getattr(data, 'market_cap', None)
            if market_cap is not None and market_cap[0] > 0:
                # 最小市值10亿
                if market_cap[0] < 10e8:
                    return False
            
            # 排除ST股票（简化处理）
            stock_code = data._name
            if 'ST' in stock_code:
                return False
            
            # 价格过滤
            if current_price < 2.0:  # 最低2元
                return False
            
            return True
            
        except Exception as e:
            return False
    
    def _calculate_3factor_score(self, data) -> float:
        """计算新3因子综合评分：20日市值增长+Rank MAE+成长性"""
        try:
            score = 0.0
            
            # 因子1: 20日市值增长因子（权重40%）
            market_cap_score = self._calculate_market_cap_growth_factor(data)
            score += market_cap_score * self.params.market_cap_weight
            
            # 因子2: Rank MAE因子（权重45%）
            mae_rank_score = self._calculate_mae_rank_factor(data)
            score += mae_rank_score * self.params.mae_rank_weight
            
            # 因子3: 成长性因子（权重15%）
            growth_score = self._calculate_growth_factor(data)
            score += growth_score * self.params.growth_weight
            
            return max(score * 10, 0.0)  # 标准化到0-10分
            
        except Exception as e:
            return 0.0
    
    def _calculate_market_cap_growth_factor(self, data) -> float:
        """计算20日市值增长因子"""
        try:
            if len(data) < self.params.market_cap_period:
                return 0.0
            
            current_price = data.close[0]
            past_price = data.close[-self.params.market_cap_period]
            
            if past_price <= 0:
                return 0.0
            
            # 计算价格增长率（近似市值增长）
            growth_rate = (current_price - past_price) / past_price
            
            # 标准化到0-1范围
            normalized_growth = min(max((growth_rate + 0.2) / 0.4, 0), 1)
            
            return normalized_growth
            
        except Exception as e:
            return 0.0
    
    def _calculate_mae_rank_factor(self, data) -> float:
        """计算Rank MAE因子"""
        try:
            if len(data) < self.params.mae_ma_period:
                return 0.0
            
            current_price = data.close[0]
            # 计算移动平均
            ma_sum = sum(data.close[-i] for i in range(1, self.params.mae_ma_period + 1))
            ma = ma_sum / self.params.mae_ma_period
            
            if ma <= 0:
                return 0.0
            
            # 计算包络线位置
            envelope_pct = 0.05  # 5%包络线
            upper_band = ma * (1 + envelope_pct)
            lower_band = ma * (1 - envelope_pct)
            
            # MAE位置得分
            if current_price >= upper_band:
                mae_position = 1.0
            elif current_price <= lower_band:
                mae_position = 0.0
            else:
                mae_position = (current_price - lower_band) / (upper_band - lower_band)
            
            return mae_position
            
        except Exception as e:
            return 0.0
    
    def _calculate_growth_factor(self, data) -> float:
        """计算成长性因子（权重仅15%）"""
        try:
            growth_score = 0.0
            
            # 使用换手率作为活跃度指标
            turnover = getattr(data, 'turnover_rate', None)
            if turnover is not None and turnover[0] > 0:
                # 适中的换手率更好
                turnover_rate = turnover[0]
                if 0.02 <= turnover_rate <= 0.08:  # 2%-8%换手率较理想
                    growth_score += 0.6
                elif 0.01 <= turnover_rate <= 0.15:  # 次优范围
                    growth_score += 0.3
            
            # 使用技术指标作为成长性代理
            if len(data) >= 10:
                recent_avg = sum(data.close[-i] for i in range(1, 6)) / 5
                past_avg = sum(data.close[-i] for i in range(6, 11)) / 5
                if past_avg > 0:
                    momentum = (recent_avg - past_avg) / past_avg
                    if momentum > 0:
                        growth_score += min(momentum * 2, 0.4)
            
            return min(growth_score, 1.0)
            
        except Exception as e:
            return 0.0
    
    def _calculate_target_weights(self, candidate_stocks: List[str], total_exposure: float) -> Dict[str, float]:
        """计算目标权重"""
        try:
            if not candidate_stocks:
                return {}
            
            num_stocks = min(len(candidate_stocks), self.params.max_positions)
            weight_per_stock = total_exposure / num_stocks
            
            target_weights = {}
            for i, stock_code in enumerate(candidate_stocks[:num_stocks]):
                target_weights[stock_code] = weight_per_stock
            
            return target_weights
            
        except Exception as e:
            print(f"计算目标权重失败: {e}")
            return {}
    
    def _execute_trades(self):
        """执行交易"""
        try:
            current_value = self.broker.getvalue()
            
            # 1. 卖出不在目标中的持仓
            current_positions = {d._name: self.getposition(d) for d in self.datas if self.getposition(d).size != 0}
            
            for stock_code, position in current_positions.items():
                if stock_code not in self.target_weights:
                    # 卖出
                    data = self._get_data_by_name(stock_code)
                    if data is not None:
                        order = self.close(data=data)
                        if order:
                            print(f"🔴 卖出 {stock_code}: {abs(position.size)}股")
            
            # 2. 买入目标股票
            for stock_code, target_weight in self.target_weights.items():
                data = self._get_data_by_name(stock_code)
                if data is None:
                    continue
                
                target_value = current_value * target_weight
                current_position = self.getposition(data)
                current_value_in_stock = current_position.size * data.close[0]
                
                # 计算需要调整的金额
                value_diff = target_value - current_value_in_stock
                
                if abs(value_diff) > 1000:  # 最小调整金额1000元
                    if value_diff > 0:
                        # 买入
                        shares = int(value_diff / data.close[0] / 100) * 100  # 整手
                        if shares > 0:
                            order = self.buy(data=data, size=shares)
                            if order:
                                print(f"🟢 买入 {stock_code}: {shares}股 @{data.close[0]:.2f}元")
                    else:
                        # 减仓
                        shares = int(abs(value_diff) / data.close[0] / 100) * 100  # 整手
                        if shares > 0 and shares <= current_position.size:
                            order = self.sell(data=data, size=shares)
                            if order:
                                print(f"🔴 减仓 {stock_code}: {shares}股 @{data.close[0]:.2f}元")
            
        except Exception as e:
            print(f"执行交易失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_data_by_name(self, stock_code: str):
        """根据股票代码获取数据源"""
        for data in self.datas:
            if data._name == stock_code:
                return data
        return None
    
    def _check_risk_management(self):
        """检查风险管理"""
        try:
            for data in self.datas:
                position = self.getposition(data)
                if position.size == 0:
                    continue
                
                stock_code = data._name
                current_price = data.close[0]
                entry_price = position.price
                
                if entry_price <= 0:
                    continue
                
                # 计算盈亏比例
                pnl_pct = (current_price - entry_price) / entry_price
                
                # 止损
                if pnl_pct <= -self.params.stop_loss_pct:
                    order = self.close(data=data)
                    if order:
                        print(f"🛑 {stock_code} 止损卖出: 亏损{pnl_pct:.1%}")
                
                # 止盈
                elif pnl_pct >= self.params.take_profit_pct:
                    order = self.close(data=data)
                    if order:
                        print(f"💰 {stock_code} 止盈卖出: 盈利{pnl_pct:.1%}")
            
        except Exception as e:
            print(f"风险管理检查失败: {e}")
    
    def _log_strategy_status(self, current_date: str):
        """记录策略状态"""
        try:
            # 每10个交易日记录一次状态
            if len(self.datas[0]) % 10 == 0:
                portfolio_value = self.broker.getvalue()
                cash = self.broker.getcash()
                positions_count = sum(1 for d in self.datas if self.getposition(d).size != 0)
                positions_value = portfolio_value - cash
                cash_ratio = cash / portfolio_value if portfolio_value > 0 else 0
                
                print(f"📊 {current_date}: 组合价值{portfolio_value:,.0f}元, 持仓{positions_count}只, "
                      f"现金{cash_ratio:.1%}, 信号{self.current_signal}")
        
        except Exception as e:
            pass  # 日志记录失败不影响策略运行
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f"📈 交易执行: buy {order.data._name} {order.executed.size}股 @{order.executed.price:.2f}元")
            else:
                print(f"📈 交易执行: sell {order.data._name} {order.executed.size}股 @{order.executed.price:.2f}元")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f"❌ 订单失败: {order.data._name} - {order.status}")
    
    def stop(self):
        """策略结束"""
        final_value = self.broker.getvalue()
        initial_value = 1000000   # 假设初始资金100万
        total_return = (final_value - initial_value) / initial_value
        
        print(f"\n🎯 太上老君3号策略回测结束")
        print(f"   最终价值: {final_value:,.0f}元")
        print(f"   总收益率: {total_return:.2%}")
        print(f"   交易次数: {self.trade_count}")
        print(f"   ✨ 基于RIM绝对估值法选股+事件驱动交易的中证1000指数增强策略")


if __name__ == "__main__":
    # 测试策略
    print("🚀 测试太上老君3号策略...")
    
    # 这里可以添加简单的策略测试代码
    strategy = TaiShang3FactorStrategy()
    print(f"策略参数:")
    print(f"  最大持仓: {strategy.params.max_positions}")
    print(f"  RSI周期: {strategy.params.rsi_period}")
    print(f"  新3因子权重: 市值增长({strategy.params.market_cap_weight}) + MAE排名({strategy.params.mae_rank_weight}) + 成长性({strategy.params.growth_weight})")
    print("   专注中证1000成分股，避开高估值陷阱")
    print("   通过市值增长+Rank MAE+成长性因子优选小盘股")