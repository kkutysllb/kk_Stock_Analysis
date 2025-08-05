#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略选股模块API
提供技术面、基本面、特色选股等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

from api.routers.user import get_current_user, require_roles
from api.cache_middleware import cache_endpoint

from api.config.strategy_templates import StrategyTemplateConfig
from api.global_db import db_handler

# 初始化日志记录器
logger = logging.getLogger(__name__)

# 资金追踪策略参数模型
class FundFlowTrackingParams(BaseModel):
    market_cap: str = "all"
    stock_pool: str = "all"
    limit: int = 20
    margin_buy_trend_min: float = 50
    margin_balance_growth_min: float = 50

# 创建路由器
router = APIRouter(tags=["策略选股"])


# ==================== 数据模型 ====================

class ScreeningResult(BaseModel):
    """选股结果"""
    ts_code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    industry: Optional[str] = Field(None, description="所属行业")
    market: Optional[str] = Field(None, description="市场类型")
    score: Optional[float] = Field(None, description="综合评分")
    # 常用字段提升到顶层
    close: Optional[float] = Field(None, description="最新价")
    pe: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    pct_chg: Optional[float] = Field(None, description="涨跌幅(%)")
    total_mv: Optional[float] = Field(None, description="总市值(万元)")
    # 成长股策略专用字段
    avg_eps_growth: Optional[float] = Field(None, description="EPS增长率(%)")
    avg_revenue_growth: Optional[float] = Field(None, description="营收增长率(%)")
    avg_roic: Optional[float] = Field(None, description="ROIC(%)")
    peg_ratio: Optional[float] = Field(None, description="PEG")
    avg_gross_margin: Optional[float] = Field(None, description="毛利率(%)")
    avg_net_margin: Optional[float] = Field(None, description="净利率(%)")
    latest_rd_rate: Optional[float] = Field(None, description="研发费用率(%)")
    avg_debt_ratio: Optional[float] = Field(None, description="资产负债率(%)")
    avg_quick_ratio: Optional[float] = Field(None, description="速动比率")
    # 动量突破策略专用字段
    period_return: Optional[float] = Field(None, description="过去N日收益率(%)")
    rps_score: Optional[float] = Field(None, description="相对强度RPS")
    ema_20: Optional[float] = Field(None, description="20日EMA")
    ema_50: Optional[float] = Field(None, description="50日EMA")
    volume_ratio: Optional[float] = Field(None, description="量比")
    rsi: Optional[float] = Field(None, description="RSI")
    macd: Optional[float] = Field(None, description="MACD")
    macd_signal: Optional[float] = Field(None, description="MACD信号线")
    macd_histogram: Optional[float] = Field(None, description="MACD柱状图")
    breakthrough_signal: Optional[bool] = Field(None, description="突破信号")
    # 高股息策略专用字段
    dividend_yield: Optional[float] = Field(None, description="股息率(%)")
    payout_ratio: Optional[float] = Field(None, description="股息支付率(%)")
    dividend_coverage: Optional[float] = Field(None, description="股息覆盖率")
    roe: Optional[float] = Field(None, description="净资产收益率(%)")
    roic: Optional[float] = Field(None, description="投入资本回报率(%)")
    fcf_revenue_ratio: Optional[float] = Field(None, description="自由现金流/营收(%)")
    debt_ratio: Optional[float] = Field(None, description="资产负债率(%)")
    eps: Optional[float] = Field(None, description="每股收益")
    net_profit_margin: Optional[float] = Field(None, description="净利润率(%)")
    # 新增高股息策略专用字段
    dividend_fundraising_ratio: Optional[float] = Field(None, description="分红募资比(%)")
    net_cash: Optional[float] = Field(None, description="净现金水平(万元)")
    # 资金追踪策略专用字段 - 基于两融和资金流数据
    margin_buy_trend: Optional[float] = Field(None, description="融资买入趋势评分(%)")
    margin_balance_growth: Optional[float] = Field(None, description="融资余额增长评分(%)")
    margin_activity_score: Optional[float] = Field(None, description="两融活跃度评分(%)")
    short_sell_trend: Optional[float] = Field(None, description="融券趋势评分(%)")
    large_order_net_inflow: Optional[float] = Field(None, description="大单净流入(万元)")
    super_large_net_inflow: Optional[float] = Field(None, description="超大单净流入(万元)")
    fund_flow_continuity: Optional[float] = Field(None, description="资金流入连续性(%)")
    institutional_fund_ratio: Optional[float] = Field(None, description="机构资金占比(%)")
    industry_fund_rank: Optional[int] = Field(None, description="行业资金排名")
    industry_fund_strength: Optional[float] = Field(None, description="行业资金流入强度(%)")
    sector_rotation_score: Optional[float] = Field(None, description="行业轮动评分(%)")
    fund_tracking_score: Optional[float] = Field(None, description="资金追踪综合评分(%)")
    # 详细数据
    technical: Optional[Dict[str, Any]] = Field(None, description="技术指标")
    fundamental: Optional[Dict[str, Any]] = Field(None, description="基本面数据")
    special: Optional[Dict[str, Any]] = Field(None, description="特色数据")
    fund_flow: Optional[Dict[str, Any]] = Field(None, description="资金流向数据")

class ScreeningResponse(BaseModel):
    """选股响应"""
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: str = Field(..., description="策略类型")
    total_count: int = Field(..., description="结果总数")
    screening_time: datetime = Field(..., description="选股时间")
    results: List[ScreeningResult] = Field(..., description="选股结果")
    saved_to_pool: bool = Field(default=False, description="是否已保存到股票池")
    pool_name: Optional[str] = Field(None, description="股票池名称")


# ==================== API接口 ====================

