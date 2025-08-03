#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一回测API接口
提供策略回测、实时数据推送、参数配置、结果分析等功能
合并了原有的 backtest.py 和 backtest_realtime.py
"""

from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
import logging
import uuid
import asyncio
import json
import os
import sys
import jwt
from dotenv import load_dotenv

# 添加项目根目录到路径以导入回测模块
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(api_dir)
sys.path.insert(0, project_root)

load_dotenv()

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"

try:
    from api.cache_middleware import cache_endpoint
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False
    def cache_endpoint(data_type='', ttl=3600):
        def decorator(func):
            return func
        return decorator

try:
    HAS_DB_HANDLER = True
except ImportError:
    HAS_DB_HANDLER = False

try:
    from routers.user import get_current_user
    HAS_USER_AUTH = True
except ImportError:
    HAS_USER_AUTH = False
    async def get_current_user():
        return {"user_id": "anonymous", "role": "user"}

def get_user_dependency():
    """根据认证可用性返回用户依赖"""
    if HAS_USER_AUTH:
        return Depends(get_current_user)
    else:
        # 返回一个直接返回匿名用户的依赖
        def anonymous_user():
            return {"user_id": "anonymous", "role": "user"}
        return Depends(anonymous_user)

# 全局任务存储 - 用于实时任务状态和数据管理
active_tasks: Dict[str, Dict[str, Any]] = {}

# WebSocket连接管理器
class WebSocketConnectionManager:
    """WebSocket连接管理器"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.task_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str = None):
        """建立WebSocket连接"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        if connection_id not in self.active_connections:
            self.active_connections[connection_id] = []
        self.active_connections[connection_id].append(websocket)
        
        if task_id:
            if task_id not in self.task_connections:
                self.task_connections[task_id] = []
            self.task_connections[task_id].append(websocket)
            logger.info(f"WebSocket连接已建立: task_id={task_id}, connection_id={connection_id}")
        else:
            logger.info(f"WebSocket连接已建立: connection_id={connection_id}")
        
        return connection_id
    
    def disconnect(self, websocket: WebSocket, task_id: str = None):
        """断开WebSocket连接"""
        # 从活跃连接中移除
        for conn_id, connections in self.active_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.active_connections[conn_id]
                break
        
        # 从任务连接中移除
        if task_id and task_id in self.task_connections:
            if websocket in self.task_connections[task_id]:
                self.task_connections[task_id].remove(websocket)
                if not self.task_connections[task_id]:
                    del self.task_connections[task_id]
                logger.info(f"WebSocket连接已断开: task_id={task_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
    
    async def broadcast_to_task(self, message: Dict[str, Any], task_id: str):
        """向指定任务的所有连接广播消息"""
        if task_id in self.task_connections:
            disconnected = []
            for websocket in self.task_connections[task_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"WebSocket广播失败: {e}")
                    disconnected.append(websocket)
            
            # 清理断开的连接
            for websocket in disconnected:
                self.disconnect(websocket, task_id)
    
    def get_task_connection_count(self, task_id: str) -> int:
        """获取任务的连接数量"""
        return len(self.task_connections.get(task_id, []))

# 全局WebSocket管理器实例
ws_manager = WebSocketConnectionManager()

# 日志配置
logger = logging.getLogger(__name__)

# =============================================================================
# 数据模型定义
# =============================================================================

class TradingConfig(BaseModel):
    """交易配置参数"""
    commission_rate: float = Field(default=0.0001, description="手续费率")
    stamp_tax_rate: float = Field(default=0.001, description="印花税率")
    min_commission: float = Field(default=5.0, description="最小手续费")

class RiskConfig(BaseModel):
    """风险控制配置"""
    max_positions: int = Field(default=10, description="最大持仓数量")
    max_single_position: float = Field(default=0.1, description="单个股票最大仓位")
    stop_loss_pct: float = Field(default=0.1, description="止损百分比")
    take_profit_pct: float = Field(default=0.15, description="止盈百分比")
    max_drawdown_limit: float = Field(default=0.2, description="最大回撤限制")

class MultiTrendParams(BaseModel):
    """多趋势共振策略参数"""
    sma_short: int = Field(default=5, description="短期均线周期")
    sma_medium: int = Field(default=20, description="中期均线周期")
    sma_long: int = Field(default=60, description="长期均线周期")
    rsi_period: int = Field(default=14, description="RSI周期")
    rsi_oversold: float = Field(default=30, description="RSI超卖阈值")
    rsi_overbought: float = Field(default=70, description="RSI超买阈值")
    min_resonance_score: float = Field(default=6.0, description="最小共振分数")
    volume_ratio_threshold: float = Field(default=1.2, description="成交量比率阈值")

class BollParams(BaseModel):
    """布林带策略参数"""
    boll_period: int = Field(default=20, description="布林带周期")
    boll_std: float = Field(default=2.0, description="布林带标准差倍数")
    rsi_period: int = Field(default=14, description="RSI周期")
    volume_threshold: float = Field(default=1.5, description="成交量阈值")
    volatility_threshold: float = Field(default=0.02, description="波动率阈值")

class TaiShang3FactorParams(BaseModel):
    """太上三因子策略参数"""
    lookback_period: int = Field(default=20, description="回看周期")
    momentum_weight: float = Field(default=0.4, description="动量因子权重")
    quality_weight: float = Field(default=0.3, description="质量因子权重")
    value_weight: float = Field(default=0.3, description="价值因子权重")

class BacktestConfig(BaseModel):
    """回测配置"""
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: str = Field(..., description="策略类型")
    initial_cash: float = Field(default=1000000.0, description="初始资金")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    index_code: str = Field(default="000510.CSI", description="指数代码")
    stock_pool: Optional[List[str]] = Field(default=None, description="自定义股票池")
    max_stocks: int = Field(default=50, description="最大股票数量")
    benchmark: str = Field(default="000300.SH", description="基准指数代码")
    
    # 交易成本配置 - 支持扁平化参数（优先级高于trading_config）
    commission_rate: Optional[float] = Field(default=0.0001, description="手续费率")
    stamp_tax_rate: Optional[float] = Field(default=0.001, description="印花税率")
    slippage_rate: Optional[float] = Field(default=0.001, description="滑点率")
    min_commission: Optional[float] = Field(default=5.0, description="最小手续费")
    
    # 嵌套配置对象（向后兼容）
    trading_config: Optional[TradingConfig] = Field(default=None)
    risk_config: RiskConfig = Field(default_factory=RiskConfig)
    strategy_params: Union[MultiTrendParams, BollParams, TaiShang3FactorParams, None] = Field(default=None)

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('结束日期必须大于开始日期')
        return v

class BacktestTask(BaseModel):
    """回测任务"""
    task_id: str
    user_id: str
    status: str
    progress: float
    message: str
    config: Optional[BacktestConfig] = None
    result: Optional[Dict] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class BacktestResult(BaseModel):
    """回测结果"""
    backtest_config: Dict[str, Any]
    strategy_info: Dict[str, Any]
    performance_report: Dict[str, Any]
    portfolio_summary: Dict[str, Any]
    trading_summary: Dict[str, Any]
    chart_files: List[str] = []
    chart_data: Optional[Dict[str, Any]] = None
    benchmark_data: Optional[Dict[str, Any]] = None
    
    class Config:
        # 允许额外的字段，提高兼容性
        extra = "allow"

class StrategyInfo(BaseModel):
    """策略信息"""
    strategy_type: str
    strategy_name: str
    description: str
    default_params: Dict[str, Any]
    param_ranges: Dict[str, Any]

# =============================================================================
# 认证相关函数
# =============================================================================

async def get_current_user_sse(token: Optional[str] = Query(None, description="认证Token")):
    """SSE专用用户验证，支持查询参数传递Token"""
    if not token:
        raise HTTPException(status_code=401, detail="缺少认证Token")
    
    try:
        # 导入MongoDB连接配置
        from .user import users_col
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token无效")
        
        user = users_col.find_one({"user_id": user_id, "status": 1})
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在或已禁用")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except Exception:
        raise HTTPException(status_code=401, detail="Token无效")

# =============================================================================
# 回测引擎相关函数
# =============================================================================

# 模拟回测引擎导入
class FallbackBacktestEngine:
    """回测引擎的备用实现"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def run_strategy_backtest(self, *args, **kwargs):
        """模拟回测执行"""
        raise HTTPException(
            status_code=503, 
            detail="回测模块暂时不可用，请稍后重试"
        )

