"""
模拟交易系统业务逻辑层

处理模拟交易的核心业务逻辑，包括买卖交易、持仓管理、账户更新等
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import asyncio

from .database import simulation_db
from .models import (
    TradeType, TradeStatus, OrderType, TradeSource, BoardType, Market,
    TradingFeeConfig, StockQuote, BuyRequest, SellRequest
)
from api.db_handler import get_db_handler


class SimulationTradingService:
    """模拟交易业务服务类"""
    
    def __init__(self):
        self.db = simulation_db
        self.logger = logging.getLogger(__name__)
        self.fee_config = TradingFeeConfig()
        
        # 股票数据库处理器
        self.stock_db_handler = get_db_handler()
    
    # ==================== 账户管理 ====================
    
    async def init_user_account(self, user_id: str, initial_capital: float = 3000000.0) -> Optional[Dict[str, Any]]:
        """
        初始化用户模拟账户
        
        Args:
            user_id: 用户ID
            initial_capital: 初始资金
            
        Returns:
            账户信息
        """
        try:
            account = self.db.create_simulation_account(user_id, initial_capital)
            if account:
                self.logger.info(f"用户 {user_id} 模拟账户初始化成功")
                return account
            return None
        except Exception as e:
            self.logger.error(f"初始化用户账户失败: {e}")
            return None
    
    async def get_account_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取账户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            账户信息
        """
        try:
            account = self.db.get_simulation_account(user_id)
            if account:
                # 实时更新持仓市值
                await self._update_account_market_value(user_id)
                # 重新获取更新后的账户信息
                account = self.db.get_simulation_account(user_id)
            return account
        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}")
            return None
    
    async def reset_account(self, user_id: str) -> bool:
        """
        重置用户账户
        
        Args:
            user_id: 用户ID
            
        Returns:
            重置是否成功
        """
        try:
            success = self.db.reset_simulation_account(user_id)
            if success:
                self.logger.info(f"用户 {user_id} 账户重置成功")
            return success
        except Exception as e:
            self.logger.error(f"重置账户失败: {e}")
            return False
    
    # ==================== 持仓管理 ====================
    
    async def get_user_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户持仓列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            持仓列表
        """
        try:
            positions = self.db.get_user_positions(user_id)
            
            # 更新持仓的当前价格和市值
            for position in positions:
                current_price = await self._get_current_stock_price(position["stock_code"])
                if current_price:
                    position["current_price"] = current_price
                    position["market_value"] = position["total_quantity"] * current_price
                    position["unrealized_pnl"] = position["market_value"] - position["cost_value"]
                    if position["cost_value"] > 0:
                        position["unrealized_pnl_rate"] = position["unrealized_pnl"] / position["cost_value"]
                    else:
                        position["unrealized_pnl_rate"] = 0.0
                    position["last_price_update"] = datetime.now()
            
            return positions
        except Exception as e:
            self.logger.error(f"获取用户持仓失败: {e}")
            return []
    
    async def get_position(self, user_id: str, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票持仓
        
        Args:
            user_id: 用户ID
            stock_code: 股票代码
            
        Returns:
            持仓信息
        """
        try:
            position = self.db.get_position(user_id, stock_code)
            if position:
                # 更新当前价格
                current_price = await self._get_current_stock_price(stock_code)
                if current_price:
                    position["current_price"] = current_price
                    position["market_value"] = position["total_quantity"] * current_price
                    position["unrealized_pnl"] = position["market_value"] - position["cost_value"]
                    if position["cost_value"] > 0:
                        position["unrealized_pnl_rate"] = position["unrealized_pnl"] / position["cost_value"]
                    else:
                        position["unrealized_pnl_rate"] = 0.0
                    position["last_price_update"] = datetime.now()
            return position
        except Exception as e:
            self.logger.error(f"获取持仓信息失败: {e}")
            return None
    
    # ==================== 交易执行 ====================
    
    async def execute_buy_order(self, user_id: str, buy_request: BuyRequest) -> Optional[str]:
        """
        执行买入订单
        
        Args:
            user_id: 用户ID
            buy_request: 买入请求
            
        Returns:
            交易ID，失败返回None
        """
        try:
            # 1. 验证账户
            account = self.db.get_simulation_account(user_id)
            if not account:
                raise ValueError("用户账户不存在")
            
            if account["status"] != 1:
                raise ValueError("账户已冻结")
            
            # 2. 验证交易时间
            if not self.db.is_trading_time():
                raise ValueError("当前不在交易时间")
            
            # 3. 获取股票信息和当前价格
            stock_info = await self._get_stock_info(buy_request.stock_code)
            if not stock_info:
                raise ValueError("股票信息不存在")
            
            current_price = await self._get_current_stock_price(buy_request.stock_code)
            if not current_price:
                raise ValueError("无法获取股票当前价格")
            
            # 4. 确定成交价格和涨跌停检查
            board_type = self._get_board_type(buy_request.stock_code)
            is_st = 'ST' in stock_info.get('name', '') or 'st' in stock_info.get('name', '')
            
            if buy_request.order_type == OrderType.MARKET:
                trade_price = current_price
            else:
                trade_price = buy_request.price or current_price
                
                # 限价单价格合理性检查
                pre_close = stock_info.get('pre_close', current_price)
                lower_limit, upper_limit = self.db.get_price_limit(board_type, pre_close, is_st)
                
                if trade_price < lower_limit or trade_price > upper_limit:
                    raise ValueError(f"价格超出涨跌停范围 [{lower_limit:.2f}, {upper_limit:.2f}]")
            
            # 5. 验证交易数量
            trading_unit = self.db.get_trading_unit(board_type)
            
            if buy_request.quantity <= 0:
                raise ValueError("交易数量必须大于0")
                
            if buy_request.quantity % trading_unit != 0:
                raise ValueError(f"交易数量必须是{trading_unit}股的整数倍")
            
            # 6. 计算交易金额和费用
            amount = buy_request.quantity * trade_price
            market = self._get_market(buy_request.stock_code)
            cost_calculation = self.db.calculate_trading_cost(
                amount, TradeType.BUY, market, self.fee_config
            )
            
            total_cost = amount + cost_calculation.total_cost
            
            # 7. 验证资金是否充足
            if account["available_cash"] < total_cost:
                available_formatted = f"{account['available_cash']:,.2f}"
                required_formatted = f"{total_cost:,.2f}"
                raise ValueError(f"资金不足，可用资金: {available_formatted}，需要资金: {required_formatted}")
            
            # 8. 检查单只股票持仓限制（不超过总资产的20%）
            max_single_position = account["total_assets"] * 0.2
            if total_cost > max_single_position:
                raise ValueError(f"单只股票投资不能超过总资产的20%（{max_single_position:,.2f}元）")
            
            # 9. 创建交易记录
            trade_data = {
                "user_id": user_id,
                "stock_code": buy_request.stock_code,
                "stock_name": buy_request.stock_name,
                "trade_type": TradeType.BUY.value,
                "order_type": buy_request.order_type.value,
                "quantity": buy_request.quantity,
                "price": trade_price,
                "amount": amount,
                "commission": cost_calculation.commission,
                "stamp_tax": cost_calculation.stamp_tax,
                "transfer_fee": cost_calculation.transfer_fee,
                "slippage": cost_calculation.slippage,
                "total_cost": total_cost,
                "trade_source": TradeSource.MANUAL.value,
                "strategy_name": buy_request.strategy_name,
                "settlement_date": self._get_settlement_date(),
                "status": TradeStatus.FILLED.value,
                "remarks": buy_request.remarks
            }
            
            trade_id = self.db.create_trade_record(trade_data)
            if not trade_id:
                raise ValueError("创建交易记录失败")
            
            # 10. 更新持仓
            await self._update_position_after_buy(
                user_id, buy_request.stock_code, buy_request.stock_name,
                buy_request.quantity, trade_price, board_type, market
            )
            
            # 11. 更新账户资金
            new_available_cash = account["available_cash"] - total_cost
            self.db.update_simulation_account(user_id, {
                "available_cash": new_available_cash,
                "trade_count": account["trade_count"] + 1
            })
            
            # 12. 更新账户总资产和收益
            await self._update_account_assets(user_id)
            
            self.logger.info(f"用户 {user_id} 买入 {buy_request.stock_code} 成功，交易ID: {trade_id}")
            return trade_id
            
        except Exception as e:
            self.logger.error(f"执行买入订单失败: {e}")
            raise e
    
    async def execute_sell_order(self, user_id: str, sell_request: SellRequest) -> Optional[str]:
        """
        执行卖出订单
        
        Args:
            user_id: 用户ID
            sell_request: 卖出请求
            
        Returns:
            交易ID，失败返回None
        """
        try:
            # 1. 验证账户
            account = self.db.get_simulation_account(user_id)
            if not account:
                raise ValueError("用户账户不存在")
            
            if account["status"] != 1:
                raise ValueError("账户已冻结")
            
            # 2. 验证交易时间
            if not self.db.is_trading_time():
                raise ValueError("当前不在交易时间")
            
            # 3. 获取持仓信息
            position = self.db.get_position(user_id, sell_request.stock_code)
            if not position:
                raise ValueError("无持仓记录")
            
            # 4. 验证卖出数量
            if sell_request.quantity <= 0:
                raise ValueError("卖出数量必须大于0")
                
            if sell_request.quantity > position["total_quantity"]:
                raise ValueError(f"卖出数量超过持有数量，当前持有: {position['total_quantity']}股")
            
            # 5. 验证可卖数量（T+1限制）
            if sell_request.quantity > position["available_quantity"]:
                raise ValueError(f"可卖数量不足（T+1限制），当前可卖: {position['available_quantity']}股")
            
            # 6. 获取股票信息和当前价格
            stock_info = await self._get_stock_info(sell_request.stock_code)
            current_price = await self._get_current_stock_price(sell_request.stock_code)
            if not current_price:
                raise ValueError("无法获取股票当前价格")
            
            # 7. 确定成交价格和涨跌停检查
            board_type = self._get_board_type(sell_request.stock_code)
            is_st = stock_info and ('ST' in stock_info.get('name', '') or 'st' in stock_info.get('name', ''))
            
            if sell_request.order_type == OrderType.MARKET:
                trade_price = current_price
            else:
                trade_price = sell_request.price or current_price
                
                # 限价单价格合理性检查
                if stock_info:
                    pre_close = stock_info.get('pre_close', current_price)
                    lower_limit, upper_limit = self.db.get_price_limit(board_type, pre_close, is_st)
                    
                    if trade_price < lower_limit or trade_price > upper_limit:
                        raise ValueError(f"价格超出涨跌停范围 [{lower_limit:.2f}, {upper_limit:.2f}]")
            
            # 8. 计算交易金额和费用
            amount = sell_request.quantity * trade_price
            market = self._get_market(sell_request.stock_code)
            cost_calculation = self.db.calculate_trading_cost(
                amount, TradeType.SELL, market, self.fee_config
            )
            
            net_amount = amount - cost_calculation.total_cost
            
            # 9. 计算本次交易盈亏
            cost_amount = sell_request.quantity * position["avg_cost"]
            pnl = net_amount - cost_amount
            pnl_rate = pnl / cost_amount if cost_amount > 0 else 0
            
            # 10. 创建交易记录
            trade_data = {
                "user_id": user_id,
                "stock_code": sell_request.stock_code,
                "stock_name": sell_request.stock_name,
                "trade_type": TradeType.SELL.value,
                "order_type": sell_request.order_type.value,
                "quantity": sell_request.quantity,
                "price": trade_price,
                "amount": amount,
                "commission": cost_calculation.commission,
                "stamp_tax": cost_calculation.stamp_tax,
                "transfer_fee": cost_calculation.transfer_fee,
                "slippage": cost_calculation.slippage,
                "total_cost": cost_calculation.total_cost,
                "trade_source": TradeSource.MANUAL.value,
                "strategy_name": sell_request.strategy_name,
                "settlement_date": self._get_settlement_date(),
                "status": TradeStatus.FILLED.value,
                "remarks": f"{sell_request.remarks or ''} 盈亏: {pnl:+.2f}元({pnl_rate:+.2%})".strip()
            }
            
            trade_id = self.db.create_trade_record(trade_data)
            if not trade_id:
                raise ValueError("创建交易记录失败")
            
            # 11. 更新持仓
            await self._update_position_after_sell(
                user_id, sell_request.stock_code, sell_request.quantity, trade_price
            )
            
            # 12. 更新账户资金和统计
            new_available_cash = account["available_cash"] + net_amount
            
            # 判断是否盈利交易
            if pnl > 0:
                profit_trades = account["profit_trades"] + 1
                loss_trades = account["loss_trades"]
            elif pnl < 0:
                profit_trades = account["profit_trades"]
                loss_trades = account["loss_trades"] + 1
            else:
                profit_trades = account["profit_trades"]
                loss_trades = account["loss_trades"]
            
            # 更新胜率
            total_sell_trades = profit_trades + loss_trades
            win_rate = profit_trades / total_sell_trades if total_sell_trades > 0 else 0
            
            self.db.update_simulation_account(user_id, {
                "available_cash": new_available_cash,
                "trade_count": account["trade_count"] + 1,
                "profit_trades": profit_trades,
                "loss_trades": loss_trades,
                "win_rate": win_rate
            })
            
            # 13. 更新账户总资产和收益
            await self._update_account_assets(user_id)
            
            self.logger.info(f"用户 {user_id} 卖出 {sell_request.stock_code} 成功，交易ID: {trade_id}，盈亏: {pnl:+.2f}元")
            return trade_id
            
        except Exception as e:
            self.logger.error(f"执行卖出订单失败: {e}")
            raise e
    
    # ==================== 私有辅助方法 ====================
    
    async def _get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        try:
            # 尝试多个可能的股票基本信息集合
            possible_collections = [
                "infrastructure_stock_basic",  # 优先使用这个集合
                "stock_basic",
                "basic_stock_info",
                "stocks"
            ]
            
            for collection_name in possible_collections:
                try:
                    collection = self.stock_db_handler.get_collection(collection_name)
                    stock_info = collection.find_one({"ts_code": stock_code})
                    if stock_info:
                        self.logger.debug(f"在集合 {collection_name} 中找到股票 {stock_code}")
                        return stock_info
                except Exception:
                    continue
            
            self.logger.warning(f"在所有集合中都未找到股票 {stock_code}")
            return None
        except Exception as e:
            self.logger.error(f"获取股票信息失败: {e}")
            return None
    
    async def _get_current_stock_price(self, stock_code: str) -> Optional[float]:
        """获取股票当前价格"""
        try:
            # 从日线数据中获取最新价格
            collection = self.stock_db_handler.get_collection("stock_kline_daily")
            latest_data = collection.find_one(
                {"ts_code": stock_code},
                sort=[("trade_date", -1)]
            )
            
            if latest_data and "close" in latest_data:
                return float(latest_data["close"])
            
            return None
        except Exception as e:
            self.logger.error(f"获取股票价格失败: {e}")
            return None
    
    async def _get_stock_price_by_date(self, stock_code: str, trade_date: str) -> Optional[float]:
        """获取股票指定日期的收盘价
        
        Args:
            stock_code: 股票代码
            trade_date: 交易日期，格式：YYYYMMDD
            
        Returns:
            指定日期的收盘价，失败返回None
        """
        try:
            collection = self.stock_db_handler.get_collection("stock_kline_daily")
            data = collection.find_one({
                "ts_code": stock_code,
                "trade_date": trade_date
            })
            
            if data and "close" in data:
                return float(data["close"])
            
            return None
        except Exception as e:
            self.logger.error(f"获取股票 {stock_code} 在 {trade_date} 的价格失败: {e}")
            return None
    
    def _get_board_type(self, stock_code: str) -> BoardType:
        """根据股票代码判断板块类型"""
        if stock_code.startswith("688"):
            return BoardType.STAR  # 科创板
        elif stock_code.startswith("300"):
            return BoardType.GEM   # 创业板
        else:
            return BoardType.MAIN  # 主板
    
    def _get_market(self, stock_code: str) -> Market:
        """根据股票代码判断市场"""
        if stock_code.endswith(".SH") or stock_code.startswith(("600", "601", "603", "605", "688")):
            return Market.SH  # 上海
        else:
            return Market.SZ  # 深圳
    
    def _get_settlement_date(self) -> str:
        """获取交割日期（T+1）"""
        today = date.today()
        # 简化处理，实际应考虑节假日
        settlement_date = today + timedelta(days=1)
        return settlement_date.strftime("%Y-%m-%d")
    
    async def _update_position_after_buy(self, user_id: str, stock_code: str, stock_name: str,
                                       quantity: int, price: float, board_type: BoardType, market: Market):
        """买入后更新持仓"""
        try:
            existing_position = self.db.get_position(user_id, stock_code)
            
            if existing_position:
                # 更新现有持仓
                old_total_quantity = existing_position["total_quantity"]
                old_cost_value = existing_position["cost_value"]
                
                new_total_quantity = old_total_quantity + quantity
                new_cost_value = old_cost_value + (quantity * price)
                new_avg_cost = new_cost_value / new_total_quantity
                
                position_data = {
                    "user_id": user_id,
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "market": market.value,
                    "board_type": board_type.value,
                    "total_quantity": new_total_quantity,
                    "available_quantity": existing_position["available_quantity"],  # T+1限制
                    "frozen_quantity": existing_position["frozen_quantity"],
                    "avg_cost": new_avg_cost,
                    "current_price": price,
                    "market_value": new_total_quantity * price,
                    "cost_value": new_cost_value,
                    "unrealized_pnl": (new_total_quantity * price) - new_cost_value,
                    "unrealized_pnl_rate": ((new_total_quantity * price) - new_cost_value) / new_cost_value,
                    "position_date": existing_position["position_date"]
                }
            else:
                # 创建新持仓
                position_data = {
                    "user_id": user_id,
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "market": market.value,
                    "board_type": board_type.value,
                    "total_quantity": quantity,
                    "available_quantity": 0,  # T+1限制，当日买入不能卖出
                    "frozen_quantity": 0,
                    "avg_cost": price,
                    "current_price": price,
                    "market_value": quantity * price,
                    "cost_value": quantity * price,
                    "unrealized_pnl": 0.0,
                    "unrealized_pnl_rate": 0.0,
                    "position_date": datetime.now()
                }
            
            self.db.create_or_update_position(position_data)
            
        except Exception as e:
            self.logger.error(f"更新买入后持仓失败: {e}")
            raise e
    
    async def _update_position_after_sell(self, user_id: str, stock_code: str, quantity: int, price: float):
        """卖出后更新持仓"""
        try:
            position = self.db.get_position(user_id, stock_code)
            if not position:
                raise ValueError("持仓记录不存在")
            
            new_total_quantity = position["total_quantity"] - quantity
            new_available_quantity = position["available_quantity"] - quantity
            
            if new_total_quantity <= 0:
                # 清仓，删除持仓记录
                self.db.delete_position(user_id, stock_code)
            else:
                # 更新持仓数量
                # 成本价不变，因为是按原成本价计算
                new_cost_value = position["avg_cost"] * new_total_quantity
                new_market_value = new_total_quantity * price
                
                position_data = {
                    "user_id": user_id,
                    "stock_code": stock_code,
                    "stock_name": position["stock_name"],
                    "market": position["market"],
                    "board_type": position["board_type"],
                    "total_quantity": new_total_quantity,
                    "available_quantity": new_available_quantity,
                    "frozen_quantity": position["frozen_quantity"],
                    "avg_cost": position["avg_cost"],
                    "current_price": price,
                    "market_value": new_market_value,
                    "cost_value": new_cost_value,
                    "unrealized_pnl": new_market_value - new_cost_value,
                    "unrealized_pnl_rate": (new_market_value - new_cost_value) / new_cost_value if new_cost_value > 0 else 0,
                    "position_date": position["position_date"]
                }
                
                self.db.create_or_update_position(position_data)
                
        except Exception as e:
            self.logger.error(f"更新卖出后持仓失败: {e}")
            raise e
    
    async def _update_account_market_value(self, user_id: str):
        """更新账户持仓市值"""
        try:
            positions = self.db.get_user_positions(user_id)
            total_market_value = 0.0
            
            for position in positions:
                current_price = await self._get_current_stock_price(position["stock_code"])
                if current_price:
                    market_value = position["total_quantity"] * current_price
                    total_market_value += market_value
                    
                    # 更新持仓当前价格和市值
                    self.db.create_or_update_position({
                        **position,
                        "current_price": current_price,
                        "market_value": market_value,
                        "unrealized_pnl": market_value - position["cost_value"],
                        "unrealized_pnl_rate": (market_value - position["cost_value"]) / position["cost_value"] if position["cost_value"] > 0 else 0,
                        "last_price_update": datetime.now()
                    })
            
            # 更新账户持仓总市值
            self.db.update_simulation_account(user_id, {
                "total_market_value": total_market_value
            })
            
        except Exception as e:
            self.logger.error(f"更新账户市值失败: {e}")
    
    async def _update_account_assets(self, user_id: str):
        """更新账户总资产和收益"""
        try:
            account = self.db.get_simulation_account(user_id)
            if not account:
                return
            
            # 更新持仓市值
            await self._update_account_market_value(user_id)
            
            # 重新获取账户信息
            account = self.db.get_simulation_account(user_id)
            
            # 计算总资产
            total_assets = account["available_cash"] + account["frozen_cash"] + account["total_market_value"]
            
            # 调试日志
            self.logger.info(f"账户资产计算 - 用户ID: {user_id}")
            self.logger.info(f"可用现金: {account['available_cash']:,.2f}")
            self.logger.info(f"冻结现金: {account['frozen_cash']:,.2f}")
            self.logger.info(f"持仓市值: {account['total_market_value']:,.2f}")
            self.logger.info(f"总资产: {total_assets:,.2f}")
            self.logger.info(f"初始资金: {account['initial_capital']:,.2f}")
            
            # 计算收益
            total_return = total_assets - account["initial_capital"]
            total_return_rate = total_return / account["initial_capital"] if account["initial_capital"] > 0 else 0
            
            self.logger.info(f"总收益: {total_return:,.2f}")
            self.logger.info(f"总收益率: {total_return_rate:.2f}%")
            
            # 更新账户数据（不包含日收益，由调度器负责更新）
            update_data = {
                "total_assets": total_assets,
                "total_return": total_return,
                "total_return_rate": total_return_rate
            }
            
            self.db.update_simulation_account(user_id, update_data)
            
        except Exception as e:
            self.logger.error(f"更新账户资产失败: {e}")
    
    # ==================== T+1处理 ====================
    
    async def process_t_plus_one_settlement(self):
        """处理T+1交割，释放可卖数量"""
        try:
            today = date.today()
            today_str = today.strftime("%Y-%m-%d")  # 转换为字符串格式
            
            # 查找今日需要交割的买入交易（settlement_date = today）
            trades_col = self.stock_db_handler.get_collection(self.db.TRADES_COLLECTION)
            buy_trades = trades_col.find({
                "trade_type": TradeType.BUY.value,
                "settlement_date": today_str,
                "status": TradeStatus.FILLED.value
            })
            
            settlement_count = 0
            
            for trade in buy_trades:
                try:
                    user_id = trade["user_id"]
                    stock_code = trade["stock_code"]
                    quantity = trade["quantity"]
                    
                    # 更新持仓可卖数量
                    position = self.db.get_position(user_id, stock_code)
                    if position:
                        new_available_quantity = position["available_quantity"] + quantity
                        
                        # 确保不超过总持仓数量
                        if new_available_quantity > position["total_quantity"]:
                            new_available_quantity = position["total_quantity"]
                        
                        self.db.create_or_update_position({
                            **position,
                            "available_quantity": new_available_quantity
                        })
                        
                        settlement_count += 1
                        self.logger.info(f"T+1交割: 用户 {user_id} 股票 {stock_code} 可卖数量增加 {quantity} 股")
                    else:
                        self.logger.warning(f"T+1交割失败: 用户 {user_id} 股票 {stock_code} 持仓不存在")
                        
                except Exception as e:
                    self.logger.error(f"处理单笔T+1交割失败: {e}")
                    continue
            
            self.logger.info(f"T+1交割处理完成，共处理 {settlement_count} 笔交易")
            
        except Exception as e:
            self.logger.error(f"T+1交割处理失败: {e}")
    
    # ==================== 账户快照 ====================
    
    async def create_daily_snapshot(self, user_id: str):
        """创建每日账户快照"""
        try:
            account = await self.get_account_info(user_id)
            if account:
                today = date.today()
                self.db.create_account_snapshot(user_id, today, account)
                self.logger.info(f"用户 {user_id} 每日快照创建成功")
        except Exception as e:
            self.logger.error(f"创建每日快照失败: {e}")
    
    # ==================== 交易记录查询 ====================
    
    async def get_trade_history(self, user_id: str, page: int = 1, page_size: int = 20,
                              stock_code: str = None, start_date: date = None, 
                              end_date: date = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取交易历史
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小
            stock_code: 股票代码筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            (交易记录列表, 总数)
        """
        try:
            skip = (page - 1) * page_size
            trades, total = self.db.get_user_trades(
                user_id, limit=page_size, skip=skip,
                stock_code=stock_code, start_date=start_date, end_date=end_date
            )
            return trades, total
        except Exception as e:
            self.logger.error(f"获取交易历史失败: {e}")
            return [], 0


# 创建服务实例
simulation_service = SimulationTradingService()