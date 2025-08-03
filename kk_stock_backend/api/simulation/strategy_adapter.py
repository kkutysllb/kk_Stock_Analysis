"""
量化策略模拟交易适配器

将量化策略信号转换为模拟交易订单，实现策略自动化交易
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging
import asyncio
import sys
import os

from .service import SimulationTradingService
from .models import BuyRequest, SellRequest, OrderType, TradeSource
from .strategy_config import strategy_config_manager
from api.db_handler import get_db_handler

# 添加项目根目录到路径以导入回测模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)


class StrategySimulationAdapter:
    """策略模拟交易适配器 - 轻量级实现"""
    
    def __init__(self, user_id: str, strategy_name: str):
        self.user_id = user_id
        self.strategy_name = strategy_name
        self.simulation_service = SimulationTradingService()
        self.logger = logging.getLogger(__name__)
        
    async def execute_strategy_signals(self, signals: List[Dict[str, Any]]) -> List[str]:
        """
        执行策略信号转换为模拟交易
        
        Args:
            signals: 策略信号列表，格式为：
                [
                    {
                        'action': 'BUY' | 'SELL',
                        'stock_code': str,
                        'quantity': int,
                        'price': float (可选),
                        'reason': str (可选)
                    }
                ]
        
        Returns:
            成功执行的交易ID列表
        """
        executed_trades = []
        
        try:
            self.logger.info(f"开始执行策略 {self.strategy_name} 的 {len(signals)} 个交易信号")
            
            for signal in signals:
                try:
                    trade_id = await self._execute_single_signal(signal)
                    if trade_id:
                        executed_trades.append(trade_id)
                        self.logger.info(f"信号执行成功: {signal['action']} {signal['stock_code']} - 交易ID: {trade_id}")
                    else:
                        self.logger.warning(f"信号执行失败: {signal}")
                except Exception as e:
                    self.logger.error(f"执行信号失败 {signal}: {e}")
                    continue
            
            self.logger.info(f"策略 {self.strategy_name} 信号执行完成，成功: {len(executed_trades)}/{len(signals)}")
            return executed_trades
            
        except Exception as e:
            self.logger.error(f"执行策略信号失败: {e}")
            return executed_trades
    
    async def _execute_single_signal(self, signal: Dict[str, Any]) -> Optional[str]:
        """执行单个交易信号"""
        action = signal.get('action', '').upper()
        stock_code = signal.get('stock_code', '')
        quantity = signal.get('quantity', 0)
        price = signal.get('price')
        reason = signal.get('reason', f'{self.strategy_name}策略信号')
        
        if not stock_code or quantity <= 0:
            self.logger.warning(f"无效信号参数: {signal}")
            return None
        
        try:
            stock_name = signal.get('stock_name', stock_code)
            if action == 'BUY':
                return await self._execute_buy_signal(stock_code, quantity, price, reason, stock_name)
            elif action == 'SELL':
                return await self._execute_sell_signal(stock_code, quantity, price, reason, stock_name)
            else:
                self.logger.warning(f"未知交易动作: {action}")
                return None
        except Exception as e:
            self.logger.error(f"执行交易信号失败 {signal}: {e}")
            return None
    
    async def _execute_buy_signal(self, stock_code: str, quantity: int, price: Optional[float], reason: str, stock_name: str = None) -> Optional[str]:
        """执行买入信号"""
        try:
            buy_request = BuyRequest(
                stock_code=stock_code,
                stock_name=stock_name or stock_code,  # 如果没有股票名称，使用股票代码
                quantity=quantity,
                order_type=OrderType.LIMIT if price else OrderType.MARKET,
                price=price,
                trade_source=TradeSource.STRATEGY,
                strategy_name=self.strategy_name,
                remarks=reason
            )
            
            trade_id = await self.simulation_service.execute_buy_order(self.user_id, buy_request)
            return trade_id
            
        except Exception as e:
            self.logger.error(f"执行买入信号失败 {stock_code}: {e}")
            return None
    
    async def _execute_sell_signal(self, stock_code: str, quantity: int, price: Optional[float], reason: str, stock_name: str = None) -> Optional[str]:
        """执行卖出信号"""
        try:
            sell_request = SellRequest(
                stock_code=stock_code,
                stock_name=stock_name or stock_code,  # 如果没有股票名称，使用股票代码
                quantity=quantity,
                order_type=OrderType.LIMIT if price else OrderType.MARKET,
                price=price,
                trade_source=TradeSource.STRATEGY,
                strategy_name=self.strategy_name,
                remarks=reason
            )
            
            trade_id = await self.simulation_service.execute_sell_order(self.user_id, sell_request)
            return trade_id
            
        except Exception as e:
            self.logger.error(f"执行卖出信号失败 {stock_code}: {e}")
            return None


class StrategyRunner:
    """策略运行器 - 复用现有回测引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_handler = get_db_handler()
        
    async def run_strategy_realtime(self, user_id: str, strategy_config: Dict[str, Any]) -> List[str]:
        """
        实时运行策略（利用现有backtest_unified.py）
        
        Args:
            user_id: 用户ID
            strategy_config: 策略配置
                {
                    'strategy_name': str,  # 策略名称
                    'allocated_cash': float,  # 分配资金
                    'custom_params': dict  # 自定义参数
                }
        
        Returns:
            执行的交易ID列表
        """
        try:
            strategy_name = strategy_config.get('strategy_name')
            self.logger.info(f"开始执行策略 {strategy_name} for user {user_id}")
            
            # 1. 调用现有的统一回测API，获取当日信号
            backtest_request = {
                "strategy_name": strategy_name,
                "start_date": datetime.now().strftime('%Y-%m-%d'),
                "end_date": datetime.now().strftime('%Y-%m-%d'),
                "initial_cash": strategy_config.get('allocated_cash', 300000),
                **strategy_config.get('custom_params', {})
            }
            
            # 2. 运行单日策略获取交易信号
            signals = await self._get_daily_signals(backtest_request)
            
            if not signals:
                self.logger.info(f"策略 {strategy_name} 今日无交易信号")
                return []
            
            # 3. 转换为模拟交易订单
            adapter = StrategySimulationAdapter(user_id, strategy_name)
            executed_trades = await adapter.execute_strategy_signals(signals)
            
            # 4. 更新策略执行记录
            await self._update_strategy_execution_record(user_id, strategy_name, len(signals), len(executed_trades))
            
            return executed_trades
            
        except Exception as e:
            self.logger.error(f"执行策略失败: {e}")
            return []
    
    async def _get_daily_signals(self, backtest_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取策略当日交易信号 - 集成真实的策略系统
        
        Args:
            backtest_request: 回测请求参数
        
        Returns:
            交易信号列表
        """
        try:
            strategy_name = backtest_request.get('strategy_name')
            
            # 调用真实的策略系统获取信号
            signals = await self._call_real_strategy_system(strategy_name, backtest_request)
            
            if not signals:
                self.logger.info(f"策略 {strategy_name} 今日无信号生成")
                return []
            
            # 将策略系统的信号转换为模拟交易格式
            converted_signals = self._convert_strategy_signals_to_simulation_format(signals, strategy_name)
            return converted_signals
            
        except Exception as e:
            self.logger.error(f"获取交易信号失败: {e}")
            return []
    
    async def _call_real_strategy_system(self, strategy_name: str, backtest_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        调用真实的策略系统 - 避免重复造轮子
        
        Args:
            strategy_name: 策略名称
            backtest_request: 回测请求参数
            
        Returns:
            策略原始信号列表
        """
        try:
            # 使用配置管理器获取策略信息
            try:
                strategy_config = strategy_config_manager.get_strategy_config(strategy_name)
                adapter_class_name = strategy_config_manager.get_strategy_adapter_class_name(strategy_name)
                module_path = strategy_config_manager.get_strategy_module_path(strategy_name)
            except ValueError as e:
                self.logger.error(f"策略配置错误: {e}")
                return []
            
            # 动态导入策略适配器
            backtrader_strategies_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'backtrader_strategies'
            )
            sys.path.insert(0, backtrader_strategies_path)
            
            # 动态导入和实例化策略适配器
            try:
                module = __import__(module_path, fromlist=[adapter_class_name])
                adapter_class = getattr(module, adapter_class_name)
                strategy_adapter = adapter_class()
                self.logger.info(f"成功加载策略适配器: {strategy_config.display_name} v{strategy_config.version}")
            except ImportError as e:
                self.logger.error(f"导入策略适配器失败: {e}")
                return []
            except AttributeError as e:
                self.logger.error(f"策略适配器类不存在: {e}")
                return []
            
            # 使用策略配置初始化上下文
            context = {
                'initial_cash': backtest_request.get('initial_cash', strategy_config.default_allocated_cash),
                'start_date': backtest_request.get('start_date'),
                'end_date': backtest_request.get('end_date')
            }
            strategy_adapter.initialize(context)
            
            # 构建当日市场数据
            current_date = backtest_request.get('start_date', datetime.now().strftime('%Y-%m-%d'))
            market_data = await self._build_unified_market_data()
            
            if not market_data:
                self.logger.warning("无法获取市场数据")
                return []
            
            # 构建组合信息
            portfolio_info = {
                'total_value': backtest_request.get('initial_cash', 300000),
                'cash_ratio': 1.0,  # 初始全现金
                'total_positions': 0
            }
            
            # 生成策略信号
            signals = strategy_adapter.generate_signals(current_date, market_data, portfolio_info)
            
            self.logger.info(f"策略 {strategy_name} 生成信号 {len(signals)} 个")
            return signals
            
        except Exception as e:
            self.logger.error(f"调用真实策略系统失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _convert_strategy_signals_to_simulation_format(self, signals: List[Dict[str, Any]], strategy_name: str) -> List[Dict[str, Any]]:
        """
        将策略系统信号转换为模拟交易格式
        
        Args:
            signals: 策略原始信号
            strategy_name: 策略名称
            
        Returns:
            模拟交易格式信号
        """
        try:
            converted_signals = []
            
            for signal in signals:
                action = signal.get('action', '').lower()
                stock_code = signal.get('stock_code', '')
                price = signal.get('price', 0)
                
                if not stock_code or not action:
                    continue
                
                # 转换为模拟交易格式
                converted_signal = {
                    'action': action.upper(),
                    'stock_code': stock_code,
                    'stock_name': signal.get('stock_name', stock_code),
                    'price': price,
                    'reason': signal.get('reason', f'{strategy_name}策略信号')
                }
                
                # 计算交易数量 - 使用策略配置
                if action == 'buy':
                    # 获取策略配置信息
                    try:
                        strategy_config = strategy_config_manager.get_strategy_config(strategy_name)
                        default_weight = strategy_config.max_single_weight
                        default_cash = strategy_config.default_allocated_cash
                    except ValueError:
                        default_weight = 0.1
                        default_cash = 300000
                    
                    # 根据策略权重和价格计算数量
                    weight = signal.get('weight', default_weight)
                    allocated_cash = signal.get('allocated_cash', default_cash)
                    
                    if weight > 0 and price > 0:
                        position_value = allocated_cash * weight
                        quantity = int(position_value / price / 100) * 100  # 整百手
                        converted_signal['quantity'] = max(quantity, 100)  # 至少100股
                    else:
                        converted_signal['quantity'] = 100
                elif action == 'sell':
                    # 卖出时需要获取持仓数量，这里简化处理
                    converted_signal['quantity'] = signal.get('quantity', 0)
                
                converted_signals.append(converted_signal)
            
            return converted_signals
            
        except Exception as e:
            self.logger.error(f"转换策略信号格式失败: {e}")
            return []
    
    async def _build_unified_market_data(self) -> Dict[str, Dict[str, Any]]:
        """
        统一的市场数据构建方法 - 替代重复的数据获取逻辑
        
        Returns:
            统一格式的市场数据
        """
        try:
            self.logger.info("构建统一市场数据...")
            
            market_data = {}
            
            # 获取最新的综合技术指标数据
            collection = self.db_handler.get_collection("stock_technical_indicators")
            
            # 查询最近的数据
            from datetime import datetime, timedelta
            recent_date = datetime.now() - timedelta(days=5)
            
            pipeline = [
                {"$match": {"trade_date": {"$gte": recent_date.strftime('%Y%m%d')}}},
                {"$sort": {"ts_code": 1, "trade_date": -1}},
                {"$group": {
                    "_id": "$ts_code",
                    "latest_data": {"$first": "$$ROOT"}
                }},
                {"$limit": 4000}  # 限制数量
            ]
            
            cursor = collection.aggregate(pipeline)
            stock_count = 0
            
            for doc in cursor:
                try:
                    stock_code = doc["_id"]
                    data = doc["latest_data"]
                    
                    # 构建统一格式的数据
                    unified_data = self._build_unified_stock_data(data)
                    if unified_data:
                        market_data[stock_code] = unified_data
                        stock_count += 1
                        
                except Exception as e:
                    self.logger.warning(f"处理股票 {stock_code} 数据失败: {e}")
                    continue
            
            # 如果技术指标数据不足，补充基础K线数据
            if stock_count < 1000:
                self.logger.info(f"技术指标数据不足({stock_count}只)，补充K线数据...")
                kline_data = await self._supplement_kline_data(market_data)
                market_data.update(kline_data)
                stock_count = len(market_data)
            
            self.logger.info(f"构建统一市场数据完成: {stock_count} 只股票")
            return market_data
            
        except Exception as e:
            self.logger.error(f"构建统一市场数据失败: {e}")
            return {}
    
    def _build_unified_stock_data(self, raw_data: Dict) -> Dict[str, Any]:
        """
        构建统一格式的股票数据
        
        Args:
            raw_data: 原始数据
            
        Returns:
            统一格式的股票数据
        """
        try:
            unified_data = {
                # 基础价格数据
                'close': float(raw_data.get('close', 0)),
                'open': float(raw_data.get('open', 0)),
                'high': float(raw_data.get('high', 0)),
                'low': float(raw_data.get('low', 0)),
                'pre_close': float(raw_data.get('pre_close', raw_data.get('close', 0))),
                'volume': float(raw_data.get('vol', 0) * 100) if raw_data.get('vol') else 0,
                'amount': float(raw_data.get('amount', 0) * 1000) if raw_data.get('amount') else 0,
                'turnover_rate': float(raw_data.get('turnover_rate', 0)),
                'pct_chg': float(raw_data.get('pct_chg', 0)),
                'circ_mv': float(raw_data.get('circ_mv', 0)),
                
                # 技术指标 - 多字段兼容
                'macd_dif': float(raw_data.get('macd_dif', raw_data.get('macd', 0))),
                'macd_dea': float(raw_data.get('macd_dea', raw_data.get('macds', 0))),
                'macd_macd': float(raw_data.get('macd_macd', raw_data.get('macdh', 0))),
                
                'kdj_k': float(raw_data.get('kdj_k', raw_data.get('kdjk', 50))),
                'kdj_d': float(raw_data.get('kdj_d', raw_data.get('kdjd', 50))),
                'kdj_j': float(raw_data.get('kdj_j', raw_data.get('kdjj', 50))),
                
                'rsi6': float(raw_data.get('rsi6', raw_data.get('rsi_6', 50))),
                'rsi12': float(raw_data.get('rsi12', raw_data.get('rsi_12', 50))),
                
                'ma5': float(raw_data.get('ma5', raw_data.get('ma_5', raw_data.get('close', 0)))),
                'ma20': float(raw_data.get('ma20', raw_data.get('ma_20', raw_data.get('close', 0)))),
                'ma60': float(raw_data.get('ma60', raw_data.get('ma_60', raw_data.get('close', 0)))),
                
                'volume_ratio': float(raw_data.get('volume_ratio', 1.0)),
                'volume_ma20': float(raw_data.get('volume_ma20', raw_data.get('vol', 0) * 100)),
                
                # 布林带指标
                'boll_upper': float(raw_data.get('boll_upper', raw_data.get('upper', raw_data.get('close', 0) * 1.1))),
                'boll_mid': float(raw_data.get('boll_mid', raw_data.get('mid', raw_data.get('close', 0)))),
                'boll_lower': float(raw_data.get('boll_lower', raw_data.get('lower', raw_data.get('close', 0) * 0.9))),
                
                # WR指标
                'wr1': float(raw_data.get('wr1', raw_data.get('wr_14', 50))),
                'wr_bfq': float(raw_data.get('wr_bfq', raw_data.get('wr1', 50))),
                
                # ATR波动率
                'atr': float(raw_data.get('atr', 0)),
            }
            
            # 数据完整性检查
            if unified_data['close'] <= 0:
                return None
                
            return unified_data
            
        except Exception as e:
            return None
    
    async def _supplement_kline_data(self, existing_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        补充K线基础数据
        
        Args:
            existing_data: 已有数据
            
        Returns:
            补充的K线数据
        """
        try:
            kline_data = {}
            
            # 从K线数据库获取最新数据
            collection = self.db_handler.get_collection("stock_kline_daily")
            
            from datetime import datetime, timedelta
            recent_date = datetime.now() - timedelta(days=5)
            
            pipeline = [
                {"$match": {
                    "trade_date": {"$gte": recent_date.strftime('%Y%m%d')},
                    "ts_code": {"$nin": list(existing_data.keys())}  # 排除已有数据
                }},
                {"$sort": {"ts_code": 1, "trade_date": -1}},
                {"$group": {
                    "_id": "$ts_code",
                    "latest_data": {"$first": "$$ROOT"}
                }},
                {"$limit": 2000}
            ]
            
            cursor = collection.aggregate(pipeline)
            
            for doc in cursor:
                try:
                    stock_code = doc["_id"]
                    data = doc["latest_data"]
                    
                    # 构建基础数据
                    basic_data = {
                        'close': float(data.get('close', 0)),
                        'open': float(data.get('open', 0)),
                        'high': float(data.get('high', 0)),
                        'low': float(data.get('low', 0)),
                        'pre_close': float(data.get('pre_close', data.get('close', 0))),
                        'volume': float(data.get('vol', 0) * 100) if data.get('vol') else 0,
                        'amount': float(data.get('amount', 0) * 1000) if data.get('amount') else 0,
                        'turnover_rate': float(data.get('turnover_rate', 0)),
                        'pct_chg': float(data.get('pct_chg', 0)),
                        'circ_mv': float(data.get('circ_mv', 0)),
                        
                        # 默认技术指标值
                        'macd_dif': 0, 'macd_dea': 0, 'macd_macd': 0,
                        'kdj_k': 50, 'kdj_d': 50, 'kdj_j': 50,
                        'rsi6': 50, 'rsi12': 50,
                        'ma5': float(data.get('close', 0)),
                        'ma20': float(data.get('close', 0)),
                        'ma60': float(data.get('close', 0)),
                        'volume_ratio': 1.0,
                        'volume_ma20': float(data.get('vol', 0) * 100),
                        'boll_upper': float(data.get('close', 0)) * 1.1,
                        'boll_mid': float(data.get('close', 0)),
                        'boll_lower': float(data.get('close', 0)) * 0.9,
                        'wr1': 50, 'wr_bfq': 50,
                        'atr': 0,
                    }
                    
                    if basic_data['close'] > 0:
                        kline_data[stock_code] = basic_data
                        
                except Exception as e:
                    continue
            
            self.logger.info(f"补充K线数据: {len(kline_data)} 只股票")
            return kline_data
            
        except Exception as e:
            self.logger.error(f"补充K线数据失败: {e}")
            return {}
    
    # 注意：原来的硬编码策略信号方法已被 _call_real_strategy_system 替代
    # 保留这些方法作为备用和兼容性，但不再使用
    
    async def _get_legacy_strategy_signals(self, strategy_name: str, backtest_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        遗留的策略信号获取方法 - 仅作为备用
        现在主要使用 _call_real_strategy_system 方法
        """
        self.logger.warning(f"使用遗留策略信号方法: {strategy_name}")
        return []
    
    # 删除原有的冗余数据构建方法，统一使用 _build_unified_market_data


# 创建全局实例
strategy_runner = StrategyRunner()