try:
    # 尝试导入实际的回测模块
    sys.path.append('/Users/libing/kk_Projects/kk_Stock/kk_stock_backend')
    from backtrader_strategies.backtest.backtest_engine import run_strategy_backtest
    HAS_BACKTEST_ENGINE = True
    logger.info("回测引擎模块加载成功")
except Exception as e:
    logger.warning(f"回测引擎模块加载失败: {e}")
    HAS_BACKTEST_ENGINE = False
    run_strategy_backtest = FallbackBacktestEngine().run_strategy_backtest

# 创建路由器
router = APIRouter(tags=["统一回测接口"])

# =============================================================================
# 策略配置相关函数
# =============================================================================

def get_strategy_class(strategy_type: str):
    """根据策略类型获取对应的策略类"""
    try:
        # 动态导入策略类
        if strategy_type == 'multi_trend':
            from backtrader_strategies.multi_trend_strategy_adapter import MultiTrendResonanceStrategyAdapter
            return MultiTrendResonanceStrategyAdapter
        elif strategy_type == 'boll':
            from backtrader_strategies.curious_ragdoll_boll_strategy_adapter import CuriousRagdollBollStrategyAdapter
            return CuriousRagdollBollStrategyAdapter
        elif strategy_type == 'taishang_3factor':
            from backtrader_strategies.taishang_3_factor_strategy_adapter import TaiShang3FactorStrategyAdapter
            return TaiShang3FactorStrategyAdapter
        else:
            return None
    except ImportError as e:
        logger.error(f"策略类导入失败: {e}")
        return None

def create_strategy_config(config: BacktestConfig):
    """创建策略配置对象"""
    try:
        # 导入Config类
        from backtrader_strategies.config import Config
        
        # 创建Config实例
        strategy_config = Config()
        
        # 设置策略名称和类型
        strategy_config.strategy_name = config.strategy_name
        strategy_config.strategy_type = config.strategy_type
        
        # 设置回测配置
        strategy_config.backtest.initial_cash = config.initial_cash
        strategy_config.backtest.start_date = config.start_date.strftime('%Y-%m-%d')
        strategy_config.backtest.end_date = config.end_date.strftime('%Y-%m-%d')
        strategy_config.backtest.index_code = config.index_code
        strategy_config.backtest.max_stocks = config.max_stocks
        
        # 设置交易配置 - 优先使用扁平化参数，如果没有则使用trading_config
        commission_rate = config.commission_rate if config.commission_rate is not None else (config.trading_config.commission_rate if config.trading_config else 0.0001)
        stamp_tax_rate = config.stamp_tax_rate if config.stamp_tax_rate is not None else (config.trading_config.stamp_tax_rate if config.trading_config else 0.001)
        min_commission = config.min_commission if config.min_commission is not None else (config.trading_config.min_commission if config.trading_config else 5.0)
        slippage_rate = config.slippage_rate if config.slippage_rate is not None else 0.001
        
        strategy_config.backtest.commission_rate = commission_rate
        strategy_config.backtest.stamp_tax_rate = stamp_tax_rate
        strategy_config.backtest.min_commission = min_commission
        strategy_config.backtest.slippage_rate = slippage_rate
        
        # 设置风险配置
        strategy_config.strategy.max_positions = config.risk_config.max_positions
        strategy_config.strategy.max_single_position = config.risk_config.max_single_position
        strategy_config.strategy.stop_loss_pct = config.risk_config.stop_loss_pct
        strategy_config.strategy.take_profit_pct = config.risk_config.take_profit_pct
        strategy_config.strategy.max_drawdown_limit = config.risk_config.max_drawdown_limit
        
        return strategy_config
        
    except ImportError as e:
        logger.error(f"Config类导入失败: {e}")
        # 回退到字典格式
        strategy_config = {
            'strategy_name': config.strategy_name,
            'backtest': {
                'initial_cash': config.initial_cash,
                'start_date': config.start_date.strftime('%Y-%m-%d'),
                'end_date': config.end_date.strftime('%Y-%m-%d'),
                'index_code': config.index_code,
                'max_stocks': config.max_stocks
            },
            'trading': {
                'commission_rate': config.commission_rate if config.commission_rate is not None else (config.trading_config.commission_rate if config.trading_config else 0.0001),
                'stamp_tax_rate': config.stamp_tax_rate if config.stamp_tax_rate is not None else (config.trading_config.stamp_tax_rate if config.trading_config else 0.001),
                'min_commission': config.min_commission if config.min_commission is not None else (config.trading_config.min_commission if config.trading_config else 5.0),
                'slippage_rate': config.slippage_rate if config.slippage_rate is not None else 0.001
            },
            'strategy': {
                'max_positions': config.risk_config.max_positions,
                'max_single_position': config.risk_config.max_single_position,
                'stop_loss_pct': config.risk_config.stop_loss_pct,
                'take_profit_pct': config.risk_config.take_profit_pct,
                'max_drawdown_limit': config.risk_config.max_drawdown_limit
            }
        }
    
        # 添加策略特定参数到字典版本
        if config.strategy_params:
            if config.strategy_type == 'multi_trend' and isinstance(config.strategy_params, MultiTrendParams):
                strategy_config['multi_trend'] = {
                    'sma_short': config.strategy_params.sma_short,
                    'sma_medium': config.strategy_params.sma_medium,
                    'sma_long': config.strategy_params.sma_long,
                    'rsi_period': config.strategy_params.rsi_period,
                    'rsi_oversold': config.strategy_params.rsi_oversold,
                    'rsi_overbought': config.strategy_params.rsi_overbought,
                    'min_score': config.strategy_params.min_resonance_score / 11.0,
                    'volume_ratio_threshold': config.strategy_params.volume_ratio_threshold
                }
            elif config.strategy_type == 'boll' and isinstance(config.strategy_params, BollParams):
                strategy_config['boll'] = {
                    'boll_period': config.strategy_params.boll_period,
                    'boll_std': config.strategy_params.boll_std,
                    'rsi_period': config.strategy_params.rsi_period,
                    'volume_ratio_threshold': config.strategy_params.volume_threshold,
                    'volatility_threshold': config.strategy_params.volatility_threshold
                }
            elif config.strategy_type == 'taishang_3factor' and isinstance(config.strategy_params, TaiShang3FactorParams):
                strategy_config['taishang_3factor'] = {
                    'lookback_period': config.strategy_params.lookback_period,
                    'momentum_weight': config.strategy_params.momentum_weight,
                    'quality_weight': config.strategy_params.quality_weight,
                    'value_weight': config.strategy_params.value_weight
                }
        
        return strategy_config
    
    # 对于成功创建的Config对象，添加策略特定参数
    if config.strategy_params:
        if config.strategy_type == 'multi_trend' and isinstance(config.strategy_params, MultiTrendParams):
            strategy_config.multi_trend.sma_short = config.strategy_params.sma_short
            strategy_config.multi_trend.sma_medium = config.strategy_params.sma_medium
            strategy_config.multi_trend.sma_long = config.strategy_params.sma_long
            strategy_config.multi_trend.rsi_period = config.strategy_params.rsi_period
            strategy_config.multi_trend.rsi_oversold = config.strategy_params.rsi_oversold
            strategy_config.multi_trend.rsi_overbought = config.strategy_params.rsi_overbought
            strategy_config.multi_trend.min_score = config.strategy_params.min_resonance_score / 11.0
            strategy_config.multi_trend.volume_ratio_threshold = config.strategy_params.volume_ratio_threshold
        elif config.strategy_type == 'boll' and isinstance(config.strategy_params, BollParams):
            strategy_config.boll.boll_period = config.strategy_params.boll_period
            strategy_config.boll.boll_std = config.strategy_params.boll_std
            strategy_config.boll.rsi_period = config.strategy_params.rsi_period
            strategy_config.boll.volume_ratio_threshold = config.strategy_params.volume_threshold
            strategy_config.boll.volatility_threshold = config.strategy_params.volatility_threshold
        elif config.strategy_type == 'taishang_3factor' and isinstance(config.strategy_params, TaiShang3FactorParams):
            strategy_config.rim_strategy.lookback_period = config.strategy_params.lookback_period
            strategy_config.rim_strategy.momentum_weight = config.strategy_params.momentum_weight
            strategy_config.rim_strategy.quality_weight = config.strategy_params.quality_weight
            strategy_config.rim_strategy.value_weight = config.strategy_params.value_weight
    
    return strategy_config

