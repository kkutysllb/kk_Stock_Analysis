#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道氏理论分析API路由
提供道氏理论分析相关的API接口
"""

import os
import sys
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from analysis.dow_theory.core.dow_theory_engine import DowTheoryEngine
from analysis.dow_theory.models.dow_theory_models import DowTheoryAnalysisResult
from analysis.dow_theory.analyzers.dow_rules_analyzer import DowRulesAnalyzer
from api.routers.user import get_current_user
from api.global_db import db_handler

# 创建路由器
router = APIRouter(prefix="/dow_theory", tags=["道氏理论分析"])

# 设置日志
logger = logging.getLogger(__name__)

# 创建全局引擎实例
dow_engine = DowTheoryEngine()


@router.get("/analyze/{stock_code}", summary="个股道氏理论分析")
async def analyze_stock(
    stock_code: str,
    start_date: Optional[str] = Query(None, description="开始日期，格式YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式YYYY-MM-DD"),
    analysis_date: Optional[str] = Query(None, description="分析日期，格式YYYY-MM-DD（兼容旧版本）"),
    current_user: dict = Depends(get_current_user)
):
    """
    对指定股票进行道氏理论分析
    
    Args:
        stock_code: 股票代码 (如: 000001.SZ)
        start_date: 开始日期，默认为30天前
        end_date: 结束日期，默认为当前日期
        analysis_date: 分析日期（兼容旧版本参数）
        current_user: 当前用户信息
    
    Returns:
        道氏理论分析结果
    """
    try:
        # 处理时间范围参数
        if start_date and end_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        elif analysis_date:
            # 兼容旧版本：单个分析日期
            try:
                analysis_datetime = datetime.strptime(analysis_date, "%Y-%m-%d")
                start_datetime = analysis_datetime - timedelta(days=30)  # 默认30天范围
                end_datetime = analysis_datetime
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        else:
            # 默认最近30天
            end_datetime = datetime.now()
            start_datetime = end_datetime - timedelta(days=30)
        
        # 验证日期范围
        if start_datetime >= end_datetime:
            raise HTTPException(status_code=400, detail="开始日期必须早于结束日期")
            
        if (end_datetime - start_datetime).days > 365:
            raise HTTPException(status_code=400, detail="分析时间范围不能超过365天")
        
        # 执行分析
        logger.info(f"用户 {current_user.get('username')} 请求分析股票 {stock_code}，时间范围: {start_datetime.date()} 至 {end_datetime.date()}")
        
        result = dow_engine.analyze_stock_range(stock_code, start_datetime, end_datetime)
        
        # 执行增强分析（使用DowRulesAnalyzer）
        enhanced_result = _get_enhanced_analysis(stock_code, start_datetime, end_datetime)
        
        # 转换为字典格式返回，确保完全序列化
        response_data = dow_engine._make_json_serializable(_format_analysis_result(result))
        
        # 合并增强分析结果，确保序列化
        if enhanced_result:
            response_data["enhanced_analysis"] = dow_engine._make_json_serializable(enhanced_result)
        
        return JSONResponse(content={
            "code": 200,
            "message": "分析完成",
            "data": response_data
        })
        
    except Exception as e:
        logger.error(f"分析股票 {stock_code} 时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/batch_analyze", summary="批量股票道氏理论分析")
async def batch_analyze_stocks(
    stock_codes: str = Query(..., description="股票代码列表，用逗号分隔"),
    analysis_date: Optional[str] = Query(None, description="分析日期，格式YYYY-MM-DD"),
    current_user: dict = Depends(get_current_user)
):
    """
    批量分析多只股票的道氏理论
    
    Args:
        stock_codes: 股票代码列表，用逗号分隔
        analysis_date: 分析日期，默认为当前日期
        current_user: 当前用户信息
    
    Returns:
        批量分析结果
    """
    try:
        # 解析股票代码列表
        codes = [code.strip() for code in stock_codes.split(",") if code.strip()]
        
        if len(codes) > 20:
            raise HTTPException(status_code=400, detail="批量分析最多支持20只股票")
        
        # 解析分析日期
        if analysis_date:
            try:
                analysis_datetime = datetime.strptime(analysis_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        else:
            analysis_datetime = datetime.now()
        
        # 批量执行分析
        logger.info(f"用户 {current_user.get('username')} 请求批量分析 {len(codes)} 只股票")
        
        results = []
        failed_stocks = []
        
        for code in codes:
            try:
                result = dow_engine.analyze_stock(code, analysis_datetime)
                formatted_result = dow_engine._make_json_serializable(_format_analysis_result(result))
                
                # 添加增强分析，确保序列化
                enhanced_result = _get_enhanced_analysis(code, analysis_datetime - timedelta(days=30), analysis_datetime)
                if enhanced_result:
                    formatted_result["enhanced_analysis"] = dow_engine._make_json_serializable(enhanced_result)
                
                results.append(formatted_result)
            except Exception as e:
                logger.error(f"分析股票 {code} 失败: {e}")
                failed_stocks.append({"stock_code": code, "error": str(e)})
        
        return JSONResponse(content={
            "code": 200,
            "message": f"批量分析完成，成功{len(results)}只，失败{len(failed_stocks)}只",
            "data": {
                "successful_analyses": results,
                "failed_analyses": failed_stocks,
                "summary": {
                    "total_requested": len(codes),
                    "successful_count": len(results),
                    "failed_count": len(failed_stocks)
                }
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量分析时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")


@router.get("/quick_screening", summary="道氏理论快速筛选")
async def quick_screening(
    trend_direction: Optional[str] = Query(None, description="趋势方向: upward/downward/sideways"),
    trend_phase: Optional[str] = Query(None, description="趋势阶段: accumulation/public_participation/panic"),
    min_confidence: Optional[float] = Query(60.0, description="最小信心指数"),
    action_filter: Optional[str] = Query(None, description="操作建议筛选: buy/sell/hold/wait"),
    limit: Optional[int] = Query(50, description="返回结果数量限制"),
    current_user: dict = Depends(get_current_user)
):
    """
    基于道氏理论条件快速筛选股票
    
    Args:
        trend_direction: 趋势方向筛选
        trend_phase: 趋势阶段筛选
        min_confidence: 最小信心指数
        action_filter: 操作建议筛选
        limit: 返回结果数量限制
        current_user: 当前用户信息
    
    Returns:
        筛选结果
    """
    try:
        logger.info(f"用户 {current_user.get('username')} 请求道氏理论筛选")
        
        # 这里应该实现筛选逻辑，简化示例
        # 实际实现中应该查询预计算的分析结果或进行实时筛选
        
        screening_results = _perform_screening(
            trend_direction, trend_phase, min_confidence, action_filter, limit
        )
        
        return JSONResponse(content={
            "code": 200,
            "message": "筛选完成",
            "data": {
                "screening_criteria": {
                    "trend_direction": trend_direction,
                    "trend_phase": trend_phase,
                    "min_confidence": min_confidence,
                    "action_filter": action_filter
                },
                "results": screening_results,
                "result_count": len(screening_results)
            }
        })
        
    except Exception as e:
        logger.error(f"道氏理论筛选时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"筛选失败: {str(e)}")


@router.get("/trend_summary", summary="市场趋势概览")
async def get_market_trend_summary(
    index_codes: Optional[str] = Query("000001.SH,399001.SZ,399006.SZ", description="指数代码列表"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取主要市场指数的道氏理论趋势概览
    
    Args:
        index_codes: 指数代码列表，用逗号分隔
        current_user: 当前用户信息
    
    Returns:
        市场趋势概览
    """
    try:
        # 解析指数代码
        codes = [code.strip() for code in index_codes.split(",") if code.strip()]
        
        logger.info(f"用户 {current_user.get('username')} 请求市场趋势概览")
        
        market_summary = []
        
        for code in codes:
            try:
                # 分析指数
                result = dow_engine.analyze_stock(code)
                
                summary_item = {
                    "index_code": code,
                    "index_name": result.stock_name,
                    "current_price": result.current_price,
                    "overall_trend": result.overall_trend.value if hasattr(result.overall_trend, 'value') else result.overall_trend,
                    "overall_phase": result.overall_phase.value if hasattr(result.overall_phase, 'value') else result.overall_phase,
                    "overall_confidence": result.overall_confidence,
                    "action_recommendation": result.action_recommendation,
                    "analysis_date": result.analysis_date.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                market_summary.append(summary_item)
                
            except Exception as e:
                logger.error(f"分析指数 {code} 失败: {e}")
                market_summary.append({
                    "index_code": code,
                    "error": str(e)
                })
        
        return JSONResponse(content={
            "code": 200,
            "message": "市场趋势概览获取完成",
            "data": {
                "market_summary": market_summary,
                "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        })
        
    except Exception as e:
        logger.error(f"获取市场趋势概览时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")


@router.get("/phase_statistics", summary="趋势阶段统计")
async def get_phase_statistics(
    market: Optional[str] = Query("all", description="市场范围: all/sh/sz/cy/kc"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取市场趋势阶段分布统计
    
    Args:
        market: 市场范围
        current_user: 当前用户信息
    
    Returns:
        趋势阶段统计结果
    """
    try:
        logger.info(f"用户 {current_user.get('username')} 请求趋势阶段统计")
        
        # 这里应该实现统计逻辑，简化示例
        statistics = _calculate_phase_statistics(market)
        
        return JSONResponse(content={
            "code": 200,
            "message": "趋势阶段统计完成",
            "data": statistics
        })
        
    except Exception as e:
        logger.error(f"获取趋势阶段统计时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}")


@router.get("/dow_rules/{stock_code}", summary="道氏理论123法则和2B法则分析")
async def analyze_dow_rules(
    stock_code: str,
    analysis_date: Optional[str] = Query(None, description="分析日期，格式YYYY-MM-DD"),
    rule_type: Optional[str] = Query("all", description="法则类型: all/rule_123/rule_2b"),
    current_user: dict = Depends(get_current_user)
):
    """
    对指定股票进行道氏理论123法则和2B法则分析
    
    Args:
        stock_code: 股票代码 (如: 000001.SZ)
        analysis_date: 分析日期，默认为当前日期
        rule_type: 法则类型筛选
        current_user: 当前用户信息
    
    Returns:
        道氏理论法则分析结果
    """
    try:
        # 解析分析日期
        if analysis_date:
            try:
                analysis_datetime = datetime.strptime(analysis_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        else:
            analysis_datetime = datetime.now()
        
        logger.info(f"用户 {current_user.get('username')} 请求分析股票 {stock_code} 的道氏理论法则")
        
        # 执行道氏理论法则分析
        result = dow_engine.analyze_stock(stock_code, analysis_datetime)
        
        # 提取法则分析结果
        dow_rules_data = _format_dow_rules_analysis(result, rule_type)
        
        # 添加增强分析结果，确保序列化
        enhanced_result = _get_enhanced_analysis(stock_code, analysis_datetime - timedelta(days=30), analysis_datetime)
        if enhanced_result:
            dow_rules_data["enhanced_analysis"] = dow_engine._make_json_serializable(enhanced_result)
        
        return JSONResponse(content={
            "code": 200,
            "message": "道氏理论法则分析完成",
            "data": dow_rules_data
        })
        
    except Exception as e:
        logger.error(f"分析股票 {stock_code} 道氏理论法则时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"法则分析失败: {str(e)}")


@router.post("/analyze-dow-rules", summary="道氏理论法则分析 (POST方法)")
async def analyze_dow_rules_post(
    request_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    对指定股票进行道氏理论123法则和2B法则分析
    
    Args:
        request_data: 请求数据，包含ts_code, start_date, end_date, trend_type等
        current_user: 当前用户信息
    
    Returns:
        道氏理论法则分析结果
    """
    try:
        # 从请求数据中提取参数
        ts_code = request_data.get('ts_code')
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        trend_type = request_data.get('trend_type', 'primary')
        
        if not ts_code:
            raise HTTPException(status_code=400, detail="缺少必需参数: ts_code")
        
        # 解析日期
        if start_date and end_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        else:
            # 默认最近30天
            end_datetime = datetime.now()
            start_datetime = end_datetime - timedelta(days=30)
        
        logger.info(f"用户 {current_user.get('username')} 请求分析股票 {ts_code} 的道氏理论法则")
        
        # 使用DowRulesAnalyzer进行增强分析
        analyzer = DowRulesAnalyzer()
        result = analyzer.analyze_with_factors(
            ts_code=ts_code,
            start_date=start_datetime.strftime('%Y%m%d'),
            end_date=end_datetime.strftime('%Y%m%d'),
            trend_type=trend_type
        )
        
        return JSONResponse(content={
            "code": 200,
            "message": "道氏理论法则分析完成",
            "data": result
        })
        
    except Exception as e:
        logger.error(f"分析股票道氏理论法则时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"法则分析失败: {str(e)}")


@router.get("/rule_123_signals", summary="批量123法则信号筛选")
async def get_rule_123_signals(
    min_probability: Optional[float] = Query(60.0, description="最小反转概率"),
    signal_strength: Optional[str] = Query(None, description="信号强度: strong/medium/weak"),
    limit: Optional[int] = Query(50, description="返回结果数量限制"),
    current_user: dict = Depends(get_current_user)
):
    """
    批量筛选123法则信号
    
    Args:
        min_probability: 最小反转概率
        signal_strength: 信号强度筛选
        limit: 返回结果数量限制
        current_user: 当前用户信息
    
    Returns:
        123法则信号筛选结果
    """
    try:
        logger.info(f"用户 {current_user.get('username')} 请求123法则信号筛选")
        
        # 这里应该实现123法则信号筛选逻辑
        signals = _screen_rule_123_signals(min_probability, signal_strength, limit)
        
        return JSONResponse(content={
            "code": 200,
            "message": "123法则信号筛选完成",
            "data": {
                "screening_criteria": {
                    "min_probability": min_probability,
                    "signal_strength": signal_strength,
                    "limit": limit
                },
                "signals": signals,
                "signal_count": len(signals)
            }
        })
        
    except Exception as e:
        logger.error(f"123法则信号筛选时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"信号筛选失败: {str(e)}")


@router.get("/rule_2b_signals", summary="批量2B法则信号筛选")
async def get_rule_2b_signals(
    min_probability: Optional[float] = Query(70.0, description="最小反转概率"),
    signal_strength: Optional[str] = Query(None, description="信号强度: strong/medium/weak"),
    limit: Optional[int] = Query(50, description="返回结果数量限制"),
    current_user: dict = Depends(get_current_user)
):
    """
    批量筛选2B法则信号
    
    Args:
        min_probability: 最小反转概率
        signal_strength: 信号强度筛选
        limit: 返回结果数量限制
        current_user: 当前用户信息
    
    Returns:
        2B法则信号筛选结果
    """
    try:
        logger.info(f"用户 {current_user.get('username')} 请求2B法则信号筛选")
        
        # 这里应该实现2B法则信号筛选逻辑
        signals = _screen_rule_2b_signals(min_probability, signal_strength, limit)
        
        return JSONResponse(content={
            "code": 200,
            "message": "2B法则信号筛选完成",
            "data": {
                "screening_criteria": {
                    "min_probability": min_probability,
                    "signal_strength": signal_strength,
                    "limit": limit
                },
                "signals": signals,
                "signal_count": len(signals)
            }
        })
        
    except Exception as e:
        logger.error(f"2B法则信号筛选时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"信号筛选失败: {str(e)}")


@router.get("/historical_data/{stock_code}", summary="获取股票历史数据")
async def get_historical_data(
    stock_code: str,
    days: Optional[int] = Query(60, description="获取天数"),
    start_date: Optional[str] = Query(None, description="开始日期，格式YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式YYYY-MM-DD")
):
    """
    获取股票历史K线数据用于图表展示
    
    Args:
        stock_code: 股票代码
        days: 获取天数（当未指定具体日期范围时使用）
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        历史K线数据
    """
    try:
        logger.info(f"请求股票 {stock_code} 历史数据")
        
        # 处理日期范围参数
        if start_date and end_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        else:
            # 使用days参数计算日期范围
            end_datetime = datetime.now()
            start_datetime = end_datetime - timedelta(days=days)
        
        # 验证日期范围
        if start_datetime >= end_datetime:
            raise HTTPException(status_code=400, detail="开始日期必须早于结束日期")
            
        if (end_datetime - start_datetime).days > 365:
            raise HTTPException(status_code=400, detail="历史数据时间范围不能超过365天")
        
        # 获取历史数据
        historical_data = dow_engine.get_historical_data(stock_code, start_datetime, end_datetime)
        
        return JSONResponse(content={
            "code": 200,
            "message": "历史数据获取成功",
            "data": historical_data
        })
        
    except Exception as e:
        logger.error(f"获取股票 {stock_code} 历史数据时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")


def _format_analysis_result(result: DowTheoryAnalysisResult) -> Dict:
    """格式化分析结果为API响应格式"""
    return {
        "basic_info": {
            "stock_code": str(result.stock_code),
            "stock_name": str(result.stock_name),
            "current_price": float(result.current_price),
            "analysis_date": result.analysis_date.strftime("%Y-%m-%d %H:%M:%S")
        },
        "overall_assessment": {
            "overall_trend": str(result.overall_trend.value if hasattr(result.overall_trend, 'value') else result.overall_trend),
            "overall_phase": str(result.overall_phase.value if hasattr(result.overall_phase, 'value') else result.overall_phase),
            "overall_confidence": round(float(result.overall_confidence), 2),
            "action_recommendation": str(result.action_recommendation)
        },
        "timeframe_analysis": {
            "monthly": _format_trend_analysis(result.monthly_analysis),
            "weekly": _format_trend_analysis(result.weekly_analysis),
            "daily": _format_trend_analysis(result.daily_analysis)
        },
        "multi_timeframe_confirmation": {
            "primary_secondary_alignment": bool(result.multi_timeframe_confirmation.primary_secondary_alignment),
            "secondary_minor_alignment": bool(result.multi_timeframe_confirmation.secondary_minor_alignment),
            "overall_alignment": bool(result.multi_timeframe_confirmation.overall_alignment),
            "confirmation_strength": result.multi_timeframe_confirmation.confirmation_strength.value if hasattr(result.multi_timeframe_confirmation.confirmation_strength, 'value') else result.multi_timeframe_confirmation.confirmation_strength,
            "conflicting_signals": list(result.multi_timeframe_confirmation.conflicting_signals) if result.multi_timeframe_confirmation.conflicting_signals else []
        },
        "risk_assessment": {
            "risk_level": str(result.risk_assessment.risk_level.value if hasattr(result.risk_assessment.risk_level, 'value') else result.risk_assessment.risk_level),
            "stop_loss_price": float(result.risk_assessment.stop_loss_price),
            "target_price": float(result.risk_assessment.target_price),
            "position_suggestion": float(result.risk_assessment.position_suggestion),
            "key_risk_factors": list(result.risk_assessment.key_risk_factors)
        },
        "key_levels": [float(x) for x in result.key_levels] if result.key_levels else [],
        "next_review_date": result.next_review_date.strftime("%Y-%m-%d"),
        "analysis_summary": str(result.analysis_summary),
        "detailed_analysis": str(result.detailed_analysis)
    }


def _format_trend_analysis(analysis) -> Dict:
    """格式化趋势分析结果"""
    return {
        "trend_type": str(analysis.trend_type.value if hasattr(analysis.trend_type, 'value') else analysis.trend_type),
        "direction": str(analysis.direction.value if hasattr(analysis.direction, 'value') else analysis.direction),
        "phase": str(analysis.phase.value if hasattr(analysis.phase, 'value') else analysis.phase),
        "confidence_score": round(float(analysis.confidence_score), 2),
        "trend_line": {
            "is_valid": bool(analysis.trend_line.is_valid) if analysis.trend_line else False,
            "slope": float(analysis.trend_line.slope) if analysis.trend_line else 0.0,
            "r_squared": float(analysis.trend_line.r_squared) if analysis.trend_line else 0.0,
            "touch_count": int(analysis.trend_line.touch_count) if analysis.trend_line else 0
        } if analysis.trend_line else None,
        "support_resistance": [
            {
                "level": float(sr.level),
                "type": str(sr.level_type.value if hasattr(sr.level_type, 'value') else sr.level_type),
                "strength": str(sr.strength.value if hasattr(sr.strength, 'value') else sr.strength),
                "touch_count": int(sr.touch_count)
            } for sr in analysis.support_resistance[:3]  # 只返回前3个重要位置
        ],
        "volume_analysis": {
            "current_volume": int(analysis.volume_analysis.current_volume),
            "avg_volume": int(analysis.volume_analysis.avg_volume_20d),
            "volume_ratio": round(analysis.volume_analysis.volume_ratio, 2),
            "pattern": str(analysis.volume_analysis.pattern.value if hasattr(analysis.volume_analysis.pattern, 'value') else analysis.volume_analysis.pattern),
            "divergence_signal": bool(analysis.volume_analysis.divergence_signal),
            "strength": str(analysis.volume_analysis.strength.value if hasattr(analysis.volume_analysis.strength, 'value') else analysis.volume_analysis.strength)
        },
        "technical_indicators": {
            "current_price": float(analysis.technical_indicators.current_price) if hasattr(analysis.technical_indicators, 'current_price') else 0.0,
            "ma_20": round(float(analysis.technical_indicators.ma_20), 2),
            "ma_60": round(float(analysis.technical_indicators.ma_60), 2),
            "ma_250": round(float(analysis.technical_indicators.ma_250), 2),
            "macd_dif": round(float(analysis.technical_indicators.macd_dif), 4),
            "macd_dea": round(float(analysis.technical_indicators.macd_dea), 4),
            "macd_histogram": round(float(analysis.technical_indicators.macd_histogram), 4),
            "rsi": round(float(analysis.technical_indicators.rsi), 2)
        },
        "breakthrough_signals": [
            {
                "breakthrough_type": str(bs.breakthrough_type.value if hasattr(bs.breakthrough_type, 'value') else bs.breakthrough_type),
                "breakout_price": float(bs.breakout_price),
                "volume_confirmation": bool(bs.volume_confirmation),
                "price_confirmation": bool(bs.price_confirmation),
                "time_confirmation": bool(bs.time_confirmation),
                "strength": str(bs.strength.value if hasattr(bs.strength, 'value') else bs.strength)
            } for bs in analysis.breakthrough_signals
        ]
    }


def _perform_screening(trend_direction: Optional[str], trend_phase: Optional[str],
                      min_confidence: float, action_filter: Optional[str],
                      limit: int) -> List[Dict]:
    """执行筛选逻辑（简化实现）"""
    # 这里应该实现真实的筛选逻辑
    # 简化返回示例数据
    sample_results = [
        {
            "stock_code": "000001.SZ",
            "stock_name": "平安银行",
            "current_price": 15.68,
            "overall_trend": "upward",
            "overall_phase": "public_participation",
            "overall_confidence": 78.5,
            "action_recommendation": "buy"
        },
        {
            "stock_code": "000002.SZ",
            "stock_name": "万科A",
            "current_price": 8.23,
            "overall_trend": "sideways",
            "overall_phase": "accumulation",
            "overall_confidence": 65.2,
            "action_recommendation": "hold"
        }
    ]
    
    return sample_results[:limit]


def _format_dow_rules_analysis(result: DowTheoryAnalysisResult, rule_type: str) -> Dict:
    """格式化道氏理论法则分析结果"""
    dow_rules_data = {
        "basic_info": {
            "stock_code": str(result.stock_code),
            "stock_name": str(result.stock_name),
            "current_price": float(result.current_price),
            "analysis_date": result.analysis_date.strftime("%Y-%m-%d %H:%M:%S")
        },
        "rule_analysis": {}
    }
    
    # 从各时间周期中提取道氏理论法则分析结果
    timeframes = {
        "daily": result.daily_analysis,
        "weekly": result.weekly_analysis,
        "monthly": result.monthly_analysis
    }
    
    for timeframe_name, analysis in timeframes.items():
        if hasattr(analysis, 'dow_rules_analysis') and analysis.dow_rules_analysis:
            dow_rules = analysis.dow_rules_analysis
            
            timeframe_data = {
                "current_trend": str(dow_rules.get('current_trend', '').value if hasattr(dow_rules.get('current_trend', ''), 'value') else dow_rules.get('current_trend', '')),
                "overall_signal_strength": str(dow_rules.get('overall_signal_strength', '').value if hasattr(dow_rules.get('overall_signal_strength', ''), 'value') else dow_rules.get('overall_signal_strength', '')),
                "reversal_probability": round(float(dow_rules.get('reversal_probability', 0)), 2),
                "trading_recommendation": str(dow_rules.get('trading_recommendation', '')),
                "key_levels_to_watch": [float(x) for x in (dow_rules.get('key_levels_to_watch', []) or [])]
            }
            
            # 根据rule_type筛选返回的信号
            if rule_type == "all" or rule_type == "rule_123":
                rule_123_signals = dow_rules.get('rule_123_signals', []) or []
                timeframe_data["rule_123_signals"] = [
                    {
                        "signal_date": signal.get('signal_date', ''),
                        "signal_price": float(signal.get('signal_price', 0)),
                        "trend_line_break": bool(signal.get('trend_line_break', False)),
                        "no_new_extreme": bool(signal.get('no_new_extreme', False)),
                        "pullback_break": bool(signal.get('pullback_break', False)),
                        "signal_strength": str(signal.get('signal_strength', '')),
                        "reversal_probability": round(float(signal.get('reversal_probability', 0)), 2),
                        "target_price": float(signal.get('target_price')) if signal.get('target_price') else None,
                        "stop_loss_price": float(signal.get('stop_loss_price')) if signal.get('stop_loss_price') else None
                    } for signal in rule_123_signals if isinstance(signal, dict)
                ]
            
            if rule_type == "all" or rule_type == "rule_2b":
                rule_2b_signals = dow_rules.get('rule_2b_signals', []) or []
                timeframe_data["rule_2b_signals"] = [
                    {
                        "signal_date": signal.get('signal_date', ''),
                        "signal_price": float(signal.get('signal_price', 0)),
                        "false_breakout_price": float(signal.get('false_breakout_price', 0)),
                        "breakout_date": signal.get('breakout_date', ''),
                        "reversal_confirmation": bool(signal.get('reversal_confirmation', False)),
                        "volume_divergence": bool(signal.get('volume_divergence', False)),
                        "signal_strength": str(signal.get('signal_strength', '')),
                        "reversal_probability": round(float(signal.get('reversal_probability', 0)), 2),
                        "target_price": float(signal.get('target_price')) if signal.get('target_price') else None,
                        "stop_loss_price": float(signal.get('stop_loss_price')) if signal.get('stop_loss_price') else None
                    } for signal in rule_2b_signals if isinstance(signal, dict)
                ]
            
            dow_rules_data["rule_analysis"][timeframe_name] = timeframe_data
    
    return dow_rules_data


def _screen_rule_123_signals(min_probability: float, signal_strength: Optional[str], limit: int) -> List[Dict]:
    """筛选123法则信号（简化实现）"""
    # 这里应该实现真实的123法则信号筛选逻辑
    # 简化返回示例数据
    sample_signals = [
        {
            "stock_code": "000001.SZ",
            "stock_name": "平安银行",
            "signal_date": "2024-01-15 14:30:00",
            "signal_price": 15.68,
            "trend_line_break": True,
            "no_new_extreme": True,
            "pullback_break": True,
            "signal_strength": "strong",
            "reversal_probability": 78.5,
            "target_price": 17.20,
            "stop_loss_price": 14.80
        },
        {
            "stock_code": "000002.SZ",
            "stock_name": "万科A",
            "signal_date": "2024-01-15 10:15:00",
            "signal_price": 8.23,
            "trend_line_break": True,
            "no_new_extreme": False,
            "pullback_break": True,
            "signal_strength": "medium",
            "reversal_probability": 65.2,
            "target_price": 9.10,
            "stop_loss_price": 7.80
        }
    ]
    
    # 根据条件筛选
    filtered_signals = []
    for signal in sample_signals:
        if signal["reversal_probability"] >= min_probability:
            if signal_strength is None or signal["signal_strength"] == signal_strength:
                filtered_signals.append(signal)
    
    return filtered_signals[:limit]


def _screen_rule_2b_signals(min_probability: float, signal_strength: Optional[str], limit: int) -> List[Dict]:
    """筛选2B法则信号（简化实现）"""
    # 这里应该实现真实的2B法则信号筛选逻辑
    # 简化返回示例数据
    sample_signals = [
        {
            "stock_code": "000001.SZ",
            "stock_name": "平安银行",
            "signal_date": "2024-01-15 14:30:00",
            "signal_price": 15.68,
            "false_breakout_price": 16.20,
            "breakout_date": "2024-01-14 09:30:00",
            "reversal_confirmation": True,
            "volume_divergence": True,
            "signal_strength": "strong",
            "reversal_probability": 82.3,
            "target_price": 14.20,
            "stop_loss_price": 16.50
        },
        {
            "stock_code": "600036.SH",
            "stock_name": "招商银行",
            "signal_date": "2024-01-15 11:20:00",
            "signal_price": 35.45,
            "false_breakout_price": 36.80,
            "breakout_date": "2024-01-13 14:15:00",
            "reversal_confirmation": True,
            "volume_divergence": False,
            "signal_strength": "medium",
            "reversal_probability": 74.6,
            "target_price": 33.20,
            "stop_loss_price": 37.10
        }
    ]
    
    # 根据条件筛选
    filtered_signals = []
    for signal in sample_signals:
        if signal["reversal_probability"] >= min_probability:
            if signal_strength is None or signal["signal_strength"] == signal_strength:
                filtered_signals.append(signal)
    
    return filtered_signals[:limit]


def _calculate_phase_statistics(market: str) -> Dict:
    """计算趋势阶段统计（简化实现）"""
    # 这里应该实现真实的统计逻辑
    return {
        "market_scope": market,
        "total_stocks": 1000,
        "phase_distribution": {
            "accumulation": {"count": 350, "percentage": 35.0},
            "public_participation": {"count": 450, "percentage": 45.0},
            "panic": {"count": 200, "percentage": 20.0}
        },
        "trend_distribution": {
            "upward": {"count": 400, "percentage": 40.0},
            "downward": {"count": 300, "percentage": 30.0},
            "sideways": {"count": 300, "percentage": 30.0}
        },
        "confidence_distribution": {
            "high_confidence": {"count": 250, "percentage": 25.0, "threshold": ">= 80"},
            "medium_confidence": {"count": 500, "percentage": 50.0, "threshold": "60-80"},
            "low_confidence": {"count": 250, "percentage": 25.0, "threshold": "< 60"}
        },
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def _get_enhanced_analysis(stock_code: str, start_datetime: datetime, end_datetime: datetime) -> Dict:
    """获取增强的道氏理论分析结果"""
    try:
        # 初始化增强分析器
        analyzer = DowRulesAnalyzer()
        
        # 执行增强分析
        result = analyzer.analyze_with_factors(
            ts_code=stock_code,
            start_date=start_datetime.strftime('%Y-%m-%d'),
            end_date=end_datetime.strftime('%Y-%m-%d')
        )
        
        # 格式化增强分析结果
        enhanced_data = {
            "enhanced_trend": result.get('enhanced_trend', {}),
            "rule_123_analysis": result.get('rule_123_analysis', {}),
            "rule_2b_analysis": result.get('rule_2b_analysis', {}),
            "macd_signals": result.get('macd_signals', {}),
            "comprehensive_score": result.get('comprehensive_score', {}),
            "final_recommendation": result.get('final_recommendation', {})
        }
        
        return enhanced_data
        
    except Exception as e:
        logger.error(f"获取增强分析失败: {e}")
        return None