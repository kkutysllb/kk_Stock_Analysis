#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多趋势共振策略回测适配器
将现有的多趋势共振策略适配到新的回测引擎
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.backtest_engine import StrategyInterface
from .config import Config


class MultiTrendResonanceStrategyAdapter(StrategyInterface):
    """
    多趋势共振策略适配器
    将原有策略逻辑适配到新的回测引擎接口
    """
    
    def __init__(self):
        """初始化策略适配器"""
        self.name = "多趋势共振策略"
        self.version = "1.0.0"
        
        # 策略参数 - 从原有策略迁移
        self.params = {
            # 基础持仓参数
            'max_positions': 8,
            'max_single_weight': 0.12,
            'rebalance_freq': 1,
            
            # 技术指标参数
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'kdj_period': 9,
            'kdj_overbought': 80,
            'kdj_oversold': 20,
            'volume_ma_period': 15,
            'volume_surge_threshold': 1.3,
            
            # 共振信号参数
            'min_resonance_score': 6,
            'strong_resonance_score': 9,
            
            # 风险控制参数
            'stop_loss_pct': 0.06,
            'take_profit_pct': 0.12,
            'profit_protect_pct': 0.08,
            'pullback_threshold': 0.04,
            
            # 选股过滤参数
            'min_volume': 5000000,
            'min_turnover_rate': 0.01,
        }
        
        # 策略状态
        self.positions_info = {}  # 持仓信息
        self.buy_signals_count = 0
        self.sell_signals_count = 0
        self.resonance_scores = {}  # 共振得分缓存
        
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
        print(f"   最小共振得分: {self.params['min_resonance_score']}")
    
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
            交易信号列表
        """
        signals = []
        
        try:
            # 1. 检查卖出信号
            sell_signals = self._check_sell_signals(current_date, market_data, portfolio_info)
            signals.extend(sell_signals)
            
            # 2. 检查买入信号
            current_positions = portfolio_info.get('total_positions', 0)
            if current_positions < self.params['max_positions']:
                buy_signals = self._check_buy_signals(current_date, market_data, portfolio_info)
                signals.extend(buy_signals)
            
            # 3. 记录信号历史
            if signals:
                self.signal_history.append({
                    'date': current_date,
                    'signals_count': len(signals),
                    'buy_count': len([s for s in signals if s['action'] == 'buy']),
                    'sell_count': len([s for s in signals if s['action'] == 'sell'])
                })
            
            # 4. 定期输出进度
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
                    
                    # 移除持仓记录
                    del self.positions_info[stock_code]
                    self.sell_signals_count += 1
                    
            except Exception as e:
                print(f"检查 {stock_code} 卖出信号失败: {e}")
        
        return sell_signals
    
    def _check_buy_signals(self, 
                          current_date: str, 
                          market_data: Dict[str, Dict],
                          portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查买入信号"""
        buy_signals = []
        
        # 获取候选股票池
        candidate_stocks = self._get_candidate_stocks(market_data)
        
        # 计算共振得分并排序
        stock_scores = []
        for stock_code in candidate_stocks:
            if stock_code not in self.positions_info:  # 排除已持仓股票
                try:
                    resonance_score = self._calculate_resonance_score(
                        stock_code, market_data[stock_code]
                    )
                    
                    if resonance_score >= self.params['min_resonance_score']:
                        stock_scores.append((stock_code, resonance_score))
                        
                except Exception as e:
                    continue
        
        # 按得分排序，选择最优股票
        stock_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 生成买入信号
        max_new_positions = self.params['max_positions'] - len(self.positions_info)
        for stock_code, score in stock_scores[:max_new_positions]:
            try:
                should_buy = self._check_buy_signal(
                    stock_code, market_data[stock_code], score
                )
                
                if should_buy:
                    buy_signals.append({
                        'action': 'buy',
                        'stock_code': stock_code,
                        'price': market_data[stock_code]['close'],
                        'weight': self.params['max_single_weight'],
                        'resonance_score': score
                    })
                    
                    # 记录持仓信息
                    self.positions_info[stock_code] = {
                        'entry_price': market_data[stock_code]['close'],
                        'entry_date': current_date,
                        'resonance_score': score
                    }
                    
                    self.buy_signals_count += 1
                    
                    # 限制每次最多买入1只股票
                    break
                    
            except Exception as e:
                print(f"检查 {stock_code} 买入信号失败: {e}")
        
        return buy_signals
    
    def _get_candidate_stocks(self, market_data: Dict[str, Dict]) -> List[str]:
        """获取候选股票池"""
        candidate_stocks = []
        
        for stock_code, stock_data in market_data.items():
            if self._is_stock_qualified(stock_code, stock_data):
                candidate_stocks.append(stock_code)
        
        return candidate_stocks[:50]  # 限制候选数量
    
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
    
    def _check_buy_signal(self, stock_code: str, stock_data: Dict, resonance_score: float) -> bool:
        """检查买入信号"""
        try:
            # 1. 共振得分检查
            if resonance_score < self.params['min_resonance_score']:
                return False
            
            # 2. 技术指标检查
            macd_signal = self._check_macd_bullish(stock_data)
            kdj_signal = self._check_kdj_signal(stock_data)
            volume_surge = self._check_volume_surge(stock_data)
            
            # 3. 基本买入条件
            basic_conditions = [
                resonance_score >= self.params['min_resonance_score'],
                macd_signal or kdj_signal,  # 至少一个技术指标确认
                volume_surge,  # 成交量放大
                not self._check_overbought_condition(stock_data)  # 非超买
            ]
            
            # 4. 强共振信号可以放宽条件
            if resonance_score >= self.params['strong_resonance_score']:
                return resonance_score >= self.params['strong_resonance_score']
            
            return all(basic_conditions)
            
        except Exception as e:
            return False
    
    def _check_sell_signal(self, stock_code: str, stock_data: Dict, current_date: str) -> tuple:
        """检查卖出信号"""
        try:
            if stock_code not in self.positions_info:
                return False, ""
            
            position_info = self.positions_info[stock_code]
            current_price = stock_data['close']
            entry_price = position_info['entry_price']
            
            pnl_ratio = (current_price - entry_price) / entry_price
            
            # 1. 止损止盈检查
            if pnl_ratio <= -self.params['stop_loss_pct']:
                return True, f"止损卖出: {pnl_ratio:.2%}"
            
            if pnl_ratio >= self.params['take_profit_pct']:
                return True, f"止盈卖出: {pnl_ratio:.2%}"
            
            # 2. 共振信号转弱检查
            current_score = self._calculate_resonance_score(stock_code, stock_data)
            if current_score < 3:
                return True, f"共振信号转弱: 得分{current_score:.1f}"
            
            # 3. 盈利保护
            if pnl_ratio > self.params['profit_protect_pct']:
                # 简化处理：如果有一定盈利且技术指标转弱
                if not self._check_macd_bullish(stock_data):
                    return True, f"盈利保护卖出: 当前盈利{pnl_ratio:.2%}"
            
            return False, ""
            
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def _calculate_resonance_score(self, stock_code: str, stock_data: Dict) -> float:
        """计算多趋势共振得分（0-11分）"""
        try:
            score = 0.0
            
            # 1. MACD指标得分（0-3分）
            score += self._calculate_macd_score(stock_data)
            
            # 2. KDJ指标得分（0-3分）
            score += self._calculate_kdj_score(stock_data)
            
            # 3. 成交量指标得分（0-2分）
            score += self._calculate_volume_score(stock_data)
            
            # 4. 趋势强度得分（0-2分）
            score += self._calculate_trend_strength_score(stock_data)
            
            # 5. 价格位置得分（0-1分）
            score += self._calculate_price_position_score(stock_data)
            
            # 缓存得分
            self.resonance_scores[stock_code] = score
            
            return min(score, 11.0)
            
        except Exception as e:
            return 0.0
    
    def _calculate_macd_score(self, stock_data: Dict) -> float:
        """计算MACD指标得分（0-3分）"""
        try:
            score = 0.0
            
            macd_dif = stock_data.get('macd_dif', 0)
            macd_dea = stock_data.get('macd_dea', 0)
            macd_hist = stock_data.get('macd_macd', 0)
            
            if not all([macd_dif, macd_dea, macd_hist]):
                return 0.0
            
            # MACD金叉和在零轴上方
            if macd_dif > macd_dea and macd_dif > 0:
                score += 2
            elif macd_dif > 0:
                score += 1
            
            # MACD柱状图转正
            if macd_hist > 0:
                score += 1
            
            return min(score, 3.0)
            
        except:
            return 0.0
    
    def _calculate_kdj_score(self, stock_data: Dict) -> float:
        """计算KDJ指标得分（0-3分）"""
        try:
            score = 0.0
            
            kdj_k = stock_data.get('kdj_k', 0)
            kdj_d = stock_data.get('kdj_d', 0)
            kdj_j = stock_data.get('kdj_j', 0)
            
            if not all([kdj_k, kdj_d, kdj_j]):
                return 0.0
            
            # KDJ金叉
            if kdj_k > kdj_d and kdj_k > 20:
                score += 2
            elif kdj_k < 20:  # 超卖反弹
                score += 1
            
            # J值向上
            if kdj_j > kdj_k:
                score += 1
            
            return min(score, 3.0)
            
        except:
            return 0.0
    
    def _calculate_volume_score(self, stock_data: Dict) -> float:
        """计算成交量指标得分（0-2分）"""
        try:
            score = 0.0
            
            volume_ratio = stock_data.get('volume_ratio', 1.0)
            turnover_rate = stock_data.get('turnover_rate', 0)
            
            # 成交量放大
            if volume_ratio >= self.params['volume_surge_threshold']:
                score += 1
            
            # 换手率适中
            if 0.02 <= turnover_rate <= 0.15:
                score += 1
            
            return min(score, 2.0)
            
        except:
            return 0.0
    
    def _calculate_trend_strength_score(self, stock_data: Dict) -> float:
        """计算趋势强度得分（0-2分）"""
        try:
            score = 0.0
            
            current_price = stock_data.get('close', 0)
            ma5 = stock_data.get('ma5', 0)
            ma20 = stock_data.get('ma20', 0)
            ma60 = stock_data.get('ma60', 0)
            
            if not all([current_price, ma5, ma20, ma60]):
                return 0.0
            
            # 多头排列
            if current_price > ma5 > ma20 > ma60:
                score += 2
            elif current_price > ma5 > ma20:
                score += 1
            
            return min(score, 2.0)
            
        except:
            return 0.0
    
    def _calculate_price_position_score(self, stock_data: Dict) -> float:
        """计算价格位置得分（0-1分）"""
        try:
            current_price = stock_data.get('close', 0)
            boll_upper = stock_data.get('boll_upper', 0)
            boll_lower = stock_data.get('boll_lower', 0)
            boll_mid = stock_data.get('boll_mid', 0)
            
            if not all([current_price, boll_upper, boll_lower, boll_mid]):
                return 0.0
            
            # 价格在中轨上方但不超买
            if boll_lower < current_price < boll_upper and current_price > boll_mid:
                return 1.0
            
            return 0.0
            
        except:
            return 0.0
    
    def _check_macd_bullish(self, stock_data: Dict) -> bool:
        """检查MACD金叉信号"""
        try:
            macd_dif = stock_data.get('macd_dif', 0)
            macd_dea = stock_data.get('macd_dea', 0)
            return macd_dif > macd_dea if all([macd_dif, macd_dea]) else False
        except:
            return False
    
    def _check_kdj_signal(self, stock_data: Dict) -> bool:
        """检查KDJ信号"""
        try:
            kdj_k = stock_data.get('kdj_k', 0)
            kdj_d = stock_data.get('kdj_d', 0)
            return (kdj_k > kdj_d) or (kdj_k < self.params['kdj_oversold']) if all([kdj_k, kdj_d]) else False
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
        """检查是否超买"""
        try:
            kdj_k = stock_data.get('kdj_k', 0)
            rsi = stock_data.get('rsi12', 0)
            
            # KDJ超买
            if kdj_k and kdj_k > self.params['kdj_overbought']:
                return True
            
            # RSI超买
            if rsi and rsi > 70:
                return True
            
            return False
        except:
            return False
    
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
            'strategy_type': '多趋势共振策略',
            'max_positions': self.params['max_positions'],
            'max_single_weight': self.params['max_single_weight'],
            'min_resonance_score': self.params['min_resonance_score'],
            'strong_resonance_score': self.params['strong_resonance_score'],
            'current_positions': len(self.positions_info),
            'buy_signals_count': self.buy_signals_count,
            'sell_signals_count': self.sell_signals_count,
            'total_signals': len(self.signal_history),
            'total_trades': len(self.trade_history),
            'description': '基于多时间周期技术分析的量化策略，通过MACD、KDJ、成交量等多重指标共振识别投资机会'
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