def get_benchmark_data(benchmark_code: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    获取基准指数数据
    
    Args:
        benchmark_code: 指数代码，如'000300.SH'
        start_date: 开始日期，格式'YYYY-MM-DD'
        end_date: 结束日期，格式'YYYY-MM-DD'
    
    Returns:
        基准指数数据列表
    """
    if not HAS_DB_HANDLER:
        logger.warning("数据库处理器不可用，返回空基准数据")
        return []
    
    try:
        collection = db_handler.get_collection('index_daily')
        
        # 构建查询条件 - 使用字符串比较
        start_date_str = start_date.replace('-', '')
        end_date_str = end_date.replace('-', '')
        
        logger.info(f"查询基准数据: {benchmark_code}, 日期范围: {start_date_str} - {end_date_str}")
        
        query = {
            'ts_code': benchmark_code,
            'trade_date': {
                '$gte': start_date_str,
                '$lte': end_date_str
            }
        }
        
        # 获取数据并按日期排序
        data = list(collection.find(query).sort('trade_date', 1))
        logger.info(f"从数据库获取到 {len(data)} 条基准数据记录")
        
        # 处理数据，返回标准格式
        benchmark_data = []
        for item in data:
            try:
                # 计算收益率
                close_price = float(item.get('close', 0))
                prev_close = float(item.get('pre_close', close_price))
                daily_return = (close_price - prev_close) / prev_close if prev_close > 0 else 0
                
                formatted_data = {
                    'date': f"{item['trade_date'][:4]}-{item['trade_date'][4:6]}-{item['trade_date'][6:8]}",
                    'close': close_price,
                    'daily_return': daily_return,
                    'volume': float(item.get('vol', 0))
                }
                benchmark_data.append(formatted_data)
                
                # 添加调试日志
                if len(benchmark_data) <= 3:
                    logger.info(f"基准数据样本: {formatted_data}")
                    
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"处理基准数据时出错: {e}, 数据: {item}")
                continue
        
        logger.info(f"成功获取基准指数{benchmark_code}数据: {len(benchmark_data)}条记录")
        return benchmark_data
        
    except Exception as e:
        logger.error(f"获取基准指数数据失败: {e}")
        return []

def calculate_benchmark_returns(benchmark_data: List[Dict[str, Any]]) -> List[float]:
    """
    计算基准指数的累计收益率序列
    
    Args:
        benchmark_data: 基准指数数据
        
    Returns:
        累计收益率序列
    """
    if not benchmark_data:
        logger.warning("基准数据为空，返回空收益率序列")
        return []
    
    cumulative_returns = []
    cumulative_return = 0.0
    
    logger.info(f"开始计算基准收益率，数据点数: {len(benchmark_data)}")
    
    for i, data_point in enumerate(benchmark_data):
        daily_return = data_point.get('daily_return', 0)
        cumulative_return = (1 + cumulative_return) * (1 + daily_return) - 1
        cumulative_returns.append(cumulative_return)
        
        # 记录前几个数据点的计算过程
        if i < 3:
            logger.info(f"基准计算第{i+1}天: 日收益={daily_return:.6f}, 累计收益={cumulative_return:.6f}")
    
    logger.info(f"基准收益率计算完成，最终收益率: {cumulative_returns[-1]:.6f}")
    return cumulative_returns

# =============================================================================
# 回测任务管理
# =============================================================================

async def run_backtest_task(task_id: str, config: BacktestConfig, user_id: str):
    """运行回测任务的后台函数"""
    try:
        # 更新任务状态为运行中
        if task_id in active_tasks:
            active_tasks[task_id].update({
                'status': 'running',
                'started_at': datetime.now(),
                'message': '回测开始执行',
                'progress': 0.0
            })
        
        # 创建策略配置
        strategy_config = create_strategy_config(config)
        strategy_class = get_strategy_class(config.strategy_type)
        
        if not strategy_class:
            raise ValueError(f"不支持的策略类型: {config.strategy_type}")
        
        # 执行回测
        logger.info(f"开始执行回测任务 {task_id}")
        # 创建策略实例
        strategy_instance = strategy_class()
        result = run_strategy_backtest(
            strategy=strategy_instance,
            config=strategy_config,
            task_id=task_id,
            active_tasks=active_tasks  # 传递给回测引擎用于实时更新
        )
        
        # 获取基准指数数据并添加到结果中
        try:
            # 使用用户指定的基准指数
            benchmark_code = config.benchmark
            logger.info(f"🎯 准备获取基准指数数据: {benchmark_code}")
            benchmark_data = get_benchmark_data(
                benchmark_code=benchmark_code,
                start_date=str(config.start_date),
                end_date=str(config.end_date)
            )
            
            if benchmark_data:
                logger.info(f"✅ 成功获取基准数据: {len(benchmark_data)}条记录")
                benchmark_returns = calculate_benchmark_returns(benchmark_data)
                final_return = benchmark_returns[-1] if benchmark_returns else 0
                logger.info(f"📊 基准指数最终收益率: {final_return:.4f} ({final_return*100:.2f}%)")
                
                # 添加基准数据到结果中
                result['benchmark_data'] = {
                    'benchmark_code': benchmark_code,
                    'benchmark_name': benchmark_code,  # 使用代码作为名称
                    'data': benchmark_data,
                    'cumulative_returns': benchmark_returns,
                    'final_return': final_return
                }
                logger.info(f"✅ 已添加基准指数数据到回测结果: {len(benchmark_returns)}个收益率数据点")
            else:
                logger.warning("❌ 未能获取基准指数数据，基准收益将显示为0")
                
        except Exception as e:
            logger.error(f"处理基准指数数据时出错: {e}")
        
        # 更新任务完成状态
        if task_id in active_tasks:
            active_tasks[task_id].update({
                'status': 'completed',
                'completed_at': datetime.now(),
                'progress': 1.0,
                'message': '回测完成',
                'result': result
            })
            
            # 尝试从结果中提取和存储结果目录路径信息
            try:
                if 'chart_data' in result and result['chart_data']:
                    # 根据策略名称映射到实际目录名
                    strategy_mapping = {
                        'multi_trend': 'MultiTrendResonanceStrategyAdapter',
                        'boll': 'CuriousRagdollBollStrategyAdapter', 
                        'taishang_3_factor': 'TaiShang3FactorStrategyAdapter'
                    }
                    strategy_name = strategy_mapping.get(config.strategy_type, config.strategy_type)
                    
                    # 查找最新的结果目录（基于修改时间）
                    import os
                    import glob
                    results_dir = "/Users/libing/kk_Projects/kk_Stock/kk_stock_backend/results"
                    strategy_dir = os.path.join(results_dir, strategy_name)
                    
                    if os.path.exists(strategy_dir):
                        # 获取该策略下最新的时间戳目录
                        subdirs = [d for d in os.listdir(strategy_dir) if os.path.isdir(os.path.join(strategy_dir, d))]
                        if subdirs:
                            latest_dir = max(subdirs)
                            result_dir_path = os.path.join(strategy_dir, latest_dir)
                            
                            # 验证该目录是否包含交易文件
                            trades_file = os.path.join(result_dir_path, f"{strategy_name}_trades.csv")
                            if os.path.exists(trades_file):
                                active_tasks[task_id]['result_dir'] = result_dir_path
                                logger.info(f"📁 存储结果目录路径: {result_dir_path}")
                            
            except Exception as e:
                logger.warning(f"存储结果目录路径失败: {e}")
        
        logger.info(f"回测任务 {task_id} 完成")
        
    except Exception as e:
        logger.error(f"回测任务 {task_id} 失败: {e}")
        if task_id in active_tasks:
            active_tasks[task_id].update({
                'status': 'failed',
                'completed_at': datetime.now(),
                'progress': 0.0,
                'message': f'回测失败: {str(e)}'
            })

# =============================================================================
# 实时数据推送 (SSE)
# =============================================================================

async def sse_generator(task_id: str, data_type: str = "realtime"):
    """SSE数据流生成器"""
    logger.info(f"开始SSE流推送 for task {task_id}, data_type: {data_type}")
    
    # 初始化状态跟踪
    last_progress_data = None
    last_portfolio_data = None
    last_chart_data = None
    last_trades_count = 0
    
    try:
        while True:
            if task_id not in active_tasks:
                # 任务不存在，发送错误并结束
                yield f"event: error\ndata: {json.dumps({'error': '任务不存在', 'task_id': task_id})}\n\n"
                break
                
            task_info = active_tasks[task_id]
            current_time = datetime.now().isoformat()
            has_new_data = False
            
            if data_type == "progress" or data_type == "realtime":
                # 进度数据 - 只在发生变化时推送
                current_progress = {
                    "progress": task_info.get('progress', 0.0),
                    "status": task_info.get('status', 'pending'),
                    "current_date": task_info.get('current_date'),
                    "message": task_info.get('message', ''),
                    "completed_days": task_info.get('completed_days', 0)
                }
                
                # 检查进度是否有变化
                if not last_progress_data or current_progress != last_progress_data:
                    progress_data = {
                        "type": "progress",
                        "task_id": task_id,
                        "status": current_progress['status'],
                        "progress": current_progress['progress'],
                        "message": current_progress['message'],
                        "current_date": current_progress['current_date'],
                        "timestamp": current_time,
                        "processing_speed": task_info.get('processing_speed', 0),
                        "estimated_remaining": task_info.get('estimated_remaining', 0)
                    }
                    yield f"event: progress\ndata: {json.dumps(progress_data)}\n\n"
                    last_progress_data = current_progress
                    has_new_data = True
            
            if data_type == "portfolio" or data_type == "realtime":
                # 组合数据 - 检查是否有新的日期数据
                current_portfolio = {
                    "current_date": task_info.get('current_date', ''),
                    "total_value": task_info.get('current_portfolio_value', task_info.get('config', {}).get('initial_cash', 1000000.0)),
                    "total_return": task_info.get('total_return', 0.0),
                    "daily_return": task_info.get('daily_return', 0.0),
                    "drawdown": task_info.get('current_drawdown', 0.0)
                }
                
                # 检查是否有新数据：日期变化或数据更新标志
                data_updated_flag = task_info.get('data_updated', False)
                date_changed = (current_portfolio['current_date'] and 
                               (not last_portfolio_data or 
                                current_portfolio['current_date'] != last_portfolio_data.get('current_date')))
                
                if date_changed or data_updated_flag:
                    logger.info(f"🔍 检测到数据变化: date_changed={date_changed}, data_updated_flag={data_updated_flag}, current_date={current_portfolio['current_date']}")
                    
                    portfolio_data = {
                        "type": "portfolio",
                        "task_id": task_id,
                        "timestamp": current_time,
                        "current_date": current_portfolio['current_date'],
                        "portfolio": {
                            "total_value": current_portfolio['total_value'],
                            "cash": task_info.get('current_cash', 0.0),
                            "positions_value": task_info.get('current_positions_value', 0.0),
                            "positions": task_info.get('current_positions', []),
                            "daily_return": current_portfolio['daily_return'],
                            "total_return": current_portfolio['total_return'],
                            "drawdown": current_portfolio['drawdown']
                        }
                    }
                    yield f"event: portfolio\ndata: {json.dumps(portfolio_data)}\n\n"
                    logger.info(f"🔄 SSE推送Portfolio数据: {current_portfolio['current_date']}, 组合价值: {current_portfolio['total_value']:,.2f}")
                    last_portfolio_data = current_portfolio
                    has_new_data = True
                    # 重置数据更新标志
                    if 'data_updated' in task_info:
                        task_info['data_updated'] = False
            
            if data_type == "trades" or data_type == "realtime":
                # 交易数据 - 只在有新交易时推送
                current_trades_count = task_info.get('total_trades', 0)
                recent_trades = task_info.get('recent_trades', [])
                
                if current_trades_count > last_trades_count and recent_trades:
                    trades_data = {
                        "type": "trades",
                        "task_id": task_id,
                        "timestamp": current_time,
                        "current_date": task_info.get('current_date', ''),
                        "recent_trades": recent_trades,
                        "trade_stats": {
                            "total_trades": current_trades_count,
                            "buy_trades": task_info.get('buy_trades', 0),
                            "sell_trades": task_info.get('sell_trades', 0),
                            "win_trades": task_info.get('win_trades', 0),
                            "lose_trades": task_info.get('lose_trades', 0),
                            "win_rate": task_info.get('win_rate', 0.0),
                            "total_pnl": task_info.get('total_pnl', 0.0),
                            "avg_win": task_info.get('avg_win', 0.0),
                            "avg_loss": task_info.get('avg_loss', 0.0),
                            "profit_factor": task_info.get('profit_factor', 0.0)
                        }
                    }
                    yield f"event: trades\ndata: {json.dumps(trades_data)}\n\n"
                    last_trades_count = current_trades_count
                    has_new_data = True
            
            if data_type == "chart" or data_type == "realtime":
                # 图表数据 - 检查是否有新的日期数据点
                current_chart_data = {
                    "current_date": task_info.get('current_date', ''),
                    "dates_count": len(task_info.get('date_series', [])),
                    "latest_portfolio_value": task_info.get('portfolio_series', [])[-1] if task_info.get('portfolio_series') else 0
                }
                
                if not last_chart_data or current_chart_data['dates_count'] > last_chart_data.get('dates_count', 0):
                    chart_data = {
                        "type": "chart",
                        "task_id": task_id,
                        "timestamp": current_time,
                        "current_date": current_chart_data['current_date'],
                        "data": {
                            "dates": task_info.get('date_series', []),
                            "portfolio_values": task_info.get('portfolio_series', []),
                            "daily_returns": task_info.get('daily_return_series', []),
                            "cumulative_returns": task_info.get('cumulative_return_series', []),
                            "drawdowns": task_info.get('drawdown_series', [])
                        }
                    }
                    yield f"event: chart\ndata: {json.dumps(chart_data)}\n\n"
                    last_chart_data = current_chart_data
                    has_new_data = True
            
            # 检查任务完成状态
            status = task_info.get('status', 'pending')
            if status in ['completed', 'failed']:
                # 发送最终完成事件
                final_data = {
                    "type": "final",
                    "task_id": task_id,
                    "status": status,
                    "timestamp": current_time,
                    "message": task_info.get('message', ''),
                    "result_available": True
                }
                yield f"event: final\ndata: {json.dumps(final_data)}\n\n"
                
                # 等待客户端处理，然后优雅关闭
                await asyncio.sleep(3)
                logger.info(f"SSE stream gracefully ended for {status} task {task_id}")
                break
            
            # 动态调整推送频率：有新数据时频繁推送，无新数据时降低频率
            if has_new_data:
                await asyncio.sleep(0.05)  # 有新数据时每0.05秒检查一次，确保实时性
            else:
                await asyncio.sleep(0.5)   # 无新数据时每0.5秒检查一次
            
    except asyncio.CancelledError:
        logger.info(f"SSE stream cancelled for task {task_id}")
    except Exception as e:
        logger.error(f"SSE stream error for task {task_id}: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e), 'task_id': task_id})}\n\n"

def update_task_realtime_data(task_id: str, update_data: Dict[str, Any]):
    """更新任务的实时数据"""
    if task_id in active_tasks:
        active_tasks[task_id].update(update_data)

# =============================================================================
# API 端点定义 - 基础管理接口
# =============================================================================

@router.get("/strategies", response_model=List[StrategyInfo])
async def get_available_strategies():
    """获取可用策略列表"""
    strategies = [
        {
            "strategy_type": "multi_trend",
            "strategy_name": "多趋势共振策略",
            "description": "基于多时间周期技术指标的共振分析，通过短中长期均线、RSI、成交量等指标的综合判断来识别趋势",
            "default_params": {
                "sma_short": 5,
                "sma_medium": 20,
                "sma_long": 60,
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "min_resonance_score": 6.0,
                "volume_ratio_threshold": 1.2
            },
            "param_ranges": {
                "sma_short": {"min": 3, "max": 10, "step": 1},
                "sma_medium": {"min": 10, "max": 30, "step": 1},
                "sma_long": {"min": 30, "max": 120, "step": 1},
                "rsi_period": {"min": 10, "max": 20, "step": 1},
                "rsi_oversold": {"min": 20, "max": 40, "step": 1},
                "rsi_overbought": {"min": 60, "max": 80, "step": 1},
                "min_resonance_score": {"min": 4.0, "max": 8.0, "step": 0.5},
                "volume_ratio_threshold": {"min": 1.0, "max": 2.0, "step": 0.1}
            }
        },
        {
            "strategy_type": "boll",
            "strategy_name": "布林带策略",
            "description": "基于布林带指标的均值回归策略，结合RSI和成交量指标进行买卖时机判断",
            "default_params": {
                "boll_period": 20,
                "boll_std": 2.0,
                "rsi_period": 14,
                "volume_threshold": 1.5,
                "volatility_threshold": 0.02
            },
            "param_ranges": {
                "boll_period": {"min": 10, "max": 30, "step": 1},
                "boll_std": {"min": 1.5, "max": 3.0, "step": 0.1},
                "rsi_period": {"min": 10, "max": 20, "step": 1},
                "volume_threshold": {"min": 1.0, "max": 3.0, "step": 0.1},
                "volatility_threshold": {"min": 0.01, "max": 0.05, "step": 0.001}
            }
        },
        {
            "strategy_type": "taishang_3factor",
            "strategy_name": "太上三因子策略",
            "description": "基于动量、质量、价值三个因子的多因子选股策略，通过因子加权评分选择优质股票",
            "default_params": {
                "lookback_period": 20,
                "momentum_weight": 0.4,
                "quality_weight": 0.3,
                "value_weight": 0.3
            },
            "param_ranges": {
                "lookback_period": {"min": 10, "max": 60, "step": 1},
                "momentum_weight": {"min": 0.2, "max": 0.6, "step": 0.05},
                "quality_weight": {"min": 0.1, "max": 0.5, "step": 0.05},
                "value_weight": {"min": 0.1, "max": 0.5, "step": 0.05}
            }
        }
    ]
    return strategies

@router.get("/config-templates")
async def get_config_templates():
    """获取配置模板"""
    templates = {
        "conservative": {
            "name": "保守型",
            "risk_config": {
                "max_positions": 8,
                "max_single_position": 0.08,
                "stop_loss_pct": 0.08,
                "take_profit_pct": 0.12,
                "max_drawdown_limit": 0.15
            }
        },
        "balanced": {
            "name": "平衡型",
            "risk_config": {
                "max_positions": 10,
                "max_single_position": 0.1,
                "stop_loss_pct": 0.1,
                "take_profit_pct": 0.15,
                "max_drawdown_limit": 0.2
            }
        },
        "aggressive": {
            "name": "激进型",
            "risk_config": {
                "max_positions": 12,
                "max_single_position": 0.15,
                "stop_loss_pct": 0.12,
                "take_profit_pct": 0.2,
                "max_drawdown_limit": 0.25
            }
        }
    }
    return templates

@router.post("/run", response_model=BacktestTask)
async def run_backtest(
    config: BacktestConfig = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = get_user_dependency()
):
    """启动回测任务"""
    if not HAS_BACKTEST_ENGINE:
        raise HTTPException(status_code=503, detail="回测引擎暂时不可用")
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    user_id = current_user.get('user_id', 'anonymous')
    
    # 调试：打印接收到的配置
    logger.info(f"🔍 后端接收的配置: strategy_name={config.strategy_name}, strategy_type={config.strategy_type}")
    
    # 创建任务记录
    task = BacktestTask(
        task_id=task_id,
        user_id=user_id,
        status='pending',
        progress=0.0,
        message='任务已创建，等待执行',
        config=config,
        created_at=datetime.now()
    )
    
    # 存储到活动任务中
    active_tasks[task_id] = {
        'task_id': task_id,
        'user_id': user_id,
        'status': 'pending',
        'progress': 0.0,
        'message': '任务已创建，等待执行',
        'config': config.dict(),
        'created_at': datetime.now(),
        'started_at': None,
        'completed_at': None,
        'result': None
    }
    
    # 添加后台任务
    background_tasks.add_task(run_backtest_task, task_id, config, user_id)
    
    logger.info(f"创建回测任务: {task_id}")
    return task

@router.get("/task/{task_id}", response_model=BacktestTask)
async def get_task_status(task_id: str, current_user: dict = get_user_dependency()):
    """获取任务状态"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = active_tasks[task_id]
    user_id = current_user.get('user_id', 'anonymous')
    
    # 检查权限
    if task['user_id'] != user_id and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="无权访问此任务")
    
    return BacktestTask(**task)

