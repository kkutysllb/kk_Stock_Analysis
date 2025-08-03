#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
好奇布偶猫BOLL择时策略 - Backtrader实现
基于布林带技术指标的小市值股票择时策略，严格按照策略文档实现
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import backtrader as bt

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtrader_strategies.strategies.enhanced_base_strategy import EnhancedBaseStrategy


class CuriousRagdollBollStrategy(EnhancedBaseStrategy):
    """
    好奇布偶猫BOLL择时策略
    
    策略特点：
    1. 基于布林带技术指标进行择时
    2. 专注于中证500成分股中的小市值股票  
    3. 捕捉超跌反弹和趋势延续机会
    4. 严格的止损机制保护资金安全
    """
    
    params = (
        # 基础持仓参数 - 按文档设计
        ('max_positions', 10),                   # 最多10只股票
        ('max_single_weight', 0.20),             # 单股最大20%仓位
        ('max_position_value', 200000),          # 单股最大20万元
        ('rebalance_frequency', 1),              # 每日检查调仓
        
        # 布林带参数 - 按文档配置
        ('boll_period', 20),                     # 布林带周期20日
        ('boll_std', 2.0),                       # 标准差倍数2.0
        
        # 技术指标参数
        ('lookback_period', 10),                 # 止损回看期10日
        ('volume_threshold', 1000000),           # 最小成交量要求
        
        # 风险控制参数 - 按文档设计
        ('stop_loss_pct', -0.10),                # 止损10%
        ('take_profit_pct', 0.15),               # 止盈15%
        ('profit_retracement_pct', 0.05),        # 盈利回撤5%
        
        # 选股参数 - 按文档要求
        ('stock_pool_size', 50),                 # 股票池大小50只
        ('min_market_cap', 10e8),                # 最小市值10亿
        ('max_market_cap', 500e8),               # 最大市值500亿
    )
    
    def __init__(self):
        super().__init__()
        
        # 策略状态
        self.positions_info = {}  # 持仓信息
        self.rebalance_counter = 0
        self.last_rebalance_date = None
        
        # 技术指标缓存
        self.boll_cache = {}
        self.price_cache = {}
        
        print(f"🎯 好奇布偶猫BOLL择时策略初始化完成！")
        print(f"   布林带周期: {self.p.boll_period}日")
        print(f"   标准差倍数: {self.p.boll_std}")
        print(f"   最大持仓: {self.p.max_positions}只")
        print(f"   单股最大仓位: {self.p.max_single_weight:.1%}")
    
    def start(self):
        """策略开始时调用"""
        super().start()
        print(f"🚀 好奇布偶猫BOLL择时策略开始运行！数据源数量: {len(self.datas)}")
    
    def next(self):
        """策略主逻辑 - 每个交易日调用"""
        try:
            current_date = self.datetime.date()
            
            # 检查是否需要调仓
            if self.should_rebalance(current_date):
                self.rebalance_portfolio(current_date)
                self.last_rebalance_date = current_date
            
            # 更新持仓信息
            self.update_positions_info()
            
        except Exception as e:
            self.log(f"策略执行错误: {e}")
    
    def should_rebalance(self, current_date) -> bool:
        """判断是否需要调仓"""
        # 每日检查
        if self.p.rebalance_frequency == 1:
            return True
        
        # 按频率检查
        if self.last_rebalance_date is None:
            return True
        
        days_since_last = (current_date - self.last_rebalance_date).days
        return days_since_last >= self.p.rebalance_frequency
    
    def rebalance_portfolio(self, current_date):
        """组合调仓逻辑"""
        try:
            self.log(f"🔄 开始调仓 - {current_date}")
            
            # 1. 检查卖出信号
            self.check_sell_signals()
            
            # 2. 获取候选股票
            candidate_stocks = self.get_candidate_stocks()
            
            # 3. 检查买入信号
            self.check_buy_signals(candidate_stocks)
            
            # 4. 输出当前持仓状态
            self.log_portfolio_status()
            
        except Exception as e:
            self.log(f"调仓失败: {e}")
    
    def get_candidate_stocks(self) -> List[str]:
        """获取候选股票池 - 中证500成分股中的小市值股票"""
        try:
            candidate_stocks = []
            
            # 从当前数据源中筛选合格股票
            for data in self.datas:
                stock_code = getattr(data, '_name', '')
                if stock_code and self.is_stock_qualified(stock_code):
                    candidate_stocks.append(stock_code)
            
            # 按市值排序，选择小市值股票
            qualified_stocks = self.sort_by_market_cap(candidate_stocks)
            
            return qualified_stocks[:self.p.stock_pool_size]
            
        except Exception as e:
            self.log(f"获取候选股票失败: {e}")
            return []
    
    def is_stock_qualified(self, stock_code: str) -> bool:
        """基础股票过滤 - 按文档过滤条件"""
        try:
            # 获取基础数据
            current_price = self.get_price_data(stock_code, 'close')
            volume = self.get_price_data(stock_code, 'volume')
            amount = self.get_price_data(stock_code, 'amount')
            
            # 基础数据完整性检查
            if not all([current_price, volume, amount]):
                return False
            
            # 过滤条件 - 按文档要求
            return (current_price > 0 and 
                    volume >= self.p.volume_threshold and  # 最小成交量
                    amount >= 5000000 and                  # 最小成交额500万
                    'ST' not in stock_code and             # 排除ST股票
                    current_price >= 3.0 and               # 最低价格3元
                    not self.is_limit_up_down(stock_code))  # 排除涨跌停
                    
        except:
            return False
    
    def sort_by_market_cap(self, stock_codes: List[str]) -> List[str]:
        """按市值排序，优先选择小市值股票"""
        try:
            market_cap_data = []
            
            for stock_code in stock_codes:
                try:
                    # 获取流通市值数据
                    circ_mv = self.get_indicator(stock_code, 'circ_mv')
                    if circ_mv and self.p.min_market_cap <= circ_mv <= self.p.max_market_cap:
                        market_cap_data.append((stock_code, circ_mv))
                except:
                    continue
            
            # 按市值升序排序（小市值优先）
            market_cap_data.sort(key=lambda x: x[1])
            
            return [stock_code for stock_code, _ in market_cap_data]
            
        except Exception as e:
            self.log(f"市值排序失败: {e}")
            return stock_codes
    
    def is_limit_up_down(self, stock_code: str) -> bool:
        """检查是否涨跌停"""
        try:
            current_price = self.get_price_data(stock_code, 'close')
            prev_close = self.get_price_data(stock_code, 'pre_close')
            
            if not all([current_price, prev_close]):
                return False
            
            # 计算涨跌幅
            pct_change = (current_price - prev_close) / prev_close
            
            # 判断是否接近涨跌停（±9.8%）
            return abs(pct_change) >= 0.098
            
        except:
            return False
    
    def check_sell_signals(self):
        """检查卖出信号 - 按文档三个卖出条件"""
        try:
            stocks_to_sell = []
            
            for stock_code in list(self.positions_info.keys()):
                should_sell, reason = self.should_sell_stock(stock_code)
                if should_sell:
                    stocks_to_sell.append((stock_code, reason))
            
            # 执行卖出
            for stock_code, reason in stocks_to_sell:
                self.sell_stock(stock_code, reason)
                
        except Exception as e:
            self.log(f"检查卖出信号失败: {e}")
    
    def should_sell_stock(self, stock_code: str) -> Tuple[bool, str]:
        """判断是否应该卖出股票 - 严格按照文档三个卖出条件"""
        try:
            if stock_code not in self.positions_info:
                return False, ""
            
            position_info = self.positions_info[stock_code]
            current_price = self.get_price_data(stock_code, 'close')
            entry_price = position_info['entry_price']
            
            if not current_price:
                return False, ""
            
            # 1. 止损保护：价格跌破止损位（前期低点）
            stop_loss_price = position_info.get('stop_loss_price', entry_price * (1 + self.p.stop_loss_pct))
            if current_price <= stop_loss_price * 1.01:  # 1%容错
                return True, f"止损卖出(价格{current_price:.2f} <= 止损位{stop_loss_price:.2f})"
            
            # 2. 布林带上轨回落
            if self.check_upper_band_reversal(stock_code):
                return True, "布林带上轨回落卖出"
            
            # 3. 盈利回撤：盈利超过15%后回撤5%
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct > self.p.take_profit_pct:  # 盈利超过15%
                if self.check_profit_retracement(stock_code, position_info):
                    return True, f"盈利回撤卖出(盈利{profit_pct:.1%}后回撤)"
            
            return False, ""
            
        except Exception as e:
            self.log(f"卖出判断失败 {stock_code}: {e}")
            return False, ""
    
    def check_upper_band_reversal(self, stock_code: str) -> bool:
        """检查布林带上轨回落"""
        try:
            # 获取布林带数据
            boll_data = self.get_bollinger_bands(stock_code)
            if not boll_data:
                return False
            
            current_price = self.get_price_data(stock_code, 'close')
            prev_price = self.get_price_data(stock_code, 'close', offset=1)
            upper_band = boll_data['upper']
            
            if not all([current_price, prev_price, upper_band]):
                return False
            
            # 前日触及上轨且当日价格回落
            return (prev_price >= upper_band * 0.95 and 
                    current_price < prev_price * 0.99)
            
        except:
            return False
    
    def check_profit_retracement(self, stock_code: str, position_info: dict) -> bool:
        """检查盈利回撤"""
        try:
            current_price = self.get_price_data(stock_code, 'close')
            
            # 获取近期最高价
            recent_high = self.get_recent_high(stock_code, 5)
            
            if not all([current_price, recent_high]):
                return False
            
            # 检查是否从高点回撤超过5%
            retracement = (recent_high - current_price) / recent_high
            return retracement >= self.p.profit_retracement_pct
            
        except:
            return False
    
    def get_recent_high(self, stock_code: str, days: int) -> Optional[float]:
        """获取近期最高价"""
        try:
            highs = []
            for i in range(days):
                high_price = self.get_price_data(stock_code, 'high', offset=i)
                if high_price:
                    highs.append(high_price)
            
            return max(highs) if highs else None
            
        except:
            return None
    
    def check_buy_signals(self, candidate_stocks: List[str]):
        """检查买入信号 - 按文档四个买入条件"""
        try:
            current_positions = len(self.positions_info)
            available_slots = self.p.max_positions - current_positions
            
            if available_slots <= 0:
                return
            
            buy_candidates = []
            
            for stock_code in candidate_stocks:
                if stock_code in self.positions_info:
                    continue  # 已持仓
                
                if self.should_buy_stock(stock_code):
                    buy_score = self.calculate_buy_score(stock_code)
                    buy_candidates.append((stock_code, buy_score))
            
            # 按买入得分排序，选择最优股票
            buy_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # 执行买入
            for i, (stock_code, score) in enumerate(buy_candidates[:available_slots]):
                self.buy_stock(stock_code, score)
                
        except Exception as e:
            self.log(f"检查买入信号失败: {e}")
    
    def should_buy_stock(self, stock_code: str) -> bool:
        """判断是否应该买入股票 - 严格按照文档四个买入条件"""
        try:
            # 基础条件检查
            if not self.is_stock_qualified(stock_code):
                return False
            
            # 获取价格数据
            current_price = self.get_price_data(stock_code, 'close')
            prev_price = self.get_price_data(stock_code, 'close', offset=1)
            
            if not all([current_price, prev_price]):
                return False
            
            # 获取布林带数据
            boll_data = self.get_bollinger_bands(stock_code)
            if not boll_data:
                return False
            
            lower_band = boll_data['lower']
            
            # 买入条件 - 按文档四个条件：
            # 1. 前一日价格跌破布林带下轨
            condition1 = prev_price < lower_band
            
            # 2. 当前价格高于前一日价格（反弹确认）
            condition2 = current_price > prev_price
            
            # 3. 当前价格高于前期10日最低价（强度验证）
            prev_low = self.get_recent_low(stock_code, self.p.lookback_period)
            condition3 = prev_low is None or current_price > prev_low
            
            # 4. 资金控制：单只股票持仓不超过20万元
            condition4 = len(self.positions_info) < self.p.max_positions
            
            return all([condition1, condition2, condition3, condition4])
            
        except Exception as e:
            self.log(f"买入判断失败 {stock_code}: {e}")
            return False
    
    def get_recent_low(self, stock_code: str, days: int) -> Optional[float]:
        """获取近期最低价"""
        try:
            lows = []
            for i in range(1, days + 1):  # 排除当日
                low_price = self.get_price_data(stock_code, 'low', offset=i)
                if low_price:
                    lows.append(low_price)
            
            return min(lows) if lows else None
            
        except:
            return None
    
    def get_bollinger_bands(self, stock_code: str) -> Optional[Dict[str, float]]:
        """获取布林带数据"""
        try:
            # 尝试从数据库获取预计算的布林带数据
            upper_band = self.get_indicator(stock_code, 'boll_upper')
            middle_band = self.get_indicator(stock_code, 'boll_mid')
            lower_band = self.get_indicator(stock_code, 'boll_lower')
            
            if all([upper_band, middle_band, lower_band]):
                return {
                    'upper': upper_band,
                    'middle': middle_band,
                    'lower': lower_band
                }
            
            # 如果没有预计算数据，则实时计算
            return self.calculate_bollinger_bands(stock_code)
            
        except Exception as e:
            self.log(f"获取布林带数据失败 {stock_code}: {e}")
            return None
    
    def calculate_bollinger_bands(self, stock_code: str) -> Optional[Dict[str, float]]:
        """实时计算布林带"""
        try:
            # 获取历史价格数据
            prices = []
            for i in range(self.p.boll_period):
                price = self.get_price_data(stock_code, 'close', offset=i)
                if price:
                    prices.append(price)
            
            if len(prices) < self.p.boll_period:
                return None
            
            # 计算布林带
            prices = np.array(prices[::-1])  # 反转为时间正序
            ma = np.mean(prices)
            std = np.std(prices)
            
            upper_band = ma + self.p.boll_std * std
            lower_band = ma - self.p.boll_std * std
            
            return {
                'upper': upper_band,
                'middle': ma,
                'lower': lower_band
            }
            
        except Exception as e:
            self.log(f"计算布林带失败 {stock_code}: {e}")
            return None
    
    def calculate_buy_score(self, stock_code: str) -> float:
        """计算买入得分 - 用于选股排序"""
        try:
            score = 0.0
            
            # 1. 布林带位置得分（0-3分）
            boll_data = self.get_bollinger_bands(stock_code)
            if boll_data:
                current_price = self.get_price_data(stock_code, 'close')
                if current_price:
                    # 价格越接近下轨得分越高
                    band_width = boll_data['upper'] - boll_data['lower']
                    price_position = (current_price - boll_data['lower']) / band_width
                    score += (1 - price_position) * 3  # 越接近下轨得分越高
            
            # 2. 成交量得分（0-2分）
            if self.check_volume_surge(stock_code):
                score += 2
            
            # 3. 市值得分（0-2分）- 小市值优先
            circ_mv = self.get_indicator(stock_code, 'circ_mv')
            if circ_mv:
                if circ_mv <= 50e8:  # 50亿以下
                    score += 2
                elif circ_mv <= 100e8:  # 100亿以下
                    score += 1
            
            # 4. 技术强度得分（0-1分）
            current_price = self.get_price_data(stock_code, 'close')
            recent_low = self.get_recent_low(stock_code, self.p.lookback_period)
            if current_price and recent_low:
                strength = (current_price - recent_low) / recent_low
                if strength > 0.02:  # 超过前期低点2%以上
                    score += 1
            
            return min(score, 8.0)  # 最高8分
            
        except Exception as e:
            self.log(f"计算买入得分失败 {stock_code}: {e}")
            return 0.0
    
    def check_volume_surge(self, stock_code: str) -> bool:
        """检查成交量放大"""
        try:
            current_volume = self.get_price_data(stock_code, 'volume')
            
            # 计算近5日平均成交量
            volumes = []
            for i in range(1, 6):
                vol = self.get_price_data(stock_code, 'volume', offset=i)
                if vol:
                    volumes.append(vol)
            
            if not volumes or not current_volume:
                return True  # 无法判断时默认通过
            
            avg_volume = sum(volumes) / len(volumes)
            
            # 当日成交量是否放大20%以上
            return current_volume > avg_volume * 1.2
            
        except:
            return True
    
    def buy_stock(self, stock_code: str, score: float):
        """买入股票"""
        try:
            current_price = self.get_price_data(stock_code, 'close')
            if not current_price:
                return
            
            # 计算买入金额
            portfolio_value = self.broker.getvalue()
            max_position_value = min(
                portfolio_value * self.p.max_single_weight,
                self.p.max_position_value
            )
            
            # 计算买入股数（手数）
            shares = int(max_position_value / current_price / 100) * 100
            
            if shares >= 100:  # 至少1手
                # 执行买入订单
                data = self.get_data_by_name(stock_code)
                if data:
                    order = self.buy(data=data, size=shares)
                    
                    if order:
                        # 记录持仓信息
                        stop_loss_price = self.get_recent_low(stock_code, self.p.lookback_period)
                        if not stop_loss_price:
                            stop_loss_price = current_price * (1 + self.p.stop_loss_pct)
                        
                        self.positions_info[stock_code] = {
                            'entry_price': current_price,
                            'entry_date': self.datetime.date(),
                            'shares': shares,
                            'buy_score': score,
                            'stop_loss_price': stop_loss_price,
                            'order_id': order.ref
                        }
                        
                        self.log(f"🟢 买入 {stock_code}: 价格{current_price:.2f}, 股数{shares}, 得分{score:.1f}")
                
        except Exception as e:
            self.log(f"买入失败 {stock_code}: {e}")
    
    def sell_stock(self, stock_code: str, reason: str):
        """卖出股票"""
        try:
            if stock_code not in self.positions_info:
                return
            
            position_info = self.positions_info[stock_code]
            current_price = self.get_price_data(stock_code, 'close')
            
            if not current_price:
                return
            
            # 执行卖出订单
            data = self.get_data_by_name(stock_code)
            if data:
                shares = position_info['shares']
                order = self.sell(data=data, size=shares)
                
                if order:
                    # 计算盈亏
                    entry_price = position_info['entry_price']
                    pnl_pct = (current_price - entry_price) / entry_price
                    
                    self.log(f"🔴 卖出 {stock_code}: 价格{current_price:.2f}, 盈亏{pnl_pct:.1%}, 原因:{reason}")
                    
                    # 移除持仓记录
                    del self.positions_info[stock_code]
                
        except Exception as e:
            self.log(f"卖出失败 {stock_code}: {e}")
    
    def update_positions_info(self):
        """更新持仓信息"""
        try:
            for stock_code in list(self.positions_info.keys()):
                position_info = self.positions_info[stock_code]
                current_price = self.get_price_data(stock_code, 'close')
                
                if current_price:
                    # 更新持仓天数
                    holding_days = (self.datetime.date() - position_info['entry_date']).days
                    position_info['holding_days'] = holding_days
                    position_info['current_price'] = current_price
                    
                    # 更新盈亏
                    entry_price = position_info['entry_price']
                    position_info['pnl_pct'] = (current_price - entry_price) / entry_price
                    
        except Exception as e:
            self.log(f"更新持仓信息失败: {e}")
    
    def log_portfolio_status(self):
        """输出组合状态"""
        try:
            current_positions = len(self.positions_info)
            portfolio_value = self.broker.getvalue()
            
            self.log(f"📊 组合状态: 持仓{current_positions}/{self.p.max_positions}, 总价值{portfolio_value:,.0f}")
            
            if self.positions_info:
                for stock_code, info in self.positions_info.items():
                    pnl_pct = info.get('pnl_pct', 0)
                    holding_days = info.get('holding_days', 0)
                    self.log(f"   {stock_code}: 盈亏{pnl_pct:.1%}, 持仓{holding_days}天")
                    
        except Exception as e:
            self.log(f"输出组合状态失败: {e}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        current_positions = len(self.positions_info)
        
        info = {
            'strategy_name': '好奇布偶猫BOLL择时策略',
            'strategy_type': 'BOLL技术择时策略',
            'total_positions': current_positions,
            'max_positions': self.p.max_positions,
            'portfolio_value': self.broker.getvalue(),
            'boll_period': self.p.boll_period,
            'boll_std': self.p.boll_std,
            'stock_pool_size': self.p.stock_pool_size,
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
                    'holding_days': pos_info.get('holding_days', 0),
                    'buy_score': pos_info.get('buy_score', 0)
                })
        
        return info


if __name__ == "__main__":
    print("🎯 好奇布偶猫BOLL择时策略模块")
    print("   基于布林带技术指标的小市值股票择时策略")
    print("   专注于中证500成分股中的小市值股票")
    print("   捕捉超跌反弹和趋势延续机会")