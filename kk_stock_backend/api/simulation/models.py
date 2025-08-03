"""
模拟交易系统数据模型

包含模拟账户、持仓、交易记录等数据结构定义
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class TradeType(str, Enum):
    """交易类型枚举"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """订单类型枚举"""
    MARKET = "MARKET"  # 市价单
    LIMIT = "LIMIT"    # 限价单


class TradeStatus(str, Enum):
    """交易状态枚举"""
    PENDING = "PENDING"    # 待成交
    FILLED = "FILLED"      # 已成交
    CANCELLED = "CANCELLED"  # 已撤销


class TradeSource(str, Enum):
    """交易来源枚举"""
    MANUAL = "MANUAL"      # 手动交易
    STRATEGY = "STRATEGY"  # 策略交易


class BoardType(str, Enum):
    """板块类型枚举"""
    MAIN = "MAIN"      # 主板
    GEM = "GEM"        # 创业板
    STAR = "STAR"      # 科创板


class Market(str, Enum):
    """市场类型枚举"""
    SH = "SH"  # 上海
    SZ = "SZ"  # 深圳


# ==================== 模拟账户相关模型 ====================

class SimulationAccount(BaseModel):
    """模拟账户数据模型"""
    user_id: str = Field(..., description="用户ID")
    account_name: str = Field(default="模拟账户", description="账户名称")
    initial_capital: float = Field(default=3000000.0, description="初始资金")
    available_cash: float = Field(..., description="可用现金")
    frozen_cash: float = Field(default=0.0, description="冻结资金")
    total_assets: float = Field(..., description="总资产")
    total_market_value: float = Field(default=0.0, description="持仓总市值")
    daily_return: float = Field(default=0.0, description="日收益金额")
    daily_return_rate: float = Field(default=0.0, description="日收益率")
    total_return: float = Field(default=0.0, description="总收益金额")
    total_return_rate: float = Field(default=0.0, description="总收益率")
    max_drawdown: float = Field(default=0.0, description="最大回撤")
    win_rate: float = Field(default=0.0, description="胜率")
    trade_count: int = Field(default=0, description="交易次数")
    profit_trades: int = Field(default=0, description="盈利交易次数")
    loss_trades: int = Field(default=0, description="亏损交易次数")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_update_time: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    status: int = Field(default=1, description="状态：1-正常，0-冻结")


class SimulationAccountCreate(BaseModel):
    """创建模拟账户请求模型"""
    user_id: str
    account_name: str = "模拟账户"
    initial_capital: float = 3000000.0


class SimulationAccountUpdate(BaseModel):
    """更新模拟账户请求模型"""
    account_name: Optional[str] = None
    status: Optional[int] = None


# ==================== 持仓相关模型 ====================

class SimulationPosition(BaseModel):
    """模拟持仓数据模型"""
    user_id: str = Field(..., description="用户ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    market: Market = Field(..., description="市场：SH-上海，SZ-深圳")
    board_type: BoardType = Field(..., description="板块类型")
    total_quantity: int = Field(..., description="总持股数量")
    available_quantity: int = Field(..., description="可卖数量（T+1限制）")
    frozen_quantity: int = Field(default=0, description="冻结数量")
    avg_cost: float = Field(..., description="平均成本价")
    current_price: float = Field(..., description="当前价格")
    market_value: float = Field(..., description="当前市值")
    cost_value: float = Field(..., description="成本市值")
    unrealized_pnl: float = Field(..., description="未实现盈亏")
    unrealized_pnl_rate: float = Field(..., description="未实现盈亏率")
    last_price_update: datetime = Field(default_factory=datetime.now, description="最后价格更新时间")
    position_date: date = Field(..., description="建仓日期")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")


# ==================== 交易相关模型 ====================

class SimulationTrade(BaseModel):
    """模拟交易记录数据模型"""
    user_id: str = Field(..., description="用户ID")
    trade_id: str = Field(..., description="交易ID（唯一）")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    trade_type: TradeType = Field(..., description="交易类型")
    order_type: OrderType = Field(..., description="订单类型")
    quantity: int = Field(..., description="交易数量")
    price: float = Field(..., description="成交价格")
    amount: float = Field(..., description="成交金额")
    commission: float = Field(..., description="手续费")
    stamp_tax: float = Field(..., description="印花税")
    transfer_fee: float = Field(..., description="过户费")
    slippage: float = Field(..., description="滑点费用")
    total_cost: float = Field(..., description="总成本")
    trade_source: TradeSource = Field(..., description="交易来源")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    trade_time: datetime = Field(default_factory=datetime.now, description="交易时间")
    settlement_date: date = Field(..., description="交割日期（T+1）")
    status: TradeStatus = Field(default=TradeStatus.FILLED, description="状态")
    remarks: Optional[str] = Field(None, description="备注")


class TradeRequest(BaseModel):
    """交易请求模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    trade_type: TradeType = Field(..., description="交易类型")
    order_type: OrderType = Field(default=OrderType.MARKET, description="订单类型")
    quantity: int = Field(..., description="交易数量")
    price: Optional[float] = Field(None, description="价格（限价单必填）")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    remarks: Optional[str] = Field(None, description="备注")


