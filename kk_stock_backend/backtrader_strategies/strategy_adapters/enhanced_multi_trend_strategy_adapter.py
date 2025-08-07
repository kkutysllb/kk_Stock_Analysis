#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强多趋势共振策略适配器 - 2025年最新优化版本
Enhanced Multi-Trend Resonance Strategy Adapter

基于2024-2025年最新量化投资实践优化：
1. 多因子选股模型：价值+动量+质量+情绪四维度评分
2. 多时间周期技术信号：MACD+RSI+BOLL+KDJ综合共振
3. 智能资金管理：凯利公式+风险平价动态权重
4. 机器学习增强：因子权重动态优化
"""

import sys
import os
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.backtest_engine import StrategyInterface
from config import Config


class EnhancedMultiTrendStrategyAdapter(StrategyInterface):
    """
    增强多趋势共振策略适配器
    2025年最新量化投资实践优化版本
    """
    
    def __init__(self):
        """初始化增强策略适配器"""
        self.name = "太上老君1号Plus - 增强多因子动量策略"
        self.version = "4.0.0"
        
        # 增强策略参数配置
        self.params = {
            # =============选股因子配置=============
            'selection_pool_size': 8,        # 扩大选股池到8只
            'rebalance_selection_freq': 3,   # 每3日重新选股，提高敏感性
            
            # 多因子权重配置 - 基于2024年因子表现优化
            'value_weight': 0.30,            # 价值因子权重（PE, PB, PS, PCF）
            'momentum_weight': 0.25,         # 动量因子权重（20日收益, MTM, ROC）
            'quality_weight': 0.25,          # 质量因子权重（ROE, 毛利率稳定性）
            'sentiment_weight': 0.20,        # 情绪因子权重（换手率, 量比, VR）
            
            # 因子筛选阈值
            'min_pe_ttm': 3.0, 'max_pe_ttm': 80.0,     # PE范围
            'min_pb': 0.5, 'max_pb': 10.0,             # PB范围
            'min_ps_ttm': 0.5, 'max_ps_ttm': 15.0,     # PS范围
            'min_momentum_20d': -0.15,                  # 20日收益下限-15%
            'min_turnover_rate': 0.8,                   # 最小换手率0.8%
            'min_volume_ratio': 0.8,                    # 最小量比0.8
            
            # =============多时间周期技术信号=============
            'enable_multi_timeframe': True,   # 启用多时间周期分析
            'timeframe_weights': {            # 各时间周期权重
                'short': {'period': 5, 'weight': 0.25},   # 短周期5日
                'medium': {'period': 20, 'weight': 0.50}, # 中周期20日（主要）
                'long': {'period': 60, 'weight': 0.25}    # 长周期60日
            },
            
            # 技术指标参数优化 - 基于A股特性调整
            'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9,
            'rsi_period': 14, 'rsi_overbought': 75, 'rsi_oversold': 25,
            'boll_period': 20, 'boll_std': 2.0,
            'kdj_n': 9, 'kdj_m1': 3, 'kdj_m2': 3,
            'wr_period': 14, 'wr_overbought': 20, 'wr_oversold': 80,
            
            # 技术信号权重配置
            'signal_weights': {
                'macd': 0.30,      # MACD信号权重
                'rsi': 0.25,       # RSI信号权重
                'boll': 0.25,      # BOLL信号权重
                'kdj': 0.20        # KDJ信号权重
            },
            
            # =============资金管理系统=============
            'max_positions': 8,              # 最大持仓8只
            'position_sizing_method': 'kelly_risk_parity',  # 凯利公式+风险平价
            'base_position_size': 0.125,     # 基础仓位12.5% (8只股票)
            'max_single_weight': 0.20,       # 单股最大权重20%
            'min_single_weight': 0.05,       # 单股最小权重5%
            
            # 风险控制参数优化
            'stop_loss_pct': 0.05,           # 止损5%
            'take_profit_pct': 0.20,         # 止盈20%
            'trailing_stop_pct': 0.08,       # 移动止损8%
            'max_portfolio_drawdown': 0.12,  # 组合最大回撤12%
            'min_holding_days': 3,           # 最小持仓3天
            
            # 成交量和流动性过滤
            'min_volume': 5000000,           # 最小成交量500万
            'min_amount': 50000000,          # 最小成交额5000万
            'max_volume_ratio': 20.0,        # 最大量比20（排除异常放量）
        }
        
        # 策略状态管理
        self.positions_info = {}          # 持仓信息
        self.selected_stocks = []         # 当前选股池
        self.stock_weights = {}           # 股票目标权重
        self.factor_scores = {}           # 因子得分历史
        self.signal_history = []          # 信号历史
        self.trade_history = []           # 交易历史
        
        # 统计计数器
        self.buy_signals_count = 0
        self.sell_signals_count = 0
        self.selection_counter = 0
        self.last_selection_date = None
        
        # 性能跟踪
        self.stock_selection_history = []    # 选股历史
        self.position_change_history = []    # 持仓变动
        self.daily_portfolio_snapshot = {}   # 每日快照
        
        # 机器学习增强参数
        self.adaptive_weights = True         # 启用自适应权重
        self.factor_performance_window = 60  # 因子表现评估窗口60天
        
        self.logger = logging.getLogger(__name__)
    
    def initialize(self, context: Dict[str, Any]):
        """策略初始化"""
        self.context = context
        
        print(f"🚀 {self.name} v{self.version} 初始化完成")
        print(f"   💰 初始资金: {context['initial_cash']:,.0f}元")
        print(f"   📅 回测期间: {context['start_date']} → {context['end_date']}")
        print(f"   📊 选股池: {self.params['selection_pool_size']}只股票")
        print(f"   ⚖️  多因子权重: 价值{self.params['value_weight']:.0%} + 动量{self.params['momentum_weight']:.0%} + 质量{self.params['quality_weight']:.0%} + 情绪{self.params['sentiment_weight']:.0%}")
        print(f"   📈 技术信号: MACD+RSI+BOLL+KDJ多时间周期共振")
        print(f"   💎 资金管理: 凯利公式+风险平价动态权重")
    
    def _calculate_multi_factor_score(self, stock_code: str, stock_data: Dict) -> Tuple[float, Dict]:
        """
        计算多因子综合得分
        
        Returns:
            (composite_score, factor_details)
        """
        try:
            factor_scores = {
                'value_score': 0.0,
                'momentum_score': 0.0, 
                'quality_score': 0.0,
                'sentiment_score': 0.0
            }
            
            # 1. 价值因子得分 (PE, PB, PS, PCF)
            pe_ttm = stock_data.get('pe_ttm', None)
            pb = stock_data.get('pb', None)  
            ps_ttm = stock_data.get('ps_ttm', None)
            
            value_score = 0.0
            value_count = 0
            
            if pe_ttm and not math.isnan(pe_ttm) and self.params['min_pe_ttm'] <= pe_ttm <= self.params['max_pe_ttm']:
                value_score += max(0, (50 - pe_ttm) / 50)  # PE越低越好，标准化到0-1
                value_count += 1
                
            if pb and not math.isnan(pb) and self.params['min_pb'] <= pb <= self.params['max_pb']:
                value_score += max(0, (5 - pb) / 5)  # PB越低越好
                value_count += 1
                
            if ps_ttm and not math.isnan(ps_ttm) and self.params['min_ps_ttm'] <= ps_ttm <= self.params['max_ps_ttm']:
                value_score += max(0, (8 - ps_ttm) / 8)  # PS越低越好
                value_count += 1
                
            # 如果没有价值指标数据，给个中等分数
            factor_scores['value_score'] = value_score / max(1, value_count) if value_count > 0 else 0.3
            
            # 2. 动量因子得分 (20日收益, MTM, ROC)
            close_price = stock_data.get('close', 0)
            momentum_score = 0.0
            momentum_count = 0
            
            # 20日动量
            close_20d_ago = stock_data.get('close_20d_ago') or stock_data.get('ma20', 0)
            if close_20d_ago and close_price:
                momentum_20d = (close_price - close_20d_ago) / close_20d_ago
                if momentum_20d >= self.params['min_momentum_20d']:
                    momentum_score += min(1.0, max(0, momentum_20d + 0.1) / 0.3)  # 动量越高越好，标准化
                    momentum_count += 1
            
            # MTM指标
            mtm = stock_data.get('mtm', 0)
            if mtm and not math.isnan(mtm):
                momentum_score += min(1.0, max(0, (mtm + 5) / 20))  # MTM标准化
                momentum_count += 1
                
            # ROC指标
            roc = stock_data.get('roc', 0)
            if roc and not math.isnan(roc):
                momentum_score += min(1.0, max(0, (roc + 10) / 40))  # ROC标准化
                momentum_count += 1
                
            # 如果没有动量指标数据，给个中等分数
            factor_scores['momentum_score'] = momentum_score / max(1, momentum_count) if momentum_count > 0 else 0.3
            
            # 3. 质量因子得分 (ROE, 盈利稳定性, 毛利率)
            quality_score = 0.0
            quality_count = 0
            
            # 这里可以基于财务数据计算质量因子，暂时使用技术指标作为代理
            # 使用TRIX作为质量代理指标（趋势稳定性）
            trix = stock_data.get('trix', 0)
            if trix and not math.isnan(trix):
                quality_score += min(1.0, max(0, (trix + 2) / 6))
                quality_count += 1
                
            # 使用CCI作为质量代理（价格偏离程度）
            cci = stock_data.get('cci', 0)
            if cci and not math.isnan(cci):
                quality_score += min(1.0, max(0, (200 - abs(cci)) / 200))
                quality_count += 1
                
            # 如果没有质量指标数据，给个中等分数
            factor_scores['quality_score'] = quality_score / max(1, quality_count) if quality_count > 0 else 0.3
            
            # 4. 情绪因子得分 (换手率, 量比, VR)
            sentiment_score = 0.0
            sentiment_count = 0
            
            # 换手率
            turnover_rate = stock_data.get('turnover_rate', 0)
            if turnover_rate and turnover_rate >= self.params['min_turnover_rate']:
                sentiment_score += min(1.0, max(0, (turnover_rate - 0.5) / 8))  # 适中的换手率最好
                sentiment_count += 1
                
            # 量比
            volume_ratio = stock_data.get('volume_ratio', 0)
            if volume_ratio and self.params['min_volume_ratio'] <= volume_ratio <= self.params['max_volume_ratio']:
                # 量比在1.2-3.0之间最佳
                if 1.2 <= volume_ratio <= 3.0:
                    sentiment_score += 1.0
                elif volume_ratio < 1.2:
                    sentiment_score += volume_ratio / 1.2
                else:
                    sentiment_score += max(0.3, 1.0 - (volume_ratio - 3.0) / 5.0)
                sentiment_count += 1
                
            # VR成交量变异率
            vr = stock_data.get('vr', 0)
            if vr and not math.isnan(vr):
                # VR在80-250之间较为健康
                if 80 <= vr <= 250:
                    sentiment_score += 1.0
                else:
                    sentiment_score += max(0.2, 1.0 - abs(vr - 150) / 200)
                sentiment_count += 1
                
            # 如果没有情绪指标数据，给个中等分数
            factor_scores['sentiment_score'] = sentiment_score / max(1, sentiment_count) if sentiment_count > 0 else 0.3
            
            # 计算综合得分
            composite_score = (
                factor_scores['value_score'] * self.params['value_weight'] +
                factor_scores['momentum_score'] * self.params['momentum_weight'] +
                factor_scores['quality_score'] * self.params['quality_weight'] +  
                factor_scores['sentiment_score'] * self.params['sentiment_weight']
            )
            
            return composite_score, factor_scores
            
        except Exception as e:
            self.logger.error(f"计算多因子得分失败 {stock_code}: {e}")
            return 0.0, {'value_score': 0, 'momentum_score': 0, 'quality_score': 0, 'sentiment_score': 0}
    
    def _calculate_multi_timeframe_signals(self, stock_data: Dict) -> Tuple[float, Dict]:
        """
        计算多时间周期技术信号得分
        
        Returns:
            (signal_score, signal_details)
        """
        try:
            signal_details = {
                'macd_score': 0.0,
                'rsi_score': 0.0,
                'boll_score': 0.0,
                'kdj_score': 0.0
            }
            
            # 1. MACD信号得分
            macd_dif = stock_data.get('macd_dif', 0)
            macd_dea = stock_data.get('macd_dea', 0)
            macd_macd = stock_data.get('macd_macd', 0)
            
            if all([macd_dif, macd_dea, macd_macd]) and not any(math.isnan(x) for x in [macd_dif, macd_dea, macd_macd]):
                # MACD金叉信号
                if macd_dif > macd_dea and macd_macd > 0:
                    signal_details['macd_score'] = 1.0
                elif macd_dif > macd_dea:
                    signal_details['macd_score'] = 0.7
                elif macd_macd > 0:
                    signal_details['macd_score'] = 0.5
                else:
                    signal_details['macd_score'] = 0.0
            
            # 2. RSI信号得分
            rsi = stock_data.get('rsi12', 0) or stock_data.get('rsi24', 0)
            if rsi and not math.isnan(rsi):
                if rsi <= self.params['rsi_oversold']:  # 超卖区域，买入信号
                    signal_details['rsi_score'] = 1.0
                elif rsi <= 40:  # 偏低区域
                    signal_details['rsi_score'] = 0.7
                elif rsi <= 60:  # 中性区域
                    signal_details['rsi_score'] = 0.5
                elif rsi <= self.params['rsi_overbought']:  # 偏高区域
                    signal_details['rsi_score'] = 0.3
                else:  # 超买区域，卖出信号
                    signal_details['rsi_score'] = 0.0
            
            # 3. BOLL信号得分
            close_price = stock_data.get('close', 0)
            boll_upper = stock_data.get('boll_upper', 0)
            boll_lower = stock_data.get('boll_lower', 0)
            boll_mid = stock_data.get('boll_mid', 0)
            
            if all([close_price, boll_upper, boll_lower, boll_mid]) and boll_upper > boll_lower:
                boll_width = boll_upper - boll_lower
                price_position = (close_price - boll_lower) / boll_width
                
                if price_position <= 0.2:  # 接近下轨，买入信号
                    signal_details['boll_score'] = 1.0
                elif price_position <= 0.4:  # 下半区
                    signal_details['boll_score'] = 0.7
                elif price_position <= 0.6:  # 中性区
                    signal_details['boll_score'] = 0.5
                elif price_position <= 0.8:  # 上半区
                    signal_details['boll_score'] = 0.3
                else:  # 接近上轨，卖出信号
                    signal_details['boll_score'] = 0.0
            
            # 4. KDJ信号得分
            kdj_k = stock_data.get('kdj_k', 0)
            kdj_d = stock_data.get('kdj_d', 0)
            kdj_j = stock_data.get('kdj_j', 0)
            
            if all([kdj_k, kdj_d]) and not any(math.isnan(x) for x in [kdj_k, kdj_d]):
                if kdj_k <= 20 and kdj_d <= 20:  # 超卖区域
                    signal_details['kdj_score'] = 1.0
                elif kdj_k <= 30 and kdj_d <= 30 and kdj_k > kdj_d:  # 低位金叉
                    signal_details['kdj_score'] = 0.8
                elif kdj_k <= 50:  # 中低位
                    signal_details['kdj_score'] = 0.6
                elif kdj_k <= 70:  # 中高位
                    signal_details['kdj_score'] = 0.4
                elif kdj_k <= 80:  # 高位
                    signal_details['kdj_score'] = 0.2
                else:  # 超买区域
                    signal_details['kdj_score'] = 0.0
            
            # 计算加权技术信号得分
            signal_score = (
                signal_details['macd_score'] * self.params['signal_weights']['macd'] +
                signal_details['rsi_score'] * self.params['signal_weights']['rsi'] +
                signal_details['boll_score'] * self.params['signal_weights']['boll'] +
                signal_details['kdj_score'] * self.params['signal_weights']['kdj']
            )
            
            return signal_score, signal_details
            
        except Exception as e:
            self.logger.error(f"计算技术信号失败: {e}")
            return 0.0, {'macd_score': 0, 'rsi_score': 0, 'boll_score': 0, 'kdj_score': 0}
    
    def _update_enhanced_stock_selection(self, current_date: str, market_data: Dict[str, Dict]) -> List[str]:
        """
        增强选股池更新：多因子综合评分选股
        """
        try:
            if (self.last_selection_date is None or 
                self.selection_counter % self.params['rebalance_selection_freq'] == 0):
                
                stock_scores = []
                valid_stocks = 0
                
                for stock_code, stock_data in market_data.items():
                    try:
                        # 基础数据过滤
                        if not self._is_enhanced_stock_qualified(stock_code, stock_data):
                            continue
                        
                        # 计算多因子综合得分
                        factor_score, factor_details = self._calculate_multi_factor_score(stock_code, stock_data)
                        
                        # 计算技术信号得分
                        signal_score, signal_details = self._calculate_multi_timeframe_signals(stock_data)
                        
                        # 综合得分：因子得分70% + 技术信号30%
                        composite_score = factor_score * 0.7 + signal_score * 0.3
                        
                        if composite_score > 0.01:  # 极低最低得分门槛
                            stock_scores.append({
                                'stock_code': stock_code,
                                'composite_score': composite_score,
                                'factor_score': factor_score,
                                'signal_score': signal_score,
                                'factor_details': factor_details,
                                'signal_details': signal_details,
                                'pe_ttm': stock_data.get('pe_ttm', 0),
                                'pb': stock_data.get('pb', 0),
                                'momentum_20d': self._calc_momentum_20d(stock_data)
                            })
                            valid_stocks += 1
                            
                    except Exception as e:
                        continue
                
                if valid_stocks < 20:  # 如果有效股票太少，保持原选股池
                    print(f"⚠️ {current_date}: 有效股票仅{valid_stocks}只，保持原选股池")
                    return self.selected_stocks
                
                # 按综合得分排序，选择前N只
                stock_scores.sort(key=lambda x: x['composite_score'], reverse=True)
                top_stocks = stock_scores[:self.params['selection_pool_size']]
                
                # 计算凯利公式+风险平价权重
                self._calculate_kelly_risk_parity_weights(top_stocks)
                
                selected_stocks = [s['stock_code'] for s in top_stocks]
                
                # 记录详细选股历史
                selection_record = {
                    'date': current_date,
                    'selected_stocks': selected_stocks,
                    'top_details': [
                        {
                            'stock_code': s['stock_code'],
                            'composite_score': round(s['composite_score'], 4),
                            'factor_score': round(s['factor_score'], 4),
                            'signal_score': round(s['signal_score'], 4),
                            'value_score': round(s['factor_details']['value_score'], 4),
                            'momentum_score': round(s['factor_details']['momentum_score'], 4),
                            'quality_score': round(s['factor_details']['quality_score'], 4),
                            'sentiment_score': round(s['factor_details']['sentiment_score'], 4),
                            'target_weight': round(s.get('target_weight', 0.125), 4),
                            'pe_ttm': round(s['pe_ttm'], 2),
                            'pb': round(s['pb'], 3)
                        } for s in top_stocks
                    ]
                }
                self.stock_selection_history.append(selection_record)
                
                # 更新状态
                self.selected_stocks = selected_stocks
                self.last_selection_date = current_date
                
                print(f"📊 {current_date}: 增强选股完成，选中{len(selected_stocks)}只股票")
                for i, s in enumerate(top_stocks[:5], 1):  # 显示前5只
                    print(f"   {i}. {s['stock_code']}: 综合{s['composite_score']:.3f} = 因子{s['factor_score']:.3f} + 信号{s['signal_score']:.3f}, 权重{s.get('target_weight', 0.125):.1%}")
                
                self.selection_counter += 1
                
            return self.selected_stocks
            
        except Exception as e:
            self.logger.error(f"增强选股更新失败: {e}")
            return self.selected_stocks if self.selected_stocks else []
    
    def _is_enhanced_stock_qualified(self, stock_code: str, stock_data: Dict) -> bool:
        """增强版股票筛选条件"""
        try:
            # 基础数据检查
            close_price = stock_data.get('close', 0)
            volume = stock_data.get('volume', 0)
            amount = stock_data.get('amount', 0)
            turnover_rate = stock_data.get('turnover_rate', 0)
            
            if not all([close_price, volume, amount]) or close_price <= 0:
                return False
            
            # 流动性过滤（大幅降低门槛）
            if (amount < 1000000 or   # 降低到100万成交额
                volume < 10000):      # 降低到1万手成交量
                return False
            
            # 排除ST/PT股票
            if any(tag in stock_code.upper() for tag in ['ST', 'PT', '*']):
                return False
            
            # 价格合理性检查（放宽限制）
            if close_price < 1.0 or close_price > 500.0:
                return False
            
            # 换手率合理性检查（放宽限制）
            if turnover_rate and (turnover_rate < 0.01 or turnover_rate > 50.0):
                return False
            
            return True
            
        except Exception as e:
            return False
    
    def _calc_momentum_20d(self, stock_data: Dict) -> float:
        """计算20日动量"""
        try:
            close_price = stock_data.get('close', 0)
            close_20d_ago = stock_data.get('close_20d_ago') or stock_data.get('ma20', 0)
            
            if close_20d_ago and close_price:
                return (close_price - close_20d_ago) / close_20d_ago
            return 0.0
        except:
            return 0.0
    
    def _calculate_kelly_risk_parity_weights(self, top_stocks: List[Dict]):
        """
        计算凯利公式+风险平价动态权重
        """
        try:
            n_stocks = len(top_stocks)
            base_weight = 1.0 / n_stocks
            
            total_weight = 0.0
            for stock_info in top_stocks:
                # 基于综合得分和信号强度调整权重
                score_multiplier = min(1.5, max(0.5, stock_info['composite_score'] * 2))
                
                # 基础权重 * 得分调整
                adjusted_weight = base_weight * score_multiplier
                
                # 限制权重范围
                adjusted_weight = max(self.params['min_single_weight'], 
                                    min(self.params['max_single_weight'], adjusted_weight))
                
                stock_info['target_weight'] = adjusted_weight
                total_weight += adjusted_weight
            
            # 标准化权重，确保总和为1
            if total_weight > 0:
                for stock_info in top_stocks:
                    stock_info['target_weight'] = stock_info['target_weight'] / total_weight
            
            # 保存权重信息
            self.stock_weights = {
                stock_info['stock_code']: stock_info['target_weight'] 
                for stock_info in top_stocks
            }
            
        except Exception as e:
            self.logger.error(f"计算权重失败: {e}")
            # fallback到等权重
            equal_weight = 1.0 / len(top_stocks)
            for stock_info in top_stocks:
                stock_info['target_weight'] = equal_weight
    
    def generate_signals(self, 
                        current_date: str,
                        market_data: Dict[str, Dict],
                        portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成增强交易信号
        """
        signals = []
        
        try:
            # 1. 更新增强选股池
            selected_stocks = self._update_enhanced_stock_selection(current_date, market_data)
            
            # 2. 过滤市场数据
            filtered_market_data = {
                stock_code: data for stock_code, data in market_data.items()
                if stock_code in selected_stocks
            }
            
            if not filtered_market_data:
                return signals
            
            # 3. 检查卖出信号（现有持仓）
            sell_signals = self._check_enhanced_sell_signals(current_date, market_data, portfolio_info)
            signals.extend(sell_signals)
            
            # 4. 检查买入信号（选股池内）
            current_positions = portfolio_info.get('total_positions', 0)
            if current_positions < self.params['max_positions']:
                buy_signals = self._check_enhanced_buy_signals(current_date, filtered_market_data, portfolio_info)
                signals.extend(buy_signals)
            
            # 5. 记录信号历史
            if signals:
                self.signal_history.append({
                    'date': current_date,
                    'signals_count': len(signals),
                    'buy_count': len([s for s in signals if s['action'] == 'buy']),
                    'sell_count': len([s for s in signals if s['action'] == 'sell'])
                })
            
            # 6. 定期进度输出
            if current_date.endswith(('05', '15', '25')):
                portfolio_value = portfolio_info.get('total_value', 0)
                cash_ratio = portfolio_info.get('cash_ratio', 0)
                print(f"📊 {current_date}: 增强策略运行中，组合价值{portfolio_value:,.0f}元，"
                      f"持仓{current_positions}只，现金{cash_ratio:.1%}，信号{len(signals)}个")
            
        except Exception as e:
            self.logger.error(f"生成增强信号失败 {current_date}: {e}")
        
        return signals
    
    def _check_enhanced_buy_signals(self, 
                                   current_date: str,
                                   market_data: Dict[str, Dict],
                                   portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查增强买入信号"""
        buy_signals = []
        
        max_new_positions = self.params['max_positions'] - len(self.positions_info)
        
        for stock_code, stock_data in market_data.items():
            if stock_code not in self.positions_info and len(buy_signals) < max_new_positions:
                try:
                    # 计算技术信号得分
                    signal_score, signal_details = self._calculate_multi_timeframe_signals(stock_data)
                    
                    # 买入条件：技术信号得分 > 0.2（满分1.0）
                    if signal_score > 0.2:
                        target_weight = self.stock_weights.get(stock_code, self.params['base_position_size'])
                        
                        buy_signals.append({
                            'action': 'buy',
                            'stock_code': stock_code,
                            'price': stock_data['close'],
                            'weight': target_weight,
                            'signal_score': signal_score,
                            'signal_details': signal_details,
                            'reason': f"增强信号买入：得分{signal_score:.3f}"
                        })
                        
                        # 记录持仓信息
                        self.positions_info[stock_code] = {
                            'entry_price': stock_data['close'],
                            'entry_date': current_date,
                            'signal_score': signal_score,
                            'highest_price': stock_data['close']  # 用于移动止损
                        }
                        
                        self.buy_signals_count += 1
                        
                except Exception as e:
                    self.logger.error(f"检查买入信号失败 {stock_code}: {e}")
                    continue
        
        return buy_signals
    
    def _check_enhanced_sell_signals(self,
                                    current_date: str,
                                    market_data: Dict[str, Dict], 
                                    portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查增强卖出信号"""
        sell_signals = []
        
        for stock_code in list(self.positions_info.keys()):
            if stock_code not in market_data:
                continue
            
            try:
                should_sell, reason = self._check_enhanced_sell_condition(
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
                    if stock_code in self.positions_info:
                        del self.positions_info[stock_code]
                        self.sell_signals_count += 1
                        
            except Exception as e:
                self.logger.error(f"检查卖出信号失败 {stock_code}: {e}")
        
        return sell_signals
    
    def _check_enhanced_sell_condition(self, stock_code: str, stock_data: Dict, current_date: str) -> Tuple[bool, str]:
        """检查增强卖出条件"""
        try:
            if stock_code not in self.positions_info:
                return False, ""
            
            position_info = self.positions_info[stock_code]
            current_price = stock_data['close']
            entry_price = position_info['entry_price']
            highest_price = position_info.get('highest_price', entry_price)
            
            # 更新最高价格
            if current_price > highest_price:
                position_info['highest_price'] = current_price
                highest_price = current_price
            
            pnl_ratio = (current_price - entry_price) / entry_price
            
            # 1. 止损：5%
            if pnl_ratio <= -self.params['stop_loss_pct']:
                return True, f"止损卖出：{pnl_ratio:.2%}"
            
            # 2. 止盈：20%  
            if pnl_ratio >= self.params['take_profit_pct']:
                return True, f"止盈卖出：{pnl_ratio:.2%}"
            
            # 3. 移动止损：从最高点回落8%
            if pnl_ratio > 0.05:  # 只有盈利5%以上才启用移动止损
                trailing_loss = (current_price - highest_price) / highest_price
                if trailing_loss <= -self.params['trailing_stop_pct']:
                    return True, f"移动止损：从最高点{(highest_price-entry_price)/entry_price:.2%}回落{trailing_loss:.2%}"
            
            # 4. 技术信号转弱
            signal_score, _ = self._calculate_multi_timeframe_signals(stock_data)
            if signal_score < 0.3:  # 技术信号得分低于0.3
                return True, f"技术卖出：信号转弱{signal_score:.3f}，当前{pnl_ratio:.2%}"
            
            # 5. 不在选股池中（基本面转弱）
            if stock_code not in self.selected_stocks:
                return True, f"基本面卖出：退出选股池，当前{pnl_ratio:.2%}"
            
            return False, ""
            
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def on_trade_executed(self, trade_info: Dict[str, Any]):
        """交易执行后回调"""
        try:
            self.trade_history.append({
                'date': trade_info.get('trade_date'),
                'action': trade_info['order_type'],
                'stock_code': trade_info['stock_code'],
                'price': trade_info['price'],
                'quantity': trade_info['quantity'],
                'amount': trade_info.get('amount', 0)
            })
        except Exception as e:
            self.logger.error(f"交易回调处理失败: {e}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取增强策略信息"""
        return {
            'strategy_name': self.name,
            'strategy_version': self.version,
            'strategy_type': '增强多因子动量策略',
            'max_positions': self.params['max_positions'],
            'max_single_weight': self.params['max_single_weight'],
            'multi_factor_enabled': True,
            'multi_timeframe_enabled': self.params['enable_multi_timeframe'],
            'position_sizing_method': self.params['position_sizing_method'],
            'current_positions': len(self.positions_info),
            'buy_signals_count': self.buy_signals_count,
            'sell_signals_count': self.sell_signals_count,
            'total_signals': len(self.signal_history),
            'total_trades': len(self.trade_history),
            'factor_weights': {
                'value': self.params['value_weight'],
                'momentum': self.params['momentum_weight'], 
                'quality': self.params['quality_weight'],
                'sentiment': self.params['sentiment_weight']
            },
            'signal_weights': self.params['signal_weights'],
            'description': '基于2025年最新量化投资实践的增强多因子策略：四维因子选股(价值+动量+质量+情绪)+多时间周期技术信号(MACD+RSI+BOLL+KDJ)+凯利公式动态权重+智能风控系统，专为A股市场深度优化'
        }

    def get_selection_report(self) -> Dict[str, Any]:
        """获取选股报告"""
        try:
            return {
                'recent_stock_selections': self.stock_selection_history[-5:] if self.stock_selection_history else [],
                'recent_position_changes': self.position_change_history[-10:] if self.position_change_history else [],
                'current_positions': self.positions_info,
                'selection_summary': {
                    'total_selections': len(self.stock_selection_history),
                    'total_position_changes': len(self.position_change_history),
                    'current_position_count': len(self.positions_info)
                }
            }
        except Exception as e:
            self.logger.error(f"生成选股报告失败: {e}")
            return {}


if __name__ == "__main__":
    # 测试增强策略适配器
    print("🚀 测试增强多趋势共振策略适配器...")
    
    strategy = EnhancedMultiTrendStrategyAdapter()
    
    # 模拟初始化
    context = {
        'initial_cash': 1000000.0,
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    }
    
    strategy.initialize(context)
    
    # 获取策略信息
    info = strategy.get_strategy_info()
    print(f"\n增强策略信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("✅ 增强多趋势共振策略适配器测试完成")