#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
太上老君3号策略适配器 - 小市值动量版本
基于小市值动量策略：RSI择时+多因子评分+WR指标+事件驱动调仓
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.backtest_engine import StrategyInterface
from config import Config


class TaiShang3FactorStrategyAdapter(StrategyInterface):
    """太上老君3号策略适配器 - 小市值动量版本"""
    
    def __init__(self):
        """初始化策略适配器"""
        self.name = "太上老君3号 - 小市值动量"
        self.version = "3.4.0"
        
        # 从配置文件加载参数
        self.config = Config()
        self.field_mapping = self.config.database.field_mapping
        
        # 回归现实的合理参数设置
        self.params = {
            # 基础参数 - 事件触发版设置
            'max_positions': 10,              # 最大持仓数量增至10只(增加分散度)
            'position_size': 0.08,            # 单股最大仓位8%(降低单股风险)
            'max_single_weight': 0.12,        # 单股最大权重12%(更均衡)
            'stock_pool_size': 20,            # 候选股票池增至20只(扩大选择面)
            
            # 事件触发调仓参数
            'use_event_driven': True,         # 启用事件驱动调仓
            'min_rebalance_interval': 1,      # 最小调仓间隔1天(允许更灵活调仓)
            'max_rebalance_interval': 30,     # 最大调仓间隔30天(强制检查)
            
            # 事件触发条件阈值
            'market_signal_change_trigger': True,    # RSI市场信号变化触发
            'rsi_extreme_trigger': True,             # RSI极端值触发(>85或<15)
            'individual_score_trigger': True,       # 个股评分变化触发
            'score_change_threshold': 0.25,         # 个股评分变化阈值25%(降低敏感度)
            'position_loss_trigger': True,          # 个股亏损触发
            'position_loss_threshold': 0.08,        # 个股亏损8%触发调仓(平衡设置)
            'new_opportunity_trigger': True,        # 新机会出现触发
            'opportunity_score_threshold': 0.80,    # 新机会评分阈值80%(适中门槛)
            
            # 市值筛选参数 - 严格筛选控制风险
            'min_market_cap': 120000.0,       # 最小市值120亿(提高门槛)
            'max_market_cap': 500000.0,       # 最大市值500亿(聚焦中盘)
            'min_turnover_rate': 1.2,         # 最小换手率1.2%(提高要求)
            'max_turnover_rate': 10.0,        # 最大换手率10%(降低上限)
            'min_volume_ratio': 0.8,          # 最小量比0.8%(提高要求)
            
            # RSI择时参数 - 优化设置
            'rsi_period': 20,                 # RSI周期20日(降低噪音)
            'rsi_upper': 75,                  # RSI上限75(放宽卖出条件)
            'rsi_lower': 25,                  # RSI下限25(放宽买入条件)
            'rsi_middle': 50,                 # RSI中线50(趋势判断)
            'market_timing_enabled': True,    # 启用市场择时
            'adaptive_rsi': True,             # 启用自适应RSI阈值
            
            # WR指标参数 - 标准设置
            'wr_period': 14,                  # WR周期14日
            'wr_oversold': 20,                # WR超卖线20(标准)
            'wr_overbought': 80,              # WR超买线80(标准)
            
            # 多因子评分 - 优化后平衡设置
            'technical_weight': 0.35,         # 技术因子权重35%(降低技术依赖)
            'fundamental_weight': 0.35,       # 基本面因子权重35%(增加基本面权重)
            'momentum_weight': 0.30,          # 动量因子权重30%(保持)
            'min_total_score': 0.65,          # 最低总分要求降至0.65(增加信号频率)
            
            # 仓位控制参数 - 稳健设置
            'stock_ratio_bullish': 0.80,      # 牛市股票比例80%
            'stock_ratio_bearish': 0.20,      # 熊市股票比例20%
            
            # 风险控制参数 - 严格控制
            'stop_loss': 0.06,                # 止损6%(严格)
            'take_profit': 0.15,              # 止盈15%(合理)
            'max_industry_weight': 0.20,      # 单行业最大权重20%(分散)
            'emergency_rsi_threshold': 80,    # 紧急止损RSI阈值80
            'emergency_turnover_threshold': 20, # 紧急止损换手率阈值20%
            'max_drawdown_stop': 0.12,        # 组合最大回撤止损12%
        }
        
        # 策略状态
        self.positions_info = {}              # 持仓信息
        self.market_signal = 0                # 市场信号：1买入股票，-1买入债券，0中性
        self.selected_stocks = []             # 当前选中的股票列表
        self.buy_signals_count = 0            # 买入信号计数
        self.sell_signals_count = 0           # 卖出信号计数
        self.trade_history = []               # 交易历史
        self.last_rebalance_date = None       # 上次调仓日期
        
        # 新增记录功能 - 与多趋势策略保持一致
        self.stock_selection_history = []     # 选股历史记录
        self.position_change_history = []     # 持仓变动历史
        self.daily_portfolio_snapshot = {}    # 每日投资组合快照
        
        # 因子数据缓存
        self.factor_cache = {}                # 因子数据缓存
        self.market_data_cache = {}           # 市场数据缓存
        
        # 调试模式
        self.debug_mode = True
    
    def get_index_code(self) -> str:
        """获取策略使用的指数代码"""
        return "000852.SH"  # 中证1000指数
    
    def initialize(self, context: Dict[str, Any]):
        """策略初始化"""
        self.context = context
        print(f"🎯 {self.name} v{self.version} 初始化完成")
        print("   基于小市值动量策略：RSI择时+多因子评分+WR指标+事件驱动调仓")
        print("   多因子：技术因子40% + 基本面因子30% + 动量因子30%")
        print("   择时：股票池平均RSI判断市场时机(30/70阈值)")
        print("   选股：WR<20超卖买入，WR>80超买卖出")
        print("   调仓：事件驱动智能调仓，根据市场信号和个股表现调整")
    
    def generate_signals(self, current_date: str, market_data: Dict[str, Dict], portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成交易信号 - 基于小市值动量策略（优化版）"""
        try:
            signals = []
            current_dt = datetime.strptime(current_date, '%Y-%m-%d')
            
            # 0. 组合级风险控制检查
            if self._check_portfolio_risk_stop(portfolio_info):
                # 触发组合止损，清仓所有股票
                return self._generate_emergency_liquidation_signals(current_date, market_data)
            
            # 1. 事件驱动调仓检查
            rebalance_trigger = self._check_rebalance_triggers(current_date, current_dt, market_data, portfolio_info)
            
            if not rebalance_trigger['should_rebalance']:
                # 非调仓条件下，只执行紧急止损检查
                emergency_signals = self._generate_emergency_sell_signals(current_date, market_data)
                if emergency_signals:
                    print(f"🚨 {current_date}: 紧急止损信号{len(emergency_signals)}个")
                return emergency_signals
            
            # 2. 调仓日：更新市场择时信号
            self._update_market_timing_signal(current_date, market_data)
            
            # 3. 多因子选股（根据小市值动量策略）
            selected_stocks = self._select_stocks_by_multi_factors(current_date, market_data)
            
            if not selected_stocks:
                print(f"⚠️ {current_date}: 调仓日无可选股票")
                # 无股票可选时，降低仓位
                return self._generate_defensive_signals(current_date, market_data)
            
            self.selected_stocks = selected_stocks
            
            # 4. 生成调仓信号（基于触发事件和选股结果）
            trigger_reason = rebalance_trigger['reason']
            if self.market_signal > 0:
                signals = self._generate_rebalance_signals(current_date, market_data, portfolio_info)
                print(f"📊 {current_date}: 事件触发调仓[{trigger_reason}]，市场信号={self.market_signal}, 选股{len(selected_stocks)}只, 信号{len(signals)}个")
            else:
                print(f"📊 {current_date}: 事件触发[{trigger_reason}]，市场信号看跌，保守策略")
                signals = self._generate_defensive_signals(current_date, market_data)
            
            # 更新调仓日期
            self.last_rebalance_date = current_dt
            
            # 记录选股历史和每日快照
            self._record_stock_selection(current_date, selected_stocks, market_data)
            self._record_daily_snapshot(current_date, portfolio_info)
            
            return signals
            
        except Exception as e:
            print(f"❌ 生成信号时出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _check_rebalance_triggers(self, current_date: str, current_dt: datetime, 
                                 market_data: Dict[str, Dict], portfolio_info: Dict[str, Any]) -> Dict[str, Any]:
        """事件驱动调仓检查 - 替代固定周期调仓"""
        try:
            triggers = []
            
            # 检查最小调仓间隔
            if hasattr(self, 'last_rebalance_date') and self.last_rebalance_date is not None:
                days_since_last = (current_dt - self.last_rebalance_date).days
                if days_since_last < self.params['min_rebalance_interval']:
                    return {'should_rebalance': False, 'reason': f'冷却期({days_since_last}天<{self.params["min_rebalance_interval"]}天)'}
            else:
                # 首次运行必须调仓
                return {'should_rebalance': True, 'reason': '首次调仓'}
            
            # 事件1：RSI市场信号重大变化
            if self.params['market_signal_change_trigger']:
                current_avg_rsi = self._calculate_portfolio_average_rsi(market_data)
                if current_avg_rsi:
                    if current_avg_rsi > 80 or current_avg_rsi < 20:
                        triggers.append(f'RSI极端值({current_avg_rsi:.1f})')
                    
                    # 检查RSI是否从一个极端区间跨越到另一个区间
                    prev_signal = getattr(self, '_prev_market_signal', 0)
                    if prev_signal != self.market_signal:
                        triggers.append(f'市场信号变化({prev_signal}→{self.market_signal})')
            
            # 事件2：持仓个股表现触发
            if self.params['position_loss_trigger'] and self.positions_info:
                for stock_code, pos_info in self.positions_info.items():
                    if stock_code in market_data:
                        current_price = market_data[stock_code].get('close', 0)
                        cost_price = pos_info.get('avg_price', 0)
                        
                        if current_price > 0 and cost_price > 0:
                            loss_pct = (current_price - cost_price) / cost_price
                            if loss_pct < -self.params['position_loss_threshold']:
                                triggers.append(f'个股亏损触发({stock_code}:{loss_pct:.1%})')
            
            # 事件3：新机会出现
            if self.params['new_opportunity_trigger']:
                # 快速计算候选股票的最高评分
                qualified_stocks = self._get_qualified_stocks(current_date, market_data)
                if qualified_stocks:
                    best_score = 0
                    for stock_code in qualified_stocks[:5]:  # 只检查前5只，避免计算过重
                        stock_data = market_data.get(stock_code, {})
                        score = self._calculate_comprehensive_score(stock_code, stock_data)
                        if score and score > best_score:
                            best_score = score
                    
                    if best_score > self.params['opportunity_score_threshold']:
                        # 检查这个高分股是否已持仓
                        current_holdings = set(self.positions_info.keys())
                        if not any(score > self.params['opportunity_score_threshold'] for score in [
                            self._calculate_comprehensive_score(stock, market_data.get(stock, {})) or 0 
                            for stock in current_holdings
                        ]):
                            triggers.append(f'新机会出现(评分{best_score:.2f})')
            
            # 事件4：强制调仓（防止过长时间不调仓）
            max_interval = self.params['max_rebalance_interval']
            if days_since_last >= max_interval:
                triggers.append(f'强制调仓({days_since_last}天≥{max_interval}天)')
            
            # 判断是否触发调仓
            should_rebalance = len(triggers) > 0
            reason = ', '.join(triggers) if triggers else '无触发事件'
            
            # 记录前一次的市场信号
            self._prev_market_signal = self.market_signal
            
            return {
                'should_rebalance': should_rebalance,
                'reason': reason,
                'triggers': triggers,
                'days_since_last': days_since_last
            }
            
        except Exception as e:
            print(f"事件触发检查失败: {e}")
            return {'should_rebalance': False, 'reason': f'检查失败: {e}'}
    
    def _calculate_portfolio_average_rsi(self, market_data: Dict[str, Dict]) -> Optional[float]:
        """计算组合股票池平均RSI"""
        try:
            available_stocks = list(market_data.keys())[:20]  # 限制计算范围
            rsi_values = []
            
            for stock_code in available_stocks:
                stock_data = market_data.get(stock_code, {})
                rsi = self._get_stock_rsi(stock_data)
                if rsi is not None and 0 <= rsi <= 100:
                    rsi_values.append(rsi)
            
            return np.mean(rsi_values) if rsi_values else None
        except Exception:
            return None
    
    def _update_market_timing_signal(self, current_date: str, market_data: Dict[str, Dict]):
        """更新RSI市场择时信号 - 基于股票池平均RSI"""
        try:
            # 获取可用股票池
            available_stocks = self._get_qualified_stocks(current_date, market_data)
            if not available_stocks:
                print(f"警告：无可用股票数据计算RSI")
                self.market_signal = 0
                return
            
            # 计算股票池平均RSI
            rsi_values = []
            for stock_code in available_stocks:
                stock_data = market_data.get(stock_code, {})
                rsi = self._get_stock_rsi(stock_data)
                if rsi is not None and 0 <= rsi <= 100:
                    rsi_values.append(rsi)
            
            if not rsi_values:
                print(f"警告：无有效RSI数据")
                self.market_signal = 0
                return
            
            # 平均RSI
            avg_rsi = np.mean(rsi_values)
            print(f"📊 股票池平均RSI: {avg_rsi:.1f} (样本{len(rsi_values)}只)")
            
            # 优化后的自适应市场择时判断
            upper_threshold = self.params['rsi_upper']  # 75
            lower_threshold = self.params['rsi_lower']  # 25
            middle_threshold = self.params['rsi_middle'] # 50
            
            # 计算RSI波动率，判断市场状态
            rsi_volatility = np.std(rsi_values) if len(rsi_values) > 1 else 0
            
            if avg_rsi <= lower_threshold:
                self.market_signal = 1  # 强烈超卖，买入股票
                print(f"🟢 强烈买入信号: 平均RSI={avg_rsi:.1f} <= {lower_threshold}, 波动率={rsi_volatility:.1f}")
            elif avg_rsi <= lower_threshold + 10:  # 25-35区间
                self.market_signal = 1  # 适度超卖，买入股票
                print(f"🟢 适度买入信号: 平均RSI={avg_rsi:.1f}, 波动率={rsi_volatility:.1f}")
            elif avg_rsi >= upper_threshold:
                # 根据波动率调整卖出决策
                if rsi_volatility > 15:  # 高波动环境下更谨慎
                    self.market_signal = 0  # 观望
                    print(f"🟡 高波动观望: 平均RSI={avg_rsi:.1f}, 高波动率={rsi_volatility:.1f}")
                else:
                    self.market_signal = -1  # 超买，减仓
                    print(f"🔴 超买减仓信号: 平均RSI={avg_rsi:.1f} >= {upper_threshold}")
            elif avg_rsi >= middle_threshold:
                self.market_signal = 1  # 趋势向上，保持股票
                print(f"🟢 趋势买入: 平均RSI={avg_rsi:.1f} >= {middle_threshold}")
            else:
                # 下降趋势，降低仓位
                self.market_signal = 0  # 谨慎观望
                print(f"🟡 下降趋势观望: 平均RSI={avg_rsi:.1f} < {middle_threshold}")
                
        except Exception as e:
            print(f"更新择时信号失败: {e}")
            self.market_signal = 0
    
    def _get_stock_rsi(self, stock_data: Dict) -> Optional[float]:
        """获取股票RSI指标"""
        try:
            # 优先使用RSI6，其次RSI12
            rsi_value = (stock_data.get('rsi6') or 
                        stock_data.get('rsi_bfq_6') or 
                        stock_data.get('rsi12') or 
                        stock_data.get('rsi_bfq_12'))
            
            if rsi_value and 0 <= rsi_value <= 100:
                return float(rsi_value)
            
            return None
            
        except Exception as e:
            return None
    
    def _get_qualified_stocks(self, current_date: str, market_data: Dict[str, Dict]) -> List[str]:
        """获取符合基础条件的股票池"""
        try:
            qualified_stocks = []
            
            for stock_code, stock_data in market_data.items():
                if self._is_stock_qualified_basic(stock_code, stock_data):
                    qualified_stocks.append(stock_code)
            
            print(f"基础筛选后股票数: {len(qualified_stocks)}")
            return qualified_stocks
            
        except Exception as e:
            print(f"获取股票池失败: {e}")
            return []
    
    def _select_stocks_by_multi_factors(self, current_date: str, market_data: Dict[str, Dict]) -> List[str]:
        """基于小市值动量策略多因子选股"""
        try:
            # 1. 获取符合基础条件的股票池
            qualified_stocks = self._get_qualified_stocks(current_date, market_data)
            
            if len(qualified_stocks) < 8:
                print(f"基础筛选股票太少: {len(qualified_stocks)}")
                return []
            
            # 2. 计算综合因子得分
            factor_scores = self._calculate_comprehensive_scores(qualified_stocks, current_date, market_data)
            
            if not factor_scores:
                print("无法计算因子得分")
                return []
            
            # 3. 按综合得分排序，选择前N只
            sorted_stocks = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
            
            # 4. 应用WR指标筛选（放宽条件）
            final_selected = []
            for stock_code, score in sorted_stocks:
                if len(final_selected) >= self.params['stock_pool_size']:
                    break
                
                if score >= self.params['min_total_score']:  # 最低分数要求
                    stock_data = market_data.get(stock_code, {})
                    wr_value = self._get_stock_wr(stock_data)
                    
                    # WR指标买入条件：WR < 95 (合理上限，避免过度交易)
                    if wr_value is not None:
                        if wr_value < 90:  # 严格的WR上限，控制交易质量
                            final_selected.append(stock_code)
                            wr_status = "超卖买入" if wr_value < self.params['wr_oversold'] else "正常买入"
                            print(f"✅ {stock_code}: 得分{score:.3f}, WR={wr_value:.1f} ({wr_status})")
                        else:
                            print(f"❌ {stock_code}: 得分{score:.3f}, WR={wr_value:.1f} (超买跳过)")
                    else:
                        # 无WR数据时，根据得分决定
                        if score >= self.params['min_total_score']:  # 使用参数中的最低得分
                            final_selected.append(stock_code)
                            print(f"✅ {stock_code}: 得分{score:.3f}, WR=N/A (高分选入)")
                        else:
                            print(f"⚠️ {stock_code}: 得分{score:.3f}, WR=N/A (得分不够跳过)")
            
            print(f"多因子选股完成: {len(final_selected)}只股票 (总候选{len(sorted_stocks)}只)")
            
            # 显示前5只股票详情
            if final_selected:
                top5_details = []
                for i, stock_code in enumerate(final_selected[:5]):
                    score = factor_scores.get(stock_code, 0)
                    stock_data = market_data.get(stock_code, {})
                    wr_value = self._get_stock_wr(stock_data)
                    wr_str = f"{wr_value:.1f}" if wr_value is not None else "N/A"
                    top5_details.append(f"{stock_code}(得分{score:.3f},WR={wr_str})")
                print(f"前5只股票: {', '.join(top5_details)}")
            
            return final_selected
            
        except Exception as e:
            print(f"多因子选股失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_stock_wr(self, stock_data: Dict) -> Optional[float]:
        """获取Williams %R指标"""
        try:
            # 尝试获取WR指标，按优先级顺序
            wr_value = (stock_data.get('wr1_bfq') or 
                       stock_data.get('wr_bfq') or
                       stock_data.get('wr1') or 
                       stock_data.get('wr2') or
                       stock_data.get('wr_14') or 
                       stock_data.get('wr14') or 
                       stock_data.get('wr_10') or 
                       stock_data.get('wr10'))
            
            if wr_value is not None:
                # WR指标通常为负值或0-100的正值
                wr_val = float(wr_value)
                
                # 如果是负值（标准WR），转换为正值
                if wr_val < 0:
                    wr_abs = abs(wr_val)
                else:
                    wr_abs = wr_val
                    
                # 确保在合理范围内
                if 0 <= wr_abs <= 100:
                    return wr_abs
            
            return None
            
        except Exception as e:
            return None
    
    def _is_stock_qualified_basic(self, stock_code: str, stock_data: Dict) -> bool:
        """股票基础资质检查 - 小市值动量策略"""
        try:
            # 基础数据获取
            current_price = stock_data.get('close', 0)
            market_cap = stock_data.get('circ_mv', 0)  # 流通市值(万元)
            turnover_rate = stock_data.get('turnover_rate', 0)  # 换手率
            volume_ratio = stock_data.get('volume_ratio', 0)  # 量比
            
            if not all([current_price, market_cap]):
                return False
            
            # 基础过滤条件
            basic_filters = (
                current_price > 0 and                                      # 有价格数据
                current_price >= 2.0 and                                   # 最低价格2元
                'ST' not in stock_code and                                  # 排除ST股票
                not stock_code.startswith('688') and                       # 排除科创板（高风险）
                market_cap >= self.params['min_market_cap'] and             # 最小市值100亿万元
                market_cap <= self.params['max_market_cap']                 # 最大市值1000亿万元
            )
            
            # 流动性检查
            liquidity_filters = True
            if turnover_rate:
                liquidity_filters = (
                    self.params['min_turnover_rate'] <= turnover_rate <= self.params['max_turnover_rate']
                )
            
            if volume_ratio and liquidity_filters:
                liquidity_filters = volume_ratio >= self.params['min_volume_ratio']
            
            return basic_filters and liquidity_filters
                    
        except Exception as e:
            return False
    
    def _calculate_comprehensive_scores(self, stock_pool: List[str], current_date: str, market_data: Dict[str, Dict]) -> Dict[str, float]:
        """计算综合因子得分 - 小市值动量策略版本"""
        try:
            factor_scores = {}
            
            # 收集所有股票的因子数据
            technical_scores = {}    # 技术因子
            fundamental_scores = {}  # 基本面因子
            momentum_scores = {}     # 动量因子
            
            total_stocks = len(stock_pool)
            valid_tech = 0
            valid_fund = 0
            valid_mom = 0
            
            for stock_code in stock_pool:
                stock_data = market_data.get(stock_code, {})
                
                # 1. 技术因子评分
                tech_score = self._calculate_technical_factor(stock_code, stock_data)
                if tech_score is not None:
                    technical_scores[stock_code] = tech_score
                    valid_tech += 1
                
                # 2. 基本面因子评分
                fund_score = self._calculate_fundamental_factor(stock_code, stock_data)
                if fund_score is not None:
                    fundamental_scores[stock_code] = fund_score
                    valid_fund += 1
                
                # 3. 动量因子评分
                mom_score = self._calculate_momentum_factor(stock_code, stock_data)
                if mom_score is not None:
                    momentum_scores[stock_code] = mom_score
                    valid_mom += 1
            
            print(f"因子计算统计: 总数{total_stocks}, 技术{valid_tech}, 基本面{valid_fund}, 动量{valid_mom}")
            
            if not technical_scores or not fundamental_scores or not momentum_scores:
                print(f"因子数据不足: 技术因子{len(technical_scores)}只, 基本面因子{len(fundamental_scores)}只, 动量因子{len(momentum_scores)}只")
                return {}
            
            # 因子标准化
            technical_normalized = self._normalize_factor(technical_scores)
            fundamental_normalized = self._normalize_factor(fundamental_scores)
            momentum_normalized = self._normalize_factor(momentum_scores)
            
            # 计算综合得分
            all_stocks = (set(technical_normalized.keys()) & 
                         set(fundamental_normalized.keys()) & 
                         set(momentum_normalized.keys()))
            
            print(f"可计算综合得分的股票数: {len(all_stocks)}")
            
            for stock_code in all_stocks:
                composite_score = (
                    technical_normalized[stock_code] * self.params['technical_weight'] +
                    fundamental_normalized[stock_code] * self.params['fundamental_weight'] +
                    momentum_normalized[stock_code] * self.params['momentum_weight']
                )
                factor_scores[stock_code] = composite_score
            
            return factor_scores
            
        except Exception as e:
            print(f"计算综合因子得分失败: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _calculate_comprehensive_score(self, stock_code: str, stock_data: Dict) -> Optional[float]:
        """计算单个股票的综合因子得分"""
        try:
            # 1. 计算技术因子评分
            tech_score = self._calculate_technical_factor(stock_code, stock_data)
            if tech_score is None:
                return None
            
            # 2. 计算基本面因子评分
            fund_score = self._calculate_fundamental_factor(stock_code, stock_data)
            if fund_score is None:
                return None
            
            # 3. 计算动量因子评分
            mom_score = self._calculate_momentum_factor(stock_code, stock_data)
            if mom_score is None:
                return None
            
            # 由于单个股票无法标准化，直接使用原始得分的加权平均
            # 假设原始得分已经在合理范围内（0-1之间）
            composite_score = (
                tech_score * self.params['technical_weight'] +
                fund_score * self.params['fundamental_weight'] +
                mom_score * self.params['momentum_weight']
            )
            
            return composite_score
            
        except Exception as e:
            print(f"计算单个股票{stock_code}综合得分失败: {e}")
            return None
    
    def _calculate_technical_factor(self, stock_code: str, stock_data: Dict) -> Optional[float]:
        """计算技术因子评分 - 优化版"""
        try:
            scores = []
            
            # RSI超卖优势因子（优化版，平衡胜率和机会）
            rsi = self._get_stock_rsi(stock_data)
            if rsi is not None:
                # 更平衡的RSI评分系统，适度放宽条件
                if rsi <= 15:
                    rsi_score = 1.0  # RSI极度超卖
                elif rsi <= 30:
                    rsi_score = 0.9 - (rsi - 15) * 0.015  # RSI超卖区间扩大
                elif rsi <= 45:
                    rsi_score = 0.7 - (rsi - 30) * 0.015  # RSI偏低区间扩大
                elif rsi <= 65:
                    rsi_score = 0.4 - (rsi - 45) * 0.008  # RSI中性区间扩大
                else:
                    rsi_score = max(0.1, 0.25 - (rsi - 65) * 0.003)  # RSI超买惩罚减轻
                scores.append(rsi_score * 2.5)  # 适中提高权重
            
            # MACD趋势因子（强化）
            macd = stock_data.get('macd') or stock_data.get('macd_bfq')
            macd_signal = stock_data.get('macd_signal') or stock_data.get('macds_bfq')
            if macd is not None and macd_signal is not None:
                macd_diff = macd - macd_signal
                if macd_diff > 0:
                    # 金叉且MACD在零轴上方更优
                    if macd > 0:
                        macd_score = 1.0
                    else:
                        macd_score = 0.7
                else:
                    # 死叉惩罚
                    macd_score = 0.2
                scores.append(macd_score)
            
            # 布林线位置因子
            close = stock_data.get('close', 0)
            boll_upper = stock_data.get('boll_upper') or stock_data.get('upper_bfq')
            boll_lower = stock_data.get('boll_lower') or stock_data.get('lower_bfq')
            
            if close > 0 and boll_upper and boll_lower and boll_upper > boll_lower:
                # 布林线位置因子（优化版）
                boll_position = (close - boll_lower) / (boll_upper - boll_lower)
                if boll_position <= 0.05:  # 跌破下轨
                    boll_score = 1.0
                elif boll_position <= 0.15:  # 接近下轨
                    boll_score = 0.9
                elif boll_position <= 0.35:  # 偏下方
                    boll_score = 0.7
                elif boll_position <= 0.65:  # 中间区域
                    boll_score = 0.4
                else:
                    boll_score = 0.2  # 接近上轨
                scores.append(boll_score)
            
            # 成交量放量因子（优化）
            volume_ratio = stock_data.get('volume_ratio', 0)
            if volume_ratio > 0:
                # 温和放量最优（1.5-2.5倍）
                if 1.5 <= volume_ratio <= 2.5:
                    vol_score = 1.0
                elif 1.0 <= volume_ratio < 1.5:
                    vol_score = 0.3 + (volume_ratio - 1.0) * 1.4
                elif volume_ratio > 2.5:
                    vol_score = max(0.3, 1.0 - (volume_ratio - 2.5) * 0.2)
                else:
                    vol_score = 0.1
                scores.append(vol_score)
            
            return np.mean(scores) if scores else None
            
        except Exception as e:
            return None
    
    def _calculate_fundamental_factor(self, stock_code: str, stock_data: Dict) -> Optional[float]:
        """计算基本面因子评分"""
        try:
            scores = []
            
            # 流通市值因子（偏向小市值）- 这是数据库中肯定存在的字段
            market_cap = stock_data.get('circ_mv', 0)  # 万元
            if market_cap > 0:
                # 小市值得分更高，100-1000亿区间
                if market_cap <= 200000:  # 200亿万元以下
                    cap_score = 1.0
                elif market_cap <= 500000:  # 500亿万元以下
                    cap_score = 1.0 - (market_cap - 200000) / 300000
                else:
                    cap_score = max(0, 1.0 - (market_cap - 500000) / 500000)
                scores.append(cap_score)
            
            # 价格相对位置因子（技术面）
            current_price = stock_data.get('close', 0)
            high_52w = stock_data.get('high_52w') or stock_data.get('high')
            low_52w = stock_data.get('low_52w') or stock_data.get('low')
            
            if current_price > 0 and high_52w and low_52w and high_52w > low_52w:
                # 价格在相对低位时得分更高
                price_position = (current_price - low_52w) / (high_52w - low_52w)
                position_score = 1.0 - price_position  # 位置越低分数越高
                scores.append(position_score)
            
            # 成交量均线偏离度因子（流动性）
            current_volume = stock_data.get('volume', 0)
            volume_ma20 = stock_data.get('volume_ma20', 0)
            
            if current_volume > 0 and volume_ma20 > 0:
                volume_ratio = current_volume / volume_ma20
                # 适度放量得分高（1.2-3倍最优）
                if 1.2 <= volume_ratio <= 3.0:
                    vol_score = 1.0
                elif volume_ratio > 3.0:
                    vol_score = max(0.3, 1.0 - (volume_ratio - 3.0) / 5.0)
                else:
                    vol_score = max(0.3, volume_ratio / 1.2)
                scores.append(vol_score)
            
            # 价格波动性因子（适度波动）
            atr = stock_data.get('atr', 0)
            if atr > 0 and current_price > 0:
                atr_ratio = atr / current_price
                # 适度波动得分高（2-8%最优）
                if 0.02 <= atr_ratio <= 0.08:
                    volatility_score = 1.0
                elif atr_ratio > 0.08:
                    volatility_score = max(0.2, 1.0 - (atr_ratio - 0.08) / 0.1)
                else:
                    volatility_score = max(0.2, atr_ratio / 0.02)
                scores.append(volatility_score)
            
            return np.mean(scores) if scores else None
            
        except Exception as e:
            return None
    
    def _calculate_momentum_factor(self, stock_code: str, stock_data: Dict) -> Optional[float]:
        """计算增强版动量因子评分"""
        try:
            scores = []
            
            # 1. 短期动量（当日涨跌幅）- 优化评分逻辑
            pct_chg = stock_data.get('pct_chg', 0)
            if pct_chg is not None:
                # 调整适度上涨区间（1-6%最优，更宽容）
                if 1 <= pct_chg <= 6:
                    mom_score = 1.0
                elif 6 < pct_chg <= 9:  # 较强上涨
                    mom_score = 0.8
                elif pct_chg > 9:  # 过度上涨，反而降分
                    mom_score = max(0.2, 1.0 - (pct_chg - 9) / 15)
                elif pct_chg >= -1:  # 小幅下跌可接受
                    mom_score = 0.6 + (pct_chg + 1) * 0.4
                elif pct_chg >= -3:  # 中度下跌
                    mom_score = 0.3 + (pct_chg + 3) * 0.15
                else:  # 大跌
                    mom_score = 0.1
                scores.append(mom_score)
            
            # 2. 中期动量（5日涨跌幅）- 新增
            pct_chg_5d = stock_data.get('pct_chg_5d', 0)
            if pct_chg_5d is not None:
                if pct_chg_5d >= 5:  # 5日累计涨5%+
                    scores.append(1.0)
                elif pct_chg_5d >= 0:
                    scores.append(0.6 + pct_chg_5d * 0.08)
                elif pct_chg_5d >= -5:
                    scores.append(0.4 + (pct_chg_5d + 5) * 0.04)
                else:
                    scores.append(0.2)
            
            # 相对强度（与均线的关系）
            close = stock_data.get('close', 0)
            ma5 = stock_data.get('ma5') or stock_data.get('ma_5', 0)
            ma20 = stock_data.get('ma20') or stock_data.get('ma_20', 0)
            
            if close > 0 and ma5 > 0 and ma20 > 0:
                # 价格高于均线得分
                if close > ma5 > ma20:
                    ma_score = 1.0  # 多头排列
                elif close > ma5:
                    ma_score = 0.7
                elif close > ma20:
                    ma_score = 0.5
                else:
                    ma_score = 0.2
                scores.append(ma_score)
            
            # 波动率适度性（ATR相对大小）
            atr = stock_data.get('atr', 0)
            if atr > 0 and close > 0:
                atr_ratio = atr / close
                # 适度波动为佳（2-6%最优）
                if 0.02 <= atr_ratio <= 0.06:
                    vol_score = 1.0
                elif atr_ratio > 0.06:
                    vol_score = max(0, 1.0 - (atr_ratio - 0.06) / 0.04)
                else:
                    vol_score = atr_ratio / 0.02
                scores.append(vol_score)
            
            return np.mean(scores) if scores else None
            
        except Exception as e:
            return None
    
    def _normalize_factor(self, factor_dict: Dict[str, float], reverse: bool = False) -> Dict[str, float]:
        """因子标准化（0-1归一化）"""
        try:
            if not factor_dict:
                return {}
            
            values = list(factor_dict.values())
            min_val = min(values)
            max_val = max(values)
            
            if max_val == min_val:
                return {k: 0.5 for k in factor_dict.keys()}
            
            normalized = {}
            for stock_code, value in factor_dict.items():
                norm_value = (value - min_val) / (max_val - min_val)
                if reverse:
                    norm_value = 1 - norm_value  # 反向因子
                normalized[stock_code] = norm_value
            
            return normalized
            
        except Exception as e:
            print(f"因子标准化失败: {e}")
            return {}
    
    def _generate_emergency_sell_signals(self, current_date: str, market_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """生成紧急止损信号"""
        try:
            signals = []
            
            for stock_code in list(self.positions_info.keys()):
                stock_data = market_data.get(stock_code, {})
                current_price = stock_data.get('close', 0)
                
                if current_price <= 0:
                    continue
                
                # 检查紧急止损条件
                emergency_reason = self._check_emergency_sell_conditions(stock_code, stock_data, current_price)
                
                if emergency_reason:
                    signals.append({
                        'action': 'sell',
                        'stock_code': stock_code,
                        'weight': 0.0,
                        'price': current_price,
                        'reason': f'紧急止损: {emergency_reason}'
                    })
            
            return signals
            
        except Exception as e:
            print(f"生成紧急止损信号失败: {e}")
            return []
    
    def _check_emergency_sell_conditions(self, stock_code: str, stock_data: Dict, current_price: float) -> Optional[str]:
        """检查紧急止损条件"""
        try:
            # 1. 止损检查
            entry_price = self.positions_info[stock_code].get('entry_price', 0)
            if entry_price > 0:
                loss_pct = (current_price - entry_price) / entry_price
                if loss_pct <= -self.params['stop_loss']:
                    return f"跌破止损位{self.params['stop_loss']:.1%} (当前{loss_pct:.1%})"
                
                # 止盈回撤检查
                if loss_pct >= self.params['take_profit']:
                    # 达到止盈位后，如果回撤超过3%则卖出
                    if loss_pct < self.params['take_profit'] - 0.03:
                        return f"止盈回撤 (峰值{self.params['take_profit']:.1%}, 当前{loss_pct:.1%})"
            
            # 2. WR指标紧急止损：WR > 90 (极度超买)
            wr_value = self._get_stock_wr(stock_data)
            if wr_value is not None and wr_value > self.params['wr_overbought']:
                return f"WR极度超买 ({wr_value:.1f}>{self.params['wr_overbought']})"
            
            # 3. RSI极端值止损
            rsi = self._get_stock_rsi(stock_data)
            if rsi is not None and rsi > self.params['emergency_rsi_threshold']:
                return f"RSI极端超买 ({rsi:.1f}>{self.params['emergency_rsi_threshold']})"
            
            # 4. 换手率异常止损
            turnover_rate = stock_data.get('turnover_rate', 0)
            if turnover_rate > self.params['emergency_turnover_threshold']:
                return f"换手率异常 ({turnover_rate:.2f}%>{self.params['emergency_turnover_threshold']}%)"
            
            return None
            
        except Exception as e:
            return None
    
    def _generate_rebalance_signals(self, current_date: str, market_data: Dict[str, Dict], portfolio_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成调仓信号"""
        try:
            signals = []
            
            # 根据市场信号决定股票权重 - 优化后的分级仓位控制
            if self.market_signal == 1:  # 看涨，增加股票权重
                target_stock_weight = self.params['stock_ratio_bullish']  # 80%
                action_desc = "看涨调仓"
            elif self.market_signal == -1:  # 看跌，减少股票权重
                target_stock_weight = self.params['stock_ratio_bearish']  # 20%
                action_desc = "看跌调仓"
            elif self.market_signal == 0:  # 观望，中等仓位
                target_stock_weight = 0.50  # 50%中性仓位
                action_desc = "中性调仓"
            else:
                return []
            
            # 1. 卖出不在新选股列表中的股票
            current_holdings = set(self.positions_info.keys())
            target_holdings = set(self.selected_stocks)
            stocks_to_sell = current_holdings - target_holdings
            
            for stock_code in stocks_to_sell:
                signals.append({
                    'action': 'sell',
                    'stock_code': stock_code,
                    'weight': 0.0,
                    'reason': f'{action_desc}-卖出非选股'
                })
            
            # 2. 买入新选股（限制最大持仓数量）
            if self.selected_stocks:
                max_stocks = min(len(self.selected_stocks), self.params['max_positions'])
                individual_weight = min(target_stock_weight / max_stocks, self.params['max_single_weight'])
                
                for i, stock_code in enumerate(self.selected_stocks[:max_stocks]):
                    stock_data = market_data.get(stock_code, {})
                    current_price = stock_data.get('close', 0)
                    
                    if current_price > 0:
                        signals.append({
                            'action': 'buy',
                            'stock_code': stock_code,
                            'weight': individual_weight,
                            'price': current_price,
                            'reason': f'{action_desc}-多因子选股'
                        })
            
            print(f"生成调仓信号: {len(signals)}个, 股票权重{target_stock_weight:.1%}")
            
            return signals
            
        except Exception as e:
            print(f"生成调仓信号失败: {e}")
            return []
    
    def _check_portfolio_risk_stop(self, portfolio_info: Dict[str, Any]) -> bool:
        """检查组合级风险控制"""
        try:
            # 获取组合当前回撤
            current_drawdown = portfolio_info.get('current_drawdown', 0)
            max_drawdown_threshold = self.params.get('max_drawdown_stop', 0.15)
            
            if abs(current_drawdown) > max_drawdown_threshold:
                print(f"🛑 触发组合止损: 当前回撤{current_drawdown:.2%} > 阈值{max_drawdown_threshold:.2%}")
                return True
                
            return False
            
        except Exception as e:
            return False
    
    def _generate_emergency_liquidation_signals(self, current_date: str, market_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """生成紧急清仓信号"""
        try:
            signals = []
            
            # 清仓所有股票持仓
            for stock_code in list(self.positions_info.keys()):
                stock_data = market_data.get(stock_code, {})
                current_price = stock_data.get('close', 0)
                
                if current_price > 0:
                    signals.append({
                        'action': 'sell',
                        'stock_code': stock_code,
                        'weight': 0.0,
                        'price': current_price,
                        'reason': '组合风险止损-紧急清仓'
                    })
            
            print(f"🚨 紧急清仓: 卖出{len(signals)}只股票")
            return signals
            
        except Exception as e:
            return []
    
    def _generate_defensive_signals(self, current_date: str, market_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """生成防守性信号 - 降低仓位或清仓"""
        try:
            signals = []
            
            # 卖出所有股票持仓，采用防守策略
            for stock_code in list(self.positions_info.keys()):
                stock_data = market_data.get(stock_code, {})
                current_price = stock_data.get('close', 0)
                
                if current_price > 0:
                    signals.append({
                        'action': 'sell',
                        'stock_code': stock_code,
                        'weight': 0.0,
                        'price': current_price,
                        'reason': '市场环境不利-防守策略'
                    })
            
            if signals:
                print(f"🛡️ 防守策略: 卖出{len(signals)}只股票")
                
            return signals
            
        except Exception as e:
            return []
    
    def on_trade_executed(self, trade_info: Dict[str, Any]):
        """交易执行后回调"""
        try:
            stock_code = trade_info['stock_code']
            # 兼容不同的字段名
            action = trade_info.get('action') or trade_info.get('order_type')
            price = trade_info.get('price', 0)
            
            # 更新信号计数器
            if action == 'buy':
                self.buy_signals_count += 1
                # 记录持仓信息
                self.positions_info[stock_code] = {
                    'entry_price': price,
                    'entry_date': trade_info.get('date', ''),
                    'entry_reason': trade_info.get('reason', ''),
                    'signal_type': '小市值动量选股'
                }
                
                # 记录持仓变动
                self._record_position_change(trade_info.get('date', ''), 'buy', stock_code, price, 0)
                
                print(f"📈 买入执行: {stock_code} @{price:.2f}元 (第{self.buy_signals_count}个买入信号)")
                
            elif action == 'sell':
                self.sell_signals_count += 1
                # 计算盈亏
                pnl_reason = ""
                if stock_code in self.positions_info:
                    entry_price = self.positions_info[stock_code].get('entry_price', 0)
                    if entry_price > 0:
                        pnl_pct = (price - entry_price) / entry_price
                        pnl_reason = f"盈亏{pnl_pct:.1%}"
                        print(f"📉 卖出执行: {stock_code} @{price:.2f}元, 盈亏{pnl_pct:.1%} (第{self.sell_signals_count}个卖出信号)")
                    
                    # 记录持仓变动
                    sell_reason = trade_info.get('reason', pnl_reason)
                    self._record_position_change(trade_info.get('date', ''), 'sell', stock_code, price, 0, sell_reason)
                    
                    del self.positions_info[stock_code]
                else:
                    # 记录持仓变动
                    self._record_position_change(trade_info.get('date', ''), 'sell', stock_code, price, 0, trade_info.get('reason', ''))
                    print(f"📉 卖出执行: {stock_code} @{price:.2f}元 (第{self.sell_signals_count}个卖出信号)")
            
            # 记录交易历史
            self.trade_history.append({
                'date': trade_info.get('date', ''),
                'action': action,
                'stock_code': stock_code,
                'price': price,
                'reason': trade_info.get('reason', '')
            })
            
        except Exception as e:
            print(f"交易回调处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _record_stock_selection(self, current_date: str, selected_stocks: List[str], market_data: Dict[str, Dict]):
        """记录选股历史 - 多因子策略版本"""
        try:
            if not selected_stocks:
                # 如果没有选股，记录一条空记录
                self.stock_selection_history.append({
                    'date': current_date,
                    'stock_code': '',
                    'resonance_score': 0,
                    'technical_score': 0,
                    'rank': 0,
                    'selected': False,
                    'reason': '无符合条件的选股(事件驱动未触发或无合格股票)'
                })
                return
            
            # 计算选中股票的综合因子得分
            stock_scores = []
            for stock_code in selected_stocks[:15]:  # 计算前15只
                stock_data = market_data.get(stock_code, {})
                comprehensive_score = self._calculate_comprehensive_score(stock_code, stock_data)
                if comprehensive_score:
                    stock_scores.append((stock_code, comprehensive_score))
            
            # 按得分排序
            stock_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 为每只选中股票创建记录，匹配CSV保存格式
            for rank, (stock_code, factor_score) in enumerate(stock_scores, 1):
                # 计算技术得分作为参考
                stock_data = market_data.get(stock_code, {})
                tech_score = self._calculate_technical_factor(stock_code, stock_data) or 0
                
                # 判断是否被选中（前max_positions只会被实际买入）
                is_selected = rank <= self.params['max_positions']
                
                self.stock_selection_history.append({
                    'date': current_date,
                    'stock_code': stock_code,
                    'resonance_score': factor_score,  # 多因子综合得分
                    'technical_score': tech_score,
                    'rank': rank,
                    'selected': is_selected,
                    'reason': f'多因子得分{factor_score:.3f},技术得分{tech_score:.3f},市场信号{self.market_signal}'
                })
            
            # 保持历史记录在合理范围内
            if len(self.stock_selection_history) > 150:
                self.stock_selection_history = self.stock_selection_history[-150:]
                
        except Exception as e:
            print(f"记录选股历史失败: {e}")
    
    def _record_position_change(self, current_date: str, action: str, stock_code: str, 
                               price: float, factor_score: float, reason: str = ""):
        """记录持仓变动历史 - 多因子策略版本"""
        try:
            self.position_change_history.append({
                'date': current_date,
                'action': action,
                'stock_code': stock_code,
                'price': price,
                'factor_score': factor_score,
                'reason': reason,
                'position_count': len(self.positions_info),
                'market_signal': self.market_signal,
                'timestamp': current_date
            })
            
            # 保持历史记录在合理范围内
            if len(self.position_change_history) > 200:
                self.position_change_history = self.position_change_history[-200:]
                
        except Exception as e:
            print(f"记录持仓变动失败: {e}")
    
    def _record_daily_snapshot(self, current_date: str, portfolio_info: Dict[str, Any]):
        """记录每日投资组合快照 - 多因子策略版本"""
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
            if hasattr(self, 'context') and self.context:
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
                'cumulative_return': cumulative_return,
                'market_signal': self.market_signal,  # 记录市场信号
                'selected_stocks_count': len(self.selected_stocks)  # 记录选股数量
            }
            
            self.daily_portfolio_snapshot[current_date] = snapshot
            
            # 保持快照数据在合理范围内（保留最近60天）
            if len(self.daily_portfolio_snapshot) > 60:
                dates = sorted(self.daily_portfolio_snapshot.keys())
                for old_date in dates[:-60]:
                    del self.daily_portfolio_snapshot[old_date]
            
            # 调试输出（仅在关键日期）
            if current_date.endswith(('01', '11', '21')) and total_value > 0:
                print(f"📊 多因子 {current_date} 快照: 总值{total_value:,.0f}, 现金{cash:,.0f}, 持仓{position_count}只, 市场信号{self.market_signal}")
                    
        except Exception as e:
            print(f"记录每日快照失败: {e}")
    
    def get_selection_report(self) -> Dict[str, Any]:
        """获取选股报告 - 多因子策略版本"""
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
                    'current_position_count': len(self.positions_info),
                    'current_market_signal': self.market_signal,
                    'selected_stocks_count': len(self.selected_stocks)
                }
            }
        except Exception as e:
            print(f"生成选股报告失败: {e}")
            return {}

    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        current_positions = len(self.positions_info)
        
        info = {
            'strategy_name': self.name,
            'strategy_version': self.version,
            'strategy_type': '小市值动量策略(多因子+RSI择时+WR指标)',
            'max_positions': self.params['max_positions'],
            'max_single_weight': self.params['max_single_weight'],
            'current_positions': current_positions,
            'buy_signals_count': self.buy_signals_count,
            'sell_signals_count': self.sell_signals_count,
            'total_signals': self.buy_signals_count + self.sell_signals_count,
            'total_trades': len(self.trade_history),
            'stock_pool_size': self.params['stock_pool_size'],
            'rsi_period': self.params['rsi_period'],
            'rsi_upper': self.params['rsi_upper'],
            'rsi_lower': self.params['rsi_lower'],
            'market_signal': self.market_signal,
            'selected_stocks_count': len(self.selected_stocks),
            'rebalance_method': "事件驱动调仓+RSI择时+多因子选股+WR指标",
            'index_code': self.get_index_code(),
            'description': "基于小市值动量策略的中证1000指数增强策略。事件驱动智能调仓(RSI极值/个股亏损/新机会/强制调仓)，使用股票池平均RSI择时，技术+基本面+动量三因子评分，WR指标买卖确认"
        }
        
        # 添加持仓详情
        positions_detail = []
        for stock_code, pos_info in self.positions_info.items():
            positions_detail.append({
                'stock_code': stock_code,
                'entry_price': pos_info['entry_price'],
                'entry_date': pos_info['entry_date'],
                'entry_reason': pos_info['entry_reason'],
                'signal_type': pos_info.get('signal_type', '小市值动量选股')
            })
        
        info['positions_detail'] = positions_detail
        
        return info


if __name__ == "__main__":
    # 测试策略适配器
    print("🚀 测试太上老君3号策略适配器...")
    
    strategy = TaiShang3FactorStrategyAdapter()
    print(f"策略名称: {strategy.name}")
    print(f"策略版本: {strategy.version}")
    print(f"指数代码: {strategy.get_index_code()}")
    
    # 测试策略信息
    info = strategy.get_strategy_info()
    print(f"策略描述: {info['description']}")
    print("   基于小市值动量策略文档重写")
    print("   择时：股票池平均RSI判断市场时机(30/70阈值)")
    print("   选股：技术因子40% + 基本面因子30% + 动量因子30%")
    print("   信号：WR<20超卖买入，WR>90超买卖出")
    print("   调仓：事件驱动智能调仓，根据市场信号和个股表现调整")
    print("   风控：止损6%，止盈15%，RSI>90紧急止损")