@router.get("/tasks", response_model=Dict[str, Any])
async def get_user_tasks(
    status: Optional[str] = Query(None, description="任务状态过滤"),
    limit: int = Query(10, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = get_user_dependency()
):
    """获取用户任务列表"""
    user_id = current_user.get('user_id', 'anonymous')
    is_admin = current_user.get('role') == 'admin'
    
    # 过滤用户的任务
    user_tasks = []
    for task in active_tasks.values():
        if is_admin or task['user_id'] == user_id:
            if not status or task['status'] == status:
                user_tasks.append(task)
    
    # 按创建时间倒序排序
    user_tasks.sort(key=lambda x: x['created_at'], reverse=True)
    
    # 统计
    stats = {
        'total': len(user_tasks),
        'pending': len([t for t in user_tasks if t['status'] == 'pending']),
        'running': len([t for t in user_tasks if t['status'] == 'running']),
        'completed': len([t for t in user_tasks if t['status'] == 'completed']),
        'failed': len([t for t in user_tasks if t['status'] == 'failed'])
    }
    
    # 分页
    paginated_tasks = user_tasks[offset:offset + limit]
    
    return {
        'tasks': [BacktestTask(**task) for task in paginated_tasks],
        'total': len(paginated_tasks),
        'total_count': len(user_tasks),
        'stats': stats
    }

@router.delete("/task/{task_id}")
async def delete_task(task_id: str, current_user: dict = get_user_dependency()):
    """删除任务"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = active_tasks[task_id]
    user_id = current_user.get('user_id', 'anonymous')
    
    # 检查权限
    if task['user_id'] != user_id and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="无权删除此任务")
    
    # 不能删除正在运行的任务
    if task['status'] == 'running':
        raise HTTPException(status_code=400, detail="不能删除正在运行的任务")
    
    # 删除任务
    del active_tasks[task_id]
    
    return {"message": "任务已删除", "task_id": task_id}

# =============================================================================
# 结果查询接口
# =============================================================================

@router.get("/result/{task_id}", response_model=BacktestResult)
async def get_backtest_result(task_id: str, current_user: dict = get_user_dependency()):
    """获取回测结果"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = active_tasks[task_id]
    user_id = current_user.get('user_id', 'anonymous')
    
    # 检查权限
    if task['user_id'] != user_id and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="无权访问此任务")
    
    if task['status'] != 'completed':
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    if not task.get('result'):
        raise HTTPException(status_code=404, detail="回测结果不存在")
    
    result = task['result']
    return BacktestResult(**result)