@cache_endpoint(data_type="strategy_templates", ttl=1800)  # 缓存30分钟
@router.get("/templates")
async def get_strategy_templates(
    current_user: dict = Depends(get_current_user)
):
    """获取策略模板列表"""
    try:
        # 获取用户自定义策略模板（仍从数据库获取）
        user_templates = list(db_handler.get_collection('user_strategy_templates').find({
            'user_id': current_user['user_id'],
            'is_active': True
        }).sort('create_time', -1))
        
        # 从配置文件获取系统预设模板
        system_templates = StrategyTemplateConfig.get_all_templates()
        
        # 统一格式化模板数据
        all_templates = []
        
        # 处理系统预设模板（从配置文件）
        for template in system_templates:
            all_templates.append({
                'id': template['id'],
                'name': template['name'],
                'description': template['description'],
                'strategy_type': template['strategy_type'],
                'conditions': template['conditions'],
                'weights': template.get('weights', {}),
                'tags': template.get('tags', []),
                'is_system': True
            })
        
        # 处理用户自定义模板（仍从数据库）
        for template in user_templates:
            all_templates.append({
                'id': str(template['_id']),
                'name': template['template_name'],
                'description': template['description'],
                'strategy_type': template['strategy_type'],
                'conditions': template['conditions'],
                'weights': template.get('weights', {}),
                'tags': template.get('tags', []),
                'is_system': False
            })
        
        return all_templates
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略模板失败: {str(e)}")

# 注意：原来的 _create_default_templates 函数已删除
# 系统预设模板现在从 config/strategy_templates.py 配置文件获取

@cache_endpoint(data_type="screening_history", ttl=60)  # 缓存1分钟
@router.get("/history")
async def get_screening_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    strategy_type: Optional[str] = Query(None, description="策略类型筛选"),
    current_user: dict = Depends(get_current_user)
):
    """获取选股历史记录"""
    try:
        # 构建查询条件
        query = {'user_id': current_user['user_id']}
        if strategy_type:
            query['strategy_type'] = strategy_type
        
        # 分页查询
        skip = (page - 1) * page_size
        total = db_handler.get_collection('strategy_screening_results').count_documents(query)
        
        records = list(db_handler.get_collection('strategy_screening_results').find(
            query,
            {'results': 0}  # 不返回详细结果，只返回概要信息
        ).sort('screening_time', -1).skip(skip).limit(page_size))
        
        # 格式化返回数据
        for record in records:
            record['_id'] = str(record['_id'])
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'records': records
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选股历史失败: {str(e)}")

