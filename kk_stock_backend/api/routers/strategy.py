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
from api.utils.strategy_screening import (
    StrategyScreeningEngine,
    TechnicalAnalyzer,
    FundamentalAnalyzer,
    SpecialDataAnalyzer
)
from api.config.strategy_templates import StrategyTemplateConfig
from api.global_db import db_handler

# 初始化日志记录器
logger = logging.getLogger(__name__)

screening_engine = StrategyScreeningEngine()

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

class TechnicalConditions(BaseModel):
    """技术面选股条件"""
    rsi_min: Optional[float] = Field(None, ge=0, le=100, description="RSI最小值")
    rsi_max: Optional[float] = Field(None, ge=0, le=100, description="RSI最大值")
    macd_positive: Optional[bool] = Field(None, description="MACD是否为正")
    above_ma20: Optional[bool] = Field(None, description="是否站上20日均线")
    volume_ratio_min: Optional[float] = Field(None, ge=0, description="量比最小值")
    kdj_k_min: Optional[float] = Field(None, ge=0, le=100, description="KDJ K值最小值")
    bb_position: Optional[str] = Field(None, description="布林带位置：upper/middle/lower")
    pct_chg_min: Optional[float] = Field(None, description="涨跌幅最小值(%)")
    pct_chg_max: Optional[float] = Field(None, description="涨跌幅最大值(%)")

class FundamentalConditions(BaseModel):
    """基本面选股条件"""
    total_score_min: Optional[float] = Field(None, ge=0, le=100, description="综合评分最小值")
    roe_min: Optional[float] = Field(None, description="净资产收益率最小值")
    pe_max: Optional[float] = Field(None, gt=0, description="市盈率最大值")
    pb_max: Optional[float] = Field(None, gt=0, description="市净率最大值")
    growth_score_min: Optional[float] = Field(None, ge=0, le=100, description="成长性评分最小值")
    profitability_score_min: Optional[float] = Field(None, ge=0, le=100, description="盈利能力评分最小值")
    debt_ratio_max: Optional[float] = Field(None, ge=0, le=100, description="资产负债率最大值")
    total_mv_min: Optional[float] = Field(None, ge=0, description="总市值最小值(万元)")
    total_mv_max: Optional[float] = Field(None, ge=0, description="总市值最大值(万元)")

class SpecialConditions(BaseModel):
    """特色选股条件"""
    limit_days_min: Optional[int] = Field(None, ge=0, description="连板天数最小值")
    net_inflow_positive: Optional[bool] = Field(None, description="资金是否净流入")
    hot_money_score_min: Optional[float] = Field(None, ge=0, le=100, description="游资关注度最小值")
    dragon_tiger_count_min: Optional[int] = Field(None, ge=0, description="龙虎榜次数最小值")
    institution_attention_min: Optional[float] = Field(None, ge=0, le=100, description="机构关注度最小值")
    
    # 资金追踪策略专用条件
    chip_concentration_min: Optional[float] = Field(None, ge=0, le=100, description="筹码集中度最小值")
    cost_advantage_min: Optional[float] = Field(None, ge=0, le=100, description="成本优势最小值")
    winner_rate_min: Optional[float] = Field(None, ge=0, le=100, description="筹码胜率最小值")
    large_order_inflow_positive: Optional[bool] = Field(None, description="大单是否净流入")
    super_large_inflow_positive: Optional[bool] = Field(None, description="超大单是否净流入")
    fund_continuity_min: Optional[float] = Field(None, ge=0, le=100, description="资金流入连续性最小值")
    institutional_ratio_min: Optional[float] = Field(None, ge=0, le=100, description="机构资金占比最小值")
    industry_rank_max: Optional[int] = Field(None, ge=1, description="行业资金排名最大值")
    fund_tracking_score_min: Optional[float] = Field(None, ge=0, le=100, description="资金追踪综合评分最小值")

