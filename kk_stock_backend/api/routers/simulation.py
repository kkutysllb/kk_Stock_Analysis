"""
模拟交易系统API路由

提供模拟交易相关的REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
import logging

from api.routers.user import get_current_user
from api.simulation.service import simulation_service
from api.simulation.models import (
    BuyRequest, SellRequest, TradeHistoryQuery,
    SimulationAccountResponse, SimulationPositionListResponse,
    SimulationTradeListResponse, SimulationTradeResponse,
    PageResponse, StockQuote, BatchQuoteRequest
)
from api.global_db import db_handler

router = APIRouter(prefix="/api/simulation", tags=["模拟交易"])
logger = logging.getLogger(__name__)


# ==================== 模拟账户接口 ====================

@router.get("/account", response_model=SimulationAccountResponse, summary="获取模拟账户信息")
async def get_simulation_account(current_user: dict = Depends(get_current_user)):
    """获取当前用户的模拟账户信息"""
    try:
        user_id = current_user["user_id"]
        account = await simulation_service.get_account_info(user_id)
        
        if not account:
            # 如果用户没有模拟账户，自动初始化
            account = await simulation_service.init_user_account(user_id)
            if not account:
                raise HTTPException(status_code=500, detail="模拟账户初始化失败")
        
        return SimulationAccountResponse(**account)
    
    except Exception as e:
        logger.error(f"获取模拟账户信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取账户信息失败: {str(e)}")


@router.post("/account/init", response_model=SimulationAccountResponse, summary="初始化模拟账户")
async def init_simulation_account(
    initial_capital: float = Query(default=3000000.0, description="初始资金"),
    current_user: dict = Depends(get_current_user)
):
    """初始化模拟账户"""
    try:
        user_id = current_user["user_id"]
        
        # 检查是否已有账户
        existing_account = await simulation_service.get_account_info(user_id)
        if existing_account:
            raise HTTPException(status_code=400, detail="用户已存在模拟账户")
        
        account = await simulation_service.init_user_account(user_id, initial_capital)
        if not account:
            raise HTTPException(status_code=500, detail="模拟账户初始化失败")
        
        return SimulationAccountResponse(**account)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化模拟账户失败: {e}")
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")


@router.post("/account/reset", response_model=dict, summary="重置模拟账户")
async def reset_simulation_account(current_user: dict = Depends(get_current_user)):
    """重置模拟账户（清空所有交易记录和持仓）"""
    try:
        user_id = current_user["user_id"]
        success = await simulation_service.reset_account(user_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="重置账户失败")
        
        return {"message": "账户重置成功", "success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置模拟账户失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")


@router.get("/account/snapshots", response_model=List[dict], summary="获取账户历史快照")
async def get_account_snapshots(
    days: int = Query(default=30, description="获取最近多少天的数据"),
    current_user: dict = Depends(get_current_user)
):
    """获取账户历史快照数据"""
    try:
        user_id = current_user["user_id"]
        snapshots = simulation_service.db.get_account_snapshots(user_id, days)
        return snapshots
    
    except Exception as e:
        logger.error(f"获取账户快照失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取快照数据失败: {str(e)}")


# ==================== 持仓管理接口 ====================

@router.get("/positions", response_model=SimulationPositionListResponse, summary="获取持仓列表")
async def get_positions(current_user: dict = Depends(get_current_user)):
    """获取用户的持仓列表"""
    try:
        user_id = current_user["user_id"]
        positions = await simulation_service.get_user_positions(user_id)
        
        return SimulationPositionListResponse(
            total=len(positions),
            data=positions
        )
    
    except Exception as e:
        logger.error(f"获取持仓列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")


@router.get("/positions/{stock_code}", response_model=dict, summary="获取单只股票持仓")
async def get_position(
    stock_code: str,
    current_user: dict = Depends(get_current_user)
):
    """获取指定股票的持仓信息"""
    try:
        user_id = current_user["user_id"]
        position = await simulation_service.get_position(user_id, stock_code)
        
        if not position:
            raise HTTPException(status_code=404, detail="未找到该股票的持仓记录")
        
        return position
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取持仓信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")


# ==================== 交易执行接口 ====================

@router.post("/trade/buy", response_model=dict, summary="提交买入订单")
async def buy_stock(
    buy_request: BuyRequest,
    current_user: dict = Depends(get_current_user)
):
    """提交买入订单"""
    try:
        user_id = current_user["user_id"]
        
        # 基本参数验证
        if buy_request.quantity <= 0:
            raise HTTPException(status_code=400, detail="交易数量必须大于0")
        
        if buy_request.order_type.value == "LIMIT" and (not buy_request.price or buy_request.price <= 0):
            raise HTTPException(status_code=400, detail="限价单必须指定有效价格")
        
        trade_id = await simulation_service.execute_buy_order(user_id, buy_request)
        
        if not trade_id:
            raise HTTPException(status_code=500, detail="买入订单执行失败")
        
        return {
            "message": "买入订单执行成功",
            "trade_id": trade_id,
            "success": True
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"买入订单执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"买入失败: {str(e)}")


@router.post("/trade/sell", response_model=dict, summary="提交卖出订单")
async def sell_stock(
    sell_request: SellRequest,
    current_user: dict = Depends(get_current_user)
):
    """提交卖出订单"""
    try:
        user_id = current_user["user_id"]
        
        # 基本参数验证
        if sell_request.quantity <= 0:
            raise HTTPException(status_code=400, detail="交易数量必须大于0")
        
        if sell_request.order_type.value == "LIMIT" and (not sell_request.price or sell_request.price <= 0):
            raise HTTPException(status_code=400, detail="限价单必须指定有效价格")
        
        trade_id = await simulation_service.execute_sell_order(user_id, sell_request)
        
        if not trade_id:
            raise HTTPException(status_code=500, detail="卖出订单执行失败")
        
        return {
            "message": "卖出订单执行成功",
            "trade_id": trade_id,
            "success": True
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"卖出订单执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"卖出失败: {str(e)}")


# ==================== 交易记录接口 ====================

@router.get("/trades", response_model=SimulationTradeListResponse, summary="获取交易记录")
async def get_trades(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    stock_code: Optional[str] = Query(default=None, description="股票代码筛选"),
    start_date: Optional[date] = Query(default=None, description="开始日期"),
    end_date: Optional[date] = Query(default=None, description="结束日期"),
    current_user: dict = Depends(get_current_user)
):
    """获取用户的交易记录"""
    try:
        user_id = current_user["user_id"]
        trades, total = await simulation_service.get_trade_history(
            user_id, page, page_size, stock_code, start_date, end_date
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return SimulationTradeListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            data=[SimulationTradeResponse(**trade) for trade in trades]
        )
    
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易记录失败: {str(e)}")


@router.get("/trades/{trade_id}", response_model=SimulationTradeResponse, summary="获取交易详情")
async def get_trade_detail(
    trade_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取指定交易的详细信息"""
    try:
        trade = simulation_service.db.get_trade_by_id(trade_id)
        
        if not trade:
            raise HTTPException(status_code=404, detail="交易记录不存在")
        
        # 验证交易是否属于当前用户
        if trade["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="无权访问该交易记录")
        
        return SimulationTradeResponse(**trade)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易详情失败: {str(e)}")


# ==================== 行情数据接口 ====================

@router.get("/quote/{stock_code}", response_model=dict, summary="获取实时股价")
async def get_stock_quote(stock_code: str):
    """获取指定股票的实时报价"""
    try:
        current_price = await simulation_service._get_current_stock_price(stock_code)
        
        if current_price is None:
            raise HTTPException(status_code=404, detail="股票数据不存在")
        
        # 这里简化处理，实际应该返回完整的报价信息
        return {
            "stock_code": stock_code,
            "current_price": current_price,
            "update_time": datetime.now()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股价失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取股价失败: {str(e)}")


@router.post("/quotes", response_model=dict, summary="批量获取股价")
async def get_batch_quotes(request: BatchQuoteRequest):
    """批量获取多只股票的报价"""
    try:
        quotes = []
        
        for stock_code in request.stock_codes:
            try:
                current_price = await simulation_service._get_current_stock_price(stock_code)
                if current_price is not None:
                    quotes.append({
                        "stock_code": stock_code,
                        "current_price": current_price,
                        "update_time": datetime.now()
                    })
            except Exception as e:
                logger.warning(f"获取股票 {stock_code} 价格失败: {e}")
                continue
        
        return {
            "quotes": quotes,
            "total": len(quotes),
            "update_time": datetime.now()
        }
    
    except Exception as e:
        logger.error(f"批量获取股价失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量获取股价失败: {str(e)}")


# ==================== 交易日历接口 ====================

@router.get("/calendar", response_model=dict, summary="获取交易日历")
async def get_trading_calendar():
    """获取交易日历信息"""
    try:
        # 简化处理，实际应该从数据库获取交易日历
        today = date.today()
        is_trading_day = simulation_service.db.is_trading_time()
        
        return {
            "today": today,
            "is_trading_day": is_trading_day,
            "trading_status": "交易中" if is_trading_day else "休市",
            "next_trading_day": today  # 简化处理
        }
    
    except Exception as e:
        logger.error(f"获取交易日历失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易日历失败: {str(e)}")


# ==================== 费用计算接口 ====================

@router.get("/trading-cost", response_model=dict, summary="计算交易费用")
async def calculate_trading_cost(
    amount: float = Query(..., description="交易金额"),
    trade_type: str = Query(..., description="交易类型：BUY或SELL"),
    market: str = Query(default="SH", description="市场：SH或SZ")
):
    """计算交易费用"""
    try:
        from api.simulation.models import TradeType, Market
        
        # 验证参数
        try:
            trade_type_enum = TradeType(trade_type)
            market_enum = Market(market)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
        
        cost_calculation = simulation_service.db.calculate_trading_cost(
            amount, trade_type_enum, market_enum
        )
        
        return {
            "amount": amount,
            "trade_type": trade_type,
            "market": market,
            "commission": cost_calculation.commission,
            "stamp_tax": cost_calculation.stamp_tax,
            "transfer_fee": cost_calculation.transfer_fee,
            "slippage": cost_calculation.slippage,
            "total_cost": cost_calculation.total_cost,
            "net_amount": amount - cost_calculation.total_cost if trade_type == "SELL" else amount + cost_calculation.total_cost
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算交易费用失败: {e}")
        raise HTTPException(status_code=500, detail=f"计算费用失败: {str(e)}")


# ==================== 系统管理接口 ====================

@router.post("/admin/process-settlement", response_model=dict, summary="处理T+1交割")
async def process_t_plus_one_settlement(current_user: dict = Depends(get_current_user)):
    """手动触发T+1交割处理（管理员功能）"""
    try:
        # 这里可以添加管理员权限检查
        await simulation_service.process_t_plus_one_settlement()
        
        return {
            "message": "T+1交割处理完成",
            "success": True,
            "timestamp": datetime.now()
        }
    
    except Exception as e:
        logger.error(f"T+1交割处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"交割处理失败: {str(e)}")


@router.post("/admin/create-snapshots", response_model=dict, summary="创建每日快照")
async def create_daily_snapshots(current_user: dict = Depends(get_current_user)):
    """为所有用户创建每日账户快照（管理员功能）"""
    try:
        # 这里可以添加管理员权限检查
        # 实际实现中应该批量处理所有用户
        user_id = current_user["user_id"]
        await simulation_service.create_daily_snapshot(user_id)
        
        return {
            "message": "每日快照创建完成",
            "success": True,
            "timestamp": datetime.now()
        }
    
    except Exception as e:
        logger.error(f"创建每日快照失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建快照失败: {str(e)}")


@router.post("/admin/init-accounts", response_model=dict, summary="批量初始化模拟账户")
async def init_simulation_accounts_for_all(current_user: dict = Depends(get_current_user)):
    """为所有用户批量初始化模拟账户（管理员功能）"""
    try:
        # 这里可以添加管理员权限检查
        from api.simulation.init import init_simulation_accounts_for_all_users
        
        success_count = await init_simulation_accounts_for_all_users()
        
        return {
            "message": f"批量初始化完成，成功创建 {success_count} 个模拟账户",
            "success_count": success_count,
            "success": True,
            "timestamp": datetime.now()
        }
    
    except Exception as e:
        logger.error(f"批量初始化模拟账户失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量初始化失败: {str(e)}")


@router.post("/admin/check-missing-accounts", response_model=dict, summary="检查并补充缺失的模拟账户")
async def check_and_init_missing_accounts(current_user: dict = Depends(get_current_user)):
    """检查并补充缺失的模拟账户（管理员功能）"""
    try:
        # 这里可以添加管理员权限检查
        from api.simulation.init import check_and_init_missing_accounts
        
        success_count = await check_and_init_missing_accounts()
        
        return {
            "message": f"检查完成，补充了 {success_count} 个缺失的模拟账户",
            "success_count": success_count,
            "success": True,
            "timestamp": datetime.now()
        }
    
    except Exception as e:
        logger.error(f"检查并补充缺失账户失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查补充失败: {str(e)}")


# ==================== 策略自动化接口 ====================

@router.post("/strategy/activate", response_model=dict, summary="激活策略自动交易")
async def activate_strategy(
    strategy_name: str = Query(..., description="策略名称：taishang_1/taishang_2/taishang_3"),
    allocated_cash: float = Query(..., description="分配资金"),
    custom_params: Optional[dict] = None,
    current_user: dict = Depends(get_current_user)
):
    """激活策略自动交易"""
    try:
        user_id = current_user["user_id"]
        
        # 使用配置管理器验证策略和参数
        try:
            from api.simulation.strategy_config import strategy_config_manager
            strategy_config = strategy_config_manager.get_strategy_config(strategy_name)
            
            # 验证参数
            validated_params = strategy_config_manager.validate_strategy_params(
                strategy_name, 
                {'allocated_cash': allocated_cash, 'custom_params': custom_params}
            )
            allocated_cash = validated_params['allocated_cash']
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # 检查用户是否有模拟账户
        account = await simulation_service.get_account_info(user_id)
        if not account:
            raise HTTPException(status_code=404, detail="用户模拟账户不存在，请先初始化账户")
        
        # 检查可用资金是否足够
        if account.get('available_cash', 0) < allocated_cash:
            raise HTTPException(status_code=400, detail="可用资金不足")
        
        # 导入策略调度器
        from api.simulation.strategy_scheduler import strategy_scheduler
        
        # 创建或更新策略配置
        config = simulation_service.db.create_user_strategy_config(
            user_id=user_id,
            strategy_name=strategy_name,
            allocated_cash=allocated_cash,
            custom_params=custom_params or {}
        )
        
        if not config:
            raise HTTPException(status_code=500, detail="创建策略配置失败")
        
        # 启动策略调度
        strategy_config = {
            'strategy_name': strategy_name,
            'allocated_cash': allocated_cash,
            'custom_params': custom_params or {}
        }
        
        success = await strategy_scheduler.start_user_strategy(user_id, strategy_config)
        
        if not success:
            raise HTTPException(status_code=500, detail="启动策略调度失败")
        
        return {
            "message": f"策略 {strategy_name} 激活成功",
            "strategy_name": strategy_name,
            "allocated_cash": allocated_cash,
            "success": True,
            "timestamp": datetime.now()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"激活策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"激活策略失败: {str(e)}")


@router.post("/strategy/deactivate", response_model=dict, summary="停止策略自动交易")  
async def deactivate_strategy(
    strategy_name: str = Query(..., description="策略名称"),
    current_user: dict = Depends(get_current_user)
):
    """停止策略自动交易"""
    try:
        user_id = current_user["user_id"]
        
        # 检查策略配置是否存在
        config = simulation_service.db.get_user_strategy_config(user_id, strategy_name)
        if not config:
            raise HTTPException(status_code=404, detail="策略配置不存在")
        
        # 导入策略调度器
        from api.simulation.strategy_scheduler import strategy_scheduler
        
        # 停止策略调度（即使任务不存在也不报错）
        await strategy_scheduler.stop_user_strategy(user_id, strategy_name)
        
        # 无论调度任务是否存在，都更新数据库状态为停止
        simulation_service.db.update_strategy_status(user_id, strategy_name, False)
        
        return {
            "message": f"策略 {strategy_name} 已停止",
            "strategy_name": strategy_name,
            "success": True,
            "timestamp": datetime.now()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止策略失败: {str(e)}")


@router.get("/strategy/configs", response_model=dict, summary="获取所有策略配置信息")
async def get_strategy_configs():
    """获取所有策略的配置信息"""
    try:
        from api.simulation.strategy_config import strategy_config_manager
        
        all_strategies = strategy_config_manager.get_all_strategies()
        strategy_info = {}
        
        for strategy_name, config in all_strategies.items():
            strategy_info[strategy_name] = strategy_config_manager.get_strategy_display_info(strategy_name)
        
        return {
            "strategies": strategy_info,
            "total_strategies": len(strategy_info),
            "success": True
        }
    
    except Exception as e:
        logger.error(f"获取策略配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略配置失败: {str(e)}")


@router.get("/strategy/status", response_model=dict, summary="查看策略运行状态")
async def get_strategy_status(current_user: dict = Depends(get_current_user)):
    """查看用户的策略运行状态和持仓"""
    try:
        user_id = current_user["user_id"]
        
        # 获取用户的所有策略配置
        configs = simulation_service.db.get_user_strategy_configs(user_id)
        
        # 导入策略调度器
        from api.simulation.strategy_scheduler import strategy_scheduler
        
        strategy_status = []
        for config in configs:
            strategy_name = config.get('strategy_name')
            
            # 获取调度任务状态
            job_status = strategy_scheduler.get_job_status(user_id, strategy_name)
            
            # 获取策略持仓（从交易记录中统计）
            strategy_positions = await _get_strategy_positions(user_id, strategy_name)
            
            # 计算策略收益（简化实现）
            strategy_return = await _calculate_strategy_return(user_id, strategy_name, config.get('allocated_cash', 0))
            
            strategy_info = {
                "strategy_name": strategy_name,
                "display_name": _get_strategy_display_name(strategy_name),
                "is_active": config.get('is_active', False),
                "allocated_cash": config.get('allocated_cash', 0),
                "execution_count": config.get('execution_count', 0),
                "total_trades": config.get('total_trades', 0),
                "last_execution": config.get('last_execution'),
                "current_positions": len(strategy_positions),
                "position_details": strategy_positions,
                "total_return": strategy_return.get('total_return', 0),
                "total_return_rate": strategy_return.get('total_return_rate', 0),
                "next_run_time": job_status.get('next_run_time') if job_status else None,
                "created_time": config.get('created_time')
            }
            
            strategy_status.append(strategy_info)
        
        return {
            "strategies": strategy_status,
            "total_strategies": len(strategy_status),
            "active_strategies": len([s for s in strategy_status if s['is_active']]),
            "timestamp": datetime.now()
        }
    
    except Exception as e:
        logger.error(f"获取策略状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略状态失败: {str(e)}")




@router.get("/strategy/positions", response_model=dict, summary="获取策略持仓")
async def get_strategy_positions(
    strategy_name: Optional[str] = Query(default=None, description="策略名称，不提供则返回所有策略持仓"),
    current_user: dict = Depends(get_current_user)
):
    """获取策略的持仓情况"""
    try:
        user_id = current_user["user_id"]
        
        # 获取用户所有持仓
        all_positions = await simulation_service.get_user_positions(user_id)
        
        # 获取策略交易记录来判断持仓来源
        trades, _ = await simulation_service.get_trade_history(user_id, page=1, page_size=10000)
        
        # 构建股票到策略的映射
        stock_strategy_map = {}
        for trade in trades:
            if trade.get('trade_source') == 'STRATEGY' and trade.get('strategy_name'):
                stock_code = trade.get('stock_code')
                trade_strategy = trade.get('strategy_name')
                stock_strategy_map[stock_code] = trade_strategy
        
        # 筛选策略持仓
        strategy_positions = []
        for position in all_positions:
            stock_code = position.get('stock_code')
            position_strategy = stock_strategy_map.get(stock_code)
            
            if position_strategy and (not strategy_name or position_strategy == strategy_name):
                position['strategy_name'] = position_strategy
                position['strategy_display_name'] = _get_strategy_display_name(position_strategy)
                strategy_positions.append(position)
        
        return {
            "positions": strategy_positions,
            "total_positions": len(strategy_positions),
            "total_market_value": sum(p.get('market_value', 0) for p in strategy_positions),
            "total_unrealized_pnl": sum(p.get('unrealized_pnl', 0) for p in strategy_positions),
            "filter_strategy": strategy_name,
            "timestamp": datetime.now()
        }
    
    except Exception as e:
        logger.error(f"获取策略持仓失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略持仓失败: {str(e)}")


# ==================== 辅助函数 ====================

def _get_strategy_display_name(strategy_name: str) -> str:
    """获取策略显示名称"""
    try:
        from api.simulation.strategy_config import strategy_config_manager
        config = strategy_config_manager.get_strategy_config(strategy_name)
        return config.display_name
    except:
        # 兜底方案
        strategy_names = {
        'value_investment': '价值投资策略',
        'growth_stock': '成长股策略',
        'momentum_breakthrough': '动量突破策略',
        'high_dividend': '高股息策略',
        'technical_breakthrough': '技术突破策略',
        'oversold_rebound': '超跌反弹策略',
        'limit_up_leader': '连板龙头策略',
        'fund_flow_tracking': '融资追踪策略'
        }
        return strategy_names.get(strategy_name, strategy_name)


async def _get_strategy_positions(user_id: str, strategy_name: str) -> List[Dict[str, Any]]:
    """获取策略当前持仓"""
    try:
        # 获取用户所有持仓
        all_positions = await simulation_service.get_user_positions(user_id)
        
        # 获取策略交易记录
        trades, _ = await simulation_service.get_trade_history(user_id, page=1, page_size=1000)
        
        # 找出属于该策略的股票
        strategy_stocks = set()
        for trade in trades:
            if (trade.get('trade_source') == 'STRATEGY' and 
                trade.get('strategy_name') == strategy_name):
                strategy_stocks.add(trade.get('stock_code'))
        
        # 筛选策略持仓
        strategy_positions = []
        for position in all_positions:
            if position.get('stock_code') in strategy_stocks:
                strategy_positions.append(position)
        
        return strategy_positions
        
    except Exception as e:
        logger.error(f"获取策略持仓失败: {e}")
        return []


async def _calculate_strategy_return(user_id: str, strategy_name: str, allocated_cash: float) -> Dict[str, float]:
    """计算策略收益"""
    try:
        # 获取策略交易记录
        trades, _ = await simulation_service.get_trade_history(user_id, page=1, page_size=1000)
        
        # 筛选策略交易
        strategy_trades = [t for t in trades if (
            t.get('trade_source') == 'STRATEGY' and 
            t.get('strategy_name') == strategy_name
        )]
        
        if not strategy_trades:
            return {'total_return': 0, 'total_return_rate': 0}
        
        # 简化计算：买入总额 - 卖出总额
        buy_amount = sum(t.get('amount', 0) for t in strategy_trades if t.get('trade_type') == 'BUY')
        sell_amount = sum(t.get('amount', 0) for t in strategy_trades if t.get('trade_type') == 'SELL')
        
        # 获取当前持仓市值
        strategy_positions = await _get_strategy_positions(user_id, strategy_name)
        current_market_value = sum(p.get('market_value', 0) for p in strategy_positions)
        
        # 计算总收益 = 卖出收入 + 当前持仓市值 - 买入成本
        total_return = sell_amount + current_market_value - buy_amount
        total_return_rate = total_return / allocated_cash if allocated_cash > 0 else 0
        
        return {
            'total_return': total_return,
            'total_return_rate': total_return_rate
        }
        
    except Exception as e:
        logger.error(f"计算策略收益失败: {e}")
        return {'total_return': 0, 'total_return_rate': 0}


def _calculate_strategy_performance(trades: List[Dict[str, Any]], allocated_cash: float) -> Dict[str, Any]:
    """计算策略表现指标"""
    try:
        if not trades:
            return {}
        
        # 基础统计
        buy_trades = [t for t in trades if t.get('trade_type') == 'BUY']
        sell_trades = [t for t in trades if t.get('trade_type') == 'SELL']
        
        buy_amount = sum(t.get('amount', 0) for t in buy_trades)
        sell_amount = sum(t.get('amount', 0) for t in sell_trades)
        
        # 计算收益
        gross_profit = sell_amount - buy_amount
        total_commission = sum(t.get('commission', 0) for t in trades)
        net_profit = gross_profit - total_commission
        
        # 计算收益率
        return_rate = net_profit / allocated_cash if allocated_cash > 0 else 0
        
        # 胜率计算（简化：假设每次买入对应一次卖出）
        win_rate = 0.5  # 简化处理，实际需要匹配交易对
        
        return {
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'return_rate': return_rate,
            'total_commission': total_commission,
            'win_rate': win_rate,
            'avg_trade_amount': (buy_amount + sell_amount) / len(trades) if trades else 0
        }
        
    except Exception as e:
        logger.error(f"计算策略表现指标失败: {e}")
        return {}


async def _get_strategy_trades(user_id: str, strategy_name: str) -> List[Dict[str, Any]]:
    """
    获取特定策略的交易记录
    
    Args:
        user_id: 用户ID
        strategy_name: 策略名称
        
    Returns:
        策略交易记录列表
    """
    try:
        trades, _ = await simulation_service.get_trade_history(
            user_id=user_id,
            page=1,
            page_size=1000  # 获取足够多的记录
        )
        
        # 过滤出属于指定策略的交易
        strategy_trades = [
            trade for trade in trades 
            if trade.get('strategy_name') == strategy_name
        ]
        
        return strategy_trades
        
    except Exception as e:
        logger.error(f"获取策略交易记录失败: {e}")
        return []


@router.get("/strategy/performance", response_model=dict, summary="获取策略绩效分析")
async def get_strategy_performance(
    strategy_name: str = Query(..., description="策略名称：taishang_1/taishang_2/taishang_3"),
    current_user: dict = Depends(get_current_user)
):
    """获取策略绩效分析"""
    try:
        user_id = current_user["user_id"]
        
        # 验证策略名称
        valid_strategies = ['taishang_1', 'taishang_2', 'taishang_3']
        if strategy_name not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"无效的策略名称，支持的策略: {valid_strategies}")
        
        # 获取策略配置
        config = simulation_service.db.get_user_strategy_config(user_id, strategy_name)
        if not config:
            # 如果策略配置不存在，返回默认值
            return {
                "strategy_name": strategy_name,
                "total_return": 0.0,
                "total_return_rate": 0.0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "trade_count": 0,
                "success": True
            }
        
        # 获取策略交易记录
        strategy_trades = await _get_strategy_trades(user_id, strategy_name)
        
        # 使用系统完整的绩效分析功能
        try:
            # 导入绩效分析器
            import sys
            import os
            backtrader_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'backtrader_strategies'
            )
            sys.path.insert(0, backtrader_path)
            
            from backtest.performance_analyzer import PerformanceAnalyzer
            
            # 创建绩效分析器实例
            analyzer = PerformanceAnalyzer()
            
            # 将交易记录转换为DataFrame
            import pandas as pd
            if strategy_trades:
                trades_df = pd.DataFrame(strategy_trades)
                # 统一字段名称
                if 'trade_type' in trades_df.columns:
                    trades_df['order_type'] = trades_df['trade_type'].map({'BUY': 'buy', 'SELL': 'sell'})
                trades_df['trade_date'] = pd.to_datetime(trades_df.get('trade_date', trades_df.get('created_at', '')))
                trades_df['commission'] = trades_df.get('commission', 0)
                trades_df['stamp_tax'] = trades_df.get('stamp_tax', 0)
            else:
                trades_df = pd.DataFrame()
            
            # 计算交易指标
            trade_metrics = analyzer.calculate_trade_metrics(trades_df)
            
            # 计算基础绩效指标（如果有组合历史数据）
            # 这里简化处理，实际应该构建组合快照历史
            allocated_cash = config.get('allocated_cash', 300000)
            
            # 分离买入和卖出交易进行基础计算
            buy_trades = [t for t in strategy_trades if t.get('trade_type') == 'BUY']
            sell_trades = [t for t in strategy_trades if t.get('trade_type') == 'SELL']
            
            # 计算基础收益指标
            total_buy_amount = sum(t.get('amount', 0) for t in buy_trades)
            total_sell_amount = sum(t.get('amount', 0) for t in sell_trades)
            total_commission = sum(t.get('commission', 0) for t in strategy_trades)
            
            gross_profit = total_sell_amount - total_buy_amount
            net_profit = gross_profit - total_commission
            return_rate = (net_profit / allocated_cash) if allocated_cash > 0 else 0.0
            
            # 计算胜率
            profitable_trades = len([t for t in sell_trades if float(t.get('amount', 0)) > float(t.get('cost_amount', t.get('amount', 0)))])
            win_rate = (profitable_trades / len(sell_trades)) if sell_trades else 0.0
            
            # 计算简化的最大回撤和夏普比率
            # TODO: 需要组合价值历史数据来计算精确的回撤和夏普比率
            max_drawdown = 0.0
            sharpe_ratio = 0.0
            
            # 如果有足够的交易数据，尝试估算波动率和夏普比率
            if len(strategy_trades) > 10:
                # 简化的波动率估算
                trade_returns = []
                for trade in sell_trades:
                    if trade.get('cost_amount'):
                        trade_return = (float(trade.get('amount', 0)) - float(trade.get('cost_amount', 0))) / float(trade.get('cost_amount', 1))
                        trade_returns.append(trade_return)
                
                if trade_returns:
                    import numpy as np
                    returns_std = np.std(trade_returns)
                    avg_return = np.mean(trade_returns)
                    # 简化的夏普比率计算
                    if returns_std > 0:
                        sharpe_ratio = (avg_return - 0.03/252) / returns_std  # 假设无风险利率3%
            
            return {
                "strategy_name": strategy_name,
                "total_return": net_profit,
                "total_return_rate": return_rate,
                "win_rate": win_rate,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "trade_count": trade_metrics.get('total_trades', len(strategy_trades)),
                "total_commission": trade_metrics.get('total_commission', total_commission),
                "total_fees": trade_metrics.get('total_fees', total_commission),
                "monthly_trade_frequency": trade_metrics.get('monthly_trade_frequency', 0),
                "avg_holding_period_days": trade_metrics.get('avg_holding_period_days', 0)
            }
            
        except Exception as e:
            self.logger.error(f"使用完整绩效分析失败，使用简化计算: {e}")
            
            # 回退到简化计算
            allocated_cash = config.get('allocated_cash', 300000)
            buy_trades = [t for t in strategy_trades if t.get('trade_type') == 'BUY']
            sell_trades = [t for t in strategy_trades if t.get('trade_type') == 'SELL']
            
            total_buy_amount = sum(t.get('amount', 0) for t in buy_trades)
            total_sell_amount = sum(t.get('amount', 0) for t in sell_trades)
            total_commission = sum(t.get('commission', 0) for t in strategy_trades)
            
            gross_profit = total_sell_amount - total_buy_amount
            net_profit = gross_profit - total_commission
            return_rate = (net_profit / allocated_cash) if allocated_cash > 0 else 0.0
            
            profitable_trades = len([t for t in sell_trades if float(t.get('amount', 0)) > float(t.get('cost_amount', t.get('amount', 0)))])
            win_rate = (profitable_trades / len(sell_trades)) if sell_trades else 0.0
            
            return {
                "strategy_name": strategy_name,
                "total_return": net_profit,
                "total_return_rate": return_rate,
                "win_rate": win_rate,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "trade_count": len(strategy_trades)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略绩效失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略绩效失败: {str(e)}")


@router.post("/strategy/manual-execute", response_model=dict, summary="手动触发策略执行（测试用）")
async def manual_execute_strategy(
    strategy_name: str = Query(..., description="策略名称：taishang_1/taishang_2/taishang_3"),
    current_user: dict = Depends(get_current_user)
):
    """手动触发策略执行（用于测试和调试）"""
    try:
        user_id = current_user["user_id"]
        
        # 验证策略名称
        valid_strategies = ['taishang_1', 'taishang_2', 'taishang_3']
        if strategy_name not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"无效的策略名称，支持的策略: {valid_strategies}")
        
        # 获取策略配置
        config = simulation_service.db.get_user_strategy_config(user_id, strategy_name)
        if not config:
            raise HTTPException(status_code=404, detail="策略配置不存在，请先激活策略")
        
        # 导入策略调度器
        from api.simulation.strategy_scheduler import strategy_scheduler
        
        # 构建策略配置
        strategy_config = {
            'strategy_name': strategy_name,
            'allocated_cash': config.get('allocated_cash', 300000),
            'custom_params': config.get('custom_params', {})
        }
        
        logger.info(f"手动触发策略执行: {user_id} - {strategy_name}")
        
        # 手动执行策略任务
        await strategy_scheduler._execute_strategy_job(user_id, strategy_config)
        
        return {
            "message": f"策略 {strategy_name} 手动执行完成",
            "strategy_name": strategy_name,
            "user_id": user_id,
            "success": True,
            "timestamp": datetime.now()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动执行策略失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"手动执行策略失败: {str(e)}")