class BuyRequest(TradeRequest):
    """买入请求模型"""
    trade_type: TradeType = Field(default=TradeType.BUY, description="交易类型")


class SellRequest(TradeRequest):
    """卖出请求模型"""  
    trade_type: TradeType = Field(default=TradeType.SELL, description="交易类型")


# ==================== 账户快照相关模型 ====================

class AccountSnapshot(BaseModel):
    """账户历史快照数据模型"""
    user_id: str = Field(..., description="用户ID")
    snapshot_date: date = Field(..., description="快照日期")
    total_assets: float = Field(..., description="总资产")
    available_cash: float = Field(..., description="可用现金")
    total_market_value: float = Field(..., description="持仓总市值")
    daily_return: float = Field(..., description="日收益")
    daily_return_rate: float = Field(..., description="日收益率")
    cumulative_return: float = Field(..., description="累计收益")
    cumulative_return_rate: float = Field(..., description="累计收益率")
    position_count: int = Field(..., description="持仓数量")
    trade_count: int = Field(..., description="当日交易次数")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")


# ==================== 响应模型 ====================

class SimulationAccountResponse(BaseModel):
    """模拟账户响应模型"""
    user_id: str
    account_name: str
    initial_capital: float
    available_cash: float
    frozen_cash: float
    total_assets: float
    total_market_value: float
    daily_return: float
    daily_return_rate: float
    total_return: float
    total_return_rate: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    profit_trades: int
    loss_trades: int
    create_time: datetime
    last_update_time: datetime
    status: int


class SimulationPositionResponse(BaseModel):
    """模拟持仓响应模型"""
    user_id: str
    stock_code: str
    stock_name: str
    market: str
    board_type: str
    total_quantity: int
    available_quantity: int
    frozen_quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    cost_value: float
    unrealized_pnl: float
    unrealized_pnl_rate: float
    last_price_update: datetime
    position_date: date
    update_time: datetime


class SimulationTradeResponse(BaseModel):
    """模拟交易响应模型"""
    user_id: str
    trade_id: str
    stock_code: str
    stock_name: str
    trade_type: str
    order_type: str
    quantity: int
    price: float
    amount: float
    commission: float
    stamp_tax: float
    transfer_fee: float
    slippage: float
    total_cost: float
    trade_source: str
    strategy_name: Optional[str]
    trade_time: datetime
    settlement_date: date
    status: str
    remarks: Optional[str]


# ==================== 分页和查询模型 ====================

class PageRequest(BaseModel):
    """分页请求模型"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")


class TradeHistoryQuery(PageRequest):
    """交易历史查询模型"""
    stock_code: Optional[str] = None
    trade_type: Optional[TradeType] = None
    trade_source: Optional[TradeSource] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PageResponse(BaseModel):
    """分页响应模型"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class SimulationTradeListResponse(PageResponse):
    """模拟交易列表响应模型"""
    data: List[SimulationTradeResponse]


class SimulationPositionListResponse(BaseModel):
    """模拟持仓列表响应模型"""
    total: int
    data: List[SimulationPositionResponse]


# ==================== 费用配置模型 ====================

class TradingFeeConfig(BaseModel):
    """交易费用配置模型"""
    commission_rate: float = Field(default=0.0001, description="手续费率（万1）")
    commission_min: float = Field(default=5.0, description="最低手续费")
    stamp_tax_rate: float = Field(default=0.001, description="印花税率（千1，仅卖出）")
    transfer_fee_rate: float = Field(default=0.00002, description="过户费率（万0.2）")
    slippage_rate: float = Field(default=0.001, description="滑点费率（千1）")


class TradingCostCalculation(BaseModel):
    """交易成本计算结果"""
    commission: float = Field(..., description="手续费")
    stamp_tax: float = Field(..., description="印花税")
    transfer_fee: float = Field(..., description="过户费")
    slippage: float = Field(..., description="滑点费")
    total_cost: float = Field(..., description="总成本")


# ==================== 股价数据模型 ====================

class StockQuote(BaseModel):
    """股票报价模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前价格")
    open_price: float = Field(..., description="开盘价")
    high_price: float = Field(..., description="最高价")
    low_price: float = Field(..., description="最低价")
    pre_close: float = Field(..., description="昨收价")
    change: float = Field(..., description="涨跌额")
    change_pct: float = Field(..., description="涨跌幅")
    volume: int = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")


class BatchQuoteRequest(BaseModel):
    """批量获取股价请求模型"""
    stock_codes: List[str] = Field(..., description="股票代码列表")


class BatchQuoteResponse(BaseModel):
    """批量获取股价响应模型"""
    quotes: List[StockQuote] = Field(..., description="股价列表")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")