@router.get("/result/{task_id}/markdown")
async def get_markdown_report(
    task_id: str, 
    current_user: dict = get_user_dependency()
):
    """获取Markdown分析报告"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = active_tasks[task_id]
    user_id = current_user.get('user_id', 'anonymous')
    
    # 检查权限
    if task['user_id'] != user_id and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="无权访问此任务")
    
    if task['status'] != 'completed':
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    result = task.get('result', {})
    
    # 尝试读取Markdown报告
    markdown_content = ""
    try:
        markdown_content = find_and_read_markdown_report(result, task_id)
    except Exception as e:
        logger.warning(f"读取Markdown报告失败: {e}")
        # 生成备用报告
        markdown_content = generate_fallback_markdown_report(result, task, task_id)
    
    return {"content": markdown_content, "task_id": task_id}

def find_and_read_markdown_report(result: dict, task_id: str) -> str:
    """查找并读取Markdown报告文件"""
    import os
    import glob
    
    try:
        # 尝试从结果中获取报告路径
        report_path = result.get('markdown_report_path')
        if report_path and os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # 尝试查找results目录中的Markdown文件
        results_dir = result.get('results_dir')
        if results_dir:
            # 查找可能的Markdown报告文件
            patterns = [
                os.path.join(results_dir, 'analysis_report.md'),
                os.path.join(results_dir, 'backtest_report.md'),
                os.path.join(results_dir, f'{task_id}_report.md'),
                os.path.join(results_dir, '*.md')
            ]
            
            for pattern in patterns[:-1]:  # 先检查具体文件名
                if os.path.exists(pattern):
                    with open(pattern, 'r', encoding='utf-8') as f:
                        return f.read()
            
            # 最后使用通配符查找任何.md文件
            md_files = glob.glob(patterns[-1])
            if md_files:
                # 按修改时间排序，选择最新的
                md_files.sort(key=os.path.getmtime, reverse=True)
                with open(md_files[0], 'r', encoding='utf-8') as f:
                    return f.read()
        
        # 如果都没找到，尝试生成报告
        logger.info(f"未找到现存的Markdown报告，尝试生成新报告")
        return generate_markdown_report_from_result(result, task_id)
        
    except Exception as e:
        logger.warning(f"读取Markdown报告失败: {e}")
        raise

def generate_markdown_report_from_result(result: dict, task_id: str) -> str:
    """从回测结果生成Markdown报告"""
    try:
        # 导入性能分析器
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backtrader_strategies'))
        from backtest.performance_analyzer import PerformanceAnalyzer
        
        # 创建性能分析器实例
        analyzer = PerformanceAnalyzer()
        
        # 生成Markdown报告内容
        markdown_content = analyzer._generate_markdown_report(result)
        
        logger.info(f"成功从结果生成Markdown报告，长度: {len(markdown_content)}")
        return markdown_content
        
    except Exception as e:
        logger.error(f"从结果生成Markdown报告失败: {e}")
        # 生成简化的备用报告
        return generate_fallback_markdown_report(result, {"status": "completed"}, task_id)

def get_friendly_strategy_name(raw_name: str, strategy_type: str) -> str:
    """
    将后端技术名称转换为用户友好的显示名称
    """
    # 策略类型到友好名称的映射
    strategy_mapping = {
        'multi_trend': '太上老君1号策略',
        'boll': '太上老君2号策略',
        'taishang_3factor': '太上老君3号策略'
    }
    
    # 优先使用strategy_type进行映射
    if strategy_type in strategy_mapping:
        return strategy_mapping[strategy_type]
    
    # 如果strategy_type没有匹配，尝试从raw_name中识别
    raw_lower = raw_name.lower()
    for key, friendly_name in strategy_mapping.items():
        if key in raw_lower or key.replace('_', '') in raw_lower:
            return friendly_name
    
    # 如果原名称已经是友好名称，直接返回
    if '太上老君' in raw_name:
        return raw_name
        
    # 默认返回通用名称，不暴露技术细节
    return '量化策略'

def generate_fallback_markdown_report(result: dict, task: dict, task_id: str) -> str:
    """生成备用Markdown报告"""
    from datetime import datetime
    
    # 提取基础信息并转换为友好名称
    raw_strategy_name = result.get('strategy_info', {}).get('strategy_name', '未知策略')
    
    # 多路径获取strategy_type
    strategy_type = (
        result.get('backtest_config', {}).get('strategy_type') or
        result.get('config', {}).get('strategy_type') or
        result.get('strategy_type') or
        ''
    )
    
    logger.info(f"API策略类型获取: raw_name={raw_strategy_name}, strategy_type={strategy_type}")
    strategy_name = get_friendly_strategy_name(raw_strategy_name, strategy_type)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    performance = result.get('performance_report', {}).get('basic_metrics', {})
    
    # 生成简化报告
    markdown = f"""# {strategy_name} 回测分析报告

