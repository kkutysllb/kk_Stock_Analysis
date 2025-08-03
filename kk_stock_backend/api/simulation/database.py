"""
模拟交易系统数据库操作层

提供模拟账户、持仓、交易记录等数据的增删改查操作
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
import uuid
import logging
from decimal import Decimal

from api.db_handler import get_db_handler
from .models import (
    SimulationAccount, SimulationPosition, SimulationTrade, AccountSnapshot,
    TradeType, TradeStatus, BoardType, Market,
    TradingFeeConfig, TradingCostCalculation
)


class SimulationDatabase:
    """模拟交易数据库操作类"""
    
    def __init__(self):
        self.db_handler = get_db_handler()
        self.db = self.db_handler.db
        self.logger = logging.getLogger(__name__)
        
        # 集合名称
        self.ACCOUNTS_COLLECTION = "simulation_accounts"
        self.POSITIONS_COLLECTION = "simulation_positions"
        self.TRADES_COLLECTION = "simulation_trades"
        self.SNAPSHOTS_COLLECTION = "account_snapshots"
        self.STRATEGY_CONFIGS_COLLECTION = "user_strategy_configs"
        
        # 初始化索引
        self._create_indexes()
    
    def _create_indexes(self):
        """创建数据库索引以优化查询性能"""
        try:
            # 模拟账户表索引
            accounts_col = self.db[self.ACCOUNTS_COLLECTION]
            accounts_col.create_index([("user_id", ASCENDING)], unique=True)
            accounts_col.create_index([("status", ASCENDING)])
            
            # 持仓表索引
            positions_col = self.db[self.POSITIONS_COLLECTION]
            positions_col.create_index([("user_id", ASCENDING), ("stock_code", ASCENDING)], unique=True)
            positions_col.create_index([("user_id", ASCENDING)])
            positions_col.create_index([("stock_code", ASCENDING)])
            
            # 交易记录表索引
            trades_col = self.db[self.TRADES_COLLECTION]
            trades_col.create_index([("trade_id", ASCENDING)], unique=True)
            trades_col.create_index([("user_id", ASCENDING), ("trade_time", DESCENDING)])
            trades_col.create_index([("user_id", ASCENDING), ("stock_code", ASCENDING)])
            trades_col.create_index([("trade_time", DESCENDING)])
            trades_col.create_index([("status", ASCENDING)])
            
            # 账户快照表索引
            snapshots_col = self.db[self.SNAPSHOTS_COLLECTION]
            snapshots_col.create_index([("user_id", ASCENDING), ("snapshot_date", ASCENDING)], unique=True)
            snapshots_col.create_index([("user_id", ASCENDING)])
            snapshots_col.create_index([("snapshot_date", DESCENDING)])
            
            # 用户策略配置表索引
            strategy_configs_col = self.db[self.STRATEGY_CONFIGS_COLLECTION]
            strategy_configs_col.create_index([("user_id", ASCENDING), ("strategy_name", ASCENDING)], unique=True)
            strategy_configs_col.create_index([("user_id", ASCENDING)])
            strategy_configs_col.create_index([("is_active", ASCENDING)])
            strategy_configs_col.create_index([("last_execution", DESCENDING)])
            
            self.logger.info("模拟交易数据库索引创建完成")
            
        except Exception as e:
            self.logger.error(f"创建数据库索引失败: {e}")
    
    # ==================== 模拟账户操作 ====================
    
    def create_simulation_account(self, user_id: str, initial_capital: float = 3000000.0, 
                                account_name: str = "模拟账户") -> Optional[Dict[str, Any]]:
        """
        创建模拟账户
        
        Args:
            user_id: 用户ID
            initial_capital: 初始资金，默认300万
            account_name: 账户名称
            
        Returns:
            创建的账户信息，失败返回None
        """
        try:
            accounts_col = self.db[self.ACCOUNTS_COLLECTION]
            
            # 检查用户是否已有模拟账户
            existing_account = accounts_col.find_one({"user_id": user_id})
            if existing_account:
                self.logger.warning(f"用户 {user_id} 已存在模拟账户")
                return existing_account
            
            # 创建新的模拟账户
            account_data = {
                "user_id": user_id,
                "account_name": account_name,
                "initial_capital": initial_capital,
                "available_cash": initial_capital,
                "frozen_cash": 0.0,
                "total_assets": initial_capital,
                "total_market_value": 0.0,
                "daily_return": 0.0,
                "daily_return_rate": 0.0,
                "total_return": 0.0,
                "total_return_rate": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "trade_count": 0,
                "profit_trades": 0,
                "loss_trades": 0,
                "create_time": datetime.now(),
                "last_update_time": datetime.now(),
                "status": 1
            }
            
            result = accounts_col.insert_one(account_data)
            account_data["_id"] = result.inserted_id
            
            self.logger.info(f"用户 {user_id} 模拟账户创建成功，初始资金: {initial_capital:,.2f}")
            return account_data
            
        except DuplicateKeyError:
            self.logger.warning(f"用户 {user_id} 已存在模拟账户")
            return accounts_col.find_one({"user_id": user_id})
        except Exception as e:
            self.logger.error(f"创建模拟账户失败: {e}")
            return None
    
    def get_simulation_account(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模拟账户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            账户信息，不存在返回None
        """
        try:
            accounts_col = self.db[self.ACCOUNTS_COLLECTION]
            account = accounts_col.find_one({"user_id": user_id})
            return account
        except Exception as e:
            self.logger.error(f"获取模拟账户失败: {e}")
            return None
    
    def update_simulation_account(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新模拟账户信息
        
        Args:
            user_id: 用户ID
            update_data: 更新数据
            
        Returns:
            更新是否成功
        """
        try:
            accounts_col = self.db[self.ACCOUNTS_COLLECTION]
            update_data["last_update_time"] = datetime.now()
            
            result = accounts_col.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"更新模拟账户失败: {e}")
            return False
    
    def reset_simulation_account(self, user_id: str) -> bool:
        """
        重置模拟账户
        
        Args:
            user_id: 用户ID
            
        Returns:
            重置是否成功
        """
        try:
            # 获取原账户信息
            account = self.get_simulation_account(user_id)
            if not account:
                return False
            
            initial_capital = account.get("initial_capital", 3000000.0)
            
            # 重置账户数据
            reset_data = {
                "available_cash": initial_capital,
                "frozen_cash": 0.0,
                "total_assets": initial_capital,
                "total_market_value": 0.0,
                "daily_return": 0.0,
                "daily_return_rate": 0.0,
                "total_return": 0.0,
                "total_return_rate": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "trade_count": 0,
                "profit_trades": 0,
                "loss_trades": 0,
                "last_update_time": datetime.now()
            }
            
            # 清空持仓
            positions_col = self.db[self.POSITIONS_COLLECTION]
            positions_col.delete_many({"user_id": user_id})
            
            # 清空交易记录
            trades_col = self.db[self.TRADES_COLLECTION]
            trades_col.delete_many({"user_id": user_id})
            
            # 更新账户
            return self.update_simulation_account(user_id, reset_data)
            
        except Exception as e:
            self.logger.error(f"重置模拟账户失败: {e}")
            return False
    
    # ==================== 持仓操作 ====================
    
    def get_user_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户持仓列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            持仓列表
        """
        try:
            positions_col = self.db[self.POSITIONS_COLLECTION]
            positions = list(positions_col.find({"user_id": user_id}))
            return positions
        except Exception as e:
            self.logger.error(f"获取用户持仓失败: {e}")
            return []
    
    def get_position(self, user_id: str, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票持仓信息
        
        Args:
            user_id: 用户ID
            stock_code: 股票代码
            
        Returns:
            持仓信息，不存在返回None
        """
        try:
            positions_col = self.db[self.POSITIONS_COLLECTION]
            position = positions_col.find_one({"user_id": user_id, "stock_code": stock_code})
            return position
        except Exception as e:
            self.logger.error(f"获取持仓信息失败: {e}")
            return None
    
    def create_or_update_position(self, position_data: Dict[str, Any]) -> bool:
        """
        创建或更新持仓
        
        Args:
            position_data: 持仓数据
            
        Returns:
            操作是否成功
        """
        try:
            positions_col = self.db[self.POSITIONS_COLLECTION]
            
            filter_query = {
                "user_id": position_data["user_id"],
                "stock_code": position_data["stock_code"]
            }
            
            position_data["update_time"] = datetime.now()
            
            result = positions_col.update_one(
                filter_query,
                {"$set": position_data},
                upsert=True
            )
            
            return result.upserted_id is not None or result.modified_count > 0
        except Exception as e:
            self.logger.error(f"创建或更新持仓失败: {e}")
            return False
    
    def delete_position(self, user_id: str, stock_code: str) -> bool:
        """
        删除持仓（当持仓为0时）
        
        Args:
            user_id: 用户ID
            stock_code: 股票代码
            
        Returns:
            删除是否成功
        """
        try:
            positions_col = self.db[self.POSITIONS_COLLECTION]
            result = positions_col.delete_one({"user_id": user_id, "stock_code": stock_code})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"删除持仓失败: {e}")
            return False
    
    # ==================== 交易记录操作 ====================
    
    def create_trade_record(self, trade_data: Dict[str, Any]) -> Optional[str]:
        """
        创建交易记录
        
        Args:
            trade_data: 交易数据
            
        Returns:
            交易ID，失败返回None
        """
        try:
            trades_col = self.db[self.TRADES_COLLECTION]
            
            # 生成唯一交易ID
            trade_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
            trade_data["trade_id"] = trade_id
            trade_data["trade_time"] = datetime.now()
            
            result = trades_col.insert_one(trade_data)
            
            if result.inserted_id:
                self.logger.info(f"交易记录创建成功: {trade_id}")
                return trade_id
            return None
            
        except Exception as e:
            self.logger.error(f"创建交易记录失败: {e}")
            return None
    
    def get_user_trades(self, user_id: str, limit: int = 100, 
                       skip: int = 0, stock_code: str = None,
                       start_date: date = None, end_date: date = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取用户交易记录
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            skip: 跳过数量
            stock_code: 股票代码筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            (交易记录列表, 总数)
        """
        try:
            trades_col = self.db[self.TRADES_COLLECTION]
            
            # 构建查询条件
            query = {"user_id": user_id}
            
            if stock_code:
                query["stock_code"] = stock_code
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = datetime.combine(start_date, datetime.min.time())
                if end_date:
                    date_filter["$lte"] = datetime.combine(end_date, datetime.max.time())
                query["trade_time"] = date_filter
            
            # 获取总数
            total = trades_col.count_documents(query)
            
            # 获取数据
            trades = list(trades_col.find(query)
                         .sort("trade_time", DESCENDING)
                         .skip(skip)
                         .limit(limit))
            
            return trades, total
            
        except Exception as e:
            self.logger.error(f"获取交易记录失败: {e}")
            return [], 0
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        根据交易ID获取交易记录
        
        Args:
            trade_id: 交易ID
            
        Returns:
            交易记录，不存在返回None
        """
        try:
            trades_col = self.db[self.TRADES_COLLECTION]
            trade = trades_col.find_one({"trade_id": trade_id})
            return trade
        except Exception as e:
            self.logger.error(f"获取交易记录失败: {e}")
            return None
    
    def update_trade_status(self, trade_id: str, status: TradeStatus) -> bool:
        """
        更新交易状态
        
        Args:
            trade_id: 交易ID
            status: 新状态
            
        Returns:
            更新是否成功
        """
        try:
            trades_col = self.db[self.TRADES_COLLECTION]
            result = trades_col.update_one(
                {"trade_id": trade_id},
                {"$set": {"status": status.value}}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"更新交易状态失败: {e}")
            return False
    
    # ==================== 账户快照操作 ====================
    
    def create_account_snapshot(self, user_id: str, snapshot_date: date, 
                              account_data: Dict[str, Any]) -> bool:
        """
        创建账户快照
        
        Args:
            user_id: 用户ID
            snapshot_date: 快照日期
            account_data: 账户数据
            
        Returns:
            创建是否成功
        """
        try:
            snapshots_col = self.db[self.SNAPSHOTS_COLLECTION]
            
            # 将date对象转换为datetime对象（MongoDB兼容）
            snapshot_datetime = datetime.combine(snapshot_date, datetime.min.time())
            
            snapshot_data = {
                "user_id": user_id,
                "snapshot_date": snapshot_datetime,
                "total_assets": account_data.get("total_assets", 0),
                "available_cash": account_data.get("available_cash", 0),
                "total_market_value": account_data.get("total_market_value", 0),
                "daily_return": account_data.get("daily_return", 0),
                "daily_return_rate": account_data.get("daily_return_rate", 0),
                "cumulative_return": account_data.get("total_return", 0),
                "cumulative_return_rate": account_data.get("total_return_rate", 0),
                "position_count": len(self.get_user_positions(user_id)),
                "trade_count": account_data.get("trade_count", 0),
                "create_time": datetime.now()
            }
            
            result = snapshots_col.update_one(
                {"user_id": user_id, "snapshot_date": snapshot_datetime},
                {"$set": snapshot_data},
                upsert=True
            )
            
            return result.upserted_id is not None or result.modified_count > 0
            
        except Exception as e:
            self.logger.error(f"创建账户快照失败: {e}")
            return False
    
    def get_account_snapshots(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取账户历史快照
        
        Args:
            user_id: 用户ID
            days: 获取最近多少天的数据
            
        Returns:
            快照列表
        """
        try:
            snapshots_col = self.db[self.SNAPSHOTS_COLLECTION]
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            snapshots = list(snapshots_col.find({
                "user_id": user_id,
                "snapshot_date": {"$gte": start_date, "$lte": end_date}
            }).sort("snapshot_date", ASCENDING))
            
            return snapshots
            
        except Exception as e:
            self.logger.error(f"获取账户快照失败: {e}")
            return []
    
    # ==================== 费用计算 ====================
    
    @staticmethod
    def calculate_trading_cost(amount: float, trade_type: TradeType, 
                             market: Market = Market.SH,
                             fee_config: TradingFeeConfig = None) -> TradingCostCalculation:
        """
        计算交易成本
        
        Args:
            amount: 交易金额
            trade_type: 交易类型
            market: 市场类型
            fee_config: 费用配置
            
        Returns:
            交易成本计算结果
        """
        if fee_config is None:
            fee_config = TradingFeeConfig()
        
        # 手续费（双向）
        commission = max(amount * fee_config.commission_rate, fee_config.commission_min)
        
        # 印花税（仅卖出）
        stamp_tax = amount * fee_config.stamp_tax_rate if trade_type == TradeType.SELL else 0
        
        # 过户费（双向，仅沪市）
        transfer_fee = amount * fee_config.transfer_fee_rate if market == Market.SH else 0
        
        # 滑点费（双向）
        slippage = amount * fee_config.slippage_rate
        
        total_cost = commission + stamp_tax + transfer_fee + slippage
        
        return TradingCostCalculation(
            commission=round(commission, 2),
            stamp_tax=round(stamp_tax, 2),
            transfer_fee=round(transfer_fee, 2),
            slippage=round(slippage, 2),
            total_cost=round(total_cost, 2)
        )
    
    # ==================== 实用工具方法 ====================
    
    def get_trading_unit(self, board_type: BoardType) -> int:
        """
        获取交易单位
        
        Args:
            board_type: 板块类型
            
        Returns:
            交易单位（股）
        """
        if board_type == BoardType.STAR:
            return 200  # 科创板200股为一手
        else:
            return 100  # 主板和创业板100股为一手
    
    def get_price_limit(self, board_type: BoardType, pre_close: float, is_st: bool = False) -> Tuple[float, float]:
        """
        获取涨跌停价格
        
        Args:
            board_type: 板块类型
            pre_close: 昨日收盘价
            is_st: 是否为ST股票
            
        Returns:
            (跌停价, 涨停价)
        """
        if is_st:
            limit_pct = 0.05  # ST股票5%
        elif board_type == BoardType.STAR:
            limit_pct = 0.20  # 科创板20%
        else:
            limit_pct = 0.10  # 主板和创业板10%
        
        lower_limit = round(pre_close * (1 - limit_pct), 2)
        upper_limit = round(pre_close * (1 + limit_pct), 2)
        
        return lower_limit, upper_limit
    
    def is_trading_time(self) -> bool:
        """
        判断是否为交易时间
        
        Returns:
            是否为交易时间
        """
        # 开发模式下允许任意时间交易
        import os
        if os.getenv('SIMULATION_DEV_MODE', 'false').lower() == 'true':
            return True
            
        now = datetime.now()
        
        # 周末不交易
        if now.weekday() >= 5:
            return False
        
        # 交易时间段
        morning_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
        morning_end = now.replace(hour=11, minute=30, second=0, microsecond=0)
        afternoon_start = now.replace(hour=13, minute=0, second=0, microsecond=0)
        afternoon_end = now.replace(hour=15, minute=0, second=0, microsecond=0)
        
        return (morning_start <= now <= morning_end) or (afternoon_start <= now <= afternoon_end)
    
    # ==================== 用户策略配置操作 ====================
    
    def create_user_strategy_config(self, user_id: str, strategy_name: str, 
                                  allocated_cash: float, custom_params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        创建用户策略配置
        
        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            allocated_cash: 分配资金
            custom_params: 自定义参数
            
        Returns:
            创建的策略配置信息
        """
        try:
            strategy_configs_col = self.db[self.STRATEGY_CONFIGS_COLLECTION]
            
            # 检查是否已存在相同配置
            existing_config = strategy_configs_col.find_one({
                "user_id": user_id,
                "strategy_name": strategy_name
            })
            
            if existing_config:
                self.logger.warning(f"用户 {user_id} 的策略 {strategy_name} 配置已存在")
                return existing_config
            
            # 创建新的策略配置
            config_data = {
                "user_id": user_id,
                "strategy_name": strategy_name,
                "is_active": False,
                "allocated_cash": allocated_cash,
                "custom_params": custom_params or {},
                "created_time": datetime.now(),
                "last_execution": None,
                "execution_count": 0,
                "total_trades": 0,
                "current_positions": []
            }
            
            result = strategy_configs_col.insert_one(config_data)
            
            if result.inserted_id:
                config_data["_id"] = result.inserted_id
                self.logger.info(f"策略配置创建成功: {user_id} - {strategy_name}")
                return config_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"创建策略配置失败: {e}")
            return None
    
    def get_user_strategy_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有策略配置
        
        Args:
            user_id: 用户ID
            
        Returns:
            策略配置列表
        """
        try:
            strategy_configs_col = self.db[self.STRATEGY_CONFIGS_COLLECTION]
            configs = list(strategy_configs_col.find({"user_id": user_id}))
            return configs
            
        except Exception as e:
            self.logger.error(f"获取策略配置失败: {e}")
            return []
    
    def get_user_strategy_config(self, user_id: str, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        获取用户特定策略配置
        
        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            
        Returns:
            策略配置信息
        """
        try:
            strategy_configs_col = self.db[self.STRATEGY_CONFIGS_COLLECTION]
            config = strategy_configs_col.find_one({
                "user_id": user_id,
                "strategy_name": strategy_name
            })
            return config
            
        except Exception as e:
            self.logger.error(f"获取策略配置失败: {e}")
            return None
    
    def update_strategy_status(self, user_id: str, strategy_name: str, is_active: bool) -> bool:
        """
        更新策略激活状态 - 使用upsert确保记录存在
        
        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            is_active: 是否激活
            
        Returns:
            更新是否成功
        """
        try:
            strategy_configs_col = self.db[self.STRATEGY_CONFIGS_COLLECTION]
            
            # 使用upsert操作，如果记录不存在则创建
            update_data = {
                "is_active": is_active,
                "last_update_time": datetime.now()
            }
            
            # 如果是新记录，设置默认值
            set_on_insert = {
                "user_id": user_id,
                "strategy_name": strategy_name,
                "allocated_cash": 300000.0,  # 默认分配资金
                "custom_params": {},
                "created_time": datetime.now(),
                "execution_count": 0,
                "total_trades": 0,
                "current_positions": []
            }
            
            result = strategy_configs_col.update_one(
                {"user_id": user_id, "strategy_name": strategy_name},
                {
                    "$set": update_data,
                    "$setOnInsert": set_on_insert
                },
                upsert=True  # 如果不存在则创建
            )
            
            if result.modified_count > 0 or result.upserted_id:
                operation = "创建" if result.upserted_id else "更新"
                self.logger.info(f"策略状态{operation}成功: {user_id} - {strategy_name} - {is_active}")
                return True
            
            self.logger.warning(f"策略状态未变更: {user_id} - {strategy_name} - {is_active}")
            return True  # 状态未变更也视为成功
            
        except Exception as e:
            self.logger.error(f"更新策略状态失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_strategy_execution_record(self, user_id: str, strategy_name: str, 
                                       execution_time: datetime, total_signals: int, 
                                       executed_trades: int, current_positions: List[str]) -> bool:
        """
        更新策略执行记录
        
        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            execution_time: 执行时间
            total_signals: 总信号数
            executed_trades: 执行的交易数
            current_positions: 当前持仓列表
            
        Returns:
            更新是否成功
        """
        try:
            strategy_configs_col = self.db[self.STRATEGY_CONFIGS_COLLECTION]
            result = strategy_configs_col.update_one(
                {"user_id": user_id, "strategy_name": strategy_name},
                {
                    "$set": {
                        "last_execution": execution_time,
                        "current_positions": current_positions
                    },
                    "$inc": {
                        "execution_count": 1,
                        "total_trades": executed_trades
                    }
                }
            )
            
            if result.modified_count > 0:
                self.logger.info(f"策略执行记录更新成功: {user_id} - {strategy_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"更新策略执行记录失败: {e}")
            return False
    
    def get_active_strategy_configs(self) -> List[Dict[str, Any]]:
        """
        获取所有激活的策略配置
        
        Returns:
            激活的策略配置列表
        """
        try:
            strategy_configs_col = self.db[self.STRATEGY_CONFIGS_COLLECTION]
            configs = list(strategy_configs_col.find({"is_active": True}))
            return configs
            
        except Exception as e:
            self.logger.error(f"获取激活策略配置失败: {e}")
            return []
    
    def delete_user_strategy_config(self, user_id: str, strategy_name: str) -> bool:
        """
        删除用户策略配置
        
        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            
        Returns:
            删除是否成功
        """
        try:
            strategy_configs_col = self.db[self.STRATEGY_CONFIGS_COLLECTION]
            result = strategy_configs_col.delete_one({
                "user_id": user_id,
                "strategy_name": strategy_name
            })
            
            if result.deleted_count > 0:
                self.logger.info(f"策略配置删除成功: {user_id} - {strategy_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"删除策略配置失败: {e}")
            return False


# 创建数据库操作实例
simulation_db = SimulationDatabase()