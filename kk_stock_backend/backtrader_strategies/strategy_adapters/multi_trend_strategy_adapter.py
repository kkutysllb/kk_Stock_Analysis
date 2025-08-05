#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多趋势共振策略回测适配器
将现有的多趋势共振策略适配到新的回测引擎
"""

import sys
import os
import math
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.backtest_engine import StrategyInterface
from config import Config


class MultiTrendResonanceStrategyAdapter(StrategyInterface):
    """
    多趋势共振策略适配器
    将原有策略逻辑适配到新的回测引擎接口
    """
    
    def __init__(self):
        """初始化策略适配器"""
        self.name = "太上老君1号 - 价值动量策略"
        self.version = "3.0.0"
        
        # 策略参数 - 选股交易分离架构
        self.params = {
            # 选股阶段参数
            'selection_pool_size': 5,        # 选择前5只股票进入交易池
            'rebalance_selection_freq': 5,   # 每5个交易日重新选股
            'pe_weight': 0.5,                # PE_TTM权重50%
            'momentum_weight': 0.5,          # 20日收益率权重50%
            'min_pe_ttm': 5.0,               # 最小PE_TTM（过滤异常值）
            'max_pe_ttm': 100.0,             # 最大PE_TTM（过滤异常值）
            
            # 波动率调整权重参数
            'volatility_adjustment': True,   # 启用波动率调整权重
            'base_volatility': 0.5,          # 基础波动率参数
            'min_weight': 0.05,              # 最小权重5%
            'max_weight': 0.30,              # 最大权重30%
            
            # 交易阶段参数
            'max_positions': 5,              # 最多持仓5只（等于选股池大小）
            'max_single_weight': 0.20,       # 单股最大仓位20%（5只平均分配）
            'rebalance_freq': 1,             # 每日检查交易信号
            
            # 技术指标参数 - 降低门槛增加信号
            'boll_period': 20,
            'boll_std': 2.0,
            'wr_period': 14,
            'wr_overbought': 20,    # WR<20极度超买
            'wr_oversold': 90,      # WR>90极度超卖
            'volume_ma_period': 15,
            'volume_surge_threshold': 1.2,   # 降低成交量门槛
            
            # 技术信号参数 - 简化BOLL+WR信号
            'enable_technical_signals': True, # 启用技术信号
            'require_boll_signal': True,      # 需要布林带信号
            'require_wr_signal': True,        # 需要威廉指标信号
            
            # 风险控制参数 - 第一阶段优化
            'stop_loss_pct': 0.03,      # 收紧止损3%，快速止损
            'take_profit_pct': 0.15,    # 降低止盈9%，提高盈亏比（3:1）
            'profit_protect_pct': 0.05, # 降低盈利保护门槛
            'pullback_threshold': 0.04,
            'max_portfolio_drawdown': 0.15, # 新增：组合最大回撤15%
            'min_holding_days': 5,       # 新增：最小持仓5天，减少频繁交易
            
            # 选股过滤参数 - 放宽条件增加候选股票
            'min_volume': 2000000,      # 降低到200万成交额
            'min_turnover_rate': 0.005, # 降低到0.5%换手率
        }
        
        # 策略状态
        self.positions_info = {}  # 持仓信息
        self.buy_signals_count = 0
        self.sell_signals_count = 0
        # 移除共振得分系统，使用简单的BOLL+WR信号
        
        # 选股池状态
        self.selected_stocks = []     # 当前选股池（前5只股票）
        self.stock_weights = {}       # 股票目标权重字典
        self.last_selection_date = None  # 上次选股日期
        self.selection_counter = 0    # 选股计数器
        
        # 选股持仓记录功能 - 新增
        self.stock_selection_history = []  # 选股历史
        self.position_change_history = []  # 持仓变动历史
        self.daily_portfolio_snapshot = {}  # 每日组合快照
        
        # 统计信息
        self.signal_history = []
        self.trade_history = []
    
    def initialize(self, context: Dict[str, Any]):
        """策略初始化"""
        self.context = context
        
        print(f"🚀 {self.name} v{self.version} 初始化完成")
        print(f"   初始资金: {context['initial_cash']:,.0f}元")
        print(f"   回测期间: {context['start_date']} 到 {context['end_date']}")
        print(f"   最大持仓: {self.params['max_positions']}只")
        print(f"   单股仓位: {self.params['max_single_weight']:.0%}")
        print(f"   技术信号: BOLL+WR组合信号")
    
    def _update_stock_selection(self, current_date: str, market_data: Dict[str, Dict]) -> List[str]:
        """
        更新选股池：基于PE_TTM和20日收益率排序选择前5只股票
        
        Args:
            current_date: 当前日期
            market_data: 市场数据
            
        Returns:
            选中的股票代码列表
        """
        try:
            # 检查是否需要更新选股池
            if (self.last_selection_date is None or 
                self.selection_counter % self.params['rebalance_selection_freq'] == 0):
                
                stock_scores = []
                valid_stocks = 0
                
                for stock_code, data in market_data.items():
                    try:
                        # 获取PE_TTM并严格过滤nan值
                        pe_ttm = data.get('pe_ttm', None)
                        if pe_ttm is None or pe_ttm <= 0:
                            continue
                        
                        # 检查是否为nan值
                        if math.isnan(pe_ttm):
                            continue
                            
                        # 过滤PE_TTM异常值
                        if pe_ttm < self.params['min_pe_ttm'] or pe_ttm > self.params['max_pe_ttm']:
                            continue
                        
                        # 计算20日收益率（正确方法）
                        close_price = data.get('close', 0)
                        
                        # 尝试获取20日前价格，如果没有则通过MA20估算
                        close_20d_ago = data.get('close_20d_ago', None)
                        if close_20d_ago is None:
                            # 使用MA20来估算20日前的平均价格水平
                            ma20 = data.get('ma20', 0)
                            if ma20 <= 0:
                                continue
                            # 假设20日前价格约等于20日均线（近似方法）
                            close_20d_ago = ma20
                        
                        if close_20d_ago <= 0 or close_price <= 0:
                            continue
                            
                        # 正确的20日收益率计算
                        momentum_20d = (close_price - close_20d_ago) / close_20d_ago
                        
                        # 检查momentum_20d是否为nan
                        if math.isnan(momentum_20d):
                            continue
                        
                        # 计算5日波动率（使用ATR作为波动率指标）
                        atr = data.get('atr', None)
                        if atr is None or atr <= 0 or math.isnan(atr):
                            # 如果没有ATR，使用简化的波动率计算
                            high = data.get('high', close_price)
                            low = data.get('low', close_price)
                            volatility_5d = (high - low) / close_price if close_price > 0 else 0.02
                        else:
                            # 使用ATR作为波动率指标，标准化到比例
                            volatility_5d = atr / close_price if close_price > 0 else 0.02
                        
                        # 检查volatility_5d是否为nan或异常值
                        if math.isnan(volatility_5d) or volatility_5d <= 0:
                            volatility_5d = 0.02  # 设置默认值2%
                        
                        # 基本流动性过滤
                        volume = data.get('volume', 0)
                        if volume < self.params['min_volume']:
                            continue
                        
                        stock_scores.append({
                            'stock_code': stock_code,
                            'pe_ttm': pe_ttm,
                            'momentum_20d': momentum_20d,
                            'volatility_5d': volatility_5d,
                            'volume': volume
                        })
                        valid_stocks += 1
                        
                    except Exception as e:
                        continue
                
                if valid_stocks < 10:  # 如果有效股票太少，使用旧的选股池
                    print(f"⚠️ {current_date}: 有效股票仅{valid_stocks}只，保持原选股池")
                    return self.selected_stocks
                
                # 标准化评分 - 增强nan处理
                if stock_scores:
                    
                    # 计算PE_TTM和momentum的标准化分数
                    pe_ttm_values = [s['pe_ttm'] for s in stock_scores]
                    momentum_values = [s['momentum_20d'] for s in stock_scores]
                    
                    # 过滤掉可能的nan值
                    pe_ttm_values = [x for x in pe_ttm_values if not math.isnan(x)]
                    momentum_values = [x for x in momentum_values if not math.isnan(x)]
                    
                    if len(pe_ttm_values) == 0 or len(momentum_values) == 0:
                        print(f"⚠️ {current_date}: 所有PE或动量值都是nan，跳过标准化")
                        return self.selected_stocks
                    
                    pe_mean = sum(pe_ttm_values) / len(pe_ttm_values)
                    pe_std = (sum((x - pe_mean)**2 for x in pe_ttm_values) / len(pe_ttm_values))**0.5
                    
                    momentum_mean = sum(momentum_values) / len(momentum_values)
                    momentum_std = (sum((x - momentum_mean)**2 for x in momentum_values) / len(momentum_values))**0.5
                    
                    # 避免除零错误，设置最小标准差
                    if pe_std == 0 or math.isnan(pe_std):
                        pe_std = 0.01  # 设置最小标准差
                    if momentum_std == 0 or math.isnan(momentum_std):
                        momentum_std = 0.01  # 设置最小标准差
                    
                    # 计算综合得分
                    for stock_info in stock_scores:
                        # 再次确认数据有效性
                        if math.isnan(stock_info['pe_ttm']) or math.isnan(stock_info['momentum_20d']):
                            stock_info['composite_score'] = -999  # 给无效数据一个很低的分数
                            continue
                            
                        # PE_TTM: 越低越好，所以取负值
                        pe_score = -(stock_info['pe_ttm'] - pe_mean) / pe_std
                        # 动量: 越高越好
                        momentum_score = (stock_info['momentum_20d'] - momentum_mean) / momentum_std
                        
                        # 综合得分
                        composite_score = (
                            self.params['pe_weight'] * pe_score + 
                            self.params['momentum_weight'] * momentum_score
                        )
                        
                        # 最终检查，确保结果不是nan
                        if math.isnan(composite_score):
                            stock_info['composite_score'] = -999
                        else:
                            stock_info['composite_score'] = composite_score
                    
                    # 按综合得分排序，选择前N只
                    stock_scores.sort(key=lambda x: x['composite_score'], reverse=True)
                    top_stocks = stock_scores[:self.params['selection_pool_size']]
                    
                    # 计算波动率调整权重
                    if self.params['volatility_adjustment']:
                        N = len(top_stocks)
                        total_weight = 0
                        for stock_info in top_stocks:
                            # 权重 = 1.0/(N*(0.5+5日波动率))
                            volatility = stock_info['volatility_5d']
                            weight = 1.0 / (N * (self.params['base_volatility'] + volatility))
                            stock_info['target_weight'] = weight
                            total_weight += weight
                        
                        # 标准化权重，确保总和为1
                        for stock_info in top_stocks:
                            stock_info['target_weight'] = stock_info['target_weight'] / total_weight
                            # 限制权重范围
                            stock_info['target_weight'] = max(
                                self.params['min_weight'], 
                                min(self.params['max_weight'], stock_info['target_weight'])
                            )
                    else:
                        # 等权重分配
                        equal_weight = 1.0 / len(top_stocks)
                        for stock_info in top_stocks:
                            stock_info['target_weight'] = equal_weight
                    
                    selected_stocks = [s['stock_code'] for s in top_stocks]
                    
                    # 记录选股历史（增加权重信息）
                    selection_record = {
                        'date': current_date,
                        'selected_stocks': selected_stocks.copy(),
                        'top_scores': [
                            {
                                'stock_code': s['stock_code'], 
                                'pe_ttm': round(s['pe_ttm'], 2),
                                'momentum_20d': round(s['momentum_20d'], 4),
                                'volatility_5d': round(s['volatility_5d'], 4),
                                'composite_score': round(s['composite_score'], 4),
                                'target_weight': round(s['target_weight'], 4)
                            } 
                            for s in top_stocks
                        ]
                    }
                    self.stock_selection_history.append(selection_record)
                    
                    # 更新状态
                    self.selected_stocks = selected_stocks
                    self.last_selection_date = current_date
                    
                    # 保存股票权重信息
                    self.stock_weights = {
                        stock_info['stock_code']: stock_info['target_weight']
                        for stock_info in top_stocks
                    }
                    
                    print(f"📊 {current_date}: 更新选股池，选中{len(selected_stocks)}只股票")
                    for i, stock_info in enumerate(top_stocks):
                        print(f"   {i+1}. {stock_info['stock_code']}: PE={stock_info['pe_ttm']:.1f}, 20日收益={stock_info['momentum_20d']:.1%}, 波动率={stock_info['volatility_5d']:.1%}, 权重={stock_info['target_weight']:.1%}, 得分={stock_info['composite_score']:.2f}")
                
                self.selection_counter += 1
                
            return self.selected_stocks
            
        except Exception as e:
            print(f"❌ 选股更新失败: {e}")
            return self.selected_stocks if self.selected_stocks else []
    
    def generate_signals(self, 
                        current_date: str, 
                        market_data: Dict[str, Dict],
                        portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成交易信号 - 新架构：先选股，再交易
        
        Args:
            current_date: 当前日期
            market_data: 市场数据 {stock_code: daily_data}
            portfolio_info: 组合信息
            
        Returns:
            交易信号列表
        """
        signals = []
        
        try:
            # 0. 更新选股池（基于PE_TTM + 20日收益率）
            selected_stocks = self._update_stock_selection(current_date, market_data)
            
            # 过滤市场数据，只保留选股池中的股票
            filtered_market_data = {
                stock_code: data for stock_code, data in market_data.items() 
                if stock_code in selected_stocks
            }
            
            if not filtered_market_data:
                print(f"⚠️ {current_date}: 选股池为空，无法生成交易信号")
                return signals
            
            # 1. 检查卖出信号（包括不在选股池中的持仓）
            sell_signals = self._check_sell_signals(current_date, market_data, portfolio_info)
            signals.extend(sell_signals)
            
            # 2. 检查买入信号（仅在选股池中）
            current_positions = portfolio_info.get('total_positions', 0)
            if current_positions < self.params['max_positions']:
                buy_signals = self._check_buy_signals(current_date, filtered_market_data, portfolio_info)
                signals.extend(buy_signals)
            
            # 3. 记录信号历史
            if signals:
                self.signal_history.append({
                    'date': current_date,
                    'signals_count': len(signals),
                    'buy_count': len([s for s in signals if s['action'] == 'buy']),
                    'sell_count': len([s for s in signals if s['action'] == 'sell'])
                })
            
            # 4. 记录每日组合快照 - 新增功能
            if current_date.endswith('1'):  # 每10天记录一次以节省内存
                self._record_daily_snapshot(current_date, portfolio_info)
            
            # 5. 定期输出进度
            if current_date.endswith(('01', '11', '21')):  # 每月几次输出
                portfolio_value = portfolio_info.get('total_value', 0)
                cash_ratio = portfolio_info.get('cash_ratio', 0)
                print(f"📊 {current_date}: 组合价值{portfolio_value:,.0f}元, "
                      f"持仓{current_positions}只, 现金{cash_ratio:.1%}, "
                      f"信号{len(signals)}个")
            
        except Exception as e:
            print(f"❌ 生成信号失败 {current_date}: {e}")
        
        return signals
    
    def _check_sell_signals(self, 
                           current_date: str, 
                           market_data: Dict[str, Dict],
                           portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查卖出信号"""
        sell_signals = []
        
        # 获取当前持仓信息（从组合管理器获取）
        # 这里简化处理，实际应该从portfolio_info获取详细持仓
        for stock_code in list(self.positions_info.keys()):
            if stock_code not in market_data:
                continue
            
            try:
                should_sell, reason = self._check_sell_signal(
                    stock_code, market_data[stock_code], current_date
                )
                
                if should_sell:
                    sell_signals.append({
                        'action': 'sell',
                        'stock_code': stock_code,
                        'price': market_data[stock_code]['close'],
                        'reason': reason
                    })
                    
                    # 记录持仓变动 - 新增功能
                    position_info = self.positions_info.get(stock_code, {})
                    entry_score = position_info.get('resonance_score', 0)
                    self._record_position_change(current_date, 'sell', stock_code, 
                                               market_data[stock_code]['close'], entry_score, reason)
                    
                    # 移除持仓记录 - 标记为已处理，避免重复
                    if stock_code in self.positions_info:
                        del self.positions_info[stock_code]
                        self.sell_signals_count += 1
                    
            except Exception as e:
                print(f"检查 {stock_code} 卖出信号失败: {e}")
        
        return sell_signals
    
    def _check_buy_signals(self, 
                          current_date: str, 
                          market_data: Dict[str, Dict],
                          portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查买入信号 - 简化版：直接在选股池中检查BOLL+WR信号"""
        buy_signals = []
        
        # 在已选择的股票池中检查技术信号
        max_new_positions = self.params['max_positions'] - len(self.positions_info)
        
        for stock_code, stock_data in market_data.items():
            if stock_code not in self.positions_info and len(buy_signals) < max_new_positions:
                try:
                    # 检查BOLL+WR技术信号
                    boll_signal = self._check_boll_signal(stock_data)
                    wr_signal = self._check_wr_signal(stock_data)
                    volume_ok = self._check_volume_surge(stock_data)
                    
                    # 简化的买入条件：BOLL信号 + WR信号 + 成交量确认
                    should_buy = False
                    if self.params['enable_technical_signals']:
                        if self.params['require_boll_signal'] and self.params['require_wr_signal']:
                            # 需要同时满足BOLL和WR信号
                            should_buy = boll_signal and wr_signal and volume_ok
                        elif self.params['require_boll_signal']:
                            # 只需要BOLL信号
                            should_buy = boll_signal and volume_ok
                        elif self.params['require_wr_signal']:
                            # 只需要WR信号
                            should_buy = wr_signal and volume_ok
                        else:
                            # 任一信号即可
                            should_buy = (boll_signal or wr_signal) and volume_ok
                    
                    if should_buy:
                        # 使用波动率调整权重
                        target_weight = self.stock_weights.get(stock_code, self.params['max_single_weight'])
                        
                        buy_signals.append({
                            'action': 'buy',
                            'stock_code': stock_code,
                            'price': stock_data['close'],
                            'weight': target_weight,
                            'boll_signal': boll_signal,
                            'wr_signal': wr_signal,
                            'volume_signal': volume_ok
                        })
                        
                        # 记录持仓信息
                        self.positions_info[stock_code] = {
                            'entry_price': stock_data['close'],
                            'entry_date': current_date,
                            'boll_signal': boll_signal,
                            'wr_signal': wr_signal
                        }
                        
                        # 记录持仓变动
                        self._record_position_change(current_date, 'buy', stock_code, 
                                                   stock_data['close'], 
                                                   f"BOLL:{boll_signal}, WR:{wr_signal}")
                        
                        self.buy_signals_count += 1
                        
                except Exception as e:
                    print(f"检查 {stock_code} 买入信号失败: {e}")
                    continue
        
        return buy_signals
    
    # 移除候选股票池方法，直接在选股池中工作
    
    def _is_stock_qualified(self, stock_code: str, stock_data: Dict) -> bool:
        """基础股票过滤"""
        try:
            # 基础数据检查
            current_price = stock_data.get('close', 0)
            volume = stock_data.get('volume', 0)
            amount = stock_data.get('amount', 0)
            turnover_rate = stock_data.get('turnover_rate', 0)
            
            # 数据完整性检查
            if not all([current_price, volume, amount, turnover_rate]):
                return False
            
            # 价格和成交量过滤
            if (current_price <= 0 or 
                amount < self.params['min_volume'] or 
                turnover_rate < self.params['min_turnover_rate']):
                return False
            
            # 排除ST股票
            if 'ST' in stock_code:
                return False
            
            return True
            
        except:
            return False
    
    # 移除旧的单个买入信号检查方法，已整合到_check_buy_signals中
    
    def _check_sell_signal(self, stock_code: str, stock_data: Dict, current_date: str) -> tuple:
        """检查卖出信号"""
        try:
            if stock_code not in self.positions_info:
                return False, ""
            
            position_info = self.positions_info[stock_code]
            current_price = stock_data['close']
            entry_price = position_info['entry_price']
            
            pnl_ratio = (current_price - entry_price) / entry_price
            
            # 1. 止损优先级最高（5%） - 无视最小持仓天数
            if pnl_ratio <= -self.params['stop_loss_pct']:
                return True, f"止损卖出: {pnl_ratio:.2%}"
            
            # 2. 止盈检查（25%）
            if pnl_ratio >= self.params['take_profit_pct']:
                return True, f"止盈卖出: {pnl_ratio:.2%}"
            
            # 3. 技术卖出信号：WR<20 + 触碰布林带上轨
            if self._check_sell_condition_advanced(stock_data):
                return True, f"技术卖出: WR<20+上轨触碰 当前盈亏{pnl_ratio:.2%}"
            
            # 4. 共振信号转弱检查
            current_score = self._calculate_resonance_score(stock_code, stock_data)
            if current_score < 2:  # 调整为更严格的2分
                return True, f"共振信号转弱: 得分{current_score:.1f}"
            
            # 5. 盈利保护
            if pnl_ratio > self.params['profit_protect_pct']:
                # 如果有一定盈利且技术指标转弱
                if not self._check_boll_signal(stock_data):
                    return True, f"盈利保护卖出: 当前盈利{pnl_ratio:.2%}"
            
            return False, ""
            
        except Exception as e:
            return False, f"检查失败: {e}"
    
    # 移除复杂的共振得分系统，简化为直接的BOLL+WR信号检查
    
    def _check_boll_signal(self, stock_data: Dict) -> bool:
        """检查布林带买入信号 - 触碰下轨"""
        try:
            current_price = stock_data.get('close', 0)
            boll_upper = stock_data.get('boll_upper', 0)
            boll_lower = stock_data.get('boll_lower', 0)
            boll_mid = stock_data.get('boll_mid', 0)
            
            if not all([current_price, boll_upper, boll_lower, boll_mid]):
                return False
            
            # 计算价格在布林带中的位置
            boll_width = boll_upper - boll_lower
            if boll_width <= 0:
                return False
                
            price_position = (current_price - boll_lower) / boll_width
            
            # 买入信号：价格触碰或接近布林带下轨（底部反弹）
            if price_position <= 0.1:  # 价格在下轨附近10%区域，触碰下轨
                return True
                
            return False
        except:
            return False
    
    def _check_wr_signal(self, stock_data: Dict) -> bool:
        """检查威廉指标买入信号 - WR>90极度超卖"""
        try:
            wr = stock_data.get('wr', 0) or stock_data.get('wr1', 0) or stock_data.get('wr2', 0)
            
            if not wr:
                return False
            
            # 威廉指标买入信号：WR>90极度超卖，强烈反弹信号
            if wr >= 90:  
                return True
                
            return False
        except:
            return False
    
    def _check_volume_surge(self, stock_data: Dict) -> bool:
        """检查成交量放大"""
        try:
            volume_ratio = stock_data.get('volume_ratio', 0)
            return volume_ratio >= self.params['volume_surge_threshold']
        except:
            return False
    
    def _check_overbought_condition(self, stock_data: Dict) -> bool:
        """检查是否超买 - WR<20极度超买 + 触碰上轨"""
        try:
            # 威廉指标超买检查 WR<20
            wr = stock_data.get('wr', 0) or stock_data.get('wr1', 0) or stock_data.get('wr2', 0)
            
            # WR超买（威廉指标<20为极度超买）
            if wr and wr <= 20:
                return True
            
            # RSI超买作为辅助确认
            rsi = stock_data.get('rsi12', 0)
            if rsi and rsi > 80:  # 提高RSI阈值，更严格
                return True
            
            return False
        except:
            return False
    
    def _check_sell_condition_advanced(self, stock_data: Dict) -> bool:
        """检查高级卖出条件 - WR<20 + 触碰布林带上轨"""
        try:
            # 1. WR极度超买
            wr = stock_data.get('wr', 0) or stock_data.get('wr1', 0) or stock_data.get('wr2', 0)
            if not wr or wr > 20:
                return False
            
            # 2. 触碰布林带上轨
            current_price = stock_data.get('close', 0)
            boll_upper = stock_data.get('boll_upper', 0)
            boll_lower = stock_data.get('boll_lower', 0)
            
            if not all([current_price, boll_upper, boll_lower]):
                return False
            
            # 计算价格在布林带中的位置
            boll_width = boll_upper - boll_lower
            if boll_width <= 0:
                return False
                
            price_position = (current_price - boll_lower) / boll_width
            
            # 卖出条件：WR<20(极度超买) + 价格触碰上轨(>90%位置)
            if wr <= 20 and price_position >= 0.9:
                return True
                
            return False
        except:
            return False
    
    def _record_stock_selection(self, date: str, stock_scores: List, market_data: Dict):
        """记录选股历史 - 新增功能"""
        try:
            # 为每只候选股票创建单独的记录，以匹配CSV保存格式
            if not stock_scores:
                # 如果没有候选股票，记录一条空记录
                self.stock_selection_history.append({
                    'date': date,
                    'stock_code': '',
                    'resonance_score': 0,
                    'technical_score': 0,
                    'rank': 0,
                    'selected': False,
                    'reason': '无符合条件的候选股票'
                })
                return
            
            # 为每只候选股票创建记录
            for rank, (stock_code, resonance_score) in enumerate(stock_scores[:20], 1):  # 记录前20只
                # 计算技术评分作为参考
                stock_data = market_data.get(stock_code, {})
                tech_score = self._calculate_boll_score(stock_data) + self._calculate_wr_score(stock_data)
                
                # 判断是否被选中（前max_positions只会被选中）
                is_selected = rank <= (self.params['max_positions'] - len(self.positions_info)) and rank <= len(stock_scores)
                
                self.stock_selection_history.append({
                    'date': date,
                    'stock_code': stock_code,
                    'resonance_score': resonance_score,
                    'technical_score': tech_score,
                    'rank': rank,
                    'selected': is_selected,
                    'reason': f'共振得分{resonance_score:.1f}/11分,技术得分{tech_score:.1f}/6分'
                })
            
            # 只保留最近200条记录（约10个交易日）
            if len(self.stock_selection_history) > 200:
                self.stock_selection_history = self.stock_selection_history[-200:]
                
        except Exception as e:
            print(f"记录选股历史失败: {e}")
    
    def _record_position_change(self, date: str, action: str, stock_code: str, 
                               price: float, score: float, reason: str = ""):
        """记录持仓变动 - 新增功能"""
        try:
            change_record = {
                'date': date,
                'action': action,  # 'buy' or 'sell'
                'stock_code': stock_code,
                'price': price,
                'resonance_score': score,
                'reason': reason,
                'position_count': len(self.positions_info),
                'timestamp': date
            }
            self.position_change_history.append(change_record)
            
            # 只保留最近100条记录
            if len(self.position_change_history) > 100:
                self.position_change_history = self.position_change_history[-100:]
                
        except Exception as e:
            print(f"记录持仓变动失败: {e}")
    
    def _record_daily_snapshot(self, date: str, portfolio_info: Dict):
        """记录每日组合快照 - 新增功能"""
        try:
            # 从portfolio_info中提取数据，适配不同的字段名
            total_value = portfolio_info.get('total_value', 0) or portfolio_info.get('portfolio_value', 0)
            cash = portfolio_info.get('cash', 0)
            cash_ratio = portfolio_info.get('cash_ratio', 0)
            daily_return = portfolio_info.get('daily_return', 0)
            
            # 计算持仓价值
            positions_value = total_value - cash if total_value > cash else 0
            position_count = len(self.positions_info)
            
            # 计算累计收益率
            cumulative_return = 0
            if hasattr(self, 'context'):
                initial_cash = self.context.get('initial_cash', 1000000)
                if initial_cash > 0 and total_value > 0:
                    cumulative_return = (total_value - initial_cash) / initial_cash
            
            # 使用与回测引擎兼容的字段名
            snapshot = {
                'total_value': total_value,
                'cash': cash,
                'positions_value': positions_value,
                'position_count': position_count,
                'cash_ratio': cash_ratio,
                'daily_return': daily_return,
                'cumulative_return': cumulative_return
            }
            
            self.daily_portfolio_snapshot[date] = snapshot
            
            # 只保留最近60天的快照
            if len(self.daily_portfolio_snapshot) > 60:
                dates = sorted(self.daily_portfolio_snapshot.keys())
                for old_date in dates[:-60]:
                    del self.daily_portfolio_snapshot[old_date]
                    
            # 调试输出（仅在关键日期）
            if date.endswith(('01', '11', '21')) and total_value > 0:
                print(f"📊 {date} 快照: 总值{total_value:,.0f}, 现金{cash:,.0f}, 持仓{position_count}只")
                    
        except Exception as e:
            print(f"记录每日快照失败: {e}")
    
    def get_selection_report(self) -> Dict[str, Any]:
        """获取选股报告 - 新增功能"""
        try:
            recent_selections = self.stock_selection_history[-5:] if self.stock_selection_history else []
            recent_changes = self.position_change_history[-10:] if self.position_change_history else []
            
            return {
                'recent_stock_selections': recent_selections,
                'recent_position_changes': recent_changes,
                'current_positions': self.positions_info,
                'selection_summary': {
                    'total_selections': len(self.stock_selection_history),
                    'total_position_changes': len(self.position_change_history),
                    'current_position_count': len(self.positions_info)
                }
            }
        except Exception as e:
            print(f"生成选股报告失败: {e}")
            return {}
    
    def on_trade_executed(self, trade_info: Dict[str, Any]):
        """交易执行后回调"""
        try:
            self.trade_history.append({
                'date': trade_info.get('trade_date'),
                'action': trade_info['order_type'],
                'stock_code': trade_info['stock_code'],
                'price': trade_info['price'],
                'quantity': trade_info['quantity']
            })
            
            # 可以在这里添加更多的交易后处理逻辑
            
        except Exception as e:
            print(f"交易回调处理失败: {e}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            'strategy_name': self.name,
            'strategy_version': self.version,
            'strategy_type': '价值动量策略',
            'max_positions': self.params['max_positions'],
            'max_single_weight': self.params['max_single_weight'],
            'enable_technical_signals': self.params['enable_technical_signals'],
            'require_boll_signal': self.params['require_boll_signal'],
            'require_wr_signal': self.params['require_wr_signal'],
            'current_positions': len(self.positions_info),
            'buy_signals_count': self.buy_signals_count,
            'sell_signals_count': self.sell_signals_count,
            'total_signals': len(self.signal_history),
            'total_trades': len(self.trade_history),
            'description': '基于BOLL+WR精确买卖点的A股量化策略：买入条件(WR>90极度超卖+触碰下轨)，卖出条件(WR<20极度超买+触碰上轨)，止损5%优先级最高，止盈25%，专为A股波动特性设计'
        }


if __name__ == "__main__":
    # 测试策略适配器
    print("🚀 测试多趋势共振策略适配器...")
    
    # 创建策略实例
    strategy = MultiTrendResonanceStrategyAdapter()
    
    # 模拟初始化
    context = {
        'initial_cash': 1000000.0,
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    }
    
    strategy.initialize(context)
    
    # 模拟市场数据
    market_data = {
        '000001.SZ': {
            'close': 10.5,
            'volume': 1000000,
            'amount': 10500000,
            'turnover_rate': 0.05,
            'macd_dif': 0.1,
            'macd_dea': 0.05,
            'macd_macd': 0.05,
            'kdj_k': 60,
            'kdj_d': 55,
            'kdj_j': 65,
            'ma5': 10.3,
            'ma20': 10.0,
            'ma60': 9.8,
            'volume_ratio': 1.5,
            'rsi12': 60,
            'boll_upper': 11.0,
            'boll_mid': 10.0,
            'boll_lower': 9.0
        }
    }
    
    portfolio_info = {
        'total_value': 1000000,
        'cash_ratio': 0.9,
        'total_positions': 0
    }
    
    # 生成信号
    signals = strategy.generate_signals('2024-01-15', market_data, portfolio_info)
    
    print(f"生成信号: {len(signals)}个")
    for signal in signals:
        print(f"  {signal}")
    
    # 获取策略信息
    info = strategy.get_strategy_info()
    print(f"\n策略信息: {info}")
    
    print("✅ 多趋势共振策略适配器测试完成")