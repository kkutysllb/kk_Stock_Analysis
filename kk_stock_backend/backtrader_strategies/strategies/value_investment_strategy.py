#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值投资策略
基于价值投资适配器选股，实现完整的买卖信号和调仓逻辑
"""

import sys
import os
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
import numpy as np

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(os.path.dirname(current_dir))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from backtrader_strategies.backtest.backtest_engine import StrategyInterface
from backtrader_strategies.strategy_adapters.value_investment_adapter import ValueInvestmentAdapter


class ValueInvestmentStrategy(StrategyInterface):
    """
    价值投资策略
    
    策略逻辑：
    1. 使用价值投资适配器选股
    2. 基于评分和市场数据生成买卖信号
    3. 实现定期调仓和风险控制
    """
    
    def __init__(self):
        """初始化策略"""
        self.strategy_name = "价值投资策略"
        self.strategy_type = "value_investment_adapter"
        self.strategy_version = "1.0.0"
        
        # 初始化适配器
        self.adapter = ValueInvestmentAdapter()
        
        # 策略参数
        self.params = {
            # 选股参数
            'market_cap': 'all',           # 市值范围
            'stock_pool': 'all',           # 股票池：全市场选股
            'candidate_limit': 100,        # 策略适配器选股数量 (增加)
            
            # 买入条件
            'min_score': 60,               # 最低评分阈值 (降低)
            'pe_max': 25,                  # PE上限
            'pb_max': 3,                   # PB上限
            'min_volume_ratio': 0.5,       # 最小成交量比率
            
            # 卖出条件
            'score_drop_threshold': 40,    # 评分下降阈值 (降低)
            'pe_sell_max': 35,            # 卖出PE上限
            'pb_sell_max': 4,             # 卖出PB上限
            
            # 仓位管理
            'max_positions': 5,            # 最大持仓数 (减少到5只)
            'max_single_position': 0.18,   # 单股最大仓位18% (5只股票平均分配)
            'cash_reserve_ratio': 0.05,    # 现金储备5%
            
            # 风险控制
            'stop_loss_pct': -0.15,        # 止损-15%
            'take_profit_pct': 0.30,       # 止盈30%
            'max_holding_days': 365,       # 最大持仓天数
            'min_holding_days': 30,        # 最小持仓天数
            
            # 调仓频率
            'rebalance_frequency': 'quarterly',  # 调仓频率：quarterly/monthly（价值投资应季度调仓）
            'last_rebalance_date': None,          # 上次调仓日期
            'min_rebalance_interval': 60,         # 最小调仓间隔（天）
        }
        
        # 持仓记录
        self.positions = {}
        self.entry_dates = {}
        self.entry_scores = {}
        self.candidate_stocks = []  # 当前候选股票池
        
        # 统计信息
        self.buy_signals_count = 0
        self.sell_signals_count = 0
        self.rebalance_count = 0
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
    def initialize(self, context: Dict[str, Any]):
        """策略初始化"""
        self.logger.info(f"🚀 {self.strategy_name} 初始化完成")
        self.logger.info(f"策略参数: {self.params}")
        
        # 从context获取回测引擎引用（用于动态数据加载）
        self.backtest_engine = context.get('backtest_engine')
        
    async def generate_signals(self, 
                             current_date: str, 
                             market_data: Dict[str, Dict],
                             portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成交易信号
        
        Args:
            current_date: 当前日期
            market_data: 市场数据（日线行情）
            portfolio_info: 组合信息
            
        Returns:
            交易信号列表
        """
        signals = []
        
        try:
            # 1. 检查是否需要调仓（传入市场数据用于环境评估）
            need_rebalance = self._check_rebalance_needed(current_date, market_data)
            
            # 2. 生成卖出信号（优先处理）
            sell_signals = await self._generate_sell_signals(
                current_date, market_data, portfolio_info
            )
            signals.extend(sell_signals)
            
            # 3. 如果需要调仓，重新评估所有持仓并进行调仓
            if need_rebalance:
                self.logger.info(f"🔄 开始调仓：重新评估持仓并选择最优股票")
                rebalance_signals = await self._generate_rebalance_signals(
                    current_date, market_data, portfolio_info
                )
                signals.extend(rebalance_signals)
                self.params['last_rebalance_date'] = current_date
                self.rebalance_count += 1
            
            # 4. 如果有空余仓位但不需要调仓，仅生成买入信号补充仓位
            elif self._has_available_positions(portfolio_info):
                buy_signals = await self._generate_buy_signals(
                    current_date, market_data, portfolio_info
                )
                signals.extend(buy_signals)
            
            # 4. 更新统计
            self.buy_signals_count += len([s for s in signals if s['action'] == 'buy'])
            self.sell_signals_count += len([s for s in signals if s['action'] == 'sell'])
            
            return signals
            
        except Exception as e:
            self.logger.error(f"生成交易信号失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _check_rebalance_needed(self, current_date: str, market_data: Dict[str, Dict] = None) -> bool:
        """
        检查是否需要调仓（智能调仓逻辑）
        
        Args:
            current_date: 当前日期
            market_data: 市场数据，用于计算市场波动率和估值水平
            
        Returns:
            是否需要调仓
        """
        if not self.params['last_rebalance_date']:
            return True
        
        try:
            last_date = datetime.strptime(self.params['last_rebalance_date'], '%Y-%m-%d')
            current_dt = datetime.strptime(current_date, '%Y-%m-%d')
            days_diff = (current_dt - last_date).days
            
            # 1. 检查最小调仓间隔
            if days_diff < self.params['min_rebalance_interval']:
                return False
            
            # 2. 基础时间触发
            base_interval = self._get_base_rebalance_interval()
            time_triggered = days_diff >= base_interval
            
            # 3. 如果时间未到，检查市场环境是否需要提前调仓
            if not time_triggered and market_data:
                market_condition = self._assess_market_condition(market_data, current_date)
                
                # 市场剧烈波动或估值环境显著变化时，提前调仓
                if market_condition['high_volatility'] or market_condition['valuation_shift']:
                    self.logger.info(f"🔄 市场环境变化触发调仓: 波动率={market_condition['volatility']:.3f}, "
                                   f"估值变化={market_condition['valuation_change']:.1%}")
                    return True
            
            return time_triggered
                
        except Exception as e:
            self.logger.error(f"调仓检查失败: {e}")
            return True
    
    def _get_base_rebalance_interval(self) -> int:
        """获取基础调仓间隔"""
        if self.params['rebalance_frequency'] == 'quarterly':
            return 90  # 季度调仓
        elif self.params['rebalance_frequency'] == 'monthly':
            return 30  # 月度调仓
        else:
            return 90  # 默认季度调仓（价值投资理念）
    
    def _assess_market_condition(self, market_data: Dict[str, Dict], current_date: str) -> Dict[str, Any]:
        """
        评估市场环境
        
        Args:
            market_data: 市场数据
            current_date: 当前日期
            
        Returns:
            市场环境评估结果
        """
        try:
            # 计算市场波动率（简化版，使用持仓股票的波动率）
            volatilities = []
            pe_ratios = []
            
            for stock_code, data in market_data.items():
                # 计算最近20日的波动率
                if 'close' in data and hasattr(data, 'index') and len(data) >= 20:
                    recent_prices = data['close'].tail(20) if hasattr(data['close'], 'tail') else data['close']
                    if len(recent_prices) >= 2:
                        returns = [recent_prices[i] / recent_prices[i-1] - 1 for i in range(1, len(recent_prices))]
                        volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
                        volatilities.append(volatility)
                
                # 收集PE数据
                if 'pe_ttm' in data:
                    pe = data.get('pe_ttm')
                    if pe and pe > 0 and pe < 100:  # 过滤异常值
                        pe_ratios.append(pe)
            
            # 计算市场指标
            avg_volatility = np.mean(volatilities) if volatilities else 0.2
            avg_pe = np.mean(pe_ratios) if pe_ratios else 15
            
            # 判断是否为高波动率环境
            high_volatility = avg_volatility > 0.4  # 年化波动率超过40%
            
            # 估值水平评估（简化版）
            # PE < 12: 低估值，PE > 25: 高估值
            valuation_level = 'normal'
            if avg_pe < 12:
                valuation_level = 'undervalued'
            elif avg_pe > 25:
                valuation_level = 'overvalued'
            
            # 估值变化评估（相对于历史平均）
            historical_pe = 18  # 假设历史平均PE为18
            valuation_change = (avg_pe - historical_pe) / historical_pe
            valuation_shift = abs(valuation_change) > 0.3  # 估值变化超过30%
            
            return {
                'volatility': avg_volatility,
                'high_volatility': high_volatility,
                'avg_pe': avg_pe,
                'valuation_level': valuation_level,
                'valuation_change': valuation_change,
                'valuation_shift': valuation_shift,
                'assessment_date': current_date
            }
            
        except Exception as e:
            self.logger.error(f"市场环境评估失败: {e}")
            return {
                'volatility': 0.2,
                'high_volatility': False,
                'avg_pe': 15,
                'valuation_level': 'normal',
                'valuation_change': 0,
                'valuation_shift': False,
                'assessment_date': current_date
            }
    
    def _has_available_positions(self, portfolio_info: Dict[str, Any]) -> bool:
        """检查是否有可用仓位"""
        current_positions = len(portfolio_info.get('positions', {}))
        return current_positions < self.params['max_positions']
    
    async def _generate_rebalance_signals(self,
                                         current_date: str,
                                         market_data: Dict[str, Dict],
                                         portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成调仓信号：重新评估持仓并优化组合
        
        Args:
            current_date: 当前日期
            market_data: 市场数据
            portfolio_info: 组合信息
            
        Returns:
            调仓信号列表（包含卖出和买入）
        """
        signals = []
        
        try:
            # 1. 使用适配器重新选股，获取最新的优质股票
            screening_result = await self.adapter.screen_stocks(
                trade_date=current_date,
                market_cap=self.params['market_cap'],
                stock_pool=self.params['stock_pool'],
                limit=self.params['candidate_limit']
            )
            
            new_candidates = screening_result.get('stocks', [])
            self.logger.info(f"📊 调仓时适配器重新选出 {len(new_candidates)} 只候选股票")
            
            # 2. 重新评估现有持仓的得分
            current_positions = portfolio_info.get('positions', {})
            holding_scores = {}
            
            for stock_code in current_positions.keys():
                # 查找该股票在新候选列表中的得分
                for candidate in new_candidates:
                    if candidate.get('stock_code') == stock_code:
                        holding_scores[stock_code] = candidate.get('score', 0)
                        break
                else:
                    # 如果现有持仓不在新候选列表中，给予较低得分
                    holding_scores[stock_code] = 30  # 低于最低要求得分
            
            # 3. 创建候选股票得分字典
            candidate_scores = {
                candidate.get('stock_code'): candidate.get('score', 0)
                for candidate in new_candidates
            }
            
            # 4. 调仓决策：保留高分股票，替换低分股票
            target_positions = self.params['max_positions']
            
            # 按得分排序所有可选股票（包括现有持仓和新候选）
            all_stocks = {}
            all_stocks.update(holding_scores)
            all_stocks.update(candidate_scores)
            
            # 选择得分最高的前N只股票作为目标持仓
            sorted_stocks = sorted(all_stocks.items(), key=lambda x: x[1], reverse=True)
            target_stocks = {stock_code: score for stock_code, score in sorted_stocks[:target_positions]}
            
            self.logger.info(f"🎯 目标持仓股票 {len(target_stocks)} 只，平均得分: {np.mean(list(target_stocks.values())):.1f}")
            
            # 5. 生成卖出信号：卖出不在目标持仓中的股票
            for stock_code in current_positions.keys():
                if stock_code not in target_stocks:
                    position = current_positions[stock_code]
                    reason = f"调仓淘汰：当前得分{holding_scores.get(stock_code, 0):.1f}，未入选目标持仓"
                    
                    signal = {
                        'action': 'sell',
                        'stock_code': stock_code,
                        'quantity': position['quantity'],
                        'price': market_data.get(stock_code, {}).get('close', 0),
                        'reason': reason,
                        'timestamp': current_date,
                        'strategy': self.strategy_type
                    }
                    signals.append(signal)
                    self.logger.info(f"🔴 调仓卖出: {stock_code} - {reason}")
            
            # 6. 生成买入信号：买入新的目标股票
            for stock_code, score in target_stocks.items():
                if stock_code not in current_positions and stock_code in market_data:
                    # 检查买入条件
                    stock_info = next((c for c in new_candidates if c.get('stock_code') == stock_code), {})
                    stock_data = market_data[stock_code]
                    
                    should_buy, buy_reason = self._should_buy(
                        stock_code, stock_data, stock_info, current_date
                    )
                    
                    if should_buy:
                        total_value = portfolio_info.get('total_value', 0)
                        cash = portfolio_info.get('cash', 0)
                        quantity = self._calculate_position_size(stock_data, total_value, cash)
                        
                        if quantity > 0:
                            signal = {
                                'action': 'buy',
                                'stock_code': stock_code,
                                'quantity': quantity,
                                'price': stock_data.get('close', 0),
                                'reason': f"调仓买入：得分{score:.1f}，{buy_reason}",
                                'timestamp': current_date,
                                'strategy': self.strategy_type
                            }
                            signals.append(signal)
                            self.logger.info(f"🟢 调仓买入: {stock_code} - 得分{score:.1f}")
            
            return signals
            
        except Exception as e:
            self.logger.error(f"生成调仓信号失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _generate_sell_signals(self, 
                                   current_date: str, 
                                   market_data: Dict[str, Dict],
                                   portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成卖出信号"""
        sell_signals = []
        current_positions = portfolio_info.get('positions', {})
        
        for stock_code, position in current_positions.items():
            if stock_code not in market_data:
                continue
                
            stock_data = market_data[stock_code]
            should_sell, reason = self._should_sell(
                stock_code, stock_data, position, current_date
            )
            
            if should_sell:
                signal = {
                    'action': 'sell',
                    'stock_code': stock_code,
                    'quantity': position.get('quantity', 0),
                    'price': stock_data.get('close', 0),
                    'reason': reason,
                    'timestamp': current_date,
                    'strategy': self.strategy_type
                }
                sell_signals.append(signal)
                self.logger.info(f"🔴 卖出信号: {stock_code} - {reason}")
        
        return sell_signals
    
    async def _generate_buy_signals(self, 
                                  current_date: str, 
                                  market_data: Dict[str, Dict],
                                  portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成买入信号"""
        buy_signals = []
        
        try:
            # 1. 使用适配器选股
            screening_result = await self.adapter.screen_stocks(
                trade_date=current_date,
                market_cap=self.params['market_cap'],
                stock_pool=self.params['stock_pool'],
                limit=self.params['candidate_limit']
            )
            
            self.candidate_stocks = screening_result.get('stocks', [])
            self.logger.info(f"📊 适配器选出 {len(self.candidate_stocks)} 只候选股票")
            
            # 2. 检查每只候选股票
            current_positions = portfolio_info.get('positions', {})
            total_value = portfolio_info.get('total_value', 0)
            cash = portfolio_info.get('cash', 0)
            
            for stock_info in self.candidate_stocks:
                stock_code = stock_info.get('stock_code')
                
                # 跳过已持仓的股票
                if stock_code in current_positions:
                    continue
                
                # 检查市场数据是否可用
                if stock_code not in market_data:
                    continue
                
                stock_data = market_data[stock_code]
                
                # 3. 判断买入条件
                should_buy, reason = self._should_buy(
                    stock_code, stock_data, stock_info, current_date
                )
                
                if should_buy:
                    # 4. 计算买入数量
                    quantity = self._calculate_position_size(
                        stock_data, total_value, cash
                    )
                    
                    if quantity > 0:
                        signal = {
                            'action': 'buy',
                            'stock_code': stock_code,
                            'quantity': quantity,
                            'price': stock_data.get('close', 0),
                            'reason': reason,
                            'timestamp': current_date,
                            'strategy': self.strategy_type,
                            'score': stock_info.get('final_score', 0)
                        }
                        buy_signals.append(signal)
                        self.logger.info(f"🟢 买入信号: {stock_code} - {reason}")
                        
                        # 检查仓位限制
                        if len(buy_signals) >= self._get_available_positions(portfolio_info):
                            break
            
            return buy_signals
            
        except Exception as e:
            self.logger.error(f"生成买入信号失败: {e}")
            return []
    
    def _should_sell(self, stock_code: str, stock_data: Dict, 
                    position: Dict, current_date: str) -> Tuple[bool, str]:
        """判断是否应该卖出"""
        try:
            current_price = stock_data.get('close', 0)
            entry_price = self.entry_dates.get(stock_code, {}).get('price', current_price)
            
            # 1. 止损止盈检查
            if entry_price > 0:
                return_pct = (current_price - entry_price) / entry_price
                
                if return_pct <= self.params['stop_loss_pct']:
                    return True, f"止损卖出({return_pct:.2%})"
                
                if return_pct >= self.params['take_profit_pct']:
                    return True, f"止盈卖出({return_pct:.2%})"
            
            # 2. 持仓时间检查
            entry_date = self.entry_dates.get(stock_code, {}).get('date')
            if entry_date:
                entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
                current_dt = datetime.strptime(current_date, '%Y-%m-%d')
                holding_days = (current_dt - entry_dt).days
                
                if holding_days >= self.params['max_holding_days']:
                    return True, f"持仓期满卖出({holding_days}天)"
            
            # 3. 估值过高检查（从stock_data获取基础指标）
            pe = stock_data.get('pe_ttm', 0)
            pb = stock_data.get('pb', 0)
            
            if pe > self.params['pe_sell_max'] and pe > 0:
                return True, f"PE过高卖出({pe:.1f})"
            
            if pb > self.params['pb_sell_max'] and pb > 0:
                return True, f"PB过高卖出({pb:.1f})"
            
            # 4. 技术面恶化检查
            close = stock_data.get('close', 0)
            ma20 = stock_data.get('ma20', 0)
            volume_ratio = stock_data.get('volume_ratio', 1)
            
            # 跌破重要支撑且缩量
            if ma20 > 0 and close < ma20 * 0.95 and volume_ratio < 0.5:
                return True, f"技术面恶化卖出(价格{close:.2f}<MA20*0.95={ma20*0.95:.2f})"
            
            return False, "继续持有"
            
        except Exception as e:
            self.logger.error(f"卖出判断失败 {stock_code}: {e}")
            return False, "判断异常"
    
    def _should_buy(self, stock_code: str, stock_data: Dict, 
                   stock_info: Dict, current_date: str) -> Tuple[bool, str]:
        """判断是否应该买入"""
        try:
            # 1. 检查适配器评分 (修复字段名问题)
            score = stock_info.get('final_score') or stock_info.get('score', 0)
            self.logger.info(f"🔍 买入检查 {stock_code}: 评分={score}, 最低要求={self.params['min_score']}")
            
            if score < self.params['min_score']:
                return False, f"评分过低({score})"
            
            # 2. 基础估值检查
            pe = stock_data.get('pe_ttm', 999)
            pb = stock_data.get('pb', 999)
            
            if pe > self.params['pe_max'] or pe <= 0:
                return False, f"PE不符合({pe})"
            
            if pb > self.params['pb_max'] or pb <= 0:
                return False, f"PB不符合({pb})"
            
            # 3. 流动性检查
            volume_ratio = stock_data.get('volume_ratio', 0)
            if volume_ratio < self.params['min_volume_ratio']:
                return False, f"成交量不足({volume_ratio:.2f})"
            
            # 4. 价格合理性检查
            close = stock_data.get('close', 0)
            if close < 2.0 or close > 300.0:
                return False, f"价格不合理({close})"
            
            # 5. 技术面确认
            ma5 = stock_data.get('ma5', 0)
            ma20 = stock_data.get('ma20', 0)
            
            # 价格在均线系统支撑之上
            if ma5 > 0 and ma20 > 0 and close < ma20 * 0.9:
                return False, f"技术面偏弱(价格{close}<MA20*0.9={ma20*0.9:.2f})"
            
            return True, f"价值投资买入(评分:{score}, PE:{pe:.1f}, PB:{pb:.1f})"
            
        except Exception as e:
            self.logger.error(f"买入判断失败 {stock_code}: {e}")
            return False, "判断异常"
    
    def _calculate_position_size(self, stock_data: Dict, 
                               total_value: float, cash: float) -> int:
        """计算买入数量"""
        try:
            current_price = stock_data.get('close', 0)
            if current_price <= 0:
                return 0
            
            # 1. 计算目标仓位金额
            target_position_value = total_value * self.params['max_single_position']
            
            # 2. 考虑现金储备
            available_cash = cash * (1 - self.params['cash_reserve_ratio'])
            
            # 3. 实际可用金额
            position_value = min(target_position_value, available_cash)
            
            # 4. 最小投资金额检查
            if position_value < 10000:  # 最少1万元
                return 0
            
            # 5. 计算股数（A股最小交易单位100股）
            shares = int(position_value / current_price / 100) * 100
            
            return shares
            
        except Exception as e:
            self.logger.error(f"仓位计算失败: {e}")
            return 0
    
    def _get_available_positions(self, portfolio_info: Dict[str, Any]) -> int:
        """获取可用仓位数"""
        current_positions_count = len(portfolio_info.get('positions', {}))
        return max(0, self.params['max_positions'] - current_positions_count)
    
    def on_trade_executed(self, trade_info: Dict[str, Any]):
        """交易执行回调"""
        stock_code = trade_info.get('stock_code')
        action = trade_info.get('action')
        price = trade_info.get('price', 0)
        timestamp = trade_info.get('timestamp')
        
        if action == 'buy':
            # 记录买入信息
            self.entry_dates[stock_code] = {
                'date': timestamp,
                'price': price
            }
            # 记录买入时的评分
            for stock in self.candidate_stocks:
                if stock.get('stock_code') == stock_code:
                    self.entry_scores[stock_code] = stock.get('final_score', 0)
                    break
            
            self.logger.info(f"✅ 买入执行: {stock_code} @ {price}")
            
        elif action == 'sell':
            # 清理卖出股票的记录
            self.entry_dates.pop(stock_code, None)
            self.entry_scores.pop(stock_code, None)
            self.logger.info(f"✅ 卖出执行: {stock_code} @ {price}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            'strategy_name': self.strategy_name,
            'strategy_type': self.strategy_type,
            'strategy_version': self.strategy_version,
            'max_positions': self.params['max_positions'],
            'max_single_weight': self.params['max_single_position'],
            'stop_loss_pct': self.params['stop_loss_pct'],
            'take_profit_pct': self.params['take_profit_pct'],
            'min_score': self.params['min_score'],
            'pe_max': self.params['pe_max'],
            'pb_max': self.params['pb_max'],
            'buy_signals_count': self.buy_signals_count,
            'sell_signals_count': self.sell_signals_count,
            'rebalance_count': self.rebalance_count,
            'description': '基于价值投资理念的股票选择策略，注重低估值、高质量、稳健增长的投资标的'
        }


if __name__ == "__main__":
    """测试策略基本功能"""
    import asyncio
    
    async def test_strategy():
        strategy = ValueInvestmentStrategy()
        
        # 初始化
        context = {'config': None}
        strategy.initialize(context)
        
        print("✅ 策略初始化成功")
        print(f"策略信息: {strategy.get_strategy_info()}")
        
        return True
    
    print("🚀 测试价值投资策略...")
    result = asyncio.run(test_strategy())
    if result:
        print("✅ 策略测试通过")
    else:
        print("❌ 策略测试失败")