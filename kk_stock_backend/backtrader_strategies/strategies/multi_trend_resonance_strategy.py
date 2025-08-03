#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多趋势共振策略 - 严格按照文档设计实现
基于日线数据计算多时间周期技术指标，实现真正的多趋势共振分析
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class MultiTrendResonanceStrategy():
    """
    多趋势共振策略
    
    严格按照文档设计实现：
    1. 多时间周期分析（日线、周线、月线）
    2. 共振得分模型（0-11分）
    3. 严格的买卖信号判断
    4. 明确的风险控制
    """
    
    params = (
        # 基础持仓参数 - 按文档设计
        ('max_positions', 8),                    # 最多8只股票
        ('max_single_weight', 0.12),             # 单股最大12%仓位
        ('rebalance_freq', 1),                   # 每日检查信号
        
        # 技术指标参数 - 按文档配置
        ('macd_fast', 12),                       # MACD快线周期
        ('macd_slow', 26),                       # MACD慢线周期
        ('macd_signal', 9),                      # MACD信号线周期
        ('kdj_period', 9),                       # KDJ指标周期
        ('kdj_overbought', 80),                  # KDJ超买线
        ('kdj_oversold', 20),                    # KDJ超卖线
        ('volume_ma_period', 15),                # 成交量均线周期
        ('volume_surge_threshold', 1.3),         # 成交量放大阈值
        
        # 共振信号参数 - 按文档设计
        ('min_resonance_score', 6),              # 最小共振得分
        ('strong_resonance_score', 9),           # 强共振得分
        
        # 风险控制参数 - 按文档设计
        ('stop_loss_pct', -0.06),                # 6%止损
        ('take_profit_pct', 0.12),               # 12%止盈
        ('profit_protect_pct', 0.08),            # 8%盈利保护线
        ('pullback_threshold', 0.04),            # 4%回撤卖出
        
        # 选股过滤参数
        ('min_volume', 5000000),                 # 最小成交额500万
        ('min_turnover_rate', 0.01),             # 最小换手率1%
    )
    
    def __init__(self):
        super(MultiTrendResonanceStrategy, self).__init__()
        
        # 持仓信息记录
        self.positions_info = {}  # {stock_code: {'entry_price': xxx, 'entry_date': xxx, 'resonance_score': xxx}}
        
        # 历史数据缓存
        self.stock_historical_data = {}  # 缓存股票的历史数据用于多时间周期分析
        
        # 交易统计属性
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.max_profit = 0.0
        self.max_loss = 0.0
        self.trade_records = []
        self.position_records = []
        
        # 性能跟踪
        self.portfolio_values = []
        self.daily_returns = []
        self.daily_values = []
        self.max_portfolio_value = self.p.initial_cash
        self.max_drawdown = 0.0
        
        print(f"🚀 多趋势共振策略初始化完成！数据源数量: {len(self.datas)}")
        print(f"🚀 股票指标访问器: {len(getattr(self, 'stock_indicators', {}))}")
        if hasattr(self, 'stock_indicators'):
            print(f"🚀 可访问的股票: {list(self.stock_indicators.keys())[:5]}")
        self.log("🚀 多趋势共振策略初始化完成！")
    
    def notify_trade(self, trade):
        """交易通知，用于统计"""
        if trade.isclosed:
            self.trade_count += 1
            profit = trade.pnl
            
            # 记录交易详情
            trade_record = {
                'date': self.datas[0].datetime.date(0).strftime('%Y-%m-%d'),
                'symbol': trade.data._name if hasattr(trade.data, '_name') else 'unknown',
                'pnl': profit,
                'pnlcomm': trade.pnlcomm,
                'size': trade.size,
                'price': trade.price,
                'commission': trade.commission
            }
            self.trade_records.append(trade_record)
            
            if profit > 0:
                self.winning_trades += 1
                self.total_profit += profit
                self.max_profit = max(self.max_profit, profit)
            else:
                self.losing_trades += 1
                self.total_loss += abs(profit)
                self.max_loss = max(self.max_loss, abs(profit))
                
            self.log(f'交易完成: 盈亏={profit:.2f}, 总交易={self.trade_count}, 胜率={self.winning_trades/max(self.trade_count,1):.2%}')
    
    def next(self):
        """每日数据更新"""
        # 记录每日组合价值
        current_value = self.broker.getvalue()
        self.daily_values.append(current_value)
        self.portfolio_values.append(current_value)
        
        # 调试输出
        if len(self.daily_values) <= 5:  # 只在前5天输出
            print(f"🔍 调试: next()被调用, 第{len(self.daily_values)}天, 资金={current_value:.0f}")
            self.log(f"🔍 调试: next()被调用, 第{len(self.daily_values)}天, 资金={current_value:.0f}")
        
        # 计算每日收益率
        if len(self.daily_values) > 1:
            daily_return = (current_value - self.daily_values[-2]) / self.daily_values[-2]
            self.daily_returns.append(daily_return)
        
        # 更新最大值和回撤
        if current_value > self.max_portfolio_value:
            self.max_portfolio_value = current_value
        
        current_drawdown = (current_value - self.max_portfolio_value) / self.max_portfolio_value
        if current_drawdown < self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # 检查是否需要调仓（每日检查）
        current_date = self.datas[0].datetime.date(0)
        should_rebalance = self.should_rebalance(current_date)
        if len(self.daily_values) <= 5:  # 调试输出
            self.log(f"🔍 调试: 检查调仓, 日期={current_date}, 需要调仓={should_rebalance}")
        
        if should_rebalance:
            self.log(f"🔄 开始调仓...")
            self.rebalance()
    
    def rebalance(self):
        """
        多趋势共振策略调仓逻辑
        """
        try:
            current_date = self.datas[0].datetime.date(0)
            
            # 1. 检查卖出信号
            self.check_sell_signals(current_date)
            
            # 2. 如果还有空余仓位，检查买入信号
            current_positions = len(self.positions_info)
            if current_positions < self.p.max_positions:
                self.check_buy_signals(current_date)
            
            # 3. 更新最后调仓日期
            self.last_rebalance_date = current_date
            
        except Exception as e:
            self.log(f"调仓失败: {e}")
    
    def check_sell_signals(self, current_date):
        """
        检查卖出信号 - 按文档设计
        """
        for stock_code in list(self.positions_info.keys()):
            try:
                position_info = self.positions_info[stock_code]
                current_price = self.get_price_data(stock_code, 'close')
                
                if current_price is None:
                    continue
                
                entry_price = position_info['entry_price']
                pnl_ratio = (current_price - entry_price) / entry_price
                
                should_sell, reason = self.check_sell_signal(stock_code, position_info, current_date)
                
                if should_sell:
                    self.sell_stock(stock_code)
                    del self.positions_info[stock_code]
                    self.log(f"卖出 {stock_code}: {reason}, 收益率: {pnl_ratio:.2%}")
                    
            except Exception as e:
                self.log(f"检查 {stock_code} 卖出信号失败: {e}")
    
    def check_buy_signals(self, current_date):
        """
        检查买入信号 - 按文档设计
        """
        try:
            # 获取候选股票池
            candidate_stocks = self.get_candidate_stocks()
            self.log(f"🔍 调试: 获取到候选股票数量: {len(candidate_stocks)}")
            if len(candidate_stocks) > 0:
                self.log(f"🔍 调试: 前5只候选股票: {candidate_stocks[:5]}")
            
            for stock_code in candidate_stocks:
                try:
                    # 检查买入信号
                    should_buy, resonance_score = self.check_buy_signal(stock_code, current_date)
                    
                    if should_buy:
                        current_price = self.get_price_data(stock_code, 'close')
                        if current_price and current_price > 0:
                            # 执行买入
                            self.buy_stock(stock_code, weight=self.p.max_single_weight)
                            
                            # 记录持仓信息
                            self.positions_info[stock_code] = {
                                'entry_price': current_price,
                                'entry_date': current_date,
                                'resonance_score': resonance_score
                            }
                            
                            self.log(f"买入 {stock_code}: 共振得分{resonance_score:.1f}, 价格{current_price:.2f}")
                            
                            # 达到最大持仓数就停止
                            if len(self.positions_info) >= self.p.max_positions:
                                break
                                
                except Exception as e:
                    self.log(f"检查 {stock_code} 买入信号失败: {e}")
                    
        except Exception as e:
            self.log(f"检查买入信号失败: {e}")
    
    def get_candidate_stocks(self) -> List[str]:
        """
        获取候选股票池 - 中证A500成分股
        """
        try:
            # 这里简化为使用当前数据源中的股票
            # 实际应该从中证A500成分股中筛选
            candidate_stocks = []
            
            for data in self.datas:
                stock_code = getattr(data, '_name', '')
                if stock_code and self.is_stock_qualified(stock_code):
                    candidate_stocks.append(stock_code)
            
            return candidate_stocks[:50]  # 限制候选数量
            
        except Exception as e:
            self.log(f"获取候选股票失败: {e}")
            return []
    
    def is_stock_qualified(self, stock_code: str) -> bool:
        """
        基础股票过滤
        """
        try:
            # 检查基础条件
            current_price = self.get_price_data(stock_code, 'close')
            volume = self.get_price_data(stock_code, 'volume')
            amount = self.get_price_data(stock_code, 'amount')
            turnover_rate = self.get_indicator(stock_code, 'turnover_rate')
            
            # 调试输出
            self.log(f"🔍 调试 {stock_code}: 价格={current_price}, 成交量={volume}, 成交额={amount}, 换手率={turnover_rate}")
            
            if not all([current_price, volume, amount, turnover_rate]):
                self.log(f"❌ {stock_code} 基础数据缺失")
                return False
            
            # 价格、成交量、换手率过滤
            if (current_price <= 0 or 
                amount < self.p.min_volume or 
                turnover_rate < self.p.min_turnover_rate):
                self.log(f"❌ {stock_code} 过滤条件不满足: 价格={current_price}, 成交额={amount}/{self.p.min_volume}, 换手率={turnover_rate}/{self.p.min_turnover_rate}")
                return False
            
            # 排除ST股票（简化处理）
            if 'ST' in stock_code:
                return False
            
            return True
            
        except:
            return False
    
    def check_buy_signal(self, stock_code: str, current_date) -> Tuple[bool, float]:
        """
        检查买入信号 - 按文档设计的严格条件
        
        Returns:
            Tuple[bool, float]: (是否买入, 共振得分)
        """
        try:
            # 1. 计算共振得分
            resonance_score = self.calculate_resonance_score(stock_code)
            
            # 2. 多时间周期趋势分析
            trends = self.analyze_multi_timeframe_trend(stock_code)
            
            # 3. 技术指标分析
            macd_signal = self.check_macd_bullish(stock_code)
            kdj_signal = self.check_kdj_signal(stock_code)
            volume_surge = self.check_volume_surge(stock_code)
            
            # 4. 检查是否超买
            not_overbought = not self.check_overbought_condition(stock_code)
            
            # 5. 买入条件检查 - 所有条件必须同时满足
            conditions = [
                resonance_score >= self.p.min_resonance_score,  # 共振得分达标
                trends['daily'] == 'bullish',                   # 日线多头
                trends['weekly'] == 'bullish',                  # 周线多头
                macd_signal,                                    # MACD金叉
                kdj_signal,                                     # KDJ信号
                volume_surge,                                   # 成交量放大
                not_overbought                                  # 非超买状态
            ]
            
            # 强共振信号可以放宽部分条件
            if resonance_score >= self.p.strong_resonance_score:
                strong_conditions = [
                    resonance_score >= self.p.strong_resonance_score,
                    trends['daily'] == 'bullish',
                    macd_signal or kdj_signal,
                    volume_surge
                ]
                return all(strong_conditions), resonance_score
            
            return all(conditions), resonance_score
            
        except Exception as e:
            self.log(f"检查买入信号失败 {stock_code}: {e}")
            return False, 0.0
    
    def check_sell_signal(self, stock_code: str, position_info: Dict, current_date) -> Tuple[bool, str]:
        """
        检查卖出信号 - 按文档设计
        
        Returns:
            Tuple[bool, str]: (是否卖出, 卖出原因)
        """
        try:
            current_price = self.get_price_data(stock_code, 'close')
            entry_price = position_info['entry_price']
            
            if not current_price or current_price <= 0:
                return False, ""
            
            pnl_ratio = (current_price - entry_price) / entry_price
            
            # 1. 止损止盈检查
            if pnl_ratio <= self.p.stop_loss_pct:
                return True, f"止损卖出: {pnl_ratio:.2%}"
            
            if pnl_ratio >= self.p.take_profit_pct:
                return True, f"止盈卖出: {pnl_ratio:.2%}"
            
            # 2. 共振信号检查
            current_score = self.calculate_resonance_score(stock_code)
            if current_score < 3:
                return True, f"共振信号转弱: 得分{current_score:.1f}"
            
            # 3. 趋势破坏检查
            trends = self.analyze_multi_timeframe_trend(stock_code)
            if trends['daily'] == 'bearish' and trends['weekly'] == 'bearish':
                return True, "多时间周期趋势转空"
            
            # 4. 技术破位检查
            if self.check_technical_breakdown(stock_code):
                return True, "关键技术位破位"
            
            # 5. 盈利保护（盈利8%后，回撤4%卖出）
            if pnl_ratio > self.p.profit_protect_pct:
                # 这里简化处理，实际应该用最近10日高点
                recent_high_price = current_price  # 简化
                if current_price < recent_high_price * (1 - self.p.pullback_threshold):
                    return True, f"盈利回撤卖出: 当前盈利{pnl_ratio:.2%}"
            
            return False, ""
            
        except Exception as e:
            self.log(f"检查卖出信号失败 {stock_code}: {e}")
            return False, ""
    
    def calculate_resonance_score(self, stock_code: str) -> float:
        """
        计算多趋势共振得分 - 按文档设计（0-11分）
        """
        try:
            score = 0.0
            
            # 1. MACD指标得分（0-3分）
            macd_score = self.calculate_macd_score(stock_code)
            score += macd_score
            
            # 2. KDJ指标得分（0-3分）
            kdj_score = self.calculate_kdj_score(stock_code)
            score += kdj_score
            
            # 3. 成交量指标得分（0-2分）
            volume_score = self.calculate_volume_score(stock_code)
            score += volume_score
            
            # 4. 趋势强度得分（0-2分）
            trend_score = self.calculate_trend_strength_score(stock_code)
            score += trend_score
            
            # 5. 价格位置得分（0-1分）
            price_score = self.calculate_price_position_score(stock_code)
            score += price_score
            
            return min(score, 11.0)  # 总分0-11分
            
        except Exception as e:
            self.log(f"计算共振得分失败 {stock_code}: {e}")
            return 0.0
    
    def analyze_multi_timeframe_trend(self, stock_code: str) -> Dict[str, str]:
        """
        分析多时间周期趋势
        基于日线数据计算周线、月线趋势
        """
        try:
            # 获取历史数据（这里简化处理，实际需要获取足够的历史数据）
            daily_trend = self.analyze_daily_trend(stock_code)
            weekly_trend = self.analyze_weekly_trend(stock_code) 
            monthly_trend = self.analyze_monthly_trend(stock_code)
            
            return {
                'daily': daily_trend,
                'weekly': weekly_trend,
                'monthly': monthly_trend
            }
            
        except Exception as e:
            self.log(f"多时间周期分析失败 {stock_code}: {e}")
            return {'daily': 'neutral', 'weekly': 'neutral', 'monthly': 'neutral'}
    
    def analyze_daily_trend(self, stock_code: str) -> str:
        """
        分析日线趋势
        """
        try:
            # 使用均线判断趋势
            current_price = self.get_price_data(stock_code, 'close')
            ma5 = self.get_indicator(stock_code, 'ma_bfq_5')
            ma20 = self.get_indicator(stock_code, 'ma_bfq_20')
            ma60 = self.get_indicator(stock_code, 'ma_bfq_60')
            
            if not all([current_price, ma5, ma20, ma60]):
                return 'neutral'
            
            # 多头排列
            if current_price > ma5 > ma20 > ma60:
                return 'bullish'
            # 空头排列
            elif current_price < ma5 < ma20 < ma60:
                return 'bearish'
            else:
                return 'neutral'
                
        except:
            return 'neutral'
    
    def analyze_weekly_trend(self, stock_code: str) -> str:
        """
        分析周线趋势 - 基于日线数据计算
        """
        try:
            # 简化处理：使用日线的长周期均线代替
            current_price = self.get_price_data(stock_code, 'close')
            ma20 = self.get_indicator(stock_code, 'ma_bfq_20')  # 约等于周线4周期
            ma60 = self.get_indicator(stock_code, 'ma_bfq_60')  # 约等于周线12周期
            
            if not all([current_price, ma20, ma60]):
                return 'neutral'
            
            if current_price > ma20 > ma60:
                return 'bullish'
            elif current_price < ma20 < ma60:
                return 'bearish'
            else:
                return 'neutral'
                
        except:
            return 'neutral'
    
    def analyze_monthly_trend(self, stock_code: str) -> str:
        """
        分析月线趋势 - 基于日线数据计算
        """
        try:
            # 简化处理：使用日线的长周期均线代替
            current_price = self.get_price_data(stock_code, 'close')
            ma60 = self.get_indicator(stock_code, 'ma_bfq_60')   # 约等于月线3周期
            ma120 = self.get_indicator(stock_code, 'ma_bfq_250') # 约等于月线12周期（用250日线代替）
            
            if not all([current_price, ma60, ma120]):
                return 'neutral'
            
            if current_price > ma60 > ma120:
                return 'bullish'
            elif current_price < ma60 < ma120:
                return 'bearish'
            else:
                return 'neutral'
                
        except:
            return 'neutral'
    
    def calculate_macd_score(self, stock_code: str) -> float:
        """
        计算MACD指标得分（0-3分）- 按文档设计
        """
        try:
            score = 0.0
            
            # 获取MACD指标
            macd_dif = self.get_indicator(stock_code, 'macd_dif_bfq')
            macd_dea = self.get_indicator(stock_code, 'macd_dea_bfq')
            macd_hist = self.get_indicator(stock_code, 'macd_bfq')
            
            if not all([macd_dif, macd_dea, macd_hist]):
                return 0.0
            
            # MACD金叉（2分）- 简化处理，实际需要历史数据判断
            if macd_dif > macd_dea and macd_dif > 0:
                score += 2
            # MACD在零轴上方（1分）
            elif macd_dif > 0:
                score += 1
            
            # MACD柱状图转正（1分）
            if macd_hist > 0:
                score += 1
            
            return min(score, 3.0)
            
        except:
            return 0.0
    
    def calculate_kdj_score(self, stock_code: str) -> float:
        """
        计算KDJ指标得分（0-3分）- 按文档设计
        """
        try:
            score = 0.0
            
            # 获取KDJ指标
            kdj_k = self.get_indicator(stock_code, 'kdj_k_bfq')
            kdj_d = self.get_indicator(stock_code, 'kdj_d_bfq')
            kdj_j = self.get_indicator(stock_code, 'kdj_bfq')
            
            if not all([kdj_k, kdj_d, kdj_j]):
                return 0.0
            
            # KDJ金叉（2分）- 简化处理
            if kdj_k > kdj_d and kdj_k > 20:
                score += 2
            # KDJ超卖反弹（1分）
            elif kdj_k < 20:
                score += 1
            
            # J值向上（1分）
            if kdj_j > kdj_k:
                score += 1
            
            return min(score, 3.0)
            
        except:
            return 0.0
    
    def calculate_volume_score(self, stock_code: str) -> float:
        """
        计算成交量指标得分（0-2分）
        """
        try:
            score = 0.0
            
            # 获取成交量相关指标
            volume_ratio = self.get_indicator(stock_code, 'volume_ratio')
            turnover_rate = self.get_indicator(stock_code, 'turnover_rate')
            
            if not volume_ratio:
                return 0.0
            
            # 成交量放大（1分）
            if volume_ratio >= self.p.volume_surge_threshold:
                score += 1
            
            # 换手率适中（1分）
            if turnover_rate and 0.02 <= turnover_rate <= 0.15:
                score += 1
            
            return min(score, 2.0)
            
        except:
            return 0.0
    
    def calculate_trend_strength_score(self, stock_code: str) -> float:
        """计算趋势强度得分（支持多时间周期）"""
        try:
            # 日线趋势
            ma5_daily = self.get_indicator(stock_code, 'ma5', timeframe='daily')
            ma20_daily = self.get_indicator(stock_code, 'ma20', timeframe='daily')
            ma60_daily = self.get_indicator(stock_code, 'ma60', timeframe='daily')
            
            # 周线趋势
            ma5_weekly = self.get_indicator(stock_code, 'ma5', timeframe='weekly')
            ma20_weekly = self.get_indicator(stock_code, 'ma20', timeframe='weekly')
            
            # 月线趋势
            ma5_monthly = self.get_indicator(stock_code, 'ma5', timeframe='monthly')
            ma20_monthly = self.get_indicator(stock_code, 'ma20', timeframe='monthly')
            
            daily_score = 0.0
            weekly_score = 0.0
            monthly_score = 0.0
            
            # 计算日线得分
            if all(v is not None for v in [ma5_daily, ma20_daily, ma60_daily]):
                if ma5_daily > ma20_daily > ma60_daily:
                    daily_score = 1.0
                elif ma5_daily > ma20_daily:
                    daily_score = 0.6
                elif ma20_daily > ma60_daily:
                    daily_score = 0.3
            
            # 计算周线得分
            if all(v is not None for v in [ma5_weekly, ma20_weekly]):
                if ma5_weekly > ma20_weekly:
                    weekly_score = 1.0
                else:
                    weekly_score = 0.0
            
            # 计算月线得分
            if all(v is not None for v in [ma5_monthly, ma20_monthly]):
                if ma5_monthly > ma20_monthly:
                    monthly_score = 1.0
                else:
                    monthly_score = 0.0
            
            # 多时间周期加权
            total_score = (daily_score * 0.5 + weekly_score * 0.3 + monthly_score * 0.2)
            
            return min(total_score, 1.0)
            
        except Exception as e:
            print(f"❌ 计算趋势强度得分失败 {stock_code}: {e}")
            return 0.0
    
    def get_indicator(self, stock_code: str, indicator_name: str, index: int = 0, timeframe: str = 'daily') -> Optional[float]:
        """获取技术指标值（支持多时间周期）"""
        if stock_code in self.stock_indicators:
            return self.stock_indicators[stock_code].get_indicator(indicator_name, index, timeframe)
        return None
    
    def calculate_price_position_score(self, stock_code: str) -> float:
        """
        计算价格位置得分（0-1分）
        """
        try:
            # 使用布林带判断价格位置
            current_price = self.get_price_data(stock_code, 'close')
            boll_upper = self.get_indicator(stock_code, 'boll_upper_bfq')
            boll_lower = self.get_indicator(stock_code, 'boll_lower_bfq')
            boll_mid = self.get_indicator(stock_code, 'boll_mid_bfq')
            
            if not all([current_price, boll_upper, boll_lower, boll_mid]):
                return 0.0
            
            # 价格在中轨上方但不超买（1分）
            if boll_lower < current_price < boll_upper and current_price > boll_mid:
                return 1.0
            
            return 0.0
            
        except:
            return 0.0
    
    def check_macd_bullish(self, stock_code: str) -> bool:
        """
        检查MACD金叉信号
        """
        try:
            macd_dif = self.get_indicator(stock_code, 'macd_dif_bfq')
            macd_dea = self.get_indicator(stock_code, 'macd_dea_bfq')
            
            if not all([macd_dif, macd_dea]):
                return False
            
            return macd_dif > macd_dea
            
        except:
            return False
    
    def check_kdj_signal(self, stock_code: str) -> bool:
        """
        检查KDJ信号
        """
        try:
            kdj_k = self.get_indicator(stock_code, 'kdj_k_bfq')
            kdj_d = self.get_indicator(stock_code, 'kdj_d_bfq')
            
            if not all([kdj_k, kdj_d]):
                return False
            
            # KDJ金叉或超卖反弹
            return (kdj_k > kdj_d) or (kdj_k < self.p.kdj_oversold)
            
        except:
            return False
    
    def check_volume_surge(self, stock_code: str) -> bool:
        """
        检查成交量放大
        """
        try:
            volume_ratio = self.get_indicator(stock_code, 'volume_ratio')
            
            if not volume_ratio:
                return False
            
            return volume_ratio >= self.p.volume_surge_threshold
            
        except:
            return False
    
    def check_overbought_condition(self, stock_code: str) -> bool:
        """
        检查是否超买
        """
        try:
            kdj_k = self.get_indicator(stock_code, 'kdj_k')
            rsi = self.get_indicator(stock_code, 'rsi_bfq_12')
            
            # KDJ超买
            if kdj_k and kdj_k > self.p.kdj_overbought:
                return True
            
            # RSI超买
            if rsi and rsi > 70:
                return True
            
            return False
            
        except:
            return False
    
    def check_technical_breakdown(self, stock_code: str) -> bool:
        """
        检查技术破位
        """
        try:
            current_price = self.get_price_data(stock_code, 'close')
            ma20 = self.get_indicator(stock_code, 'ma_hfq_20')
            boll_lower = self.get_indicator(stock_code, 'boll_lower')
            
            if not all([current_price, ma20]):
                return False
            
            # 跌破20日均线
            if current_price < ma20 * 0.95:
                return True
            
            # 跌破布林带下轨
            if boll_lower and current_price < boll_lower:
                return True
            
            return False
            
        except:
            return False
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略信息
        """
        current_positions = len(self.positions_info)
        
        info = {
            'strategy_name': '多趋势共振策略',
            'total_positions': current_positions,
            'max_positions': self.p.max_positions,
            'portfolio_value': self.broker.getvalue(),
            'positions_info': []
        }
        
        # 添加持仓详情
        for stock_code, pos_info in self.positions_info.items():
            current_price = self.get_price_data(stock_code, 'close')
            if current_price:
                pnl_pct = (current_price - pos_info['entry_price']) / pos_info['entry_price']
                info['positions_info'].append({
                    'stock_code': stock_code,
                    'entry_price': pos_info['entry_price'],
                    'current_price': current_price,
                    'pnl_pct': pnl_pct,
                    'resonance_score': pos_info['resonance_score']
                })
        
        return info