## 📋 基本信息

| 项目 | 内容 |
|------|------|
| 任务ID | {task_id} |
| 策略名称 | {strategy_name} |
| 报告生成时间 | {current_time} |
| 任务状态 | {task.get('status', '未知')} |

## 📊 核心绩效指标

| 指标 | 数值 |
|------|------|
| 总收益率 | {performance.get('total_return', 0):.2%} |
| 年化收益率 | {performance.get('annual_return', 0):.2%} |
| 最大回撤 | {performance.get('max_drawdown', 0):.2%} |
| 夏普比率 | {performance.get('sharpe_ratio', 0):.3f} |

---

*备注：这是一个简化版本的报告。完整报告生成中遇到问题，仅显示基础信息。*
"""
    
    return markdown

@router.get("/result/{task_id}/trades")
async def get_trades_data(
    task_id: str,
    limit: int = Query(10000, ge=1, le=10000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = get_user_dependency()
):
    """获取交易数据"""
    try:
        logger.info(f"🔍 开始获取任务 {task_id} 的交易数据")
        logger.info(f"📋 当前活跃任务数量: {len(active_tasks)}")
        logger.info(f"📋 活跃任务ID列表: {list(active_tasks.keys())}")
        
        # 从任务存储获取任务
        task = active_tasks.get(task_id)
        trades = []
        
        if not task:
            logger.warning(f"任务 {task_id} 不在活跃任务中，尝试直接读取CSV文件")
        else:
            logger.info(f"📋 找到任务，状态: {task.get('status')}")
            # 如果任务未完成，返回空数据
            if task.get('status') != 'completed':
                logger.info(f"任务 {task_id} 未完成，返回空数据")
                return {"trades": [], "total": 0}
            
            # 获取任务结果
            result = task.get('result')
            if not result:
                logger.warning(f"任务 {task_id} 没有结果数据")
            else:
                # 方法1: 从trading_summary中获取
                trading_summary = result.get('trading_summary', {})
                logger.info(f"📋 trading_summary结构: {type(trading_summary)}, keys: {list(trading_summary.keys()) if isinstance(trading_summary, dict) else 'not dict'}")
                
                if 'trades' in trading_summary:
                    trades_from_summary = trading_summary['trades']
                    logger.info(f"📊 trading_summary['trades']类型: {type(trades_from_summary)}, 值: {trades_from_summary}")
                    
                    if isinstance(trades_from_summary, list):
                        trades = trades_from_summary
                        logger.info(f"✅ 从trading_summary获取到 {len(trades)} 条交易记录")
                    else:
                        logger.warning(f"⚠️ trading_summary['trades']不是列表类型: {type(trades_from_summary)}")
                        trades = []
        
        # 方法2: 如果没有trades，尝试读取CSV文件
        if not trades:
            logger.info(f"📁 尝试从CSV文件读取交易数据")
            try:
                # 获取结果目录路径（基于任务配置）
                import os
                results_dir = "/home/libing/kk_Projects/kk_stock/kk_stock_backend/results"
                
                # 优先尝试：如果任务在active_tasks中，且有结果目录信息
                matching_files = []
                if task and 'result_dir' in task:
                    potential_trades_file = os.path.join(task['result_dir'], f"*_trades.csv")
                    import glob
                    matching_files = glob.glob(potential_trades_file)
                    if matching_files:
                        logger.info(f"📄 从任务信息找到交易文件: {matching_files[0]}")
                
                # 备选方案：全局搜索CSV文件
                if not matching_files:
                    import glob
                    pattern = f"{results_dir}/**/*_trades.csv"
                    trade_files = glob.glob(pattern, recursive=True)
                    logger.info(f"🔍 全局搜索找到 {len(trade_files)} 个交易CSV文件")
                    
                    # 查找包含task_id的文件或最新的文件
                    matching_files = [f for f in trade_files if task_id in f]
                    if not matching_files and trade_files:
                        # 如果没有找到匹配的，使用最新的文件
                        matching_files = [max(trade_files, key=os.path.getmtime)]
                        logger.info(f"📄 未找到匹配task_id的文件，使用最新文件: {matching_files[0]}")
                    elif matching_files:
                        logger.info(f"📄 找到匹配文件: {matching_files[0]}")
                
                if matching_files:
                    import pandas as pd
                    df = pd.read_csv(matching_files[0])
                    logger.info(f"📊 CSV文件包含 {len(df)} 行数据")
                    
                    # 转换数据格式
                    for _, row in df.iterrows():
                        trade = {
                            "trade_id": str(row.get('trade_id', '')),
                            "date": str(row.get('trade_date', '')),
                            "symbol": str(row.get('stock_code', '')),
                            "name": str(row.get('stock_code', '')),
                            "action": str(row.get('order_type', '')),
                            "shares": float(row.get('quantity', 0)),
                            "price": float(row.get('price', 0)),
                            "amount": float(row.get('net_amount', 0)),
                            "commission": float(row.get('commission', 0)),
                            "stamp_tax": float(row.get('stamp_tax', 0)),
                            "total_cost": abs(float(row.get('net_amount', 0)))
                        }
                        trades.append(trade)
                    
                    # 按交易日期倒序排序（最新的在前面）
                    trades.sort(key=lambda x: x.get('date', ''), reverse=True)
                    logger.info(f"✅ 从CSV文件获取任务 {task_id} 的交易记录: {len(trades)} 条，已按日期倒序排序")
                else:
                    logger.warning(f"❌ 没有找到匹配的交易CSV文件")
                    
            except Exception as e:
                logger.error(f"读取交易记录CSV文件失败: {e}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")
        
        # 确保trades是列表并进行类型检查
        logger.info(f"🔍 trades类型检查: type={type(trades)}, isinstance(list)={isinstance(trades, list)}")
        if not isinstance(trades, list):
            logger.warning(f"⚠️ trades不是列表类型: {type(trades)}, 值: {trades}, 重置为空列表")
            trades = []
        
        # 最终排序确保按时间倒序
        if trades:
            trades.sort(key=lambda x: x.get('date', ''), reverse=True)
            logger.info(f"📅 交易记录最终排序完成，最新交易: {trades[0].get('date', 'N/A')} {trades[0].get('symbol', 'N/A')}")
        
        # 分页处理
        total = len(trades)
        logger.info(f"📄 分页处理: total={total}, offset={offset}, limit={limit}")
        
        # 如果limit达到最大值(10000)且total超过limit，则返回所有数据
        if limit == 10000 and total > limit:
            logger.info(f"📄 检测到总记录数({total})超过默认限制，返回所有交易记录")
            trades = trades[offset:]  # 只应用offset，不限制数量
        else:
            trades = trades[offset:offset+limit]
        
        logger.info(f"✅ 成功获取任务 {task_id} 的交易记录: {len(trades)}/{total}")
        return {"trades": trades, "total": total}
        
    except Exception as e:
        logger.error(f"获取交易数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易数据失败: {str(e)}")

@router.get("/result/{task_id}/portfolio")
async def get_portfolio_data(
    task_id: str,
    limit: int = Query(1000, ge=1, le=10000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = get_user_dependency()
):
    """获取组合历史数据"""
    # 实现组合数据查询逻辑
    _ = task_id, limit, offset, current_user  # 暂时未使用
    return {"portfolio_history": [], "total": 0}

@router.get("/benchmark/{benchmark_code}")
async def get_benchmark_index_data(
    benchmark_code: str,
    start_date: str = Query(..., description="开始日期，格式YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期，格式YYYY-MM-DD"),
    current_user: dict = get_user_dependency()
):
    """
    获取基准指数数据
    支持的指数代码：000300.SH, 000905.SH, 000852.SH, 000001.SH等
    """
    try:
        # 基准指数名称映射
        benchmark_names = {
            '000300.SH': '沪深300',
            '000905.SH': '中证500', 
            '000852.SH': '中证1000',
            '000001.SH': '上证指数'
        }
        
        benchmark_name = benchmark_names.get(benchmark_code, benchmark_code)
        
        # 获取基准指数数据
        benchmark_data = get_benchmark_data(benchmark_code, start_date, end_date)
        
        if not benchmark_data:
            raise HTTPException(status_code=404, detail=f"未找到基准指数{benchmark_code}的数据")
        
        # 计算累计收益率
        benchmark_returns = calculate_benchmark_returns(benchmark_data)
        
        return {
            "benchmark_code": benchmark_code,
            "benchmark_name": benchmark_name,
            "start_date": start_date,
            "end_date": end_date,
            "data_count": len(benchmark_data),
            "data": benchmark_data,
            "cumulative_returns": benchmark_returns,
            "final_return": benchmark_returns[-1] if benchmark_returns else 0,
            "annualized_return": (benchmark_returns[-1] if benchmark_returns else 0) * 252 / len(benchmark_data) if benchmark_data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基准指数数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取基准指数数据失败: {str(e)}")

# =============================================================================
# 实时数据推送端点 (SSE)
# =============================================================================

@router.get("/sse/test")
async def test_connection():
    """测试SSE连接"""
    return {"message": "SSE测试连接成功", "timestamp": datetime.now().isoformat()}

@router.get("/sse/test-stream")
async def test_stream():
    """测试SSE流是否正常"""
    async def test_generator():
        for i in range(5):
            yield f"data: {{\"message\": \"测试消息 {i+1}\", \"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"
            await asyncio.sleep(1)
        yield f"data: {{\"message\": \"测试完成\", \"final\": true}}\n\n"
    
    return StreamingResponse(
        test_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/sse/progress/{task_id}")
async def stream_progress(task_id: str, user: dict = Depends(get_current_user_sse)):
    """推送进度数据"""
    _ = user  # 用户验证已通过，此处暂不使用
    return StreamingResponse(
        sse_generator(task_id, "progress"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/sse/portfolio/{task_id}")
async def stream_portfolio(task_id: str, user: dict = Depends(get_current_user_sse)):
    """推送组合数据"""
    _ = user  # 用户验证已通过，此处暂不使用
    return StreamingResponse(
        sse_generator(task_id, "portfolio"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/sse/trades/{task_id}")
async def stream_trades(task_id: str, user: dict = Depends(get_current_user_sse)):
    """推送交易数据"""
    _ = user  # 用户验证已通过，此处暂不使用
    return StreamingResponse(
        sse_generator(task_id, "trades"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/sse/chart/{task_id}")
async def stream_chart(task_id: str, user: dict = Depends(get_current_user_sse)):
    """推送图表数据"""
    _ = user  # 用户验证已通过，此处暂不使用
    return StreamingResponse(
        sse_generator(task_id, "chart"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/sse/realtime/{task_id}")
async def stream_realtime(task_id: str, user: dict = Depends(get_current_user_sse)):
    """推送实时综合数据（推荐使用）"""
    _ = user  # 用户验证已通过，此处暂不使用
    return StreamingResponse(
        sse_generator(task_id, "realtime"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

# =============================================================================
# 辅助查询接口
# =============================================================================

@router.get("/indices")
@cache_endpoint(data_type='indices', ttl=3600)
async def get_available_indices():
    """获取可用指数列表"""
    indices = [
        {"code": "000510.CSI", "name": "中证500", "description": "中证500指数成分股"},
        {"code": "399006.SZ", "name": "创业板指", "description": "创业板指数成分股"},
        {"code": "000001.SH", "name": "上证指数", "description": "上证综合指数成分股"},
        {"code": "399001.SZ", "name": "深证成指", "description": "深证成份指数成分股"}
    ]
    return indices

@router.get("/stock-pool/{index_code}")
@cache_endpoint(data_type='stock_pool', ttl=3600)
async def get_stock_pool(
    index_code: str,
    limit: int = Query(100, ge=10, le=1000, description="返回数量限制")
):
    """获取指数成分股池"""
    # 这里应该实现真实的股票池查询逻辑
    # 简化版本返回模拟数据
    stocks = [
        {"code": f"00000{i}.SZ", "name": f"股票{i}", "weight": 0.01}
        for i in range(1, min(limit + 1, 101))
    ]
    
    return {
        "index_code": index_code,
        "stocks": stocks,
        "total": len(stocks),
        "update_time": datetime.now().isoformat()
    }

@router.get("/health")
async def backtest_health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "backtest_unified",
        "has_backtest_engine": HAS_BACKTEST_ENGINE,
        "has_cache": HAS_CACHE,
        "has_db_handler": HAS_DB_HANDLER,
        "has_user_auth": HAS_USER_AUTH,
        "active_tasks_count": len(active_tasks),
        "timestamp": datetime.now().isoformat()
    }

# =============================================================================
# WebSocket实时数据推送
# =============================================================================

async def websocket_data_broadcaster(task_id: str):
    """WebSocket数据广播器 - 持续监控任务状态并推送数据"""
    logger.info(f"开始WebSocket数据广播: task_id={task_id}")
    
    last_progress_data = None
    last_portfolio_data = None
    last_trades_count = 0
    
    try:
        while task_id in active_tasks:
            task_info = active_tasks[task_id]
            has_new_data = False
            
            # 检查进度变化
            current_progress = {
                "progress": task_info.get('progress', 0.0),
                "status": task_info.get('status', 'pending'),
                "current_date": task_info.get('current_date'),
                "message": task_info.get('message', '')
            }
            
            if not last_progress_data or current_progress != last_progress_data:
                progress_message = {
                    "type": "progress",
                    "task_id": task_id,
                    "data": current_progress,
                    "timestamp": datetime.now().isoformat()
                }
                await ws_manager.broadcast_to_task(progress_message, task_id)
                last_progress_data = current_progress
                has_new_data = True
            
            # 检查组合数据变化
            current_portfolio = {
                "current_date": task_info.get('current_date', ''),
                "total_value": task_info.get('current_portfolio_value', 0.0),
                "total_return": task_info.get('total_return', 0.0),
                "daily_return": task_info.get('daily_return', 0.0),
                "drawdown": task_info.get('current_drawdown', 0.0)
            }
            
            data_updated_flag = task_info.get('data_updated', False)
            date_changed = (current_portfolio['current_date'] and 
                           (not last_portfolio_data or 
                            current_portfolio['current_date'] != last_portfolio_data.get('current_date')))
            
            if date_changed or data_updated_flag:
                portfolio_message = {
                    "type": "portfolio",
                    "task_id": task_id,
                    "data": {
                        "current_date": current_portfolio['current_date'],
                        "portfolio": {
                            "total_value": current_portfolio['total_value'],
                            "cash": task_info.get('current_cash', 0.0),
                            "positions_value": task_info.get('current_positions_value', 0.0),
                            "positions": task_info.get('current_positions', []),
                            "daily_return": current_portfolio['daily_return'],
                            "total_return": current_portfolio['total_return'],
                            "drawdown": current_portfolio['drawdown']
                        }
                    },
                    "timestamp": datetime.now().isoformat()
                }
                await ws_manager.broadcast_to_task(portfolio_message, task_id)
                logger.info(f"🔄 WebSocket推送Portfolio数据: {current_portfolio['current_date']}, 组合价值: {current_portfolio['total_value']:,.2f}")
                last_portfolio_data = current_portfolio
                has_new_data = True
                
                # 重置数据更新标志
                if 'data_updated' in task_info:
                    task_info['data_updated'] = False
            
            # 检查交易数据变化
            current_trades_count = task_info.get('total_trades', 0)
            if current_trades_count > last_trades_count:
                trades_message = {
                    "type": "trades",
                    "task_id": task_id,
                    "data": {
                        "current_date": task_info.get('current_date', ''),
                        "recent_trades": task_info.get('recent_trades', []),
                        "trade_stats": {
                            "total_trades": current_trades_count,
                            "buy_trades": task_info.get('buy_trades', 0),
                            "sell_trades": task_info.get('sell_trades', 0),
                            "win_trades": task_info.get('win_trades', 0),
                            "lose_trades": task_info.get('lose_trades', 0),
                            "win_rate": task_info.get('win_rate', 0.0),
                            "total_pnl": task_info.get('total_pnl', 0.0)
                        }
                    },
                    "timestamp": datetime.now().isoformat()
                }
                await ws_manager.broadcast_to_task(trades_message, task_id)
                last_trades_count = current_trades_count
                has_new_data = True
            
            # 检查图表数据变化
            if task_info.get('date_series'):
                chart_message = {
                    "type": "chart",
                    "task_id": task_id,
                    "data": {
                        "current_date": task_info.get('current_date', ''),
                        "chart_data": {
                            "dates": task_info.get('date_series', []),
                            "portfolio_values": task_info.get('portfolio_series', []),
                            "daily_returns": task_info.get('daily_return_series', []),
                            "cumulative_returns": task_info.get('cumulative_return_series', []),
                            "drawdowns": task_info.get('drawdown_series', [])
                        }
                    },
                    "timestamp": datetime.now().isoformat()
                }
                await ws_manager.broadcast_to_task(chart_message, task_id)
                has_new_data = True
            
            # 检查任务完成状态
            status = task_info.get('status', 'pending')
            if status in ['completed', 'failed']:
                final_message = {
                    "type": "final",
                    "task_id": task_id,
                    "data": {
                        "status": status,
                        "message": task_info.get('message', ''),
                        "result_available": status == 'completed'
                    },
                    "timestamp": datetime.now().isoformat()
                }
                await ws_manager.broadcast_to_task(final_message, task_id)
                logger.info(f"WebSocket广播任务完成: task_id={task_id}, status={status}")
                break
            
            # 动态调整推送频率
            if has_new_data:
                await asyncio.sleep(0.05)  # 有新数据时快速推送
            else:
                await asyncio.sleep(0.5)   # 无新数据时降低频率
                
    except Exception as e:
        logger.error(f"WebSocket广播器异常: task_id={task_id}, error={e}")
    finally:
        logger.info(f"WebSocket广播器结束: task_id={task_id}")

async def websocket_authenticate(websocket: WebSocket, token: str) -> dict:
    """WebSocket认证"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token无效")
        
        # 简化的用户验证，实际应该查询数据库
        return {"user_id": user_id, "role": "user"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except Exception:
        raise HTTPException(status_code=401, detail="Token无效")

def update_task_realtime_data(task_id: str, update_data: Dict[str, Any]):
    """更新任务的实时数据 - 保留兼容性函数"""
    if task_id in active_tasks:
        active_tasks[task_id].update(update_data)

# =============================================================================
# WebSocket端点
# =============================================================================

@router.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """WebSocket测试端点"""
    await websocket.accept()
    try:
        # 发送欢迎消息
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": "WebSocket连接测试成功",
            "timestamp": datetime.now().isoformat()
        }))
        
        # 发送几条测试消息
        for i in range(5):
            await asyncio.sleep(1)
            await websocket.send_text(json.dumps({
                "type": "test",
                "message": f"测试消息 {i+1}",
                "timestamp": datetime.now().isoformat()
            }))
        
        # 发送完成消息
        await websocket.send_text(json.dumps({
            "type": "complete",
            "message": "测试完成",
            "timestamp": datetime.now().isoformat()
        }))
        
    except WebSocketDisconnect:
        logger.info("WebSocket测试连接断开")
    except Exception as e:
        logger.error(f"WebSocket测试异常: {e}")

