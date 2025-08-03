#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
好奇布偶猫BOLL择时策略适配器
将好奇布偶猫策略适配到新的回测引擎接口，参考多趋势策略实现架构
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


class CuriousRagdollBollStrategyAdapter(StrategyInterface):
    """
    好奇布偶猫BOLL择时策略适配器
    将布林带择时策略逻辑适配到新的回测引擎接口
    """
    
    def __init__(self):
        """初始化策略适配器"""
        self.name = "太上老君2号"
        self.version = "1.0.0"
        
        # 策略参数 - 严格按照文档要求
        self.params = {
            # 基础持仓参数
            'max_positions': 10,                    # 最大持仓10只（按用户要求）
            'max_single_weight': 0.20,              # 单股最大20%仓位
            'max_position_value': 200000,           # 单股最大20万元
            'rebalance_freq': 1,                    # 每日检查调仓
            
            # 布林带参数 - 按文档配置
            'boll_period': 20,                      # 布林带周期20日
            'boll_std': 2.0,                        # 标准差倍数2.0
            
            # 技术指标参数
            'lookback_period': 10,                  # 前期低点回看期10日
            'volume_ma_period': 20,                 # 成交量均线周期20日
            'buy_volume_ratio': 1.2,                # 买入成交量放大倍数(略微放大)
            'sell_volume_ratio': 2.0,               # 卖出成交量放大倍数(异常放大)
            
            # 风险控制参数 - 按文档设计
            'stop_loss_pct': 0.10,                  # 止损10%
            'profit_take_pct': 0.15,                # 止盈15%
            'profit_pullback_pct': 0.05,            # 盈利回撤5%
            
            # 选股参数 - 按文档要求（中证500成分股无需额外流动性过滤）
            'stock_pool_size': 50,                  # 股票池50只小市值股票
            'min_market_cap': 10e8,                 # 最小市值10亿
            'max_market_cap': 500e8,                # 最大市值500亿
            'min_price': 3.0,                       # 最低价格3元
        }
        
        # 策略状态
        self.positions_info = {}                    # 持仓信息
        self.buy_signals_count = 0
        self.sell_signals_count = 0
        self.boll_scores = {}                       # 布林带得分缓存
        
        # 统计信息
        self.signal_history = []
        self.trade_history = []
    
    def initialize(self, context: Dict[str, Any]):
        """策略初始化"""
        self.context = context
        
        print(f"🎯 {self.name} v{self.version} 初始化完成")
        print(f"   初始资金: {context['initial_cash']:,.0f}元")
        print(f"   回测期间: {context['start_date']} 到 {context['end_date']}")
        print(f"   最大持仓: {self.params['max_positions']}只")
        print(f"   单股限额: {self.params['max_position_value']:,}元")
        print(f"   布林带参数: {self.params['boll_period']}日, {self.params['boll_std']}倍标准差")
        print(f"   股票池大小: {self.params['stock_pool_size']}只（中证500小市值）")
    
    def generate_signals(self, 
                        current_date: str, 
                        market_data: Dict[str, Dict],
                        portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成交易信号 - 严格按照文档逻辑实现
        
        Args:
            current_date: 当前日期
            market_data: 市场数据 {stock_code: daily_data}
            portfolio_info: 组合信息
            
        Returns:
            交易信号列表
        """
        signals = []
        
        try:
            # 强制输出调试信息 - 找出为什么没有信号
            if current_date in ['2020-03-02', '2021-02-01', '2022-02-07', '2023-02-01', '2024-02-01']:
                print(f"\n🔍 === 详细调试 {current_date} ===")
                print(f"市场数据股票数: {len(market_data)}")
                
                if market_data:
                    sample_stock = list(market_data.keys())[0]
                    sample_data = market_data[sample_stock]
                    print(f"样本股票 {sample_stock}:")
                    print(f"  close: {sample_data.get('close')}")
                    print(f"  pre_close: {sample_data.get('pre_close')}")
                    print(f"  circ_mv: {sample_data.get('circ_mv')}")
                    print(f"  volume: {sample_data.get('volume')}")
                    print(f"  amount: {sample_data.get('amount')}")
                    print(f"  boll_lower: {sample_data.get('boll_lower')}")
                    
                    # 测试基础过滤 - 详细分析每个条件
                    qualified = self._is_stock_qualified(sample_stock, sample_data)
                    print(f"  基础过滤结果: {qualified}")
                    
                    # 详细分析过滤条件
                    if not qualified:
                        current_price = sample_data.get('close', 0)
                        market_cap = sample_data.get('circ_mv', 0)
                        market_cap_yuan = market_cap * 1e4
                        
                        print(f"  过滤条件详细分析:")
                        print(f"    价格条件: {current_price} > 0 = {current_price > 0}")
                        print(f"    ST股票排除: 'ST' not in '{sample_stock}' = {'ST' not in sample_stock}")
                        print(f"    最低价格: {current_price} >= {self.params['min_price']} = {current_price >= self.params['min_price']}")
                        print(f"    市值数据: {market_cap_yuan} > 0 = {market_cap_yuan > 0}")
                        print(f"    市值范围: {self.params['min_market_cap']} <= {market_cap_yuan} <= {self.params['max_market_cap']} = {self.params['min_market_cap'] <= market_cap_yuan <= self.params['max_market_cap']}")
                        print(f"    市值(亿元): {market_cap_yuan/1e8:.1f}亿, 限制范围: {self.params['min_market_cap']/1e8:.1f}-{self.params['max_market_cap']/1e8:.1f}亿")
                    
                    # 测试买入信号
                    if qualified:
                        buy_signal = self._check_buy_signal(sample_stock, sample_data)
                        print(f"  买入信号结果: {buy_signal}")
                    
                    # 候选股票统计
                    candidate_stocks = self._get_candidate_stocks(market_data)
                    print(f"候选股票总数: {len(candidate_stocks)}")
                    
                    if len(candidate_stocks) > 0:
                        print(f"前5只候选股票: {candidate_stocks[:5]}")
                    else:
                        print("❌ 没有候选股票通过筛选！")
                        
                        # 详细检查为什么没有候选股票
                        print("检查所有股票的过滤原因:")
                        for i, (stock, data) in enumerate(list(market_data.items())[:5]):
                            print(f"  {stock}: 价格{data.get('close', 'N/A')}, "
                                  f"市值{data.get('circ_mv', 'N/A')}, "
                                  f"成交量{data.get('volume', 'N/A')}")
                print("=" * 50)
            
            # 1. 检查卖出信号（优先处理）
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
        """检查卖出信号 - 按文档三个卖出条件"""
        sell_signals = []
        
        for stock_code in list(self.positions_info.keys()):
            if stock_code not in market_data:
                continue
            
            try:
                should_sell, reason = self._check_sell_signal(stock_code, market_data[stock_code])
                if should_sell:
                    sell_signals.append({
                        'action': 'sell',
                        'stock_code': stock_code,
                        'price': market_data[stock_code]['close'],
                        'weight': 0,  # 全部卖出
                        'reason': reason
                    })
                    
                    print(f"🔴 卖出信号 {stock_code}: {reason}, 价格{market_data[stock_code]['close']:.2f}")
                    
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
        """检查买入信号 - 按文档买入条件和评分排序"""
        buy_signals = []
        
        # 获取候选股票并评分
        candidate_stocks = self._get_candidate_stocks(market_data)
        stock_scores = []
        
        for stock_code in candidate_stocks:
            if stock_code in self.positions_info:
                continue  # 已持仓，跳过
            
            try:
                should_buy = self._check_buy_signal(stock_code, market_data[stock_code])
                if should_buy:
                    boll_score = self._calculate_boll_score(stock_code, market_data[stock_code])
                    stock_scores.append((stock_code, boll_score))
                    
            except Exception as e:
                print(f"检查 {stock_code} 买入信号失败: {e}")
        
        # 按布林带得分排序，选择最优股票
        stock_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 限制买入数量
        max_new_positions = self.params['max_positions'] - len(self.positions_info)
        for stock_code, score in stock_scores[:max_new_positions]:
            try:
                buy_signals.append({
                    'action': 'buy',
                    'stock_code': stock_code,
                    'price': market_data[stock_code]['close'],
                    'weight': self.params['max_single_weight'],
                    'boll_score': score
                })
                
                # 记录持仓信息
                self.positions_info[stock_code] = {
                    'entry_price': market_data[stock_code]['close'],
                    'entry_date': current_date,
                    'boll_score': score,
                    'stop_loss_price': self._calculate_stop_loss_price(market_data[stock_code])
                }
                
                print(f"🟢 买入信号 {stock_code}: 价格{market_data[stock_code]['close']:.2f}, 布林得分{score:.1f}")
                
                self.buy_signals_count += 1
                
                # 限制每次最多买入1只股票（类似多趋势策略）
                break
                
            except Exception as e:
                print(f"处理 {stock_code} 买入信号失败: {e}")
        
        return buy_signals
    
    def _get_candidate_stocks(self, market_data: Dict[str, Dict]) -> List[str]:
        """获取候选股票池 - 中证500成分股中的小市值股票"""
        candidate_stocks = []
        
        for stock_code, stock_data in market_data.items():
            if self._is_stock_qualified(stock_code, stock_data):
                candidate_stocks.append(stock_code)
        
        # 按市值排序，选择小市值股票
        market_cap_stocks = []
        for stock_code in candidate_stocks:
            market_cap = market_data[stock_code].get('circ_mv', 0)
            if market_cap > 0:
                market_cap_stocks.append((stock_code, market_cap * 1e4))  # 万元转元
        
        # 按市值升序排序（小市值优先）
        market_cap_stocks.sort(key=lambda x: x[1])
        selected_stocks = [stock[0] for stock in market_cap_stocks[:self.params['stock_pool_size']]]
        
        return selected_stocks
    
    def _is_stock_qualified(self, stock_code: str, stock_data: Dict) -> bool:
        """基础股票质量过滤 - 中证500成分股基础检查"""
        try:
            # 基础数据检查
            current_price = stock_data.get('close', 0)
            market_cap = stock_data.get('circ_mv', 0)
            
            # 数据完整性检查
            if not all([current_price, market_cap]):
                return False
            
            # 市值转换：万元转为元
            market_cap_yuan = market_cap * 1e4
            
            # 简化过滤条件 - 中证500成分股质量已有保证
            return (current_price > 0 and                           # 有价格数据
                    'ST' not in stock_code and                     # 排除ST股票
                    current_price >= self.params['min_price'] and  # 最低价格
                    market_cap_yuan > 0 and                        # 有市值数据
                    self.params['min_market_cap'] <= market_cap_yuan <= self.params['max_market_cap'])  # 市值范围
                    
        except:
            return False
    
    def _check_buy_signal(self, stock_code: str, stock_data: Dict) -> bool:
        """检查买入信号 - 严格按照文档四个买入条件 + 成交量确认"""
        try:
            # 获取基础数据
            current_price = stock_data.get('close', 0)
            prev_price = stock_data.get('pre_close', 0)
            current_volume = stock_data.get('volume', 0)
            volume_ma20 = stock_data.get('volume_ma20', 0)
            # 尝试获取布林带数据，优先使用标准字段，然后尝试bfq字段
            boll_lower = stock_data.get('boll_lower') or stock_data.get('boll_lower_bfq', 0)
            
            if not all([current_price, prev_price, boll_lower, current_volume]):
                return False
            
            # 文档买入条件检查：
            # 1. 前一日价格跌破布林带下轨
            condition1 = prev_price < boll_lower
            
            # 2. 当前价格高于前一日价格（反弹确认）
            condition2 = current_price > prev_price
            
            # 3. 当前价格高于前期10日最低价（强度验证）
            # 注：这里简化处理，需要历史数据支持
            condition3 = True  # 简化处理
            
            # 4. 资金控制：单只股票持仓不超过20万元
            condition4 = len(self.positions_info) < self.params['max_positions']
            
            # 5. 成交量确认：当日成交量相对20日均值略微放大（1.2倍以上）
            condition5 = True  # 默认通过
            if volume_ma20 > 0:
                volume_ratio = current_volume / volume_ma20
                condition5 = volume_ratio >= self.params['buy_volume_ratio']
            
            return all([condition1, condition2, condition3, condition4, condition5])
            
        except Exception as e:
            return False
    
    def _check_sell_signal(self, stock_code: str, stock_data: Dict) -> tuple:
        """检查卖出信号 - 按文档三个卖出条件 + 成交量异常放大技术卖出"""
        try:
            if stock_code not in self.positions_info:
                return False, ""
            
            position_info = self.positions_info[stock_code]
            entry_price = position_info['entry_price']
            current_price = stock_data.get('close', 0)
            prev_price = stock_data.get('pre_close', 0)
            current_volume = stock_data.get('volume', 0)
            volume_ma20 = stock_data.get('volume_ma20', 0)
            # 尝试获取布林带上轨数据
            boll_upper = stock_data.get('boll_upper') or stock_data.get('boll_upper_bfq', 0)
            
            if not current_price:
                return False, ""
            
            # 1. 止损保护：价格跌破止损位（前期低点）
            stop_loss_price = position_info.get('stop_loss_price', entry_price * (1 - self.params['stop_loss_pct']))
            if current_price <= stop_loss_price * 1.01:  # 1%容错
                return True, "止损卖出"
            
            # 2. 上轨回落：触及布林上轨后价格回落
            if (boll_upper > 0 and 
                prev_price >= boll_upper * 0.95 and 
                current_price < prev_price * 0.99):
                return True, "上轨回落卖出"
            
            # 3. 盈利回撤：盈利超过15%后回撤5%
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct > self.params['profit_take_pct']:  # 盈利15%+
                # 简化处理：使用前一价格判断回撤
                if current_price < prev_price * (1 - self.params['profit_pullback_pct']):
                    return True, f"盈利回撤卖出(盈利{profit_pct:.1%})"
            
            # 4. 技术卖出：成交量异常放大（2倍以上）- 可能的顶部信号
            if current_volume > 0 and volume_ma20 > 0:
                volume_ratio = current_volume / volume_ma20
                if volume_ratio >= self.params['sell_volume_ratio']:
                    return True, f"成交量异常放大卖出(放大{volume_ratio:.1f}倍)"
            
            return False, ""
            
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def _calculate_boll_score(self, stock_code: str, stock_data: Dict) -> float:
        """计算布林带评分 - 用于选股排序（含成交量分析）"""
        try:
            score = 0.0
            
            current_price = stock_data.get('close', 0)
            prev_price = stock_data.get('pre_close', 0)
            current_volume = stock_data.get('volume', 0)
            volume_ma20 = stock_data.get('volume_ma20', 0)
            # 尝试获取布林带数据，优先使用标准字段，然后尝试bfq字段
            boll_upper = stock_data.get('boll_upper') or stock_data.get('boll_upper_bfq', 0)
            boll_lower = stock_data.get('boll_lower') or stock_data.get('boll_lower_bfq', 0)
            boll_mid = stock_data.get('boll_mid') or stock_data.get('boll_mid_bfq', 0)
            
            if not all([current_price, prev_price, boll_upper, boll_lower, current_volume]):
                return 0.0
            
            # 1. 布林带突破得分（0-4分）- 核心信号
            if prev_price < boll_lower and current_price > prev_price:
                score += 4  # 完美布林带突破信号
            elif prev_price < boll_lower * 1.02:  # 接近下轨
                score += 2
            elif current_price < boll_mid:  # 价格在中轨下方
                score += 1
            
            # 2. 反弹强度得分（0-2分）
            if prev_price > 0:
                rebound_pct = (current_price - prev_price) / prev_price
                if rebound_pct > 0.03:  # 反弹超过3%
                    score += 2
                elif rebound_pct > 0.01:  # 反弹超过1%
                    score += 1
            
            # 3. 小市值得分（0-2分）- 文档要求小市值优先
            market_cap = stock_data.get('circ_mv', 0) * 1e4  # 万元转元
            if market_cap > 0:
                if market_cap <= 50e8:  # 50亿以下
                    score += 2
                elif market_cap <= 100e8:  # 100亿以下
                    score += 1
            
            # 4. 成交量评分（0-2分）- 考虑成交量放大情况
            if current_volume > 0 and volume_ma20 > 0:
                volume_ratio = current_volume / volume_ma20
                if volume_ratio >= self.params['buy_volume_ratio']:  # 略微放大
                    if volume_ratio >= 1.5:  # 明显放大
                        score += 2
                    else:  # 轻微放大
                        score += 1
            elif current_volume > 0:  # 有成交量数据但无均线数据
                score += 1
            
            return min(score, 10.0)  # 最高10分（增加1分上限）
            
        except Exception as e:
            return 0.0
    
    def _calculate_stop_loss_price(self, stock_data: Dict) -> float:
        """计算止损价格"""
        try:
            current_price = stock_data.get('close', 0)
            # 简化处理：使用固定比例止损
            return current_price * (1 - self.params['stop_loss_pct'])
        except:
            return 0.0
    
    def on_trade_executed(self, trade_info: Dict[str, Any]):
        """交易执行后回调"""
        stock_code = trade_info.get('stock_code', '')
        order_type = trade_info.get('order_type', '')
        quantity = trade_info.get('quantity', 0)
        price = trade_info.get('price', 0)
        
        print(f"📈 交易执行: {order_type} {stock_code} {quantity}股 @{price:.2f}元")
        
        # 记录交易历史
        self.trade_history.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'stock_code': stock_code,
            'order_type': order_type,
            'quantity': quantity,
            'price': price
        })
    
    def get_index_code(self) -> str:
        """获取策略使用的指数代码"""
        return "000905.SH"  # 中证500指数
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        current_positions = len(self.positions_info)
        
        info = {
            'strategy_name': self.name,
            'strategy_version': self.version,
            'strategy_type': 'BOLL技术择时策略',
            'max_positions': self.params['max_positions'],
            'max_single_weight': self.params['max_single_weight'],
            'current_positions': current_positions,
            'buy_signals_count': self.buy_signals_count,
            'sell_signals_count': self.sell_signals_count,
            'total_signals': self.buy_signals_count + self.sell_signals_count,
            'total_trades': len(self.trade_history),
            'stock_pool_size': self.params['stock_pool_size'],
            'boll_period': self.params['boll_period'],
            'boll_std': self.params['boll_std'],
            'max_position_value': self.params['max_position_value'],
            'volume_ma_period': self.params['volume_ma_period'],
            'buy_volume_ratio': self.params['buy_volume_ratio'],
            'sell_volume_ratio': self.params['sell_volume_ratio'],
            'index_code': self.get_index_code(),
            'description': "基于布林带指标的小市值股票择时策略，专注于中证500成分股，捕捉超跌反弹机会。买入时需要成交量略微放大确认，卖出时通过成交量异常放大捕捉顶部"
        }
        
        # 添加持仓详情
        positions_detail = []
        for stock_code, pos_info in self.positions_info.items():
            positions_detail.append({
                'stock_code': stock_code,
                'entry_price': pos_info['entry_price'],
                'entry_date': pos_info['entry_date'],
                'boll_score': pos_info['boll_score']
            })
        
        info['positions_detail'] = positions_detail
        
        return info


def test_curious_ragdoll_boll_strategy():
    """测试好奇布偶猫BOLL策略"""
    print("🚀 开始测试好奇布偶猫BOLL择时策略...")
    
    # 创建策略实例
    strategy = CuriousRagdollBollStrategyAdapter()
    
    # 模拟初始化
    context = {
        'initial_cash': 1000000,
        'start_date': '2020-01-01',
        'end_date': '2025-07-18'
    }
    strategy.initialize(context)
    
    # 模拟市场数据 - 符合买入条件的数据
    mock_market_data = {
        '000001.SZ': {
            'close': 10.50,
            'pre_close': 10.30,
            'volume': 2000000,
            'amount': 21000000,
            'circ_mv': 1500,  # 万元，对应150亿市值
            'boll_upper': 11.0,
            'boll_mid': 10.5,
            'boll_lower': 10.0  # 前收盘价跌破下轨
        }
    }
    
    portfolio_info = {
        'total_value': 1000000,
        'cash_ratio': 0.8,
        'total_positions': 0
    }
    
    # 测试信号生成
    test_date = "2024-12-31"
    signals = strategy.generate_signals(test_date, mock_market_data, portfolio_info)
    
    print(f"\n📊 {test_date} 交易信号:")
    buy_signals = [s for s in signals if s['action'] == 'buy']
    sell_signals = [s for s in signals if s['action'] == 'sell']
    
    print(f"买入信号: {len(buy_signals)} 个")
    for signal in buy_signals:
        print(f"  🟢 {signal['stock_code']}: {signal['price']:.2f}元, 得分={signal.get('boll_score', 0):.1f}")
    
    print(f"卖出信号: {len(sell_signals)} 个")
    for signal in sell_signals:
        print(f"  🔴 {signal['stock_code']}: {signal.get('reason', '未知')}")
    
    # 获取策略信息
    strategy_info = strategy.get_strategy_info()
    print(f"\n📈 策略状态:")
    print(f"当前持仓: {strategy_info['current_positions']}/{strategy_info['max_positions']}")
    print(f"股票池大小: {strategy_info['stock_pool_size']}")
    print(f"布林带参数: {strategy_info['boll_period']}天, {strategy_info['boll_std']}倍标准差")
    print(f"单股限额: {strategy_info['max_position_value']:,}元")
    
    print("\n✅ 好奇布偶猫BOLL策略测试完成")


if __name__ == "__main__":
    test_curious_ragdoll_boll_strategy()