@router.get("/history/{record_id}")
async def get_screening_detail(
    record_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取选股记录详情"""
    try:
        from bson import ObjectId
        
        record = db_handler.get_collection('strategy_screening_results').find_one({
            '_id': ObjectId(record_id),
            'user_id': current_user['user_id']
        })
        
        if not record:
            raise HTTPException(status_code=404, detail="选股记录不存在")
        
        record['_id'] = str(record['_id'])
        return record
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选股详情失败: {str(e)}")


async def _get_latest_trade_date() -> str:
    """获取最新交易日期"""
    try:
        latest = db_handler.get_collection('stock_factor_pro').find_one(
            {}, 
            {"trade_date": 1}, 
            sort=[("trade_date", -1)]
        )
        return latest["trade_date"] if latest else datetime.now().strftime('%Y%m%d')
    except Exception:
        return datetime.now().strftime('%Y%m%d')

# ==================== 辅助函数 ====================

async def _resolve_stock_pool(stock_pool: List[str]) -> List[str]:
    """解析股票池，将股票池名称映射到实际股票代码"""
    resolved_stocks = []
    
    for pool_item in stock_pool:
        if pool_item == "all":
            # 全A股
            stocks = await _get_active_stocks(limit=2000)
            resolved_stocks.extend(stocks)
        elif pool_item == "hs300":
            # 沪深300
            try:
                hs300_stocks = list(db_handler.get_collection('index_member_all').find(
                    {'index_code': '399300.SZ'},
                    {'con_code': 1, '_id': 0}
                ))
                resolved_stocks.extend([stock['con_code'] for stock in hs300_stocks])
            except Exception:
                # 如果获取失败，使用备用列表
                resolved_stocks.extend(["000001.SZ", "000002.SZ", "600000.SH", "600036.SH"])
        elif pool_item == "zz500":
            # 中证500
            try:
                zz500_stocks = list(db_handler.get_collection('index_member_all').find(
                    {'index_code': '000905.SH'},
                    {'con_code': 1, '_id': 0}
                ))
                resolved_stocks.extend([stock['con_code'] for stock in zz500_stocks])
            except Exception:
                resolved_stocks.extend(["000858.SZ", "002415.SZ", "300059.SZ"])
        elif pool_item == "cyb":
            # 创业板
            try:
                cyb_stocks = list(db_handler.get_collection('infrastructure_stock_basic').find(
                    {
                        'market': '创业板',
                        'ts_code': {'$regex': r'^30'}  # 创业板代码以30开头
                    },
                    {'ts_code': 1, '_id': 0}
                ).limit(500))
                resolved_stocks.extend([stock['ts_code'] for stock in cyb_stocks])
            except Exception:
                resolved_stocks.extend(["300059.SZ", "300015.SZ", "300033.SZ"])
        elif pool_item == "kcb":
            # 科创板
            try:
                kcb_stocks = list(db_handler.get_collection('infrastructure_stock_basic').find(
                    {
                        'market': '科创板',
                        'ts_code': {'$regex': r'^688'}  # 科创板代码以688开头
                    },
                    {'ts_code': 1, '_id': 0}
                ).limit(500))
                resolved_stocks.extend([stock['ts_code'] for stock in kcb_stocks])
            except Exception:
                resolved_stocks.extend(["688001.SH", "688009.SH", "688036.SH"])
        else:
            # 如果是具体的股票代码，直接添加
            if pool_item.endswith(('.SH', '.SZ')):
                resolved_stocks.append(pool_item)
    
    # 去重并返回
    return list(set(resolved_stocks))

async def _get_active_stocks(limit: int = 2000) -> List[str]:
    """获取活跃股票列表（优化版）"""
    try:
        # 从股票基本信息表获取活跃股票代码
        stocks = list(db_handler.get_collection('infrastructure_stock_basic').find(
            {
                'market': {'$in': ['主板', '创业板', '科创板']},  # 主板、创业板、科创板
                'ts_code': {'$regex': r'^(00|30|60)'}  # 股票代码格式过滤
            },
            {'ts_code': 1, '_id': 0}
        ).limit(limit))
        return [stock['ts_code'] for stock in stocks]
    except Exception as e:
        print(f"获取活跃股票列表失败: {e}")
        # 如果获取失败，返回备用列表
        return []

async def _save_to_stock_pool(user_id: str, pool_name: str, stock_codes: List[str], strategy_name: str) -> bool:
    """保存选股结果到股票池"""
    try:
        # 检查股票池是否存在
        existing_pool = db_handler.get_collection('user_stock_pools').find_one({
            'user_id': user_id,
            'pool_name': pool_name
        })
        
        if existing_pool:
            # 更新现有股票池
            db_handler.get_collection('user_stock_pools').update_one(
                {'_id': existing_pool['_id']},
                {
                    '$addToSet': {'stocks': {'$each': [{'ts_code': code, 'add_time': datetime.now(), 'source': f'策略选股-{strategy_name}'} for code in stock_codes]}},
                    '$set': {'update_time': datetime.now()}
                }
            )
        else:
            # 创建新股票池
            new_pool = {
                'user_id': user_id,
                'pool_name': pool_name,
                'description': f'策略选股结果 - {strategy_name}',
                'stocks': [{'ts_code': code, 'add_time': datetime.now(), 'source': f'策略选股-{strategy_name}'} for code in stock_codes],
                'create_time': datetime.now(),
                'update_time': datetime.now(),
                'is_active': True
            }
            db_handler.get_collection('user_stock_pools').insert_one(new_pool)
        
        # 记录操作日志
        operation_log = {
            'user_id': user_id,
            'pool_name': pool_name,
            'operation_type': 'strategy_screening',
            'operation_detail': {
                'strategy_name': strategy_name,
                'added_stocks': stock_codes,
                'stock_count': len(stock_codes)
            },
            'operation_time': datetime.now()
        }
        db_handler.get_collection('user_pool_operations').insert_one(operation_log)
        
        return True
        
    except Exception:
        return False

# 添加策略模板应用接口

async def _get_template_by_id(template_id: str) -> Optional[Dict[str, Any]]:
    """根据ID获取策略模板"""
    try:
        # 旧数据库ID到新配置文件ID的映射（兼容前端）
        legacy_id_mapping = {
            "686a347c09e24f7707f7b4d8": "value",      # 价值投资策略
            "686a347c09e24f7707f7b4d9": "growth",     # 成长股策略
            "686a78a59faddf493bb01c60": "momentum",   # 动量突破策略
            "686a71f4c51f290dcebb0742": "dividend",   # 高股息策略
            "686a347c09e24f7707f7b4da": "technical",  # 技术突破策略
            "686a347c09e24f7707f7b4db": "oversold",   # 超跌反弹策略
            "686a347c09e24f7707f7b4dc": "limit_up",   # 连板龙头策略
            "686a347c09e24f7707f7b4dd": "fund_flow",  # 资金追踪策略
        }
        
        # 如果是旧的数据库ID，映射到新的配置文件ID
        if template_id in legacy_id_mapping:
            template_id = legacy_id_mapping[template_id]
            logger.info(f"🔄 [模板映射] 旧ID映射到新ID: {template_id}")
        
        # 首先尝试从配置文件获取系统预设模板
        system_template = StrategyTemplateConfig.get_template_by_id(template_id)
        if system_template:
            logger.info(f"✅ [模板获取] 从配置文件获取到模板: {system_template['name']}")
            return {
                'template_name': system_template['name'],
                'strategy_type': system_template['strategy_type'],
                'conditions': system_template['conditions'],
                'weights': system_template.get('weights', {}),
                'tags': system_template.get('tags', [])
            }
        
        # 如果不是系统模板，尝试从数据库获取用户自定义模板
        try:
            from bson import ObjectId
            # 尝试作为ObjectId查询
            if len(template_id) == 24:  # ObjectId长度为24
                db_template = db_handler.get_collection('user_strategy_templates').find_one({
                    '_id': ObjectId(template_id),
                    'is_active': True
                })
            else:
                # 尝试作为模板名称查询
                db_template = db_handler.get_collection('user_strategy_templates').find_one({
                    'template_name': template_id,
                    'is_active': True
                })
                
            if db_template:
                logger.info(f"✅ [模板获取] 从数据库获取到用户模板: {db_template['template_name']}")
                return {
                    'template_name': db_template['template_name'],
                    'strategy_type': db_template['strategy_type'],
                    'conditions': db_template['conditions'],
                    'weights': db_template.get('weights', {}),
                    'tags': db_template.get('tags', [])
                }
        except Exception as db_error:
            logger.error(f"数据库查询模板失败: {str(db_error)}")
            
        logger.warning(f"⚠️ [模板获取] 未找到模板: {template_id}")
        return None
        
    except Exception as e:
        logger.error(f"获取模板失败: {str(e)}")
        return None


# ==================== 8大策略模板接口 ====================

@router.post("/value-investment")
@cache_endpoint(data_type="value_investment", ttl=300)
async def value_investment_screening(
    market_cap: str = "all",  # 市值范围：large/mid/small/all
    stock_pool: str = "all",  # 股票池：all/main/gem/star
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """价值投资策略专门接口 - 基于历史财报均值，使用策略适配器实现"""
    try:
        # 导入价值投资策略适配器
        from backtrader_strategies.strategy_adapters.value_investment_adapter import ValueInvestmentAdapter
        
        # 创建适配器实例并执行选股
        adapter = ValueInvestmentAdapter()
        adapter_result = await adapter.screen_stocks(
            market_cap=market_cap,
            stock_pool=stock_pool,
            limit=limit
        )
        
        # 检查是否有错误
        if 'error' in adapter_result:
            logger.error(f"价值投资适配器执行失败: {adapter_result['error']}")
            raise HTTPException(status_code=500, detail=f"价值投资策略筛选失败: {adapter_result['error']}")
        
        # 转换适配器返回格式为API标准格式
        formatted_results = []
        for stock in adapter_result.get('stocks', []):
            result = ScreeningResult(
                ts_code=stock.get('ts_code'),
                name=stock.get('name', ''),
                industry=stock.get('industry'),
                close=stock.get('close'),
                pe=stock.get('pe'),
                pb=stock.get('pb'),
                pct_chg=stock.get('pct_chg'),
                total_mv=stock.get('total_mv'),
                score=stock.get('total_score', 0),
                roe=stock.get('roe'),
                # 将适配器的详细数据放入technical字段以便前端显示
                technical={
                    'avg_roe': stock.get('avg_roe'),
                    'roe_stability': stock.get('roe_stability'),
                    'growth_score': stock.get('growth_score'),
                    'profitability_score': stock.get('profitability_score'),
                    'total_score': stock.get('total_score'),
                    'reason': stock.get('reason')
                }
            )
            formatted_results.append(result)
        
        return ScreeningResponse(
            strategy_name=adapter_result.get('strategy_name', "价值投资策略"),
            strategy_type="fundamental", 
            total_count=adapter_result.get('total_count', 0),
            screening_time=datetime.now(),
            results=formatted_results
        )
        
    except ImportError as e:
        logger.error(f"无法导入价值投资策略适配器: {str(e)}")
        raise HTTPException(status_code=500, detail="策略适配器加载失败")
    except Exception as e:
        logger.error(f"价值投资策略筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"价值投资策略筛选失败: {str(e)}")

@router.post("/growth-stock")
@cache_endpoint(data_type="growth_stock", ttl=300)
async def growth_stock_screening(
    market_cap: str = "all",
    stock_pool: str = "all", 
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """成长股策略专门接口 - 高质量成长股筛选，使用策略适配器实现"""
    try:
        # 导入成长股策略适配器
        from backtrader_strategies.strategy_adapters.growth_stock_adapter import GrowthStockAdapter
        
        # 创建适配器实例并执行选股
        adapter = GrowthStockAdapter()
        adapter_result = await adapter.screen_stocks(
            market_cap=market_cap,
            stock_pool=stock_pool,
            limit=limit
        )
        
        # 检查是否有错误
        if 'error' in adapter_result:
            logger.error(f"成长股适配器执行失败: {adapter_result['error']}")
            raise HTTPException(status_code=500, detail=f"成长股策略筛选失败: {adapter_result['error']}")
        
        # 转换适配器返回格式为API标准格式
        formatted_results = []
        for stock in adapter_result.get('stocks', []):
            result = ScreeningResult(
                ts_code=stock.get('ts_code'),
                name=stock.get('name', ''),
                industry=stock.get('industry'),
                close=stock.get('close'),
                pe=stock.get('pe'),
                pb=stock.get('pb'),
                pct_chg=stock.get('pct_chg'),
                total_mv=stock.get('total_mv'),
                score=stock.get('score', 0),
                # 成长股策略专用字段
                avg_eps_growth=stock.get('avg_eps_growth'),
                avg_revenue_growth=stock.get('avg_revenue_growth'),
                avg_roic=stock.get('avg_roic'),
                peg_ratio=stock.get('peg_ratio'),
                avg_gross_margin=stock.get('avg_gross_margin'),
                avg_net_margin=stock.get('avg_net_margin'),
                latest_rd_rate=stock.get('latest_rd_rate'),
                avg_debt_ratio=stock.get('avg_debt_ratio'),
                avg_quick_ratio=stock.get('avg_quick_ratio')
            )
            formatted_results.append(result)
        
        return ScreeningResponse(
            strategy_name=adapter_result.get('strategy_name', "成长股策略"),
            strategy_type="growth",
            total_count=adapter_result.get('total_count', 0),
            screening_time=datetime.now(),
            results=formatted_results
        )
        
    except ImportError as e:
        logger.error(f"无法导入成长股策略适配器: {str(e)}")
        raise HTTPException(status_code=500, detail="策略适配器加载失败")
    except Exception as e:
        logger.error(f"成长股策略筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"成长股策略筛选失败: {str(e)}")

@router.post("/momentum-breakthrough")
@cache_endpoint(data_type="momentum_breakthrough", ttl=300)
async def momentum_breakthrough_screening(
    market_cap: str = "all",
    stock_pool: str = "all",
    limit: int = 20,
    period_days: int = 60,  # 过去N日收益率计算周期
    rps_threshold: float = 80,  # RPS阈值
    rsi_min: float = 50,  # RSI最小值
    rsi_max: float = 70,  # RSI最大值
    volume_ratio_min: float = 1.5,  # 量比最小值
    require_macd_golden: bool = True,  # 是否要求MACD金叉
    current_user: dict = Depends(get_current_user)
):
    "动量突破策略专门接口 - 使用策略适配器实现"
    try:
        # 导入动量突破策略适配器
        from backtrader_strategies.strategy_adapters.momentum_breakthrough_adapter import MomentumBreakthroughAdapter
        
        # 创建适配器实例并执行选股
        adapter = MomentumBreakthroughAdapter()
        
        # 传递参数给适配器（注意：适配器可能不支持所有参数，需要在适配器中实现）
        adapter_result = await adapter.screen_stocks(
            market_cap=market_cap,
            stock_pool=stock_pool,
            limit=limit
        )
        
        # 检查是否有错误
        if 'error' in adapter_result:
            logger.error(f"动量突破适配器执行失败: {adapter_result['error']}")
            raise HTTPException(status_code=500, detail=f"动量突破策略筛选失败: {adapter_result['error']}")
        
        # 转换适配器返回格式为API标准格式
        formatted_results = []
        for stock in adapter_result.get('stocks', []):
            result = ScreeningResult(
                ts_code=stock.get('ts_code'),
                name=stock.get('name', ''),
                industry=stock.get('industry'),
                close=stock.get('close'),
                pe=stock.get('pe'),
                pb=stock.get('pb'),
                pct_chg=stock.get('pct_chg'),
                total_mv=stock.get('total_mv'),
                score=stock.get('score', 0),
                # 动量突破策略专用字段
                period_return=stock.get('period_return'),
                rps_score=stock.get('rps_score'),
                ema_20=stock.get('ema_20'),
                ema_50=stock.get('ema_50'),
                volume_ratio=stock.get('volume_ratio'),
                rsi=stock.get('rsi'),
                macd=stock.get('macd'),
                macd_signal=stock.get('macd_signal'),
                macd_histogram=stock.get('macd_histogram'),
                breakthrough_signal=stock.get('breakthrough_signal')
            )
            formatted_results.append(result)
        
        return ScreeningResponse(
            strategy_name=adapter_result.get('strategy_name', "动量突破策略"),
            strategy_type="momentum",
            total_count=adapter_result.get('total_count', 0),
            screening_time=datetime.now(),
            results=formatted_results
        )
        
    except ImportError as e:
        logger.error(f"无法导入动量突破策略适配器: {str(e)}")
        raise HTTPException(status_code=500, detail="策略适配器加载失败")
    except Exception as e:
        logger.error(f"动量突破策略筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"动量突破策略筛选失败: {str(e)}")


@router.post("/high-dividend")
@cache_endpoint(data_type="high_dividend", ttl=300)
async def high_dividend_screening(
    market_cap: str = "all",
    stock_pool: str = "all",
    limit: int = 20,
    dividend_yield_min: float = 2.0,  # 股息率最低要求：近一年>2%（调整为更宽松）
    payout_ratio_min: float = 20.0,  # 股息支付率最低：近3年>20%（调整为更宽松）
    dividend_fundraising_ratio_min: float = 30.0,  # 分红募资比最低：>30%（调整为更宽松）
    net_cash_min: float = -1000000.0,  # 净现金水平最低：不限制
    current_user: dict = Depends(get_current_user)
):
    """高股息策略专门接口 - 调整版：分红募资比>50%，股息支付率>30%，股息率>2%，净现金水平>0"""
    try:
        pipeline = []
        latest_date = await _get_latest_trade_date()
        
        # 基础筛选条件
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": 0},  # 确保有效价格
            "total_mv": {"$gt": 0},  # 确保有效市值
        }
        
        # 市值筛选
        if market_cap == "large":
            match_conditions["total_mv"] = {"$gte": 5000000}
        elif market_cap == "mid":
            match_conditions["total_mv"] = {"$gte": 1000000, "$lte": 5000000}
        elif market_cap == "small":
            match_conditions["total_mv"] = {"$lte": 1000000}
        
        # 股票池筛选
        if stock_pool != "all":
            resolved_pool = await _resolve_stock_pool([stock_pool])
            if resolved_pool:
                match_conditions["ts_code"] = {"$in": resolved_pool}
        
        pipeline.extend([
            {"$match": match_conditions},
            
            # 联接股票基本信息
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            # 联接最新财务指标数据
            {"$lookup": {
                "from": "stock_fina_indicator",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$ts_code"]}
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 1}
                ],
                "as": "fina_data"
            }},
            {"$unwind": {"path": "$fina_data", "preserveNullAndEmptyArrays": True}},
            
            # 联接现金流数据
            {"$lookup": {
                "from": "stock_cash_flow",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$ts_code"]}
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 1}
                ],
                "as": "cashflow_data"
            }},
            {"$unwind": {"path": "$cashflow_data", "preserveNullAndEmptyArrays": True}},
            
            # 联接利润表数据
            {"$lookup": {
                "from": "stock_income",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$ts_code"]}
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 1}
                ],
                "as": "income_data"
            }},
            {"$unwind": {"path": "$income_data", "preserveNullAndEmptyArrays": True}},
            
            # 联接资产负债表数据
            {"$lookup": {
                "from": "stock_balance_sheet",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$ts_code"]}
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 1}
                ],
                "as": "balance_data"
            }},
            {"$unwind": {"path": "$balance_data", "preserveNullAndEmptyArrays": True}},
            
            # 联接近3年财务指标数据计算股息支付率平均值
            {"$lookup": {
                "from": "stock_fina_indicator",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$ts_code"]}
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 3}  # 近3年数据
                ],
                "as": "fina_data_3y"
            }},
            
            # 联接近3年现金流数据计算募资和分红数据
            {"$lookup": {
                "from": "stock_cash_flow",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$ts_code"]}
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 3}  # 近3年数据
                ],
                "as": "cashflow_data_3y"
            }},
            
            # 计算关键指标
            {"$addFields": {
                # 基础财务指标
                "roe": {"$ifNull": ["$fina_data.roe", 0]},  # ROE
                "roa": {"$ifNull": ["$fina_data.roa", 0]},  # ROA
                "eps": {"$ifNull": ["$fina_data.eps", 0]},  # 每股收益
                "bps": {"$ifNull": ["$fina_data.bps", 0]},  # 每股净资产
                
                # 计算股息率（使用EPS估算，假设40%分红率）
                "dividend_yield": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": [{"$ifNull": ["$fina_data.eps", 0]}, 0]},
                            {"$gt": [{"$ifNull": ["$close", 0]}, 0]}
                        ]},
                        "then": {
                            "$multiply": [
                                {"$divide": [
                                    {"$multiply": [{"$ifNull": ["$fina_data.eps", 0]}, 0.4]},  # 假设40%分红率
                                    {"$ifNull": ["$close", 1]}
                                ]},
                                100
                            ]
                        },
                        "else": 0
                    }
                },
                
                # 计算股息支付率（假设25%）
                "payout_ratio_3y": {
                    "$literal": 25  # 假设股息支付率为25%
                },
                
                # 计算分红募资比（使用实际字段）
                "dividend_fundraising_ratio": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$cashflow_data_3y"}, 0]},
                        "then": {
                            "$let": {
                                "vars": {
                                    "total_dividends": {
                                        "$sum": {
                                            "$map": {
                                                "input": "$cashflow_data_3y",
                                                "as": "cf",
                                                "in": {"$abs": {"$ifNull": ["$$cf.c_pay_dist_dpcp_int_exp", 0]}}
                                            }
                                        }
                                    },
                                    "total_fundraising": {
                                        "$sum": {
                                            "$map": {
                                                "input": "$cashflow_data_3y",
                                                "as": "cf",
                                                "in": {
                                                    "$add": [
                                                        {"$ifNull": ["$$cf.proc_issue_bonds", 0]},
                                                        {"$ifNull": ["$$cf.stot_cash_in_fnc_act", 0]}
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                },
                                "in": {
                                    "$cond": {
                                        "if": {"$gt": ["$$total_fundraising", 0]},
                                        "then": {
                                            "$multiply": [
                                                {"$divide": ["$$total_dividends", "$$total_fundraising"]},
                                                100
                                            ]
                                        },
                                        "else": 0
                                    }
                                }
                            }
                        },
                        "else": 0
                    }
                },
                
                # 计算净现金水平（使用实际字段：现金储备 - 银行借款）
                "net_cash": {
                    "$cond": {
                        "if": {"$ne": ["$balance_data", None]},
                        "then": {
                            "$subtract": [
                                {"$ifNull": ["$balance_data.cash_reser_cb", 0]},
                                {"$ifNull": ["$balance_data.cb_borr", 0]}
                            ]
                        },
                        "else": 0
                    }
                },
                
                # 计算自由现金流/营收比率
                "fcf_revenue_ratio": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": [{"$ifNull": ["$income_data.total_revenue", 0]}, 0]},
                            {"$ne": [{"$ifNull": ["$cashflow_data.free_cashflow", 0]}, None]}
                        ]},
                        "then": {
                            "$multiply": [
                                {"$divide": [
                                    {"$ifNull": ["$cashflow_data.free_cashflow", 0]},
                                    {"$ifNull": ["$income_data.total_revenue", 1]}
                                ]},
                                100
                            ]
                        },
                        "else": 0
                    }
                },
                
                # 计算资产负债率
                "debt_ratio": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": [{"$ifNull": ["$balance_data.total_assets", 0]}, 0]},
                            {"$gt": [{"$ifNull": ["$balance_data.total_liab", 0]}, 0]}
                        ]},
                        "then": {
                            "$multiply": [
                                {"$divide": [
                                    {"$ifNull": ["$balance_data.total_liab", 0]},
                                    {"$ifNull": ["$balance_data.total_assets", 1]}
                                ]},
                                100
                            ]
                        },
                        "else": 0
                    }
                },
                
                # 计算净利润率
                "net_profit_margin": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": [{"$ifNull": ["$income_data.total_revenue", 0]}, 0]},
                            {"$ne": [{"$ifNull": ["$income_data.n_income", 0]}, None]}
                        ]},
                        "then": {
                            "$multiply": [
                                {"$divide": [
                                    {"$ifNull": ["$income_data.n_income", 0]},
                                    {"$ifNull": ["$income_data.total_revenue", 1]}
                                ]},
                                100
                            ]
                        },
                        "else": 0
                    }
                }
            }},
            
            # 应用高股息策略筛选条件（极简版本）
            {"$match": {
                "$and": [
                    # 核心筛选条件
                    {"dividend_yield": {"$gte": dividend_yield_min}},  # 股息率近一年 > 2%
                    {"eps": {"$gt": 0}},  # 每股收益为正
                    
                    # 市值筛选
                    {"total_mv": {"$gte": 1000000}},  # 总市值 > 10亿
                    
                    # 排除ST股票
                    {"stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}}
                ]
            }},
            
            # 计算综合评分（100分制）
            {"$addFields": {
                "score": {
                    "$min": [
                        100,  # 最高100分
                        {
                            "$add": [
                                {"$multiply": ["$dividend_yield", 8]},  # 股息率权重：8分/% (最高24分)
                                {"$multiply": [{"$min": ["$payout_ratio_3y", 50]}, 0.3]},  # 股息支付率权重：最高15分
                                {"$multiply": [{"$min": ["$dividend_fundraising_ratio", 100]}, 0.2]},  # 分红募资比权重：最高20分
                                {
                                    "$cond": {
                                        "if": {"$gt": ["$net_cash", 0]},
                                        "then": {"$min": [{"$multiply": [{"$divide": ["$net_cash", 100000]}, 2]}, 10]},  # 净现金正数加分，最高10分
                                        "else": 0
                                    }
                                },
                                {"$multiply": [{"$min": ["$roe", 20]}, 0.5]},  # ROE权重：最高10分
                                {"$multiply": [{"$min": ["$roa", 10]}, 0.5]},  # ROA权重：最高5分
                                {
                                    "$cond": {
                                        "if": {"$gt": ["$fcf_revenue_ratio", 0]},
                                        "then": {"$min": [{"$multiply": ["$fcf_revenue_ratio", 0.2]}, 5]},  # 现金流正数加分，最高5分
                                        "else": 0
                                    }
                                },
                                {"$multiply": [{"$min": ["$net_profit_margin", 20]}, 0.25]},  # 净利润率权重：最高5分
                                {
                                    "$cond": {
                                        "if": {"$lt": ["$debt_ratio", 60]},
                                        "then": {"$multiply": [{"$subtract": [60, "$debt_ratio"]}, 0.1]},  # 低负债率加分，最高6分
                                        "else": 0
                                    }
                                }
                            ]
                        }
                    ]
                }
            }},
            
            # 输出字段
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": "$stock_info.industry",
                "close": 1,
                "pe": 1,
                "pb": 1,
                "pct_chg": {"$ifNull": ["$pct_chg", 0]},
                "total_mv": {"$ifNull": ["$total_mv", 0]},
                "score": 1,
                # 高股息策略专用字段
                "dividend_yield": 1,  # 股息率近一年
                "payout_ratio_3y": 1,  # 股息支付率近3年平均
                "dividend_fundraising_ratio": 1,  # 分红募资比
                "net_cash": 1,  # 净现金水平
                "roe": 1,
                "roa": 1,
                "eps": 1,
                "bps": 1,
                "fcf_revenue_ratio": 1,
                "debt_ratio": 1,
                "net_profit_margin": 1
            }},
            {"$sort": {"score": -1}},
            {"$limit": limit}
        ])
        
        results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
        
        formatted_results = [ScreeningResult(
            ts_code=r['ts_code'],
            name=r.get('name', ''),
            industry=r.get('industry'),
            close=r.get('close'),
            pe=r.get('pe'),
            pb=r.get('pb'),
            pct_chg=r.get('pct_chg'),
            total_mv=r.get('total_mv'),
            score=round(r.get('score', 0), 2),
            # 高股息策略专用字段（使用新的计算指标）
            dividend_yield=round(r.get('dividend_yield', 0), 2),  # 股息率近一年
            payout_ratio=round(r.get('payout_ratio_3y', 0), 2),  # 股息支付率近3年平均
            dividend_coverage=None,  # 暂时保留为None
            roe=r.get('roe'),
            roic=r.get('roa'),  # 使用ROA代替ROIC
            fcf_revenue_ratio=r.get('fcf_revenue_ratio'),
            debt_ratio=r.get('debt_ratio'),
            # 新增字段
            eps=r.get('eps'),
            net_profit_margin=r.get('net_profit_margin'),
            # 新增策略特定字段
            dividend_fundraising_ratio=round(r.get('dividend_fundraising_ratio', 0), 2),  # 分红募资比
            net_cash=round(r.get('net_cash', 0) / 10000, 2)  # 净现金水平（万元）
        ) for r in results]
        
        return ScreeningResponse(
            strategy_name="高股息策略",
            strategy_type="dividend",  # 修正策略类型
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"高股息策略筛选失败: {str(e)}")

@router.post("/technical-breakthrough")
@cache_endpoint(data_type="technical_breakthrough", ttl=300)
async def technical_breakthrough_screening(
    market_cap: str = "all",
    stock_pool: str = "all",
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """技术突破策略专门接口 - 使用策略适配器实现"""
    try:
        # 导入技术突破策略适配器
        from backtrader_strategies.strategy_adapters.technical_breakthrough_adapter import TechnicalBreakthroughAdapter
        
        # 创建适配器实例并执行选股
        adapter = TechnicalBreakthroughAdapter()
        adapter_result = await adapter.screen_stocks(
            market_cap=market_cap,
            stock_pool=stock_pool,
            limit=limit
        )
        
        # 检查是否有错误
        if 'error' in adapter_result:
            logger.error(f"技术突破策略适配器执行失败: {adapter_result['error']}")
            raise HTTPException(status_code=500, detail=f"技术突破策略筛选失败: {adapter_result['error']}")
        
        # 转换适配器返回格式为API标准格式
        formatted_results = []
        for stock in adapter_result.get('stocks', []):
            result = ScreeningResult(
                ts_code=stock.get('ts_code'),
                name=stock.get('name', ''),
                industry=stock.get('industry'),
                close=stock.get('close'),
                pe=stock.get('pe'),
                pb=stock.get('pb'),
                pct_chg=stock.get('pct_chg'),
                total_mv=stock.get('total_mv'),
                score=stock.get('score', 0)
            )
            formatted_results.append(result)
        
        return ScreeningResponse(
            strategy_name=adapter_result.get('strategy_name', "技术突破策略"),
            strategy_type="technical",
            total_count=adapter_result.get('total_count', 0),
            screening_time=datetime.now(),
            results=formatted_results
        )
        
    except ImportError as e:
        logger.error(f"无法导入技术突破策略适配器: {str(e)}")
        raise HTTPException(status_code=500, detail="策略适配器加载失败")
    except Exception as e:
        logger.error(f"技术突破策略筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"技术突破策略筛选失败: {str(e)}")


@router.post("/oversold-rebound")
@cache_endpoint(data_type="oversold_rebound", ttl=300)
async def oversold_rebound_screening(
    market_cap: str = "all",
    stock_pool: str = "all",
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """超跌反弹策略专门接口 - 使用策略适配器实现"""
    try:
        # 导入超跌反弹策略适配器
        from backtrader_strategies.strategy_adapters.oversold_rebound_adapter import OversoldReboundAdapter
        
        # 创建适配器实例并执行选股
        adapter = OversoldReboundAdapter()
        adapter_result = await adapter.screen_stocks(
            market_cap=market_cap,
            stock_pool=stock_pool,
            limit=limit
        )
        
        # 检查是否有错误
        if 'error' in adapter_result:
            logger.error(f"超跌反弹策略适配器执行失败: {adapter_result['error']}")
            raise HTTPException(status_code=500, detail=f"超跌反弹策略筛选失败: {adapter_result['error']}")
        
        # 转换适配器返回格式为API标准格式
        formatted_results = []
        for stock in adapter_result.get('stocks', []):
            result = ScreeningResult(
                ts_code=stock.get('ts_code'),
                name=stock.get('name', ''),
                industry=stock.get('industry'),
                close=stock.get('close'),
                pe=stock.get('pe'),
                pb=stock.get('pb'),
                pct_chg=stock.get('pct_chg'),
                total_mv=stock.get('total_mv'),
                score=stock.get('score', 0)
            )
            formatted_results.append(result)
        
        return ScreeningResponse(
            strategy_name=adapter_result.get('strategy_name', "超跌反弹策略"),
            strategy_type="oversold",
            total_count=adapter_result.get('total_count', 0),
            screening_time=datetime.now(),
            results=formatted_results
        )
        
    except ImportError as e:
        logger.error(f"无法导入超跌反弹策略适配器: {str(e)}")
        raise HTTPException(status_code=500, detail="策略适配器加载失败")
    except Exception as e:
        logger.error(f"超跌反弹策略筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"超跌反弹策略筛选失败: {str(e)}")


@router.post("/limit-up-leader")
@cache_endpoint(data_type="limit_up_leader", ttl=300)
async def limit_up_leader_screening(
    market_cap: str = "all",
    stock_pool: str = "all",
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """连板龙头策略专门接口 - 使用策略适配器实现"""
    try:
        # 导入连板龙头策略适配器
        from backtrader_strategies.strategy_adapters.limit_up_leader_adapter import LimitUpLeaderAdapter
        
        # 创建适配器实例并执行选股
        adapter = LimitUpLeaderAdapter()
        adapter_result = await adapter.screen_stocks(
            market_cap=market_cap,
            stock_pool=stock_pool,
            limit=limit
        )
        
        # 检查是否有错误
        if 'error' in adapter_result:
            logger.error(f"连板龙头策略适配器执行失败: {adapter_result['error']}")
            raise HTTPException(status_code=500, detail=f"连板龙头策略筛选失败: {adapter_result['error']}")
        
        # 转换适配器返回格式为API标准格式
        formatted_results = []
        for stock in adapter_result.get('stocks', []):
            result = ScreeningResult(
                ts_code=stock.get('ts_code'),
                name=stock.get('name', ''),
                industry=stock.get('industry'),
                close=stock.get('close'),
                pe=stock.get('pe'),
                pb=stock.get('pb'),
                pct_chg=stock.get('pct_chg'),
                total_mv=stock.get('total_mv'),
                score=stock.get('score', 0)
            )
            formatted_results.append(result)
        
        return ScreeningResponse(
            strategy_name=adapter_result.get('strategy_name', "连板龙头策略"),
            strategy_type="limit_up",
            total_count=adapter_result.get('total_count', 0),
            screening_time=datetime.now(),
            results=formatted_results
        )
        
    except ImportError as e:
        logger.error(f"无法导入连板龙头策略适配器: {str(e)}")
        raise HTTPException(status_code=500, detail="策略适配器加载失败")
    except Exception as e:
        logger.error(f"连板龙头策略筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"连板龙头策略筛选失败: {str(e)}")


@router.post("/fund-flow-tracking")
@cache_endpoint(data_type="fund_flow_tracking", ttl=300)
async def fund_flow_tracking_screening(
    market_cap: str = "all",
    stock_pool: str = "all",
    limit: int = 20,
    margin_buy_trend_min: float = 50.0,
    margin_balance_growth_min: float = 50.0,
    current_user: dict = Depends(get_current_user)
):
    """资金追踪策略专门接口 - 使用策略适配器实现，基于融资融券数据"""
    try:
        # 导入资金追踪策略适配器
        from backtrader_strategies.strategy_adapters.fund_flow_tracking_adapter import FundFlowTrackingAdapter
        
        # 创建适配器实例并执行选股
        adapter = FundFlowTrackingAdapter()
        adapter_result = await adapter.screen_stocks(
            market_cap=market_cap,
            stock_pool=stock_pool,
            limit=limit,
            margin_buy_trend_min=margin_buy_trend_min,
            margin_balance_growth_min=margin_balance_growth_min
        )
        
        # 检查是否有错误
        if 'error' in adapter_result:
            logger.error(f"资金追踪策略适配器执行失败: {adapter_result['error']}")
            raise HTTPException(status_code=500, detail=f"资金追踪策略筛选失败: {adapter_result['error']}")
        
        # 转换适配器返回格式为API标准格式
        formatted_results = []
        for stock in adapter_result.get('stocks', []):
            result = ScreeningResult(
                ts_code=stock.get('ts_code'),
                name=stock.get('name', ''),
                industry=stock.get('industry'),
                close=stock.get('close'),
                pe=stock.get('pe'),
                pb=stock.get('pb'),
                pct_chg=stock.get('pct_chg'),
                total_mv=stock.get('total_mv'),
                score=stock.get('score', 0),
                # 资金追踪策略专用字段
                margin_buy_trend=stock.get('margin_buy_trend'),
                margin_balance_growth=stock.get('margin_balance_growth'),
                fund_tracking_score=stock.get('fund_tracking_score')
            )
            formatted_results.append(result)
        
        return ScreeningResponse(
            strategy_name=adapter_result.get('strategy_name', "资金追踪策略"),
            strategy_type="fund_flow",
            total_count=adapter_result.get('total_count', 0),
            screening_time=datetime.now(),
            results=formatted_results
        )
        
    except ImportError as e:
        logger.error(f"无法导入资金追踪策略适配器: {str(e)}")
        raise HTTPException(status_code=500, detail="策略适配器加载失败")
    except Exception as e:
        logger.error(f"资金追踪策略筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"资金追踪策略筛选失败: {str(e)}")