class StrategyRequest(BaseModel):
    """策略选股请求"""
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: str = Field(..., description="策略类型：technical/fundamental/special/comprehensive/fund_flow")
    technical_conditions: Optional[TechnicalConditions] = Field(None, description="技术面条件")
    fundamental_conditions: Optional[FundamentalConditions] = Field(None, description="基本面条件")
    special_conditions: Optional[SpecialConditions] = Field(None, description="特色条件")
    stock_pool: Optional[List[str]] = Field(None, description="指定股票池")
    market_cap: Optional[str] = Field(None, description="市值范围：small/medium/large/all")
    limit: int = Field(default=50, ge=1, le=200, description="返回结果数量限制")
    save_to_pool: bool = Field(default=False, description="是否保存到股票池")
    pool_name: Optional[str] = Field(None, description="股票池名称（保存时使用）")

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
@router.post("/screening", response_model=ScreeningResponse)
@cache_endpoint(data_type="strategy_screening", ttl=600)  # 缓存10分钟
async def strategy_screening(
    request: StrategyRequest,
    current_user: dict = Depends(get_current_user)
):
    """策略选股"""
    try:
        # 获取股票池（如果指定）
        stock_pool = request.stock_pool
        if not stock_pool:
            # 获取全市场股票列表
            stock_pool = await _get_all_stocks()
        
        # 执行选股
        screening_results = await screening_engine.comprehensive_screening(
            stock_pool=stock_pool,
            technical_conditions=request.technical_conditions.dict(exclude_none=True) if request.technical_conditions else {},
            fundamental_conditions=request.fundamental_conditions.dict(exclude_none=True) if request.fundamental_conditions else {},
            special_conditions=request.special_conditions.dict(exclude_none=True) if request.special_conditions else {},
            strategy_type=request.strategy_type,
            limit=request.limit
        )
        
        # 转换结果格式
        results = []
        for result in screening_results:
            results.append(ScreeningResult(
                ts_code=result['ts_code'],
                name=result['name'],
                industry=result.get('industry'),
                market=result.get('market'),
                score=result.get('score'),
                technical=result.get('technical'),
                fundamental=result.get('fundamental'),
                special=result.get('special')
            ))
        
        # 保存选股结果到数据库
        screening_record = {
            'user_id': current_user['user_id'],
            'strategy_name': request.strategy_name,
            'strategy_type': request.strategy_type,
            'conditions': {
                'technical': request.technical_conditions.dict(exclude_none=True) if request.technical_conditions else {},
                'fundamental': request.fundamental_conditions.dict(exclude_none=True) if request.fundamental_conditions else {},
                'special': request.special_conditions.dict(exclude_none=True) if request.special_conditions else {}
            },
            'results': [r.dict() for r in results],
            'total_count': len(results),
            'screening_time': datetime.now(),
            'saved_to_pool': request.save_to_pool,
            'pool_name': request.pool_name
        }
        
        # 保存到策略选股结果集合
        db_handler.get_collection('strategy_screening_results').insert_one(screening_record)
        
        # 如果需要保存到股票池
        saved_to_pool = False
        if request.save_to_pool and request.pool_name:
            saved_to_pool = await _save_to_stock_pool(
                current_user['user_id'],
                request.pool_name,
                [r.ts_code for r in results],
                request.strategy_name
            )
        
        return ScreeningResponse(
            strategy_name=request.strategy_name,
            strategy_type=request.strategy_type,
            total_count=len(results),
            screening_time=datetime.now(),
            results=results,
            saved_to_pool=saved_to_pool,
            pool_name=request.pool_name if saved_to_pool else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略选股失败: {str(e)}")

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
        return [
            "000001.SZ", "000002.SZ", "000858.SZ", "002415.SZ", "300059.SZ",
            "600000.SH", "600036.SH", "600519.SH", "600887.SH", "601318.SH"
        ]

async def _get_all_stocks() -> List[str]:
    """获取全市场股票列表"""
    try:
        # 从股票基本信息表获取所有股票代码
        stocks = list(db_handler.get_collection('infrastructure_stock_basic').find(
            {'market': {'$in': ['主板', '创业板', '科创板', '北交所']}},  # 获取所有主要市场股票
            {'ts_code': 1, '_id': 0}
        ))
        return [stock['ts_code'] for stock in stocks]
    except Exception as e:
        print(f"获取全市场股票列表失败: {e}")
        # 如果获取失败，返回空列表
        return []

async def _process_stock_batch(
    stocks: List[str],
    technical_analyzer: TechnicalAnalyzer,
    fundamental_analyzer: FundamentalAnalyzer,
    special_analyzer: SpecialDataAnalyzer,
    request: StrategyRequest
) -> List[Dict[str, Any]]:
    """批量处理股票分析"""
    import asyncio
    
    results = []
    
    for stock in stocks:
        try:
            # 并行获取所有分析数据
            tasks = [
                technical_analyzer.get_stock_technical_indicators(stock),
                fundamental_analyzer.get_stock_fundamental_scores(stock),
                special_analyzer.get_stock_special_features(stock)
            ]
            
            technical, fundamental, special = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查是否符合筛选条件
            if not _check_screening_conditions(technical, fundamental, special, request):
                continue
            
            # 计算综合评分
            score = _calculate_comprehensive_score(technical, fundamental, special)
            
            # 获取股票基本信息
            stock_info = await _get_stock_basic_info_fast(stock)
            
            result = {
                'ts_code': stock,
                'name': stock_info.get('name', ''),
                'industry': stock_info.get('industry', ''),
                'market': stock_info.get('market', ''),
                'score': score,
                'technical': _format_technical_data(technical) if technical and not isinstance(technical, Exception) else None,
                'fundamental': _format_fundamental_data(fundamental) if fundamental and not isinstance(fundamental, Exception) else None,
                'special': _format_special_data(special) if special and not isinstance(special, Exception) else None
            }
            
            results.append(result)
            
        except Exception as e:
            # 记录错误但继续处理其他股票
            print(f"处理股票 {stock} 失败: {e}")
            continue
    
    return results

def _check_screening_conditions(technical, fundamental, special, request: StrategyRequest) -> bool:
    """检查是否符合筛选条件"""
    try:
        # 技术面条件检查
        if request.technical_conditions and technical and not isinstance(technical, Exception):
            if not _check_technical_conditions_fast(technical, request.technical_conditions):
                return False
        
        # 基本面条件检查
        if request.fundamental_conditions and fundamental and not isinstance(fundamental, Exception):
            if not _check_fundamental_conditions_fast(fundamental, request.fundamental_conditions):
                return False
        
        # 特色条件检查
        if request.special_conditions and special and not isinstance(special, Exception):
            if not _check_special_conditions_fast(special, request.special_conditions):
                return False
        
        return True
    except Exception:
        return False

def _check_technical_conditions_fast(technical, conditions: TechnicalConditions) -> bool:
    """快速检查技术面条件"""
    if conditions.rsi_min is not None and (technical.rsi is None or technical.rsi < conditions.rsi_min):
        return False
    if conditions.rsi_max is not None and (technical.rsi is None or technical.rsi > conditions.rsi_max):
        return False
    if conditions.macd_positive is not None and technical.macd is not None:
        if conditions.macd_positive and technical.macd <= 0:
            return False
        if not conditions.macd_positive and technical.macd >= 0:
            return False
    if conditions.above_ma20 is not None and technical.ma20 is not None and technical.close is not None:
        above_ma20 = technical.close > technical.ma20
        if conditions.above_ma20 != above_ma20:
            return False
    if conditions.volume_ratio_min is not None and (technical.volume_ratio is None or technical.volume_ratio < conditions.volume_ratio_min):
        return False
    return True

def _check_fundamental_conditions_fast(fundamental, conditions: FundamentalConditions) -> bool:
    """快速检查基本面条件"""
    if conditions.total_score_min is not None and (fundamental.total_score is None or fundamental.total_score < conditions.total_score_min):
        return False
    if conditions.roe_min is not None and (fundamental.roe is None or fundamental.roe < conditions.roe_min):
        return False
    if conditions.pe_max is not None and (fundamental.pe is None or fundamental.pe > conditions.pe_max):
        return False
    if conditions.pb_max is not None and (fundamental.pb is None or fundamental.pb > conditions.pb_max):
        return False
    return True

def _check_special_conditions_fast(special, conditions: SpecialConditions) -> bool:
    """快速检查特色条件"""
    if conditions.limit_days_min is not None and (special.limit_days is None or special.limit_days < conditions.limit_days_min):
        return False
    if conditions.net_inflow_positive is not None and special.net_inflow is not None:
        if conditions.net_inflow_positive and special.net_inflow <= 0:
            return False
        if not conditions.net_inflow_positive and special.net_inflow >= 0:
            return False
    return True

def _calculate_comprehensive_score(technical, fundamental, special) -> float:
    """计算综合评分"""
    scores = []
    weights = []
    
    if technical and not isinstance(technical, Exception):
        # 技术面评分
        tech_score = 0
        if technical.rsi is not None:
            tech_score += min(100, max(0, 100 - abs(technical.rsi - 50)))  # RSI接近50分数更高
        if technical.macd is not None and technical.macd > 0:
            tech_score += 20  # MACD为正加分
        if technical.close and technical.ma20 and technical.close > technical.ma20:
            tech_score += 20  # 站上20日均线加分
        
        scores.append(tech_score)
        weights.append(0.3)
    
    if fundamental and not isinstance(fundamental, Exception) and fundamental.total_score:
        scores.append(fundamental.total_score)
        weights.append(0.5)
    
    if special and not isinstance(special, Exception):
        # 特色评分
        special_score = 50  # 基础分
        if special.limit_days and special.limit_days > 0:
            special_score += min(30, special.limit_days * 10)  # 连板加分
        if special.net_inflow and special.net_inflow > 0:
            special_score += 20  # 资金净流入加分
        
        scores.append(special_score)
        weights.append(0.2)
    
    if not scores:
        return 50.0  # 默认分数
    
    # 加权平均
    total_weight = sum(weights)
    if total_weight == 0:
        return 50.0
    
    weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / total_weight
    return round(weighted_score, 2)

async def _get_stock_basic_info_fast(ts_code: str) -> Dict[str, Any]:
    """快速获取股票基本信息"""
    try:
        stock_info = db_handler.get_collection('infrastructure_stock_basic').find_one(
            {'ts_code': ts_code},
            {'name': 1, 'industry': 1, 'market': 1, '_id': 0}
        )
        return stock_info or {}
    except Exception:
        return {}

def _format_technical_data(technical) -> Dict[str, Any]:
    """格式化技术面数据"""
    if not technical:
        return {}
    
    return {
        'close': technical.close,
        'rsi': technical.rsi,
        'macd': technical.macd,
        'ma20': technical.ma20,
        'volume_ratio': technical.volume_ratio,
        'kdj_k': technical.kdj_k,
        'pe': technical.pe,
        'pb': technical.pb
    }

def _format_fundamental_data(fundamental) -> Dict[str, Any]:
    """格式化基本面数据"""
    if not fundamental:
        return {}
    
    return {
        'total_score': fundamental.total_score,
        'growth_score': fundamental.growth_score,
        'profitability_score': fundamental.profitability_score,
        'valuation_score': fundamental.valuation_score,
        'roe': fundamental.roe,
        'pe': fundamental.pe,
        'pb': fundamental.pb
    }

def _format_special_data(special) -> Dict[str, Any]:
    """格式化特色数据"""
    if not special:
        return {}
    
    return {
        'limit_days': special.limit_days,
        'net_inflow': special.net_inflow,
        'hot_money_score': special.hot_money_score,
        'dragon_tiger_count': special.dragon_tiger_count
    }

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
@router.post("/templates/{template_id}/apply")
# @cache_endpoint(data_type="strategy_screening", ttl=300)  # 临时移除缓存
async def apply_strategy_template(
    template_id: str,
    additional_params: Optional[Dict[str, Any]] = Body(None),
    current_user: dict = Depends(get_current_user)
):
    """应用策略模板进行选股"""
    try:
        logger.info(f"🔍 [模板应用] 开始处理模板ID: {template_id}")
        
        # 获取模板信息
        template = await _get_template_by_id(template_id)
        if not template:
            logger.error(f"❌ [模板应用] 模板不存在: {template_id}")
            raise HTTPException(status_code=404, detail="策略模板不存在")
        
        logger.info(f"✅ [模板应用] 获取到模板信息:")
        logger.info(f"   - 模板名称: {template['template_name']}")
        logger.info(f"   - 策略类型: {template['strategy_type']}")
        
        # 构建请求参数
        request_data = {
            "strategy_name": template["template_name"],
            "strategy_type": template["strategy_type"],
            "technical_conditions": template["conditions"].get("technical"),
            "fundamental_conditions": template["conditions"].get("fundamental"), 
            "special_conditions": template["conditions"].get("special"),
            "stock_pool": ["all"],  # 默认全A股
            "limit": 20
        }
        
        # 合并额外参数
        if additional_params:
            if "limit" in additional_params:
                request_data["limit"] = additional_params["limit"]
            if "stock_pool" in additional_params:
                request_data["stock_pool"] = additional_params["stock_pool"]
            if "market_cap" in additional_params:
                request_data["market_cap"] = additional_params["market_cap"]
        
        # 创建请求对象
        request = StrategyRequest(**request_data)
        
        # 根据模板名称调用相应的策略函数（基于数据库字段）
        template_name = template["template_name"]
        logger.info(f"🎯 [模板应用] 查找策略函数，模板名称: '{template_name}'")
        
        strategy_func_mapping = {
            "价值投资策略": value_investment_screening,
            "成长股策略": growth_stock_screening,
            "动量突破策略": momentum_breakthrough_screening,  # 添加缺失的映射
            "高股息策略": high_dividend_screening,           # 添加缺失的映射
            "技术突破策略": technical_breakthrough_screening,
            "超跌反弹策略": oversold_rebound_screening,
            "连板龙头策略": limit_up_leader_screening,
            "资金追踪策略": fund_flow_tracking_screening
        }
        
        if template_name not in strategy_func_mapping:
            logger.warning(f"⚠️ [模板应用] 未找到专门策略函数，使用通用筛选: {template_name}")
            logger.info(f"📋 [模板应用] 可用的策略映射: {list(strategy_func_mapping.keys())}")
            # 如果没有专门的策略函数，使用通用筛选
            return await _generic_template_screening(request, current_user)
        
        strategy_func = strategy_func_mapping[template_name]
        logger.info(f"✅ [模板应用] 找到对应策略函数: {strategy_func.__name__}")
        
        market_cap = getattr(request, 'market_cap', 'all')
        stock_pool = request.stock_pool[0] if request.stock_pool else 'all'
        limit = request.limit
        
        logger.info(f"📊 [模板应用] 调用策略函数参数:")
        logger.info(f"   - market_cap: {market_cap}")
        logger.info(f"   - stock_pool: {stock_pool}")
        logger.info(f"   - limit: {limit}")
        
        result = await strategy_func(market_cap, stock_pool, limit, current_user)
        
        logger.info(f"🎉 [模板应用] 策略函数执行完成:")
        logger.info(f"   - 返回类型: {type(result)}")
        
        # 处理缓存装饰器可能返回字典的情况
        if isinstance(result, dict):
            # 如果返回的是字典，检查是否有data字段（缓存装饰器的格式）
            if 'data' in result:
                actual_result = result['data']
                logger.info(f"   - 从缓存响应中提取data字段")
            else:
                # 直接是策略响应数据
                actual_result = result
                logger.info(f"   - 直接使用字典数据")
                
            # 手动构建ScreeningResponse对象
            from datetime import datetime
            response = ScreeningResponse(
                strategy_name=actual_result.get('strategy_name', template['template_name']),
                strategy_type=actual_result.get('strategy_type', template['strategy_type']),
                total_count=actual_result.get('total_count', 0),
                screening_time=datetime.now(),
                results=actual_result.get('results', []),
                saved_to_pool=actual_result.get('saved_to_pool', False),
                pool_name=actual_result.get('pool_name')
            )
            
            logger.info(f"   - 构建响应对象:")
            logger.info(f"     - 策略名称: {response.strategy_name}")
            logger.info(f"     - 策略类型: {response.strategy_type}")
            logger.info(f"     - 结果数量: {response.total_count}")
            
            return response
        else:
            # 如果返回的是ScreeningResponse对象，直接使用
            logger.info(f"   - 返回策略名称: {result.strategy_name}")
            logger.info(f"   - 返回策略类型: {result.strategy_type}")
            logger.info(f"   - 结果数量: {result.total_count}")
            return result
        
    except Exception as e:
        logger.error(f"💥 [模板应用] 应用模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"应用模板失败: {str(e)}")


# 添加前端兼容的高级筛选接口
@router.post("/advanced-screening-compatible") 
@cache_endpoint(data_type="strategy_screening", ttl=300)  # 缓存5分钟
async def advanced_screening_compatible(
    params: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """前端兼容的高级筛选接口"""
    try:
        # 转换前端参数格式到后端格式
        converted_params = _convert_advanced_params(params)
        
        # 创建请求对象
        request = StrategyRequest(**converted_params)
        
        # 使用聚合查询版本
        return await _advanced_screening_aggregation(request, current_user)
        
    except Exception as e:
        logger.error(f"高级筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"高级筛选失败: {str(e)}")

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

def _convert_frontend_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """转换前端快速选股参数到后端格式"""
    # 处理股票池参数
    stock_pool = params.get("stock_pool", "all")
    if isinstance(stock_pool, list):
        # 如果已经是列表，直接使用
        stock_pool_list = stock_pool
    else:
        # 如果是字符串，转换为列表
        stock_pool_list = [stock_pool]
    
    converted = {
        "strategy_name": f"快速选股-{params.get('strategy_type', 'default')}",
        "strategy_type": params.get("strategy_type", "comprehensive"),
        "stock_pool": stock_pool_list,
        "limit": params.get("limit", 20)
    }
    
    # 根据策略类型设置对应的条件 - 与模板保持一致
    strategy_type = params.get("strategy_type")
    
    if strategy_type == "growth":
        # 成长股策略
        converted["fundamental_conditions"] = {
            "growth_score_min": 80,
            "roe_min": 15,
            "profitability_score_min": 75
        }
    elif strategy_type == "value":
        # 价值投资策略
        converted["fundamental_conditions"] = {
            "total_score_min": 70,
            "roe_min": 10,
            "pe_max": 25,
            "pb_max": 3,
            "profitability_score_min": 70
        }
    elif strategy_type == "momentum":
        # 动量突破策略
        converted["technical_conditions"] = {
            "rsi_min": 50,
            "rsi_max": 80,
            "macd_positive": True,
            "above_ma20": True,
            "volume_ratio_min": 1.5
        }
    elif strategy_type == "dividend":
        # 高股息策略
        converted["fundamental_conditions"] = {
            "roe_min": 8,
            "pe_max": 30,
            "pb_max": 5,
            "profitability_score_min": 60,
            "debt_ratio_max": 60
        }
    elif strategy_type == "technical":
        # 技术突破策略
        converted["technical_conditions"] = {
            "rsi_min": 50,
            "rsi_max": 80,
            "macd_positive": True,
            "above_ma20": True,
            "volume_ratio_min": 1.5
        }
    elif strategy_type == "oversold":
        # 超跌反弹策略
        converted["technical_conditions"] = {
            "rsi_min": 20,
            "rsi_max": 40,
            "volume_ratio_min": 1.2
        }
        converted["fundamental_conditions"] = {
            "pe_max": 30,
            "pb_max": 5
        }
    elif strategy_type == "limit_up":
        # 连板龙头策略 - 修复条件
        converted["special_conditions"] = {
            "limit_days_min": 2,
            "net_inflow_positive": True,
            "hot_money_score_min": 60
        }
        converted["technical_conditions"] = {
            "volume_ratio_min": 2.0,
            "pct_chg_min": 0.0  # 涨跌幅必须为正
        }
    elif strategy_type == "fund_flow":
        # 资金追踪策略
        converted["special_conditions"] = {
            "net_inflow_positive": True,
            "institution_attention_min": 70,
            "dragon_tiger_count_min": 1
        }
        converted["fundamental_conditions"] = {
            "total_score_min": 60
        }
    
    # 处理市值筛选
    market_cap = params.get("market_cap")
    if market_cap and market_cap != "all":
        if not converted.get("fundamental_conditions"):
            converted["fundamental_conditions"] = {}
        
        if market_cap == "large":  # 大盘股 > 500亿
            converted["fundamental_conditions"]["total_mv_min"] = 5000000  # 500亿万元
        elif market_cap == "mid":  # 中盘股 100-500亿
            converted["fundamental_conditions"]["total_mv_min"] = 1000000  # 100亿万元
            converted["fundamental_conditions"]["total_mv_max"] = 5000000  # 500亿万元
        elif market_cap == "small":  # 小盘股 < 100亿
            converted["fundamental_conditions"]["total_mv_max"] = 1000000  # 100亿万元
    
    return converted

def _convert_advanced_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """转换前端高级筛选参数到后端格式"""
    # 处理股票池参数
    stock_pool = params.get("stock_pool", "all")
    if isinstance(stock_pool, list):
        # 如果已经是列表，直接使用
        stock_pool_list = stock_pool
    else:
        # 如果是字符串，转换为列表
        stock_pool_list = [stock_pool]
    
    converted = {
        "strategy_name": "高级筛选",
        "strategy_type": "comprehensive",
        "stock_pool": stock_pool_list,
        "limit": params.get("limit", 50)
    }
    
    # 转换技术面条件
    if "technical" in params:
        tech = params["technical"]
        tech_conditions = {}
        
        # RSI范围转换
        if "rsi_range" in tech and tech["rsi_range"]:
            tech_conditions["rsi_min"] = tech["rsi_range"][0]
            tech_conditions["rsi_max"] = tech["rsi_range"][1]
        
        # MACD信号转换
        if "macd_signal" in tech:
            if tech["macd_signal"] == "golden_cross":
                tech_conditions["macd_positive"] = True
            elif tech["macd_signal"] == "death_cross":
                tech_conditions["macd_positive"] = False
        
        # 均线趋势转换
        if "ma_trend" in tech:
            if tech["ma_trend"] == "bullish":
                tech_conditions["above_ma20"] = True
            elif tech["ma_trend"] == "bearish":
                tech_conditions["above_ma20"] = False
        
        if tech_conditions:
            converted["technical_conditions"] = tech_conditions
    
    # 转换基本面条件
    if "fundamental" in params:
        fund = params["fundamental"]
        fund_conditions = {}
        
        if "pe_min" in fund or "pe_max" in fund:
            if "pe_max" in fund:
                fund_conditions["pe_max"] = fund["pe_max"]
        
        if "pb_min" in fund or "pb_max" in fund:
            if "pb_max" in fund:
                fund_conditions["pb_max"] = fund["pb_max"]
        
        if "roe_min" in fund or "roe_max" in fund:
            if "roe_min" in fund:
                fund_conditions["roe_min"] = fund["roe_min"]
        
        if fund_conditions:
            converted["fundamental_conditions"] = fund_conditions
    
    # 转换特色条件
    if "special" in params:
        special = params["special"]
        special_conditions = {}
        
        if "limit_days" in special and special["limit_days"]:
            special_conditions["limit_days_min"] = special["limit_days"]
        
        if "dragon_tiger" in special and special["dragon_tiger"]:
            special_conditions["dragon_tiger_count_min"] = 1
        
        if special_conditions:
            converted["special_conditions"] = special_conditions
    
    return converted

async def _advanced_screening_aggregation(
    request: StrategyRequest,
    current_user: dict
) -> ScreeningResponse:
    """高级筛选聚合查询版本"""
    try:
        import time
        start_time = time.time()
        
        # 构建聚合查询管道
        pipeline = []
        
        # 获取最新交易日期
        latest_date = await _get_latest_trade_date()
        
        # 基础匹配条件
        match_conditions = {"trade_date": latest_date}
        
        # 添加技术面条件
        if request.technical_conditions:
            tech = request.technical_conditions
            
            if tech.rsi_min is not None:
                match_conditions["rsi_qfq_12"] = {"$gte": tech.rsi_min}
            if tech.rsi_max is not None:
                if "rsi_qfq_12" in match_conditions:
                    match_conditions["rsi_qfq_12"]["$lte"] = tech.rsi_max
                else:
                    match_conditions["rsi_qfq_12"] = {"$lte": tech.rsi_max}
            
            if tech.macd_positive is not None:
                if tech.macd_positive:
                    match_conditions["macd_qfq"] = {"$gt": 0}
                else:
                    match_conditions["macd_qfq"] = {"$lte": 0}
            
            if tech.volume_ratio_min is not None:
                match_conditions["volume_ratio"] = {"$gte": tech.volume_ratio_min}
            
            # 添加涨跌幅条件
            if tech.pct_chg_min is not None:
                match_conditions["pct_chg"] = {"$gte": tech.pct_chg_min}
            if tech.pct_chg_max is not None:
                if "pct_chg" in match_conditions:
                    match_conditions["pct_chg"]["$lte"] = tech.pct_chg_max
                else:
                    match_conditions["pct_chg"] = {"$lte": tech.pct_chg_max}
        
        # 添加基本面条件
        if request.fundamental_conditions:
            fund = request.fundamental_conditions
            
            if fund.pe_max is not None:
                match_conditions["pe"] = {"$lte": fund.pe_max, "$gt": 0}
            if fund.pb_max is not None:
                match_conditions["pb"] = {"$lte": fund.pb_max, "$gt": 0}
            if fund.roe_min is not None:
                match_conditions["roe"] = {"$gte": fund.roe_min}
            
            # 市值条件
            if fund.total_mv_min is not None:
                match_conditions["total_mv"] = {"$gte": fund.total_mv_min}
            if fund.total_mv_max is not None:
                if "total_mv" in match_conditions:
                    match_conditions["total_mv"]["$lte"] = fund.total_mv_max
                else:
                    match_conditions["total_mv"] = {"$lte": fund.total_mv_max}
        
        # 添加特色条件
        if request.special_conditions:
            special = request.special_conditions
            
            # 连板条件需要关联其他数据表，这里先简化处理
            if special.limit_days_min is not None:
                # 连板股票通常涨跌幅较大，添加额外筛选条件
                if "pct_chg" not in match_conditions:
                    match_conditions["pct_chg"] = {"$gte": 5.0}  # 涨幅至少5%
        
        # 添加股票池筛选
        if request.stock_pool and request.stock_pool != ["all"]:
            resolved_pool = await _resolve_stock_pool(request.stock_pool)
            if resolved_pool:
                match_conditions["ts_code"] = {"$in": resolved_pool}
        
        pipeline.append({"$match": match_conditions})
        
        # 关联股票基本信息
        pipeline.extend([
            {
                "$lookup": {
                    "from": "infrastructure_stock_basic",
                    "localField": "ts_code",
                    "foreignField": "ts_code",
                    "as": "stock_info"
                }
            },
            {
                "$unwind": {
                    "path": "$stock_info",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ])
        
        # 计算综合评分
        pipeline.append({
            "$addFields": {
                "score": {
                    "$add": [
                        {"$cond": {"if": {"$gte": ["$rsi_qfq_12", 30]}, "then": 50, "else": 20}},
                        {"$cond": {"if": {"$gt": ["$macd_qfq", 0]}, "then": 20, "else": 0}},
                        {"$cond": {"if": {"$gt": ["$close", "$ma_qfq_20"]}, "then": 20, "else": 0}}
                    ]
                }
            }
        })
        
        # 选择字段 - 将常用字段提升到顶层
        pipeline.append({
            "$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": "$stock_info.industry",
                "market": "$stock_info.market",
                "score": 1,
                # 提升到顶层的常用字段
                "close": "$close",
                "pe": "$pe",
                "pb": "$pb",
                "pct_chg": {"$ifNull": ["$pct_chg", 0]},  # 涨跌幅，如果没有则为0
                "total_mv": {"$ifNull": ["$total_mv", 0]},  # 总市值，如果没有则为0
                # 技术指标详情
                "technical": {
                    "close": "$close",
                    "rsi": "$rsi_qfq_12",
                    "macd": "$macd_qfq",
                    "ma20": "$ma_qfq_20",
                    "volume_ratio": "$volume_ratio",
                    "kdj_k": "$kdj_k_qfq",
                    "pe": "$pe",
                    "pb": "$pb"
                }
            }
        })
        
        # 排序和限制
        pipeline.extend([
            {"$sort": {"score": -1}},
            {"$limit": min(request.limit, 50)}
        ])
        
        # 执行查询
        results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append(ScreeningResult(
                ts_code=result['ts_code'],
                name=result.get('name', ''),
                industry=result.get('industry'),
                market=result.get('market'),
                score=round(result.get('score', 0), 2),
                # 顶层常用字段
                close=result.get('close'),
                pe=result.get('pe'),
                pb=result.get('pb'),
                pct_chg=result.get('pct_chg'),
                total_mv=result.get('total_mv'),
                # 详细数据
                technical=result.get('technical'),
                fundamental=None,
                special=None
            ))
        
        # 保存记录
        screening_record = {
            'user_id': current_user['user_id'],
            'strategy_name': request.strategy_name,
            'strategy_type': request.strategy_type,
            'conditions': {
                'technical': request.technical_conditions.dict(exclude_none=True) if request.technical_conditions else {},
                'fundamental': request.fundamental_conditions.dict(exclude_none=True) if request.fundamental_conditions else {},
                'special': request.special_conditions.dict(exclude_none=True) if request.special_conditions else {}
            },
            'results': [r.dict() for r in formatted_results],
            'total_count': len(formatted_results),
            'screening_time': datetime.now(),
            'processing_time': processing_time,
            'version': 'advanced_aggregation'
        }
        
        db_handler.get_collection('strategy_screening_results').insert_one(screening_record)
        
        return ScreeningResponse(
            strategy_name=request.strategy_name,
            strategy_type=request.strategy_type,
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results,
            saved_to_pool=False,
            pool_name=None
        )
        
    except Exception as e:
        logger.error(f"高级筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"高级筛选失败: {str(e)}")

# ==================== 策略模板聚合分析API ====================

@router.get("/templates/analytics")
@cache_endpoint(data_type="template_analytics", ttl=1800)  # 缓存30分钟
async def get_template_analytics(
    current_user: dict = Depends(get_current_user)
):
    """获取策略模板聚合分析数据"""
    try:
        # 获取所有策略模板
        templates = await get_strategy_templates(current_user)
        
        # 获取策略筛选历史数据
        results_collection = db_handler.get_collection('strategy_screening_results')
        
        analytics_data = []
        
        for template in templates:
            template_id = template['id']
            template_name = template['name']
            
            # 查询该模板的使用历史
            usage_history = list(results_collection.find({
                'user_id': current_user['user_id'],
                'strategy_name': {'$regex': template_name, '$options': 'i'}
            }).sort('screening_time', -1).limit(10))
            
            # 计算统计数据
            total_usage = len(usage_history)
            avg_results = sum([h.get('total_count', 0) for h in usage_history]) / max(total_usage, 1)
            
            # 最近使用时间
            last_used = usage_history[0]['screening_time'] if usage_history else None
            
            # 计算成功率（有结果的筛选次数 / 总筛选次数）
            successful_screenings = len([h for h in usage_history if h.get('total_count', 0) > 0])
            success_rate = (successful_screenings / max(total_usage, 1)) * 100
            
            analytics_data.append({
                'template_id': template_id,
                'template_name': template_name,
                'strategy_type': template['strategy_type'],
                'description': template['description'],
                'usage_stats': {
                    'total_usage': total_usage,
                    'avg_results': round(avg_results, 1),
                    'success_rate': round(success_rate, 1),
                    'last_used': last_used
                },
                'recent_performance': [
                    {
                        'screening_time': h['screening_time'],
                        'total_count': h.get('total_count', 0),
                        'processing_time': h.get('processing_time', 0)
                    } for h in usage_history[:5]
                ]
            })
        
        return {
            'total_templates': len(templates),
            'analytics': analytics_data,
            'generated_at': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"获取模板分析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板分析数据失败: {str(e)}")

@router.get("/templates/{template_id}/performance")
@cache_endpoint(data_type="template_performance", ttl=600)  # 缓存10分钟
async def get_template_performance(
    template_id: str,
    days: int = Query(30, ge=1, le=365, description="分析天数"),
    current_user: dict = Depends(get_current_user)
):
    """获取特定策略模板的性能分析"""
    try:
        # 获取模板信息
        template = await _get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="策略模板不存在")
        
        # 查询指定天数内的筛选记录
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        results_collection = db_handler.get_collection('strategy_screening_results')
        history = list(results_collection.find({
            'user_id': current_user['user_id'],
            'strategy_name': {'$regex': template['template_name'], '$options': 'i'},
            'screening_time': {'$gte': start_date}
        }).sort('screening_time', -1))
        
        if not history:
            return {
                'template_id': template_id,
                'template_name': template['template_name'],
                'analysis_period': f'{days}天',
                'performance_summary': {
                    'total_screenings': 0,
                    'avg_results': 0,
                    'success_rate': 0,
                    'avg_processing_time': 0
                },
                'trend_analysis': [],
                'recommendations': ['暂无使用数据，建议先使用该策略进行筛选']
            }
        
        # 计算性能指标
        total_screenings = len(history)
        total_results = sum([h.get('total_count', 0) for h in history])
        avg_results = total_results / total_screenings
        successful_screenings = len([h for h in history if h.get('total_count', 0) > 0])
        success_rate = (successful_screenings / total_screenings) * 100
        
        processing_times = [h.get('processing_time', 0) for h in history if h.get('processing_time')]
        avg_processing_time = sum(processing_times) / max(len(processing_times), 1)
        
        # 趋势分析（按天分组）
        from collections import defaultdict
        daily_stats = defaultdict(list)
        
        for record in history:
            date_key = record['screening_time'].strftime('%Y-%m-%d')
            daily_stats[date_key].append(record.get('total_count', 0))
        
        trend_data = []
        for date, counts in sorted(daily_stats.items()):
            trend_data.append({
                'date': date,
                'avg_results': sum(counts) / len(counts),
                'screenings_count': len(counts)
            })
        
        # 生成建议
        recommendations = []
        if success_rate < 50:
            recommendations.append("成功率较低，建议调整筛选条件或选择其他策略")
        if avg_results < 10:
            recommendations.append("平均筛选结果较少，可考虑放宽筛选条件")
        if avg_processing_time > 5:
            recommendations.append("处理时间较长，建议使用更精确的股票池")
        if not recommendations:
            recommendations.append("策略表现良好，可继续使用")
        
        return {
            'template_id': template_id,
            'template_name': template['template_name'],
            'analysis_period': f'{days}天',
            'performance_summary': {
                'total_screenings': total_screenings,
                'total_results': total_results,
                'avg_results': round(avg_results, 1),
                'success_rate': round(success_rate, 1),
                'avg_processing_time': round(avg_processing_time, 3)
            },
            'trend_analysis': trend_data,
            'recommendations': recommendations,
            'generated_at': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"获取模板性能数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板性能数据失败: {str(e)}")

# @router.post("/templates/compare")
# @cache_endpoint(data_type="template_comparison", ttl=600)  # 缓存10分钟
# async def compare_templates(
#     template_ids: List[str],
#     days: int = Query(30, ge=1, le=365, description="分析天数"),
#     current_user: dict = Depends(get_current_user)
# ):
#     """对比多个策略模板的性能"""
#     try:
#         if len(template_ids) < 2 or len(template_ids) > 5:
#             raise HTTPException(status_code=400, detail="请选择2-5个策略模板进行对比")
        
#         from datetime import timedelta
#         start_date = datetime.now() - timedelta(days=days)
#         results_collection = db_handler.get_collection('strategy_screening_results')
        
#         comparison_data = []
        
#         for template_id in template_ids:
#             # 获取模板信息
#             template = await _get_template_by_id(template_id)
#             if not template:
#                 continue
            
#             # 查询筛选历史
#             history = list(results_collection.find({
#                 'user_id': current_user['user_id'],
#                 'strategy_name': {'$regex': template['template_name'], '$options': 'i'},
#                 'screening_time': {'$gte': start_date}
#             }))
            
#             # 计算指标
#             total_screenings = len(history)
#             if total_screenings > 0:
#                 total_results = sum([h.get('total_count', 0) for h in history])
#                 avg_results = total_results / total_screenings
#                 successful_screenings = len([h for h in history if h.get('total_count', 0) > 0])
#                 success_rate = (successful_screenings / total_screenings) * 100
                
#                 processing_times = [h.get('processing_time', 0) for h in history if h.get('processing_time')]
#                 avg_processing_time = sum(processing_times) / max(len(processing_times), 1)
#             else:
#                 avg_results = 0
#                 success_rate = 0
#                 avg_processing_time = 0
            
#             comparison_data.append({
#                 'template_id': template_id,
#                 'template_name': template['template_name'],
#                 'strategy_type': template['strategy_type'],
#                 'metrics': {
#                     'total_screenings': total_screenings,
#                     'avg_results': round(avg_results, 1),
#                     'success_rate': round(success_rate, 1),
#                     'avg_processing_time': round(avg_processing_time, 3)
#                 }
#             })
        
#         # 排序（按平均结果数排序）
#         comparison_data.sort(key=lambda x: x['metrics']['avg_results'], reverse=True)
        
#         # 生成对比结论
#         if comparison_data:
#             best_template = comparison_data[0]
#             conclusions = [
#                 f"在{days}天内，{best_template['template_name']}表现最佳",
#                 f"平均每次筛选出{best_template['metrics']['avg_results']}只股票",
#                 f"成功率为{best_template['metrics']['success_rate']}%"
#             ]
#         else:
#             conclusions = ["暂无足够数据进行对比分析"]
        
#         return {
#             'comparison_period': f'{days}天',
#             'templates_compared': len(comparison_data),
#             'comparison_data': comparison_data,
#             'conclusions': conclusions,
#             'generated_at': datetime.now()
#         }
        
#     except Exception as e:
#         logger.error(f"模板对比分析失败: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"模板对比分析失败: {str(e)}")

@router.post("/templates/optimize")
async def optimize_template(
    template_id: str,
    optimization_type: str = Query("performance", description="优化类型：performance/results/speed"),
    current_user: dict = Depends(get_current_user)
):
    """策略模板优化建议"""
    try:
        # 获取模板信息
        template = await _get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="策略模板不存在")
        
        # 获取该模板的历史表现
        results_collection = db_handler.get_collection('strategy_screening_results')
        history = list(results_collection.find({
            'user_id': current_user['user_id'],
            'strategy_name': {'$regex': template['template_name'], '$options': 'i'}
        }).sort('screening_time', -1).limit(20))
        
        optimization_suggestions = []
        
        if not history:
            optimization_suggestions.append({
                'type': 'usage',
                'priority': 'high',
                'suggestion': '建议先使用该策略进行筛选，积累使用数据后再进行优化',
                'reason': '暂无历史使用数据'
            })
        else:
            # 分析历史数据
            avg_results = sum([h.get('total_count', 0) for h in history]) / len(history)
            success_rate = len([h for h in history if h.get('total_count', 0) > 0]) / len(history) * 100
            
            if optimization_type == "performance":
                if success_rate < 70:
                    optimization_suggestions.append({
                        'type': 'conditions',
                        'priority': 'high',
                        'suggestion': '建议放宽筛选条件，提高成功率',
                        'reason': f'当前成功率仅为{success_rate:.1f}%'
                    })
                
                if avg_results < 5:
                    optimization_suggestions.append({
                        'type': 'scope',
                        'priority': 'medium',
                        'suggestion': '建议扩大股票池范围或调整筛选条件',
                        'reason': f'平均筛选结果仅为{avg_results:.1f}只股票'
                    })
            
            elif optimization_type == "results":
                if avg_results > 100:
                    optimization_suggestions.append({
                        'type': 'precision',
                        'priority': 'medium',
                        'suggestion': '建议收紧筛选条件，提高结果精度',
                        'reason': f'平均筛选结果过多({avg_results:.1f}只)，可能影响选择效率'
                    })
            
            elif optimization_type == "speed":
                processing_times = [h.get('processing_time', 0) for h in history if h.get('processing_time')]
                if processing_times:
                    avg_time = sum(processing_times) / len(processing_times)
                    if avg_time > 3:
                        optimization_suggestions.append({
                            'type': 'performance',
                            'priority': 'medium',
                            'suggestion': '建议使用更精确的股票池或简化筛选条件',
                            'reason': f'平均处理时间较长({avg_time:.2f}秒)'
                        })
        
        # 基于策略类型的通用建议
        strategy_type = template['strategy_type']
        if strategy_type == 'technical':
            optimization_suggestions.append({
                'type': 'market_timing',
                'priority': 'low',
                'suggestion': '技术策略建议在市场趋势明确时使用',
                'reason': '技术分析在震荡市场中效果可能不佳'
            })
        elif strategy_type == 'fundamental':
            optimization_suggestions.append({
                'type': 'timing',
                'priority': 'low', 
                'suggestion': '基本面策略适合中长期投资，建议定期更新筛选',
                'reason': '基本面数据变化相对缓慢'
            })
        
        if not optimization_suggestions:
            optimization_suggestions.append({
                'type': 'maintenance',
                'priority': 'low',
                'suggestion': '策略表现良好，建议继续使用并定期评估',
                'reason': '当前策略运行正常'
            })
        
        return {
            'template_id': template_id,
            'template_name': template['template_name'],
            'optimization_type': optimization_type,
            'suggestions': optimization_suggestions,
            'generated_at': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"策略优化分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"策略优化分析失败: {str(e)}")

# ==================== 策略模板回测API ====================

@router.post("/templates/{template_id}/backtest")
async def backtest_template(
    template_id: str,
    backtest_days: int = Query(30, ge=7, le=90, description="回测天数"),
    stock_pool: Optional[List[str]] = Query(None, description="指定股票池"),
    current_user: dict = Depends(get_current_user)
):
    """策略模板历史回测分析"""
    try:
        # 获取模板信息
        template = await _get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="策略模板不存在")
        
        from datetime import timedelta
        
        # 设置回测时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=backtest_days)
        
        # 获取历史交易日
        trade_dates = list(db_handler.get_collection('stock_factor_pro').distinct(
            'trade_date',
            {'trade_date': {'$gte': start_date.strftime('%Y%m%d'), '$lte': end_date.strftime('%Y%m%d')}}
        ))
        trade_dates.sort()
        
        if len(trade_dates) < 5:
            raise HTTPException(status_code=400, detail="回测期间交易日不足")
        
        backtest_results = []
        
        # 对每个交易日进行策略筛选模拟
        for i, trade_date in enumerate(trade_dates[::5]):  # 每5个交易日测试一次
            try:
                # 构建该日期的筛选请求
                request_data = {
                    "strategy_name": f"回测-{template['template_name']}",
                    "strategy_type": template["strategy_type"],
                    "technical_conditions": template["conditions"].get("technical"),
                    "fundamental_conditions": template["conditions"].get("fundamental"), 
                    "special_conditions": template["conditions"].get("special"),
                    "stock_pool": stock_pool or ["all"],
                    "limit": 20
                }
                
                # 模拟在该日期执行筛选
                pipeline = []
                
                # 匹配该交易日数据
                match_conditions = {"trade_date": trade_date}
                
                # 添加技术面条件
                if template["conditions"].get("technical"):
                    tech_conditions = template["conditions"]["technical"]
                    if tech_conditions.get("rsi_min"):
                        match_conditions["rsi_qfq_12"] = {"$gte": tech_conditions["rsi_min"]}
                    if tech_conditions.get("macd_positive"):
                        match_conditions["macd_qfq"] = {"$gt": 0}
                    if tech_conditions.get("above_ma20"):
                        match_conditions["$expr"] = {"$gt": ["$close", "$ma_qfq_20"]}
                
                pipeline.extend([
                    {"$match": match_conditions},
                    {"$lookup": {
                        "from": "infrastructure_stock_basic",
                        "localField": "ts_code",
                        "foreignField": "ts_code",
                        "as": "stock_info"
                    }},
                    {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
                    {"$addFields": {
                        "score": {"$add": [
                            {"$cond": {"if": {"$gte": ["$rsi_qfq_12", 30]}, "then": 50, "else": 20}},
                            {"$cond": {"if": {"$gt": ["$macd_qfq", 0]}, "then": 20, "else": 0}},
                            {"$cond": {"if": {"$gt": ["$close", "$ma_qfq_20"]}, "then": 20, "else": 0}}
                        ]}
                    }},
                    {"$sort": {"score": -1}},
                    {"$limit": 20}
                ])
                
                # 执行查询
                results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
                
                backtest_results.append({
                    'date': trade_date,
                    'stocks_found': len(results),
                    'avg_score': sum([r.get('score', 0) for r in results]) / max(len(results), 1),
                    'top_stocks': [r.get('ts_code') for r in results[:5]]
                })
                
            except Exception as e:
                logger.warning(f"回测日期 {trade_date} 处理失败: {str(e)}")
                continue
        
        # 计算回测统计
        if backtest_results:
            avg_stocks_found = sum([r['stocks_found'] for r in backtest_results]) / len(backtest_results)
            avg_score = sum([r['avg_score'] for r in backtest_results]) / len(backtest_results)
            success_rate = len([r for r in backtest_results if r['stocks_found'] > 0]) / len(backtest_results) * 100
        else:
            avg_stocks_found = 0
            avg_score = 0
            success_rate = 0
        
        return {
            'template_id': template_id,
            'template_name': template['template_name'],
            'backtest_period': f'{backtest_days}天',
            'backtest_summary': {
                'total_test_days': len(backtest_results),
                'avg_stocks_found': round(avg_stocks_found, 1),
                'avg_score': round(avg_score, 1),
                'success_rate': round(success_rate, 1)
            },
            'daily_results': backtest_results,
            'generated_at': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"策略回测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"策略回测失败: {str(e)}")

# ==================== 策略模板专门聚合查询接口 ====================

@router.post("/value-investment")
@cache_endpoint(data_type="value_investment", ttl=300)
async def value_investment_screening(
    market_cap: str = "all",  # 市值范围：large/mid/small/all
    stock_pool: str = "all",  # 股票池：all/main/gem/star
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """价值投资策略专门接口 - 基于历史财报均值"""
    try:
        pipeline = []
        latest_date = await _get_latest_trade_date()
        
        # 第一阶段：获取最新的技术指标和估值数据
        match_conditions = {
            "trade_date": latest_date,
            "pe": {"$gt": 0, "$lte": 25},      # PE < 25 (估值合理)
            "pb": {"$gt": 0, "$lte": 3},       # PB < 3 (估值不贵)
            "pe_ttm": {"$gt": 0},              # 确保TTM市盈率有效
            "total_mv": {"$gt": 100000}        # 总市值 > 10亿，过滤小股票
        }
        
        # 市值筛选
        if market_cap == "large":
            match_conditions["total_mv"] = {"$gte": 5000000}  # >= 500亿
        elif market_cap == "mid":
            match_conditions["total_mv"] = {"$gte": 1000000, "$lte": 5000000}  # 100-500亿
        elif market_cap == "small":
            match_conditions["total_mv"] = {"$lte": 1000000}  # <= 100亿
        
        # 股票池筛选
        if stock_pool != "all":
            resolved_pool = await _resolve_stock_pool([stock_pool])
            if resolved_pool:
                match_conditions["ts_code"] = {"$in": resolved_pool}
        
        pipeline.extend([
            # 第一步：匹配基础技术条件
            {"$match": match_conditions},
            
            # 第二步：关联股票基本信息
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            # 第三步：关联历史财务指标（过去8个季度）
            {"$lookup": {
                "from": "stock_fina_indicator",
                "let": {"stock_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$stock_code"]},
                        "end_date": {
                            "$gte": "20230101",  # 过去2年的财报数据
                            "$lte": "20241231"
                        },
                        "roe": {"$exists": True, "$ne": None, "$gt": 0}  # 确保有有效ROE数据
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 8},  # 最近8个季度
                    {"$project": {
                        "end_date": 1,
                        "roe": 1,
                        "roe_yearly": 1,
                        "current_ratio": 1,      # 流动比率（高现金流）
                        "quick_ratio": 1,        # 速动比率
                        "debt_to_assets": 1,     # 资产负债率（低负债）
                        "debt_to_eqt": 1,        # 产权比率
                        "profit_dedt": 1,        # 利润增长率（业绩超预期）
                        "profit_yoy": 1,         # 利润同比增长
                        "netprofit_yoy": 1       # 净利润同比增长
                    }}
                ],
                "as": "financial_history"
            }},
            
            # 第四步：过滤掉没有足够财务数据的股票
            {"$match": {
                "$expr": {"$gte": [{"$size": "$financial_history"}, 4]}  # 至少需要4个季度的数据
            }},
            
            # 第五步：计算历史财务指标均值和评分
            {"$addFields": {
                # 计算ROE均值（最高优先级）
                "avg_roe": {
                    "$avg": {
                        "$map": {
                            "input": "$financial_history",
                            "as": "fh",
                            "in": {"$ifNull": ["$$fh.roe", 0]}
                        }
                    }
                },
                
                # 计算年化ROE均值
                "avg_roe_yearly": {
                    "$avg": {
                        "$map": {
                            "input": "$financial_history",
                            "as": "fh", 
                            "in": {"$ifNull": ["$$fh.roe_yearly", 0]}
                        }
                    }
                },
                
                # 计算平均流动比率（高现金流指标）
                "avg_current_ratio": {
                    "$avg": {
                        "$map": {
                            "input": "$financial_history",
                            "as": "fh",
                            "in": {"$ifNull": ["$$fh.current_ratio", 1]}
                        }
                    }
                },
                
                # 计算平均资产负债率（低负债指标）
                "avg_debt_ratio": {
                    "$avg": {
                        "$map": {
                            "input": "$financial_history",
                            "as": "fh",
                            "in": {"$ifNull": ["$$fh.debt_to_assets", 50]}
                        }
                    }
                },
                
                # 计算平均利润增长率（业绩超预期指标）
                "avg_profit_growth": {
                    "$avg": {
                        "$map": {
                            "input": "$financial_history",
                            "as": "fh",
                            "in": {"$ifNull": ["$$fh.netprofit_yoy", 0]}
                        }
                    }
                }
            }},
            
            # 第六步：应用价值投资核心筛选条件
            {"$match": {
                "avg_roe": {"$gte": 10},           # ROE均值 > 10%（最高优先级）
                "avg_current_ratio": {"$gte": 1.2}, # 流动比率 > 1.2（高现金流）
                "avg_debt_ratio": {"$lte": 60},     # 资产负债率 < 60%（低负债）
                "avg_profit_growth": {"$gte": 5}    # 利润增长率 > 5%（业绩超预期）
            }},
            
            # 第七步：计算综合评分（按优先级加权）
            {"$addFields": {
                "value_score": {
                    "$add": [
                        # ROE评分（权重40%，最高优先级）
                        {"$multiply": [
                            {"$min": [{"$divide": ["$avg_roe", 20]}, 2]}, 40
                        ]},
                        
                        # 现金流评分（权重20%）
                        {"$multiply": [
                            {"$min": [{"$divide": ["$avg_current_ratio", 2]}, 1]}, 20
                        ]},
                        
                        # 低负债评分（权重20%）
                        {"$multiply": [
                            {"$max": [{"$subtract": [1, {"$divide": ["$avg_debt_ratio", 100]}]}, 0]}, 20
                        ]},
                        
                        # 业绩增长评分（权重10%）
                        {"$multiply": [
                            {"$min": [{"$divide": ["$avg_profit_growth", 30]}, 1]}, 10
                        ]},
                        
                        # PE评分（权重5%）
                        {"$multiply": [
                            {"$max": [{"$subtract": [1, {"$divide": ["$pe", 50]}]}, 0]}, 5
                        ]},
                        
                        # PB评分（权重5%）
                        {"$multiply": [
                            {"$max": [{"$subtract": [1, {"$divide": ["$pb", 6]}]}, 0]}, 5
                        ]}
                    ]
                }
            }},
            
            # 第八步：输出字段
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": "$stock_info.industry",
                "close": 1,
                "pe": 1,
                "pb": 1,
                "pct_chg": {"$ifNull": ["$pct_chg", 0]},
                "total_mv": {"$ifNull": ["$total_mv", 0]},
                "avg_roe": {"$round": ["$avg_roe", 2]},
                "avg_roe_yearly": {"$round": ["$avg_roe_yearly", 2]},
                "avg_current_ratio": {"$round": ["$avg_current_ratio", 2]},
                "avg_debt_ratio": {"$round": ["$avg_debt_ratio", 2]},
                "avg_profit_growth": {"$round": ["$avg_profit_growth", 2]},
                "value_score": {"$round": ["$value_score", 2]},
                "financial_periods": {"$size": "$financial_history"}
            }},
            
            # 第九步：按评分排序
            {"$sort": {"value_score": -1}},
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
            score=r.get('value_score', 0),
            # 添加财务指标到technical字段中以便前端显示
            technical={
                'roe': r.get('avg_roe'),
                'roe_yearly': r.get('avg_roe_yearly'),
                'current_ratio': r.get('avg_current_ratio'),
                'debt_ratio': r.get('avg_debt_ratio'),
                'profit_growth': r.get('avg_profit_growth'),
                'financial_count': r.get('financial_periods')
            }
        ) for r in results]
        
        return ScreeningResponse(
            strategy_name="价值投资策略（历史均值）",
            strategy_type="fundamental",
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results
        )
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
    """成长股策略专门接口 - 高质量成长股筛选"""
    try:
        pipeline = []
        latest_date = await _get_latest_trade_date()
        
        # 构建严格的成长股筛选条件
        pipeline.extend([
            # 第一步：联接财务指标数据（最近8个季度）
            {"$lookup": {
                "from": "stock_fina_indicator",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$ts_code"]},
                        "end_date": {"$gte": "20210331"}  # 最近3年数据
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 12}  # 最近12个季度
                ],
                "as": "fina_indicators"
            }},
            
            # 第二步：联接基本信息
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            # 第三步：计算关键财务指标的多年均值和趋势
            {"$addFields": {
                # 计算EPS连续三年增长率
                "avg_eps_growth": {
                    "$avg": {
                        "$map": {
                            "input": {"$slice": ["$fina_indicators.basic_eps_yoy", 0, 12]},
                            "as": "eps_yoy",
                            "in": {"$ifNull": ["$$eps_yoy", 0]}
                        }
                    }
                },
                # 计算营收连续三年增长率
                "avg_revenue_growth": {
                    "$avg": {
                        "$map": {
                            "input": {"$slice": ["$fina_indicators.or_yoy", 0, 12]},
                            "as": "or_yoy", 
                            "in": {"$ifNull": ["$$or_yoy", 0]}
                        }
                    }
                },
                # 计算ROIC均值
                "avg_roic": {
                    "$avg": {
                        "$map": {
                            "input": {"$slice": ["$fina_indicators.roic", 0, 8]},
                            "as": "roic",
                            "in": {"$ifNull": ["$$roic", 0]}
                        }
                    }
                },
                # 计算毛利率均值
                "avg_gross_margin": {
                    "$avg": {
                        "$map": {
                            "input": {"$slice": ["$fina_indicators.grossprofit_margin", 0, 8]},
                            "as": "gross_margin",
                            "in": {"$ifNull": ["$$gross_margin", 0]}
                        }
                    }
                },
                # 计算净利率均值
                "avg_net_margin": {
                    "$avg": {
                        "$map": {
                            "input": {"$slice": ["$fina_indicators.netprofit_margin", 0, 8]},
                            "as": "net_margin",
                            "in": {"$ifNull": ["$$net_margin", 0]}
                        }
                    }
                },
                # 计算资产负债率
                "avg_debt_ratio": {
                    "$avg": {
                        "$map": {
                            "input": {"$slice": ["$fina_indicators.debt_to_assets", 0, 8]},
                            "as": "debt_ratio",
                            "in": {"$ifNull": ["$$debt_ratio", 0]}
                        }
                    }
                },
                # 计算速动比率
                "avg_quick_ratio": {
                    "$avg": {
                        "$map": {
                            "input": {"$slice": ["$fina_indicators.quick_ratio", 0, 8]},
                            "as": "quick_ratio",
                            "in": {"$ifNull": ["$$quick_ratio", 0]}
                        }
                    }
                },
                # 计算研发费用率（最新季度）
                "latest_rd_rate": {
                    "$let": {
                        "vars": {
                            "latest_fina": {"$arrayElemAt": ["$fina_indicators", 0]},
                        },
                        "in": {"$ifNull": ["$$latest_fina.rd_exp", 0]}
                    }
                },
                # 计算PEG
                "peg_ratio": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": ["$pe", 0]},
                            {"$gt": [{"$avg": {"$slice": ["$fina_indicators.basic_eps_yoy", 0, 4]}}, 0]}
                        ]},
                        "then": {
                            "$divide": [
                                "$pe",
                                {"$avg": {"$slice": ["$fina_indicators.basic_eps_yoy", 0, 4]}}
                            ]
                        },
                        "else": 999
                    }
                }
            }},
            
            # 第四步：应用调整后的筛选条件（分级筛选）
            {"$match": {
                "trade_date": latest_date,
                # 基础条件：确保有财务数据
                "fina_indicators.0": {"$exists": True},
                # 核心成长性条件（二选一即可）
                "$or": [
                    {"avg_eps_growth": {"$gte": 10}},      # EPS增长率>10%
                    {"avg_revenue_growth": {"$gte": 8}}    # 营收增长率>8%
                ],
                # 盈利能力条件（三选二即可）
                "$expr": {
                    "$gte": [
                        {"$size": {
                            "$filter": {
                                "input": [
                                    {"$gte": [{"$ifNull": ["$avg_roic", 0]}, 6]},
                                    {"$gte": [{"$ifNull": ["$avg_gross_margin", 0]}, 15]},
                                    {"$gte": [{"$ifNull": ["$avg_net_margin", 0]}, 5]}
                                ],
                                "cond": "$$this"
                            }
                        }},
                        2
                    ]
                },
                # 财务安全基础要求
                "avg_debt_ratio": {"$lt": 80},          # 资产负债率<80%
                "avg_quick_ratio": {"$gt": 0.5}         # 速动比率>0.5
            }}
        ])
        
        # 第五步：市值和股票池筛选
        additional_match = {}
        if market_cap == "large":
            additional_match["total_mv"] = {"$gte": 5000000}
        elif market_cap == "mid":
            additional_match["total_mv"] = {"$gte": 1000000, "$lte": 5000000}
        elif market_cap == "small":
            additional_match["total_mv"] = {"$lte": 1000000}
        
        # 股票池筛选
        if stock_pool != "all":
            resolved_pool = await _resolve_stock_pool([stock_pool])
            if resolved_pool:
                additional_match["ts_code"] = {"$in": resolved_pool}
        
        # 添加基本的PE/PB筛选（使用存在性检查而非范围查询）
        additional_match["pe"] = {"$exists": True, "$ne": None, "$type": "number"}
        additional_match["pb"] = {"$exists": True, "$ne": None, "$type": "number"}
        
        if additional_match:
            pipeline.append({"$match": additional_match})
        
        # 第六步：计算综合评分和最终输出
        pipeline.extend([
            {"$addFields": {
                "score": {
                    "$add": [
                        # 成长性评分 (40%) - 使用加权平均，控制在0-40分
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_eps_growth", 0]}, 50]}, 0.4]},
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_revenue_growth", 0]}, 50]}, 0.4]},
                        
                        # 盈利能力评分 (35%) - 控制在0-35分
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_roic", 0]}, 25]}, 0.7]},
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_gross_margin", 0]}, 80]}, 0.25]},
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_net_margin", 0]}, 40]}, 0.5]},
                        
                        # 创新投入评分 (15%) - 控制在0-15分
                        {"$multiply": [{"$min": [{"$ifNull": ["$latest_rd_rate", 0]}, 15]}, 1]},
                        
                        # 财务安全评分 (10%) - 控制在0-10分
                        {"$cond": {"if": {"$lt": [{"$ifNull": ["$avg_debt_ratio", 100]}, 50]}, "then": 5, "else": 2}},
                        {"$cond": {"if": {"$gt": [{"$ifNull": ["$avg_quick_ratio", 0]}, 1.2]}, "then": 5, "else": 2}},
                        
                        # PEG奖励分 - 最多10分
                        {"$cond": {"if": {"$and": [
                            {"$lt": [{"$ifNull": ["$peg_ratio", 999]}, 1.5]},
                            {"$gt": [{"$ifNull": ["$peg_ratio", 0]}, 0.2]}
                        ]}, "then": 10, "else": 0}}
                    ]
                }
            }},
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
                "avg_eps_growth": {"$round": ["$avg_eps_growth", 2]},
                "avg_revenue_growth": {"$round": ["$avg_revenue_growth", 2]},
                "avg_roic": {"$round": ["$avg_roic", 2]},
                "avg_gross_margin": {"$round": ["$avg_gross_margin", 2]},
                "avg_net_margin": {"$round": ["$avg_net_margin", 2]},
                "peg_ratio": {"$round": ["$peg_ratio", 2]},
                "avg_debt_ratio": {"$round": ["$avg_debt_ratio", 2]},
                "avg_quick_ratio": {"$round": ["$avg_quick_ratio", 2]},
                "latest_rd_rate": {"$round": ["$latest_rd_rate", 2]}
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
            # 成长股策略专用字段
            avg_eps_growth=r.get('avg_eps_growth'),
            avg_revenue_growth=r.get('avg_revenue_growth'),
            avg_roic=r.get('avg_roic'),
            peg_ratio=r.get('peg_ratio'),
            avg_gross_margin=r.get('avg_gross_margin'),
            avg_net_margin=r.get('avg_net_margin'),
            latest_rd_rate=r.get('latest_rd_rate'),
            avg_debt_ratio=r.get('avg_debt_ratio'),
            avg_quick_ratio=r.get('avg_quick_ratio')
        ) for r in results]
        
        return ScreeningResponse(
            strategy_name="高质量成长股策略",
            strategy_type="growth",  # 修复：从fundamental改为growth
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results
        )
    except Exception as e:
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
    """动量突破策略专门接口 - 增强版"""
    try:
        pipeline = []
        latest_date = await _get_latest_trade_date()
        
        # 基础筛选条件 - 放宽条件以获得更多结果
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": 0},  # 确保有效价格
            "total_mv": {"$gt": 0},  # 确保有效市值
            "rsi_qfq_12": {"$gte": 30, "$lte": 85},  # 放宽RSI区间
            "volume_ratio": {"$gte": 1.0},  # 放宽量比要求
        }
        
        # 可选的技术条件
        if rsi_min > 30 or rsi_max < 85:
            match_conditions["rsi_qfq_12"] = {"$gte": rsi_min, "$lte": rsi_max}
        
        if volume_ratio_min > 1.0:
            match_conditions["volume_ratio"] = {"$gte": volume_ratio_min}
        
        # MACD金叉条件（可选）
        if require_macd_golden:
            match_conditions["macd_qfq"] = {"$gt": 0}  # MACD > 0
        
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
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {
                # 计算过去N日收益率（简化处理，用当前涨跌幅代替）
                "period_return": {
                    "$multiply": [
                        {"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 
                        {"$divide": [{"$convert": {"input": {"$literal": period_days}, "to": "double", "onError": 1}}, 20]}
                    ]
                },
                # 计算RPS相对强度（简化处理，基于涨跌幅排名）
                "rps_score": {
                    "$cond": {
                        "if": {"$gt": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 5]},
                        "then": {"$add": [80, {"$multiply": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 2]}]},
                        "else": {"$add": [60, {"$multiply": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 4]}]}
                    }
                },
                # EMA近似值（使用移动平均线）
                "ema_20": {"$convert": {"input": "$ma_qfq_20", "to": "double", "onError": 0}},
                "ema_50": {"$convert": {"input": "$ma_qfq_50", "to": "double", "onError": 0}},
                # 突破信号判断
                "breakthrough_signal": {
                    "$and": [
                        {"$gt": [{"$convert": {"input": "$close", "to": "double", "onError": 0}}, {"$convert": {"input": "$ma_qfq_20", "to": "double", "onError": 0}}]},
                        {"$gt": [{"$convert": {"input": "$ma_qfq_20", "to": "double", "onError": 0}}, {"$convert": {"input": "$ma_qfq_50", "to": "double", "onError": 0}}]},
                        {"$gte": [{"$convert": {"input": "$volume_ratio", "to": "double", "onError": 0}}, {"$literal": volume_ratio_min}]},
                        {"$gte": [{"$convert": {"input": "$rsi_qfq_12", "to": "double", "onError": 0}}, {"$literal": rsi_min}]},
                        {"$lte": [{"$convert": {"input": "$rsi_qfq_12", "to": "double", "onError": 100}}, {"$literal": rsi_max}]}
                    ]
                },
                # 综合评分计算
                "score": {
                    "$add": [
                        # RSI权重 (15%)
                        {"$multiply": [
                            {"$subtract": [75, {"$abs": {"$subtract": [{"$convert": {"input": "$rsi_qfq_12", "to": "double", "onError": 50}}, 60]}}]}, 
                            0.15
                        ]},
                        # 量比权重 (25%)
                        {"$multiply": [{"$convert": {"input": "$volume_ratio", "to": "double", "onError": 1}}, 25]},
                        # MACD权重 (20%)
                        {"$cond": {"if": {"$gt": [{"$convert": {"input": "$macd_qfq", "to": "double", "onError": 0}}, 0]}, "then": 20, "else": 0}},
                        # 涨跌幅权重 (15%)
                        {"$multiply": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 3]},
                        # 突破信号权重 (15%)
                        {"$cond": {"if": {"$gt": [{"$convert": {"input": "$close", "to": "double", "onError": 0}}, {"$convert": {"input": "$ma_qfq_20", "to": "double", "onError": 0}}]}, "then": 15, "else": 0}},
                        # 相对强度权重 (10%)
                        {"$cond": {"if": {"$gt": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 2]}, "then": 10, "else": 0}}
                    ]
                }
            }},
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
                # 动量突破策略专用字段
                "period_return": 1,
                "rps_score": 1,
                "ema_20": 1,
                "ema_50": 1,
                "volume_ratio": 1,
                "rsi": "$rsi_qfq_12",
                "macd": "$macd_qfq",
                "macd_signal": "$macd_signal_qfq",
                "macd_histogram": "$macd_histogram_qfq",
                "breakthrough_signal": 1
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
            # 动量突破策略专用字段
            period_return=r.get('period_return'),
            rps_score=r.get('rps_score'),
            ema_20=r.get('ema_20'),
            ema_50=r.get('ema_50'),
            volume_ratio=r.get('volume_ratio'),
            rsi=r.get('rsi'),
            macd=r.get('macd'),
            macd_signal=r.get('macd_signal'),
            macd_histogram=r.get('macd_histogram'),
            breakthrough_signal=r.get('breakthrough_signal')
        ) for r in results]
        
        return ScreeningResponse(
            strategy_name="动量突破策略",
            strategy_type="momentum",  # 修正策略类型
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results
        )
    except Exception as e:
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
    rsi_min: float = 45.0,           # RSI下限：确保动能充足（放宽）
    rsi_max: float = 85.0,           # RSI上限：避免超买（放宽）
    volume_ratio_min: float = 1.2,   # 量比下限：确保成交量放大（放宽）
    macd_requirement: bool = False,   # 是否要求MACD金叉（默认不要求）
    ma_alignment: bool = False,       # 是否要求均线多头排列（默认不要求）
    bollinger_position: str = "upper", # 布林带位置要求：upper/middle/any
    current_user: dict = Depends(get_current_user)
):
    """技术突破策略专门接口 - 多重技术指标确认突破"""
    try:
        pipeline = []
        latest_date = await _get_latest_trade_date()
        
        # 基础筛选条件
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": 0},
            "total_mv": {"$gt": 0},
            "rsi_qfq_12": {"$gte": rsi_min, "$lte": rsi_max},  # RSI动能区间
            "volume_ratio": {"$gte": volume_ratio_min},         # 量比放大
            "turnover_rate": {"$gte": 1, "$lte": 15}           # 换手率适中
        }
        
        # 构建$expr条件列表
        expr_conditions = [
            {"$gt": ["$close", "$ma_qfq_20"]}  # 站上20日均线（基础要求）
        ]
        
        # MACD金叉要求（如果启用）
        if macd_requirement:
            expr_conditions.extend([
                {"$gt": ["$macd_dif_qfq", "$macd_dea_qfq"]},  # DIF > DEA（金叉）
                {"$gt": ["$macd_qfq", 0]}                     # MACD柱状线为正
            ])
        
        # 均线多头排列要求
        if ma_alignment:
            expr_conditions.extend([
                {"$gt": ["$ma_qfq_5", "$ma_qfq_10"]},       # 5日线 > 10日线
                {"$gt": ["$ma_qfq_10", "$ma_qfq_20"]}       # 10日线 > 20日线
            ])
        
        # 将所有$expr条件合并
        if len(expr_conditions) > 1:
            match_conditions["$expr"] = {"$and": expr_conditions}
        else:
            match_conditions["$expr"] = expr_conditions[0]
        
        # 市值筛选
        if market_cap == "large":
            match_conditions["total_mv"] = {"$gte": 5000000}
        elif market_cap == "mid":
            match_conditions["total_mv"] = {"$gte": 1000000, "$lte": 5000000}
        elif market_cap == "small":
            match_conditions["total_mv"] = {"$lte": 1000000}
        else:
            match_conditions["total_mv"] = {"$gte": 500000}  # 最小5亿市值
        
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
            
            # 排除ST股票
            {"$match": {
                "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
            }},
            
            # 计算技术突破评分（简化版本 - 100分制）
            {"$addFields": {
                "score": {
                    "$add": [
                        # 基础分：站上20日线得20分
                        20,
                        
                        # RSI得分：45-85区间，得0-20分
                        {"$multiply": [{"$max": [0, {"$subtract": ["$rsi_qfq_12", 45]}]}, 0.5]},
                        
                        # MACD得分：MACD>0得15分
                        {"$cond": {"if": {"$gt": ["$macd_qfq", 0]}, "then": 15, "else": 0}},
                        
                        # 成交量得分：量比每超过1得10分，最高25分
                        {"$min": [25, {"$multiply": [{"$max": [0, {"$subtract": ["$volume_ratio", 1]}]}, 10]}]},
                        
                        # 涨跌幅得分：涨幅每1%得2分，最高20分
                        {"$min": [20, {"$max": [0, {"$multiply": ["$pct_chg", 2]}]}]}
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
                # 技术突破策略专用字段
                "rsi": "$rsi_qfq_12",
                "macd": "$macd_qfq",
                "macd_signal": "$macd_dea_qfq",
                "volume_ratio": 1,
                "ema_20": "$ma_qfq_20",
                "ema_50": "$ma_qfq_60",
                "bollinger_upper": "$boll_upper_qfq",
                "bollinger_middle": "$boll_mid_qfq",
                "bollinger_lower": "$boll_lower_qfq",
                "breakthrough_signal": {
                    "$cond": {
                        "if": {"$gte": ["$score", 70]},
                        "then": True,
                        "else": False
                    }
                }
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
            # 技术突破策略专用字段
            rsi=round(r.get('rsi', 0), 2),
            macd=round(r.get('macd', 0), 4),
            macd_signal=round(r.get('macd_signal', 0), 4),
            volume_ratio=round(r.get('volume_ratio', 0), 2),
            ema_20=round(r.get('ema_20', 0), 2),
            ema_50=round(r.get('ema_50', 0), 2),
            breakthrough_signal=r.get('breakthrough_signal', False)
        ) for r in results]
        
        return ScreeningResponse(
            strategy_name="技术突破策略",
            strategy_type="technical",
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"技术突破策略筛选失败: {str(e)}")

@router.post("/oversold-rebound")
@cache_endpoint(data_type="oversold_rebound", ttl=300)
async def oversold_rebound_screening(
    market_cap: str = "all",
    stock_pool: str = "all",
    limit: int = 20,
    rsi_max: float = 35.0,              # RSI上限：超跌区域
    rsi_min: float = 15.0,              # RSI下限：避免极端情况
    volume_ratio_min: float = 1.3,      # 量比下限：成交量放大
    pe_max: float = 50.0,               # PE上限：避免高估值
    pb_max: float = 8.0,                # PB上限：避免高估值
    decline_days: int = 3,              # 连续下跌天数要求
    current_user: dict = Depends(get_current_user)
):
    """超跌反弹策略专门接口 - 多维度识别超跌反弹机会"""
    try:
        pipeline = []
        latest_date = await _get_latest_trade_date()
        
        # 基础筛选条件
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": 0},
            "total_mv": {"$gte": 300000},              # 市值 >= 3亿
            "rsi_qfq_12": {"$gte": rsi_min, "$lte": rsi_max},  # RSI超跌区域
            "volume_ratio": {"$gte": volume_ratio_min},         # 量比放大
            "pe": {"$gt": 0, "$lte": pe_max},                  # PE合理
            "pb": {"$gt": 0, "$lte": pb_max},                  # PB合理
            "turnover_rate": {"$gte": 1.5, "$lte": 25}        # 换手率适中
        }
        
        # 构建$expr条件：技术位判断
        expr_conditions = [
            {"$lt": ["$close", "$ma_qfq_20"]},     # 低于20日均线
            {"$lt": ["$close", "$ma_qfq_60"]},     # 低于60日均线
        ]
        
        match_conditions["$expr"] = {"$and": expr_conditions}
        
        # 市值筛选
        if market_cap == "large":
            match_conditions["total_mv"] = {"$gte": 5000000}
        elif market_cap == "mid":
            match_conditions["total_mv"] = {"$gte": 1000000, "$lte": 5000000}
        elif market_cap == "small":
            match_conditions["total_mv"] = {"$lte": 1000000}
        else:
            match_conditions["total_mv"] = {"$gte": 300000}  # 最小3亿市值
        
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
            
            # 排除ST股票
            {"$match": {
                "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
            }},
            
            # 计算超跌反弹评分（100分制）
            {"$addFields": {
                "score": {
                    "$add": [
                        # 基础分：符合超跌条件得20分
                        20,
                        
                        # RSI得分：越低得分越高，15-35区间得0-25分
                        {"$multiply": [{"$subtract": [35, "$rsi_qfq_12"]}, 1.25]},
                        
                        # 量比得分：量比越高得分越高，最高20分
                        {"$min": [20, {"$multiply": [{"$subtract": ["$volume_ratio", 1]}, 4]}]},
                        
                        # 估值得分：PE越低得分越高，最高15分
                        {"$min": [15, {"$multiply": [{"$divide": [25, "$pe"]}, 3]}]},
                        
                        # 反弹信号得分：当日表现评分，最高15分
                        {"$cond": {
                            "if": {"$gt": ["$pct_chg", 3]},
                            "then": 15,
                            "else": {"$cond": {
                                "if": {"$gt": ["$pct_chg", 0]},
                                "then": 10,
                                "else": {"$cond": {
                                    "if": {"$gt": ["$pct_chg", -2]},
                                    "then": 5,
                                    "else": 0
                                }}
                            }}
                        }},
                        
                        # 换手率得分：适中的换手率得分，最高5分
                        {"$cond": {
                            "if": {"$and": [{"$gte": ["$turnover_rate", 2]}, {"$lte": ["$turnover_rate", 10]}]},
                            "then": 5,
                            "else": 0
                        }}
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
                # 超跌反弹策略专用字段
                "rsi": "$rsi_qfq_12",
                "volume_ratio": 1,
                "turnover_rate": 1,
                "ma_20": "$ma_qfq_20",
                "ma_60": "$ma_qfq_60",
                "rebound_signal": {
                    "$cond": {
                        "if": {"$gte": ["$score", 55]},
                        "then": True,
                        "else": False
                    }
                }
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
            # 超跌反弹策略专用字段
            rsi=round(r.get('rsi', 0), 2),
            volume_ratio=round(r.get('volume_ratio', 0), 2),
            turnover_rate=round(r.get('turnover_rate', 0), 2),
            ma_20=round(r.get('ma_20', 0), 2),
            ma_60=round(r.get('ma_60', 0), 2),
            rebound_signal=r.get('rebound_signal', False)
        ) for r in results]
        
        return ScreeningResponse(
            strategy_name="超跌反弹策略",
            strategy_type="technical",
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"超跌反弹策略筛选失败: {str(e)}")

@router.post("/limit-up-leader")
@cache_endpoint(data_type="limit_up_leader", ttl=300)
async def limit_up_leader_screening(
    market_cap: str = "all",
    stock_pool: str = "all",
    limit: int = 20,
    min_limit_times: int = 2,           # 最小连板次数
    max_limit_times: int = 10,          # 最大连板次数
    max_open_times: int = 3,            # 最大开板次数
    min_turnover: float = 5.0,          # 最小换手率
    max_turnover: float = 30.0,         # 最大换手率
    current_user: dict = Depends(get_current_user)
):
    """连板龙头策略专门接口 - 基于涨跌停数据的真实连板分析"""
    try:
        # 获取最新交易日期
        latest_limit_data = list(db_handler.get_collection('limit_list_daily').find({}).sort('trade_date', -1).limit(1))
        if not latest_limit_data:
            raise HTTPException(status_code=404, detail="找不到涨跌停数据")
        
        latest_date = latest_limit_data[0]['trade_date']
        
        # 构建聚合管道
        pipeline = [
            # 第一步：筛选涨停连板股票
            {"$match": {
                "trade_date": latest_date,
                "limit": "U",                                    # 涨停
                "limit_times": {"$gte": min_limit_times, "$lte": max_limit_times},  # 连板次数范围
                "open_times": {"$lte": max_open_times}           # 开板次数限制
            }},
            
            # 第二步：关联股票基本信息
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            # 第三步：排除ST股票
            {"$match": {
                "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
            }},
            
            # 第四步：关联技术因子数据
            {"$lookup": {
                "from": "stock_factor_pro",
                "let": {"stock_code": "$ts_code", "date": "$trade_date"},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$ts_code", "$$stock_code"]},
                                {"$eq": ["$trade_date", "$$date"]}
                            ]
                        }
                    }},
                    {"$project": {
                        "total_mv": 1,
                        "turnover_rate": 1,
                        "amount": 1,
                        "pe": 1,
                        "pb": 1,
                        "pct_chg": 1
                    }}
                ],
                "as": "tech_data"
            }},
            {"$unwind": {"path": "$tech_data", "preserveNullAndEmptyArrays": True}},
            
            # 第五步：换手率筛选
            {"$match": {
                "tech_data.turnover_rate": {"$gte": min_turnover, "$lte": max_turnover}
            }},
            
            # 第六步：市值筛选
            {"$addFields": {
                "total_mv_yi": {"$divide": [{"$ifNull": ["$tech_data.total_mv", 0]}, 10000]}  # 转换为亿元
            }},
        ]
        
        # 添加市值筛选条件
        if market_cap == "large":
            pipeline.append({"$match": {"total_mv_yi": {"$gte": 500}}})  # >= 500亿
        elif market_cap == "mid":
            pipeline.append({"$match": {"total_mv_yi": {"$gte": 100, "$lte": 500}}})  # 100-500亿
        elif market_cap == "small":
            pipeline.append({"$match": {"total_mv_yi": {"$lte": 100}}})  # <= 100亿
        else:
            pipeline.append({"$match": {"total_mv_yi": {"$gte": 20}}})  # 最小20亿市值
        
        # 继续添加聚合步骤
        pipeline.extend([
            # 第七步：关联板块涨停数据
            {"$lookup": {
                "from": "limit_cpt_list",
                "let": {"date": "$trade_date", "industry": "$industry"},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$trade_date", "$$date"]},
                                {"$eq": ["$concept", "$$industry"]}
                            ]
                        }
                    }},
                    {"$project": {"up_nums": 1, "cons_nums": 1}}
                ],
                "as": "sector_data"
            }},
            {"$unwind": {"path": "$sector_data", "preserveNullAndEmptyArrays": True}},
            
            # 第八步：计算连板龙头评分
            {"$addFields": {
                "score": {
                    "$add": [
                        # 连板次数得分：2-6连板得分递增，超过6连板得分递减
                        {"$cond": {
                            "if": {"$lte": ["$limit_times", 6]},
                            "then": {"$multiply": ["$limit_times", 10]},  # 2连20分，6连60分
                            "else": {"$subtract": [80, {"$multiply": [{"$subtract": ["$limit_times", 6]}, 5]}]}  # 7连75分，递减
                        }},
                        
                        # 封板强度得分：开板次数越少得分越高，最高25分
                        {"$subtract": [25, {"$multiply": [{"$ifNull": ["$open_times", 0]}, 6]}]},
                        
                        # 板块热度得分：板块涨停股数越多得分越高，最高20分
                        {"$min": [20, {"$multiply": [{"$ifNull": ["$sector_data.up_nums", 0]}, 2]}]},
                        
                        # 市值得分：中等市值得分较高，最高15分
                        {"$cond": {
                            "if": {"$and": [
                                {"$gte": ["$total_mv_yi", 50]},   # >= 50亿
                                {"$lte": ["$total_mv_yi", 200]}   # <= 200亿
                            ]},
                            "then": 15,
                            "else": {"$cond": {
                                "if": {"$gte": ["$total_mv_yi", 20]},  # >= 20亿
                                "then": 10,
                                "else": 5
                            }}
                        }},
                        
                        # 换手率得分：适中换手率得分高，最高10分
                        {"$cond": {
                            "if": {"$and": [
                                {"$gte": [{"$ifNull": ["$tech_data.turnover_rate", 0]}, 8]},    # >= 8%
                                {"$lte": [{"$ifNull": ["$tech_data.turnover_rate", 0]}, 20]}    # <= 20%
                            ]},
                            "then": 10,
                            "else": 5
                        }}
                    ]
                }
            }},
            
            # 第九步：输出字段
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": 1,
                "limit_times": 1,
                "open_times": 1,
                "first_time": 1,
                "last_time": 1,
                "close": 1,
                "pct_chg": "$tech_data.pct_chg",
                "amount": "$tech_data.amount",
                "total_mv": "$tech_data.total_mv",
                "turnover_rate": "$tech_data.turnover_rate",
                "pe": "$tech_data.pe",
                "pb": "$tech_data.pb",
                "sector_up_nums": "$sector_data.up_nums",
                "score": 1,
                "leader_signal": {
                    "$cond": {
                        "if": {"$gte": ["$score", 70]},
                        "then": True,
                        "else": False
                    }
                }
            }},
            
            {"$sort": {"score": -1}},
            {"$limit": limit}
        ])
        
        results = list(db_handler.get_collection('limit_list_daily').aggregate(pipeline))
        
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
            # 连板龙头策略专用字段放到special中
            special={
                'limit_times': r.get('limit_times'),
                'open_times': r.get('open_times'),
                'first_time': r.get('first_time'),
                'last_time': r.get('last_time'),
                'amount': r.get('amount'),
                'turnover_rate': round(r.get('turnover_rate', 0), 2),
                'sector_up_nums': r.get('sector_up_nums'),
                'leader_signal': r.get('leader_signal', False)
            }
        ) for r in results]
        
        return ScreeningResponse(
            strategy_name="连板龙头策略",
            strategy_type="special",
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连板龙头策略筛选失败: {str(e)}")

@router.post("/fund-flow-tracking")
@cache_endpoint(data_type="fund_flow_tracking", ttl=300)
async def fund_flow_tracking_screening(
    params: FundFlowTrackingParams,
    current_user: dict = Depends(get_current_user)
):
    """资金追踪策略专门接口 - 使用优化的交集查询算法"""
    logger.info("🔥 fund_flow_tracking_screening 接口被调用!")
    logger.info(f"参数: {params}")
    try:
        # 使用优化的资金追踪筛选逻辑 - 交集查询
        results = await _optimized_fund_flow_screening(params)
        
        # 格式化结果 - 直接使用优化后的简化结果
        formatted_results = []
        for r in results:
            result = ScreeningResult(
                ts_code=r['ts_code'],
                name=r.get('name', ''),
                industry=r.get('industry'),
                close=r.get('close'),
                pe=None,  # 暂不提供
                pb=None,  # 暂不提供  
                pct_chg=r.get('pct_chg'),
                total_mv=r.get('total_mv'),
                score=round(r.get('score', 0), 2),
                # 资金追踪核心字段
                margin_buy_trend=r.get('margin_buy_trend'),
                margin_balance_growth=r.get('margin_balance_growth'),
                fund_tracking_score=r.get('fund_tracking_score')
            )
            formatted_results.append(result)
        
        return ScreeningResponse(
            strategy_name="资金追踪策略",
            strategy_type="fund_flow",
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results
        )
    except Exception as e:
        logger.error(f"资金追踪策略筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"资金追踪策略筛选失败: {str(e)}")

async def _optimized_fund_flow_screening(params: FundFlowTrackingParams) -> List[Dict[str, Any]]:
    """优化的资金追踪筛选 - 使用交集查询"""
    try:
        # 步骤1: 并行查询各个条件的TOP股票
        logger.info("🔍 开始并行查询各资金条件...")
        
        # 1.1 融资买入趋势TOP500
        margin_buy_candidates = await _query_margin_buy_top_stocks(params.margin_buy_trend_min, 500)
        logger.info(f"融资买入趋势候选: {len(margin_buy_candidates)}只")
        
        # 1.2 融资余额增长TOP500  
        margin_balance_candidates = await _query_margin_balance_growth_stocks(params.margin_balance_growth_min, 500)
        logger.info(f"融资余额增长候选: {len(margin_balance_candidates)}只")
        
        # 步骤2: 求交集 (只使用融资买入趋势和融资余额增长两个条件)
        logger.info("🔄 计算候选股票交集...")
        intersection_stocks = set(margin_buy_candidates)
        intersection_stocks &= set(margin_balance_candidates)
        
        logger.info(f"交集结果: {len(intersection_stocks)}只股票")
        
        if not intersection_stocks:
            return []
            
        # 步骤3: 计算最终评分并排序（跳过行业筛选）
        logger.info("📊 计算综合评分...")
        scored_results = await _calculate_final_scores(list(intersection_stocks), params)
        
        # 返回TOP N结果
        return sorted(scored_results, key=lambda x: x.get('score', 0), reverse=True)[:params.limit]
        
    except Exception as e:
        logger.error(f"优化资金追踪筛选失败: {str(e)}")
        return []

async def _query_margin_buy_top_stocks(min_trend: float, limit: int = 500) -> List[str]:
    """查询融资买入趋势TOP股票"""
    try:
        # 获取最近交易日
        recent_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        # 聚合查询：计算每只股票的融资买入趋势
        pipeline = [
            {"$match": {"trade_date": {"$gte": recent_date}}},
            {"$group": {
                "_id": "$ts_code",
                "recent_buy": {"$avg": {"$toDouble": "$rzmre"}},
                "total_records": {"$sum": 1}
            }},
            {"$match": {"total_records": {"$gte": 3}}},  # 至少3条记录
            {"$sort": {"recent_buy": -1}},
            {"$limit": limit}
        ]
        
        result = list(db_handler.get_collection('margin_detail').aggregate(pipeline))
        return [doc['_id'] for doc in result if doc.get('recent_buy', 0) >= min_trend]
        
    except Exception as e:
        logger.error(f"查询融资买入TOP股票失败: {str(e)}")
        return []

async def _query_margin_balance_growth_stocks(min_growth: float, limit: int = 500) -> List[str]:
    """查询融资余额增长TOP股票"""
    try:
        recent_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
        
        pipeline = [
            {"$match": {"trade_date": {"$gte": recent_date}}},
            {"$group": {
                "_id": "$ts_code",
                "avg_balance": {"$avg": {"$toDouble": "$rzye"}},
                "max_balance": {"$max": {"$toDouble": "$rzye"}},
                "min_balance": {"$min": {"$toDouble": "$rzye"}},
                "total_records": {"$sum": 1}
            }},
            {"$match": {"total_records": {"$gte": 5}}},
            {"$addFields": {
                "growth_rate": {
                    "$multiply": [
                        {"$divide": [
                            {"$subtract": ["$max_balance", "$min_balance"]},
                            "$min_balance"
                        ]},
                        100
                    ]
                }
            }},
            {"$match": {"growth_rate": {"$gte": min_growth}}},
            {"$sort": {"growth_rate": -1}},
            {"$limit": limit}
        ]
        
        result = list(db_handler.get_collection('margin_detail').aggregate(pipeline))
        return [doc['_id'] for doc in result]
        
    except Exception as e:
        logger.error(f"查询融资余额增长股票失败: {str(e)}")
        return []


async def _calculate_final_scores(stock_codes: List[str], params: FundFlowTrackingParams) -> List[Dict[str, Any]]:
    """计算最终综合评分并获取完整数据"""
    results = []
    
    for ts_code in stock_codes:
        try:
            # 获取基本信息
            stock_info = db_handler.get_collection('infrastructure_stock_basic').find_one(
                {"ts_code": ts_code},
                {"name": 1, "industry": 1, "_id": 0}
            )
            
            if not stock_info:
                continue
            
            # 获取最新价格数据 - 只查询必要字段
            price_data = db_handler.get_collection('stock_factor_pro').find_one(
                {"ts_code": ts_code},
                {"close": 1, "pct_chg": 1, "total_mv": 1, "_id": 0},
                sort=[("trade_date", -1)]
            )
            
            # 获取融资融券数据（最近7天）
            margin_cursor = db_handler.get_collection('margin_detail').find(
                {"ts_code": ts_code},
                {"rzmre": 1, "rzye": 1, "trade_date": 1, "_id": 0}
            ).sort("trade_date", -1).limit(10)
            
            margin_list = list(margin_cursor)
            
            # 计算融资买入趋势和余额增长
            margin_buy_trend = None
            margin_balance_growth = None
            
            if len(margin_list) >= 3:
                try:
                    # 计算融资买入趋势（最近3天vs前3天）
                    recent_buy = []
                    for i in range(min(3, len(margin_list))):
                        buy_amount = float(margin_list[i].get("rzmre", 0))
                        recent_buy.append(buy_amount)
                    
                    baseline_buy = []
                    for i in range(3, min(6, len(margin_list))):
                        buy_amount = float(margin_list[i].get("rzmre", 0))
                        baseline_buy.append(buy_amount)
                    
                    if recent_buy and baseline_buy:
                        recent_avg = sum(recent_buy) / len(recent_buy)
                        baseline_avg = sum(baseline_buy) / len(baseline_buy)
                        
                        if baseline_avg > 0:
                            growth_rate = (recent_avg - baseline_avg) / baseline_avg * 100
                            margin_buy_trend = round(growth_rate, 2)  # 直接返回实际趋势百分比
                    
                    # 计算融资余额增长率（最新vs一周前）
                    if len(margin_list) >= 2:
                        latest_balance = float(margin_list[0].get("rzye", 0))
                        week_ago_balance = float(margin_list[-1].get("rzye", 0))
                        
                        if week_ago_balance > 0:
                            growth_rate = (latest_balance - week_ago_balance) / week_ago_balance * 100
                            margin_balance_growth = round(growth_rate, 2)  # 直接返回实际增长率
                            
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
            
            # 动态评分计算 - 基于融资买入趋势和余额增长
            base_score = 50  # 基础分
            
            # 根据融资买入趋势加分（-25到+25分）
            if margin_buy_trend is not None:
                trend_score = max(-25, min(25, margin_buy_trend * 0.25))
                base_score += trend_score
            
            # 根据融资余额增长加分（-25到+25分）
            if margin_balance_growth is not None:
                growth_score = max(-25, min(25, margin_balance_growth * 0.25))
                base_score += growth_score
            
            # 确保评分在0-100范围内
            base_score = max(0, min(100, round(base_score, 1)))
            
            
            # 精简结果对象，只包含前端表格需要的字段
            result = {
                'ts_code': ts_code,
                'name': stock_info.get('name', ''),
                'industry': stock_info.get('industry', ''),
                'score': base_score,
                'close': float(price_data.get('close', 0)) if price_data and price_data.get('close') else None,
                'pct_chg': float(price_data.get('pct_chg', 0)) if price_data and price_data.get('pct_chg') else None,
                'total_mv': float(price_data.get('total_mv', 0)) if price_data and price_data.get('total_mv') else None,
                'margin_buy_trend': margin_buy_trend,
                'margin_balance_growth': margin_balance_growth,
                'fund_tracking_score': base_score
            }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"计算{ts_code}评分失败: {str(e)}")
            continue
    
    return results

async def _generic_template_screening(
    request: StrategyRequest,
    current_user: dict
) -> ScreeningResponse:
    """通用模板筛选 - 基于数据库中的strategy_type字段"""
    try:
        # 获取股票池
        stock_pool = request.stock_pool[0] if request.stock_pool else 'all'
        if stock_pool == 'all':
            stock_pool = await _get_all_stocks()
        else:
            stock_pool = await _get_stock_pool(stock_pool)
        
        # 使用策略筛选引擎进行通用筛选
        results = await screening_engine.comprehensive_screening(
            stock_pool=stock_pool,
            technical_conditions=request.technical_conditions,
            fundamental_conditions=request.fundamental_conditions,
            special_conditions=request.special_conditions,
            strategy_type=request.strategy_type,  # 使用数据库中的实际strategy_type
            limit=request.limit
        )
        
        # 格式化结果
        formatted_results = [ScreeningResult(
            ts_code=r['ts_code'],
            name=r.get('name', ''),
            industry=r.get('industry'),
            close=r.get('technical', {}).get('close') if r.get('technical') else None,
            pe=r.get('fundamental', {}).get('pe') if r.get('fundamental') else None,
            pb=r.get('fundamental', {}).get('pb') if r.get('fundamental') else None,
            pct_chg=None,  # 需要从日线数据获取
            total_mv=None,  # 需要从基本数据获取
            score=round(r.get('score', 0), 2)
        ) for r in results]
        
        return ScreeningResponse(
            strategy_name=request.strategy_name,
            strategy_type=request.strategy_type,
            total_count=len(formatted_results),
            screening_time=datetime.now(),
            results=formatted_results
        )
        
    except Exception as e:
        logger.error(f"通用模板筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"通用模板筛选失败: {str(e)}")