@router.websocket("/ws/realtime/{task_id}")
async def websocket_realtime_endpoint(websocket: WebSocket, task_id: str, token: str = Query(...)):
    """WebSocket实时数据推送端点"""
    try:
        # 认证
        user = await websocket_authenticate(websocket, token)
        logger.info(f"WebSocket用户认证成功: user_id={user['user_id']}, task_id={task_id}")
        
        # 检查任务权限
        if task_id not in active_tasks:
            await websocket.close(code=1008, reason="任务不存在")
            return
        
        task = active_tasks[task_id]
        if task['user_id'] != user['user_id'] and user.get('role') != 'admin':
            await websocket.close(code=1008, reason="无权访问此任务")
            return
        
        # 建立连接
        connection_id = await ws_manager.connect(websocket, task_id)
        
        # 发送连接确认
        await websocket.send_text(json.dumps({
            "type": "connected",
            "task_id": task_id,
            "connection_id": connection_id,
            "message": "WebSocket连接已建立",
            "timestamp": datetime.now().isoformat()
        }))
        
        # 启动数据广播器（如果还没有的话）
        if ws_manager.get_task_connection_count(task_id) == 1:
            # 第一个连接，启动广播器
            asyncio.create_task(websocket_data_broadcaster(task_id))
        
        # 启动服务端心跳任务
        async def server_heartbeat():
            """服务端心跳任务"""
            while True:
                try:
                    await asyncio.sleep(30)  # 每30秒发送一次心跳
                    if websocket.client_state.DISCONNECTED:
                        break
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                        "task_id": task_id
                    }))
                except Exception as e:
                    logger.error(f"服务端心跳发送失败: {e}")
                    break
        
        heartbeat_task = asyncio.create_task(server_heartbeat())
        
        # 保持连接活跃
        while True:
            try:
                # 使用timeout等待客户端消息，避免无限期阻塞
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                    data = json.loads(message)
                    
                    # 处理客户端消息
                    if data.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                    elif data.get("type") == "heartbeat_response":
                        # 客户端响应心跳
                        logger.debug(f"收到客户端心跳响应: task_id={task_id}")
                    elif data.get("type") == "get_current_status":
                        # 发送当前任务状态
                        current_task = active_tasks.get(task_id, {})
                        await websocket.send_text(json.dumps({
                            "type": "current_status",
                            "task_id": task_id,
                            "data": {
                                "status": current_task.get('status', 'unknown'),
                                "progress": current_task.get('progress', 0.0),
                                "message": current_task.get('message', ''),
                                "current_date": current_task.get('current_date', '')
                            },
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                except asyncio.TimeoutError:
                    # 超时是正常的，继续循环等待消息
                    continue
                except WebSocketDisconnect:
                    logger.info(f"WebSocket客户端主动断开连接: task_id={task_id}")
                    break
                except Exception as e:
                    logger.error(f"WebSocket消息接收异常: {e}")
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket连接断开: task_id={task_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket消息处理异常: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
    finally:
        # 取消心跳任务
        if 'heartbeat_task' in locals():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 清理连接
        ws_manager.disconnect(websocket, task_id)
        logger.info(f"WebSocket连接已清理: task_id={task_id}")