"""相对估值分析API路由"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from analysis.relative_valuation.core.relative_valuation_analyzer import RelativeValuationAnalyzer
from analysis.relative_valuation.core.industry_comparator import IndustryComparator
from analysis.relative_valuation.core.historical_analyzer import HistoricalAnalyzer
from analysis.relative_valuation.core.valuation_calculator import ValuationCalculator
from analysis.relative_valuation.core.dynamic_valuation_analyzer import DynamicValuationAnalyzer
from api.global_db import db_handler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/relative-valuation", tags=["相对估值分析"])

# 初始化分析器
valuation_analyzer = RelativeValuationAnalyzer()
industry_comparator = IndustryComparator()
historical_analyzer = HistoricalAnalyzer()
valuation_calculator = ValuationCalculator()
dynamic_valuation_analyzer = DynamicValuationAnalyzer()


@router.get("/analyze/{ts_code}")
async def analyze_stock_valuation(
    ts_code: str,
    end_date: Optional[str] = Query(None, description="截止日期，格式YYYYMMDD")
) -> Dict[str, Any]:
    """分析个股相对估值
    
    Args:
        ts_code: 股票代码
        end_date: 截止日期
        
    Returns:
        相对估值分析结果
    """
    try:
        # 获取静态估值分析结果
        result = valuation_analyzer.analyze_stock_valuation(ts_code, end_date)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"无法分析股票 {ts_code} 的相对估值")
        
        # 获取动态估值分析结果
        dynamic_result = dynamic_valuation_analyzer.analyze_comprehensive_valuation(ts_code, end_date)
        
        # 构建返回结果，包含静态和动态估值
        response_data = {
            "code": 200,
            "message": "分析成功",
            "data": {
                "ts_code": result.ts_code,
                "stock_name": result.stock_name,
                "industry": result.industry,
                "analysis_date": result.analysis_date,
                "current_metrics": {
                    "pe_ratio": result.current_metrics.pe_ratio,
                    "pb_ratio": result.current_metrics.pb_ratio,
                    "ps_ratio": result.current_metrics.ps_ratio,
                    "pcf_ratio": result.current_metrics.pcf_ratio,
                    "market_cap": result.current_metrics.market_cap,
                    "end_date": result.current_metrics.end_date
                },
                "industry_comparison": {
                    "industry": result.industry_comparison.industry,
                    "pe_percentile": result.industry_comparison.industry_pe_percentile,
                    "pb_percentile": result.industry_comparison.industry_pb_percentile,
                    "ps_percentile": result.industry_comparison.industry_ps_percentile,
                    "pe_median": result.industry_comparison.industry_pe_median,
                    "pb_median": result.industry_comparison.industry_pb_median,
                    "ps_median": result.industry_comparison.industry_ps_median,
                    "sample_count": result.industry_comparison.industry_sample_count,
                    "pe_rating": result.industry_comparison.pe_rating,
                    "pb_rating": result.industry_comparison.pb_rating,
                    "ps_rating": result.industry_comparison.ps_rating,
                    "overall_rating": result.industry_comparison.overall_rating
                },
                "historical_analysis": {
                    "pe_percentile_1y": result.historical_analysis.pe_percentile_1y,
                    "pe_percentile_3y": result.historical_analysis.pe_percentile_3y,
                    "pe_percentile_5y": result.historical_analysis.pe_percentile_5y,
                    "pb_percentile_1y": result.historical_analysis.pb_percentile_1y,
                    "pb_percentile_3y": result.historical_analysis.pb_percentile_3y,
                    "pb_percentile_5y": result.historical_analysis.pb_percentile_5y,
                    "ps_percentile_1y": result.historical_analysis.ps_percentile_1y,
                    "ps_percentile_3y": result.historical_analysis.ps_percentile_3y,
                    "ps_percentile_5y": result.historical_analysis.ps_percentile_5y,
                    "rating_1y": result.historical_analysis.historical_rating_1y,
                    "rating_3y": result.historical_analysis.historical_rating_3y,
                    "rating_5y": result.historical_analysis.historical_rating_5y
                },
                "overall_rating": result.overall_rating,
                "rating_score": result.rating_score,
                "investment_advice": result.investment_advice,
                "risk_warnings": result.risk_warnings,
                "analysis_summary": result.analysis_summary
            }
        }
        
        # 如果动态估值分析成功，添加动态估值数据
        if dynamic_result:
            response_data["data"]["dynamic_valuation"] = {
                "growth_metrics": {
                    "revenue_growth_1y": dynamic_result.growth_metrics.revenue_growth_1y,
                    "revenue_growth_3y": dynamic_result.growth_metrics.revenue_growth_3y,
                    "revenue_growth_5y": dynamic_result.growth_metrics.revenue_growth_5y,
                    "profit_growth_1y": dynamic_result.growth_metrics.profit_growth_1y,
                    "profit_growth_3y": dynamic_result.growth_metrics.profit_growth_3y,
                    "profit_growth_5y": dynamic_result.growth_metrics.profit_growth_5y,
                    "growth_sustainability_score": dynamic_result.growth_metrics.growth_sustainability_score,
                    "growth_trend": dynamic_result.growth_metrics.growth_trend,
                    "revenue_growth_stability": dynamic_result.growth_metrics.revenue_growth_stability,
                    "profit_growth_stability": dynamic_result.growth_metrics.profit_growth_stability
                },
                "profitability_metrics": {
                    "roe": dynamic_result.profitability_metrics.roe,
                    "roa": dynamic_result.profitability_metrics.roa,
                    "roic": dynamic_result.profitability_metrics.roic,
                    "gross_margin": dynamic_result.profitability_metrics.gross_margin,
                    "net_margin": dynamic_result.profitability_metrics.net_margin,
                    "operating_margin": dynamic_result.profitability_metrics.operating_margin,
                    "cash_conversion_ratio": dynamic_result.profitability_metrics.cash_conversion_ratio,
                    "profitability_score": dynamic_result.profitability_metrics.profitability_score,
                    "quality_score": dynamic_result.profitability_metrics.quality_score,
                    "roe_trend": dynamic_result.profitability_metrics.roe_trend,
                    "margin_trend": dynamic_result.profitability_metrics.margin_trend
                },
                "dynamic_metrics": {
                    "peg_1y": dynamic_result.dynamic_valuation.peg_1y,
                    "peg_3y": dynamic_result.dynamic_valuation.peg_3y,
                    "pe_to_growth": dynamic_result.dynamic_valuation.pe_to_growth,
                    "forward_pe": dynamic_result.dynamic_valuation.forward_pe,
                    "adjusted_pe": dynamic_result.dynamic_valuation.adjusted_pe,
                    "adjusted_pb": dynamic_result.dynamic_valuation.adjusted_pb,
                    "peg_rating": dynamic_result.dynamic_valuation.peg_rating,
                    "growth_adjusted_rating": dynamic_result.dynamic_valuation.growth_adjusted_rating
                },
                "valuation_forecast": {
                    "revenue_forecast_1y": dynamic_result.valuation_forecast.revenue_forecast_1y,
                    "profit_forecast_1y": dynamic_result.valuation_forecast.profit_forecast_1y,
                    "target_pe": dynamic_result.valuation_forecast.target_pe,
                    "target_price": dynamic_result.valuation_forecast.target_price,
                    "bull_case_price": dynamic_result.valuation_forecast.bull_case_price,
                    "bear_case_price": dynamic_result.valuation_forecast.bear_case_price,
                    "base_case_price": dynamic_result.valuation_forecast.base_case_price
                },
                "comprehensive_rating": {
                    "static_rating": dynamic_result.static_rating,
                    "dynamic_rating": dynamic_result.dynamic_rating,
                    "comprehensive_rating": dynamic_result.comprehensive_rating,
                    "static_score": dynamic_result.static_score,
                    "growth_score": dynamic_result.growth_score,
                    "quality_score": dynamic_result.quality_score,
                    "comprehensive_score": dynamic_result.comprehensive_score
                },
                "investment_recommendation": {
                    "investment_action": dynamic_result.investment_action,
                    "confidence_level": dynamic_result.confidence_level,
                    "time_horizon": dynamic_result.time_horizon,
                    "key_risks": dynamic_result.key_risks,
                    "catalysts": dynamic_result.catalysts,
                    "recommendation_rationale": dynamic_result.recommendation_rationale
                }
            }
        
        return response_data
        
    except Exception as e:
        logger.error(f"相对估值分析API错误: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/trend/{ts_code}")
async def get_valuation_trend(
    ts_code: str,
    days: int = Query(252, description="分析天数，默认252个交易日")
) -> Dict[str, Any]:
    """获取估值趋势分析
    
    Args:
        ts_code: 股票代码
        days: 分析天数
        
    Returns:
        估值趋势分析结果
    """
    try:
        trend = valuation_analyzer.get_valuation_trend(ts_code, days)
        
        if not trend:
            raise HTTPException(status_code=404, detail=f"无法获取股票 {ts_code} 的估值趋势")
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "ts_code": trend.ts_code,
                "pe_trend": {
                    "direction": trend.pe_trend,
                    "strength": trend.pe_trend_strength,
                    "duration": trend.pe_trend_duration
                },
                "pb_trend": {
                    "direction": trend.pb_trend,
                    "strength": trend.pb_trend_strength,
                    "duration": trend.pb_trend_duration
                },
                "ps_trend": {
                    "direction": trend.ps_trend,
                    "strength": trend.ps_trend_strength,
                    "duration": trend.ps_trend_duration
                }
            }
        }
        
    except Exception as e:
        logger.error(f"估值趋势分析API错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/batch-analyze")
async def batch_analyze_stocks(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """批量分析多只股票的相对估值
    
    Args:
        request: 请求参数 {"ts_codes": ["000001.SZ", "000002.SZ"], "end_date": "20240331"}
        
    Returns:
        批量分析结果
    """
    try:
        ts_codes = request.get("ts_codes", [])
        end_date = request.get("end_date")
        
        if not ts_codes:
            raise HTTPException(status_code=400, detail="股票代码列表不能为空")
        
        if len(ts_codes) > 50:  # 限制批量分析数量
            raise HTTPException(status_code=400, detail="批量分析股票数量不能超过50只")
        
        results = valuation_analyzer.batch_analyze_stocks(ts_codes, end_date)
        
        # 格式化返回结果
        formatted_results = {}
        for ts_code, result in results.items():
            if result:
                formatted_results[ts_code] = {
                    "stock_name": result.stock_name,
                    "industry": result.industry,
                    "overall_rating": result.overall_rating,
                    "rating_score": result.rating_score,
                    "investment_advice": result.investment_advice,
                    "current_pe": result.current_metrics.pe_ratio,
                    "current_pb": result.current_metrics.pb_ratio,
                    "industry_pe_percentile": result.industry_comparison.industry_pe_percentile,
                    "historical_pe_percentile_3y": result.historical_analysis.pe_percentile_3y
                }
        
        return {
            "code": 200,
            "message": "批量分析成功",
            "data": {
                "total_count": len(ts_codes),
                "success_count": len(formatted_results),
                "results": formatted_results
            }
        }
        
    except Exception as e:
        logger.error(f"批量估值分析API错误: {e}")
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")


@router.get("/industry-comparison/{ts_code}")
async def get_industry_comparison(
    ts_code: str,
    end_date: Optional[str] = Query(None, description="截止日期，格式YYYYMMDD")
) -> Dict[str, Any]:
    """获取行业对比分析
    
    Args:
        ts_code: 股票代码
        end_date: 截止日期
        
    Returns:
        行业对比分析结果
    """
    try:
        comparison = industry_comparator.compare_with_industry(ts_code, end_date)
        
        if not comparison:
            raise HTTPException(status_code=404, detail=f"无法进行股票 {ts_code} 的行业对比分析")
        
        return {
            "code": 200,
            "message": "分析成功",
            "data": {
                "ts_code": comparison.ts_code,
                "industry": comparison.industry,
                "end_date": comparison.end_date,
                "stock_metrics": {
                    "pe_ratio": comparison.stock_metrics.pe_ratio,
                    "pb_ratio": comparison.stock_metrics.pb_ratio,
                    "ps_ratio": comparison.stock_metrics.ps_ratio
                },
                "industry_stats": {
                    "pe_median": comparison.industry_pe_median,
                    "pe_mean": comparison.industry_pe_mean,
                    "pb_median": comparison.industry_pb_median,
                    "pb_mean": comparison.industry_pb_mean,
                    "ps_median": comparison.industry_ps_median,
                    "ps_mean": comparison.industry_ps_mean,
                    "sample_count": comparison.industry_sample_count
                },
                "percentiles": {
                    "pe_percentile": comparison.industry_pe_percentile,
                    "pb_percentile": comparison.industry_pb_percentile,
                    "ps_percentile": comparison.industry_ps_percentile
                },
                "ratings": {
                    "pe_rating": comparison.pe_rating,
                    "pb_rating": comparison.pb_rating,
                    "ps_rating": comparison.ps_rating,
                    "overall_rating": comparison.overall_rating
                }
            }
        }
        
    except Exception as e:
        logger.error(f"行业对比分析API错误: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/historical-analysis/{ts_code}")
async def get_historical_analysis(
    ts_code: str,
    end_date: Optional[str] = Query(None, description="截止日期，格式YYYYMMDD")
) -> Dict[str, Any]:
    """获取历史估值分析
    
    Args:
        ts_code: 股票代码
        end_date: 截止日期
        
    Returns:
        历史估值分析结果
    """
    try:
        analysis = historical_analyzer.analyze_historical_valuation(ts_code, end_date)
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"无法进行股票 {ts_code} 的历史估值分析")
        
        return {
            "code": 200,
            "message": "分析成功",
            "data": {
                "ts_code": analysis.ts_code,
                "historical_data": {
                    "pe_data": analysis.historical_pe[-20:] if analysis.historical_pe else [],  # 返回最近20个数据点
                    "pb_data": analysis.historical_pb[-20:] if analysis.historical_pb else [],
                    "ps_data": analysis.historical_ps[-20:] if analysis.historical_ps else []
                },
                "percentiles": {
                    "pe_1y": analysis.pe_percentile_1y,
                    "pe_3y": analysis.pe_percentile_3y,
                    "pe_5y": analysis.pe_percentile_5y,
                    "pb_1y": analysis.pb_percentile_1y,
                    "pb_3y": analysis.pb_percentile_3y,
                    "pb_5y": analysis.pb_percentile_5y,
                    "ps_1y": analysis.ps_percentile_1y,
                    "ps_3y": analysis.ps_percentile_3y,
                    "ps_5y": analysis.ps_percentile_5y
                },
                "ratings": {
                    "rating_1y": analysis.historical_rating_1y,
                    "rating_3y": analysis.historical_rating_3y,
                    "rating_5y": analysis.historical_rating_5y
                }
            }
        }
        
    except Exception as e:
        logger.error(f"历史估值分析API错误: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/metrics/{ts_code}")
async def get_valuation_metrics(
    ts_code: str,
    end_date: Optional[str] = Query(None, description="截止日期，格式YYYYMMDD")
) -> Dict[str, Any]:
    """获取估值指标
    
    Args:
        ts_code: 股票代码
        end_date: 截止日期
        
    Returns:
        估值指标数据
    """
    try:
        metrics = valuation_calculator.calculate_valuation_metrics(ts_code, end_date)
        
        if not metrics:
            raise HTTPException(status_code=404, detail=f"无法计算股票 {ts_code} 的估值指标")
        
        return {
            "code": 200,
            "message": "计算成功",
            "data": {
                "ts_code": metrics.ts_code,
                "end_date": metrics.end_date,
                "valuation_ratios": {
                    "pe_ratio": metrics.pe_ratio,
                    "pb_ratio": metrics.pb_ratio,
                    "ps_ratio": metrics.ps_ratio,
                    "pcf_ratio": metrics.pcf_ratio
                },
                "ttm_ratios": {
                    "pe_ttm": metrics.pe_ttm,
                    "pb_ttm": metrics.pb_ttm,
                    "ps_ttm": metrics.ps_ttm,
                    "pcf_ttm": metrics.pcf_ttm
                },
                "financial_data": {
                    "market_cap": metrics.market_cap,
                    "total_revenue": metrics.total_revenue,
                    "net_profit": metrics.net_profit,
                    "total_assets": metrics.total_assets,
                    "shareholders_equity": metrics.shareholders_equity,
                    "operating_cash_flow": metrics.operating_cash_flow
                }
            }
        }
        
    except Exception as e:
        logger.error(f"估值指标计算API错误: {e}")
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.get("/industry-top/{industry}")
async def get_industry_top_stocks(
    industry: str,
    metric: str = Query("pe_ratio", description="排序指标: pe_ratio, pb_ratio, ps_ratio"),
    limit: int = Query(10, description="返回数量"),
    end_date: Optional[str] = Query(None, description="截止日期，格式YYYYMMDD")
) -> Dict[str, Any]:
    """获取行业内估值排名靠前的股票
    
    Args:
        industry: 行业名称
        metric: 排序指标
        limit: 返回数量
        end_date: 截止日期
        
    Returns:
        行业排名结果
    """
    try:
        if metric not in ['pe_ratio', 'pb_ratio', 'ps_ratio']:
            raise HTTPException(status_code=400, detail="排序指标必须是 pe_ratio, pb_ratio 或 ps_ratio")
        
        if limit > 50:
            raise HTTPException(status_code=400, detail="返回数量不能超过50")
        
        top_stocks = industry_comparator.get_industry_top_stocks(
            industry, metric, limit, end_date
        )
        
        if not top_stocks:
            raise HTTPException(status_code=404, detail=f"未找到行业 {industry} 的股票数据")
        
        # 格式化返回结果
        formatted_results = []
        for i, stock in enumerate(top_stocks, 1):
            formatted_results.append({
                "rank": i,
                "ts_code": stock['ts_code'],
                "metric_value": stock['metric_value'],
                "pe_ratio": stock['metrics'].pe_ratio,
                "pb_ratio": stock['metrics'].pb_ratio,
                "ps_ratio": stock['metrics'].ps_ratio,
                "market_cap": stock['metrics'].market_cap
            })
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "industry": industry,
                "metric": metric,
                "total_count": len(formatted_results),
                "stocks": formatted_results
            }
        }
        
    except Exception as e:
        logger.error(f"行业排名API错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/dynamic-valuation/{ts_code}")
async def analyze_dynamic_valuation(
    ts_code: str,
    end_date: Optional[str] = Query(None, description="截止日期，格式YYYYMMDD")
) -> Dict[str, Any]:
    """动态估值分析API
    
    Args:
        ts_code: 股票代码
        end_date: 截止日期
        
    Returns:
        动态估值分析结果，包含成长性、盈利质量、PEG比率等
    """
    try:
        result = dynamic_valuation_analyzer.analyze_comprehensive_valuation(ts_code, end_date)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"无法分析股票 {ts_code} 的动态估值")
        
        return {
            "code": 200,
            "message": "动态估值分析成功",
            "data": {
                "basic_info": {
                    "ts_code": result.ts_code,
                    "stock_name": result.stock_name,
                    "industry": result.industry,
                    "analysis_date": result.analysis_date
                },
                "static_valuation": {
                    "pe_ratio": result.static_valuation.pe_ratio,
                    "pb_ratio": result.static_valuation.pb_ratio,
                    "ps_ratio": result.static_valuation.ps_ratio,
                    "pcf_ratio": result.static_valuation.pcf_ratio,
                    "market_cap": result.static_valuation.market_cap
                },
                "growth_metrics": {
                    "revenue_growth": {
                        "growth_1y": result.growth_metrics.revenue_growth_1y,
                        "growth_3y": result.growth_metrics.revenue_growth_3y,
                        "growth_5y": result.growth_metrics.revenue_growth_5y,
                        "growth_ttm": result.growth_metrics.revenue_growth_ttm,
                        "stability": result.growth_metrics.revenue_growth_stability
                    },
                    "profit_growth": {
                        "growth_1y": result.growth_metrics.profit_growth_1y,
                        "growth_3y": result.growth_metrics.profit_growth_3y,
                        "growth_5y": result.growth_metrics.profit_growth_5y,
                        "growth_ttm": result.growth_metrics.profit_growth_ttm,
                        "stability": result.growth_metrics.profit_growth_stability
                    },
                    "cashflow_growth": {
                        "growth_1y": result.growth_metrics.cashflow_growth_1y,
                        "growth_3y": result.growth_metrics.cashflow_growth_3y,
                        "growth_5y": result.growth_metrics.cashflow_growth_5y
                    },
                    "growth_sustainability_score": result.growth_metrics.growth_sustainability_score,
                    "growth_trend": result.growth_metrics.growth_trend
                },
                "profitability_metrics": {
                    "profitability_ratios": {
                        "roe": result.profitability_metrics.roe,
                        "roa": result.profitability_metrics.roa,
                        "roic": result.profitability_metrics.roic
                    },
                    "margin_analysis": {
                        "gross_margin": result.profitability_metrics.gross_margin,
                        "net_margin": result.profitability_metrics.net_margin,
                        "operating_margin": result.profitability_metrics.operating_margin,
                        "ebitda_margin": result.profitability_metrics.ebitda_margin
                    },
                    "quality_metrics": {
                        "cash_conversion_ratio": result.profitability_metrics.cash_conversion_ratio,
                        "roe_trend": result.profitability_metrics.roe_trend,
                        "margin_trend": result.profitability_metrics.margin_trend
                    },
                    "industry_comparison": {
                        "roe_vs_industry": result.profitability_metrics.roe_vs_industry,
                        "margin_vs_industry": result.profitability_metrics.margin_vs_industry
                    },
                    "scores": {
                        "profitability_score": result.profitability_metrics.profitability_score,
                        "quality_score": result.profitability_metrics.quality_score
                    }
                },
                "dynamic_valuation_metrics": {
                    "peg_ratios": {
                        "peg_1y": result.dynamic_valuation.peg_1y,
                        "peg_3y": result.dynamic_valuation.peg_3y,
                        "peg_forecast": result.dynamic_valuation.peg_forecast,
                        "peg_rating": result.dynamic_valuation.peg_rating
                    },
                    "dynamic_pe": {
                        "pe_to_growth": result.dynamic_valuation.pe_to_growth,
                        "forward_pe": result.dynamic_valuation.forward_pe,
                        "adjusted_pe": result.dynamic_valuation.adjusted_pe
                    },
                    "cash_flow_metrics": {
                        "fcf_yield": result.dynamic_valuation.fcf_yield,
                        "ev_ebitda": result.dynamic_valuation.ev_ebitda
                    },
                    "adjusted_ratios": {
                        "adjusted_pb": result.dynamic_valuation.adjusted_pb,
                        "growth_adjusted_rating": result.dynamic_valuation.growth_adjusted_rating
                    }
                },
                "valuation_forecast": {
                    "growth_forecast": {
                        "revenue_forecast_1y": result.valuation_forecast.revenue_forecast_1y,
                        "revenue_forecast_2y": result.valuation_forecast.revenue_forecast_2y,
                        "profit_forecast_1y": result.valuation_forecast.profit_forecast_1y,
                        "profit_forecast_2y": result.valuation_forecast.profit_forecast_2y
                    },
                    "price_targets": {
                        "target_pe": result.valuation_forecast.target_pe,
                        "target_price": result.valuation_forecast.target_price,
                        "bull_case_price": result.valuation_forecast.bull_case_price,
                        "bear_case_price": result.valuation_forecast.bear_case_price,
                        "base_case_price": result.valuation_forecast.base_case_price
                    },
                    "risk_metrics": {
                        "beta": result.valuation_forecast.beta,
                        "volatility": result.valuation_forecast.volatility,
                        "downside_risk": result.valuation_forecast.downside_risk
                    }
                },
                "comprehensive_rating": {
                    "ratings": {
                        "static_rating": result.static_rating,
                        "dynamic_rating": result.dynamic_rating,
                        "comprehensive_rating": result.comprehensive_rating
                    },
                    "scores": {
                        "static_score": result.static_score,
                        "growth_score": result.growth_score,
                        "quality_score": result.quality_score,
                        "comprehensive_score": result.comprehensive_score
                    }
                },
                "investment_recommendation": {
                    "recommendation": {
                        "investment_action": result.investment_action,
                        "confidence_level": result.confidence_level,
                        "time_horizon": result.time_horizon
                    },
                    "analysis": {
                        "key_risks": result.key_risks,
                        "catalysts": result.catalysts,
                        "recommendation_rationale": result.recommendation_rationale
                    },
                    "summary": {
                        "analysis_summary": result.analysis_summary
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"动态估值分析API错误: {e}")
        raise HTTPException(status_code=500, detail=f"动态估值分析失败: {str(e)}")