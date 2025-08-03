"""动态估值分析器核心模块"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, median
import math

from analysis.relative_valuation.models.dynamic_valuation_models import (
    GrowthMetrics, ProfitabilityMetrics, DynamicValuationMetrics,
    ValuationForecast, ComprehensiveDynamicValuation, IndustryGrowthBenchmark
)
from analysis.relative_valuation.core.valuation_calculator import ValuationCalculator
from api.global_db import db_handler

logger = logging.getLogger(__name__)


class DynamicValuationAnalyzer:
    """动态估值分析器
    
    提供基于成长性、盈利质量的动态估值分析
    """
    
    def __init__(self):
        """初始化动态估值分析器"""
        self.db_handler = db_handler
        self.valuation_calculator = ValuationCalculator()
        
    def analyze_comprehensive_valuation(self, ts_code: str, end_date: str = None) -> Optional[ComprehensiveDynamicValuation]:
        """综合动态估值分析
        
        Args:
            ts_code: 股票代码
            end_date: 截止日期
            
        Returns:
            ComprehensiveDynamicValuation: 综合动态估值结果
        """
        try:
            # 获取股票基本信息
            stock_info = self._get_stock_info(ts_code)
            if not stock_info:
                logger.warning(f"无法获取股票 {ts_code} 的基本信息")
                return None
            
            # 计算静态估值
            static_valuation = self.valuation_calculator.calculate_valuation_metrics(ts_code, end_date)
            if not static_valuation:
                logger.warning(f"无法计算股票 {ts_code} 的静态估值")
                return None
            
            # 计算成长性指标
            growth_metrics = self.calculate_growth_metrics(ts_code, end_date)
            if not growth_metrics:
                logger.warning(f"无法计算股票 {ts_code} 的成长性指标")
                return None
            
            # 计算盈利能力指标
            profitability_metrics = self.calculate_profitability_metrics(ts_code, end_date)
            if not profitability_metrics:
                logger.warning(f"无法计算股票 {ts_code} 的盈利能力指标")
                return None
            
            # 计算动态估值指标
            dynamic_valuation = self.calculate_dynamic_valuation(ts_code, static_valuation, growth_metrics)
            if not dynamic_valuation:
                logger.warning(f"无法计算股票 {ts_code} 的动态估值")
                return None
            
            # 生成估值预测
            valuation_forecast = self.generate_valuation_forecast(ts_code, growth_metrics, profitability_metrics, static_valuation)
            
            # 生成综合评级
            static_rating, static_score = self._generate_static_rating(static_valuation)
            dynamic_rating, comprehensive_score = self._generate_dynamic_rating(
                growth_metrics, profitability_metrics, dynamic_valuation
            )
            comprehensive_rating = self._generate_comprehensive_rating(static_score, comprehensive_score)
            
            # 生成投资建议
            investment_action, confidence_level, time_horizon = self._generate_investment_recommendation(
                static_score, comprehensive_score, dynamic_valuation
            )
            
            # 生成风险和催化因素
            key_risks = self._identify_key_risks(growth_metrics, profitability_metrics, dynamic_valuation)
            catalysts = self._identify_catalysts(growth_metrics, profitability_metrics)
            
            # 生成分析摘要
            analysis_summary = self._generate_analysis_summary(
                stock_info, static_valuation, growth_metrics, dynamic_valuation, comprehensive_rating
            )
            recommendation_rationale = self._generate_recommendation_rationale(
                investment_action, dynamic_valuation, growth_metrics
            )
            
            return ComprehensiveDynamicValuation(
                ts_code=ts_code,
                stock_name=stock_info.get('name', ''),
                industry=stock_info.get('industry', ''),
                analysis_date=end_date or datetime.now().strftime('%Y%m%d'),
                static_valuation=static_valuation,
                growth_metrics=growth_metrics,
                profitability_metrics=profitability_metrics,
                dynamic_valuation=dynamic_valuation,
                valuation_forecast=valuation_forecast,
                static_rating=static_rating,
                dynamic_rating=dynamic_rating,
                comprehensive_rating=comprehensive_rating,
                static_score=static_score,
                growth_score=growth_metrics.growth_sustainability_score or 0,
                quality_score=profitability_metrics.quality_score or 0,
                comprehensive_score=comprehensive_score,
                investment_action=investment_action,
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                key_risks=key_risks,
                catalysts=catalysts,
                analysis_summary=analysis_summary,
                recommendation_rationale=recommendation_rationale
            )
            
        except Exception as e:
            logger.error(f"综合动态估值分析失败: {e}")
            return None
    
    def calculate_growth_metrics(self, ts_code: str, end_date: str = None) -> Optional[GrowthMetrics]:
        """计算成长性指标"""
        try:
            # 获取历史财务数据
            financial_history = self._get_financial_history(ts_code, end_date, years=5)
            if len(financial_history) < 2:
                logger.warning(f"股票 {ts_code} 的历史数据不足")
                return None
            
            # 计算各类增长率
            revenue_growth = self._calculate_growth_rates(financial_history, 'revenue')
            profit_growth = self._calculate_growth_rates(financial_history, 'net_income')
            cashflow_growth = self._calculate_growth_rates(financial_history, 'operating_cashflow')
            
            # 计算增长稳定性
            revenue_stability = self._calculate_growth_stability(revenue_growth)
            profit_stability = self._calculate_growth_stability(profit_growth)
            
            # 计算成长可持续性评分
            sustainability_score = self._calculate_growth_sustainability(
                revenue_growth, profit_growth, revenue_stability, profit_stability
            )
            
            # 判断成长趋势
            growth_trend = self._determine_growth_trend(revenue_growth, profit_growth)
            
            return GrowthMetrics(
                ts_code=ts_code,
                revenue_growth_1y=revenue_growth.get('1y'),
                revenue_growth_3y=revenue_growth.get('3y'),
                revenue_growth_5y=revenue_growth.get('5y'),
                revenue_growth_ttm=revenue_growth.get('ttm'),
                profit_growth_1y=profit_growth.get('1y'),
                profit_growth_3y=profit_growth.get('3y'),
                profit_growth_5y=profit_growth.get('5y'),
                profit_growth_ttm=profit_growth.get('ttm'),
                cashflow_growth_1y=cashflow_growth.get('1y'),
                cashflow_growth_3y=cashflow_growth.get('3y'),
                cashflow_growth_5y=cashflow_growth.get('5y'),
                revenue_growth_stability=revenue_stability,
                profit_growth_stability=profit_stability,
                growth_sustainability_score=sustainability_score,
                growth_trend=growth_trend
            )
            
        except Exception as e:
            logger.error(f"计算成长性指标失败: {e}")
            return None
    
    def calculate_profitability_metrics(self, ts_code: str, end_date: str = None) -> Optional[ProfitabilityMetrics]:
        """计算盈利能力指标"""
        try:
            # 获取最新财务数据
            latest_data = self._get_latest_financial_data(ts_code, end_date)
            if not latest_data:
                return None
            
            # 获取历史数据用于趋势分析
            historical_data = self._get_financial_history(ts_code, end_date, years=3)
            
            # 计算基础盈利指标
            roe = self._calculate_roe(latest_data)
            roa = self._calculate_roa(latest_data)
            roic = self._calculate_roic(latest_data)
            gross_margin = self._calculate_gross_margin(latest_data)
            net_margin = self._calculate_net_margin(latest_data)
            operating_margin = self._calculate_operating_margin(latest_data)
            ebitda_margin = self._calculate_ebitda_margin(latest_data)
            cash_conversion = self._calculate_cash_conversion_ratio(latest_data)
            
            # 计算趋势
            roe_trend = self._calculate_roe_trend(historical_data)
            margin_trend = self._calculate_margin_trend(historical_data)
            
            # 行业对比
            industry = self.valuation_calculator.get_stock_industry(ts_code)
            roe_vs_industry = self._compare_roe_with_industry(ts_code, roe, industry)
            margin_vs_industry = self._compare_margin_with_industry(ts_code, net_margin, industry)
            
            # 综合评分
            profitability_score = self._calculate_profitability_score(roe, roa, gross_margin, net_margin)
            quality_score = self._calculate_quality_score(cash_conversion, operating_margin, roe_trend)
            
            return ProfitabilityMetrics(
                ts_code=ts_code,
                roe=roe,
                roa=roa,
                roic=roic,
                gross_margin=gross_margin,
                net_margin=net_margin,
                operating_margin=operating_margin,
                ebitda_margin=ebitda_margin,
                cash_conversion_ratio=cash_conversion,
                roe_trend=roe_trend,
                margin_trend=margin_trend,
                roe_vs_industry=roe_vs_industry,
                margin_vs_industry=margin_vs_industry,
                profitability_score=profitability_score,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"计算盈利能力指标失败: {e}")
            return None
    
    def calculate_dynamic_valuation(self, ts_code: str, static_valuation, growth_metrics: GrowthMetrics) -> Optional[DynamicValuationMetrics]:
        """计算动态估值指标"""
        try:
            # 计算PEG比率
            peg_1y = self._calculate_peg(static_valuation.pe_ratio, growth_metrics.profit_growth_1y)
            peg_3y = self._calculate_peg(static_valuation.pe_ratio, growth_metrics.profit_growth_3y)
            
            # 计算其他动态指标
            pe_to_growth = self._calculate_pe_to_growth_ratio(static_valuation.pe_ratio, growth_metrics.profit_growth_ttm)
            forward_pe = self._calculate_forward_pe(static_valuation.pe_ratio, growth_metrics.profit_growth_1y)
            
            # 现金流相关指标
            fcf_yield = self._calculate_fcf_yield(ts_code)
            ev_ebitda = self._calculate_ev_ebitda(ts_code)
            
            # 调整后估值
            adjusted_pe = self._calculate_growth_adjusted_pe(static_valuation.pe_ratio, growth_metrics)
            adjusted_pb = self._calculate_quality_adjusted_pb(static_valuation.pb_ratio, growth_metrics)
            
            # 评级
            peg_rating = self._generate_peg_rating(peg_1y, peg_3y)
            growth_adjusted_rating = self._generate_growth_adjusted_rating(adjusted_pe, adjusted_pb)
            
            return DynamicValuationMetrics(
                ts_code=ts_code,
                peg_1y=peg_1y,
                peg_3y=peg_3y,
                pe_to_growth=pe_to_growth,
                forward_pe=forward_pe,
                fcf_yield=fcf_yield,
                ev_ebitda=ev_ebitda,
                adjusted_pe=adjusted_pe,
                adjusted_pb=adjusted_pb,
                peg_rating=peg_rating,
                growth_adjusted_rating=growth_adjusted_rating
            )
            
        except Exception as e:
            logger.error(f"计算动态估值指标失败: {e}")
            return None
    
    def generate_valuation_forecast(self, ts_code: str, growth_metrics: GrowthMetrics, 
                                   profitability_metrics: ProfitabilityMetrics, static_valuation) -> Optional[ValuationForecast]:
        """生成估值预测"""
        try:
            # 基于历史增长率预测未来增长
            revenue_forecast_1y = self._forecast_revenue_growth(growth_metrics)
            profit_forecast_1y = self._forecast_profit_growth(growth_metrics, profitability_metrics)
            
            # 计算目标PE和价格
            target_pe = self._calculate_target_pe(growth_metrics, profitability_metrics)
            current_price = self._get_current_price(ts_code)
            target_price = self._calculate_target_price(current_price, static_valuation.pe_ratio, target_pe)
            
            # 风险调整
            beta = self._calculate_beta(ts_code)
            volatility = self._calculate_volatility(ts_code)
            
            # 情景分析
            bull_case = target_price * 1.2 if target_price else None
            bear_case = target_price * 0.8 if target_price else None
            
            return ValuationForecast(
                ts_code=ts_code,
                revenue_forecast_1y=revenue_forecast_1y,
                profit_forecast_1y=profit_forecast_1y,
                target_pe=target_pe,
                target_price=target_price,
                beta=beta,
                volatility=volatility,
                bull_case_price=bull_case,
                bear_case_price=bear_case,
                base_case_price=target_price
            )
            
        except Exception as e:
            logger.error(f"生成估值预测失败: {e}")
            return None
    
    # ========== 私有辅助方法 ==========
    
    def _get_stock_info(self, ts_code: str) -> Optional[Dict]:
        """获取股票基本信息"""
        try:
            stock_basic = list(self.db_handler.get_collection("infrastructure_stock_basic").find({
                "ts_code": ts_code
            }).limit(1))
            
            return stock_basic[0] if stock_basic else None
            
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            return None
    
    def _get_financial_history(self, ts_code: str, end_date: str = None, years: int = 5) -> List[Dict]:
        """获取历史财务数据"""
        try:
            query = {"ts_code": ts_code}
            if end_date:
                query["end_date"] = {"$lte": end_date}
            
            # 获取收入数据
            income_data = list(self.db_handler.get_collection("stock_income").find(
                query
            ).sort("end_date", -1).limit(years * 4))  # 获取季度数据
            
            # 获取现金流数据
            cashflow_data = list(self.db_handler.get_collection("stock_cash_flow").find(
                query
            ).sort("end_date", -1).limit(years * 4))
            
            # 合并数据
            financial_history = []
            for income in income_data:
                cashflow = next((cf for cf in cashflow_data if cf.get("end_date") == income.get("end_date")), {})
                financial_history.append({
                    "end_date": income.get("end_date"),
                    "revenue": income.get("revenue", 0),
                    "net_income": income.get("n_income", 0),
                    "operating_cashflow": cashflow.get("n_cashflow_act", 0)
                })
            
            return financial_history
            
        except Exception as e:
            logger.error(f"获取历史财务数据失败: {e}")
            return []
    
    def _get_latest_financial_data(self, ts_code: str, end_date: str = None) -> Optional[Dict]:
        """获取最新财务数据"""
        try:
            query = {"ts_code": ts_code}
            if end_date:
                query["end_date"] = {"$lte": end_date}
            
            # 获取最新的财务指标
            fina_indicator = list(self.db_handler.get_collection("stock_fina_indicator").find(
                query
            ).sort("end_date", -1).limit(1))
            
            if not fina_indicator:
                return None
            
            latest_end_date = fina_indicator[0]["end_date"]
            
            # 获取对应的收入数据
            income_data = list(self.db_handler.get_collection("stock_income").find({
                "ts_code": ts_code,
                "end_date": latest_end_date
            }).limit(1))
            
            # 获取资产负债表数据
            balance_data = list(self.db_handler.get_collection("stock_balance_sheet").find({
                "ts_code": ts_code,
                "end_date": latest_end_date
            }).limit(1))
            
            # 获取现金流数据
            cashflow_data = list(self.db_handler.get_collection("stock_cash_flow").find({
                "ts_code": ts_code,
                "end_date": latest_end_date
            }).limit(1))
            
            return {
                "fina_indicator": fina_indicator[0],
                "income": income_data[0] if income_data else {},
                "balance_sheet": balance_data[0] if balance_data else {},
                "cash_flow": cashflow_data[0] if cashflow_data else {}
            }
            
        except Exception as e:
            logger.error(f"获取最新财务数据失败: {e}")
            return None
    
    def _calculate_growth_rates(self, financial_history: List[Dict], field: str) -> Dict[str, float]:
        """计算增长率"""
        if len(financial_history) < 2:
            return {}
        
        growth_rates = {}
        
        try:
            # 按日期排序
            sorted_data = sorted(financial_history, key=lambda x: x["end_date"])
            values = [d.get(field, 0) for d in sorted_data if d.get(field) is not None and d.get(field) > 0]
            
            if len(values) < 2:
                return {}
            
            # 1年增长率
            if len(values) >= 5:  # 至少5个季度数据
                growth_rates['1y'] = ((values[-1] / values[-5]) ** 1 - 1) * 100 if values[-5] > 0 else None
            
            # 3年年化增长率
            if len(values) >= 13:  # 至少13个季度数据
                years = 3
                growth_rates['3y'] = ((values[-1] / values[-13]) ** (1/years) - 1) * 100 if values[-13] > 0 else None
            
            # 5年年化增长率
            if len(values) >= 21:  # 至少21个季度数据
                years = 5
                growth_rates['5y'] = ((values[-1] / values[-21]) ** (1/years) - 1) * 100 if values[-21] > 0 else None
            
            # TTM增长率（最近4个季度 vs 前4个季度）
            if len(values) >= 8:
                recent_ttm = sum(values[-4:])
                previous_ttm = sum(values[-8:-4])
                growth_rates['ttm'] = ((recent_ttm / previous_ttm) - 1) * 100 if previous_ttm > 0 else None
            
        except Exception as e:
            logger.error(f"计算{field}增长率失败: {e}")
        
        return growth_rates
    
    def _calculate_growth_stability(self, growth_rates: Dict[str, float]) -> Optional[float]:
        """计算增长稳定性（变异系数）"""
        try:
            rates = [v for v in growth_rates.values() if v is not None and not math.isnan(v)]
            if len(rates) < 2:
                return None
            
            mean_rate = mean(rates)
            if mean_rate == 0:
                return None
            
            variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
            std_dev = math.sqrt(variance)
            
            # 变异系数 = 标准差 / 均值，值越小越稳定
            cv = std_dev / abs(mean_rate)
            return cv
            
        except Exception as e:
            logger.error(f"计算增长稳定性失败: {e}")
            return None
    
    def _calculate_growth_sustainability(self, revenue_growth: Dict, profit_growth: Dict, 
                                       revenue_stability: float, profit_stability: float) -> float:
        """计算成长可持续性评分"""
        try:
            score = 0
            
            # 营收增长评分 (0-40分)
            rev_1y = revenue_growth.get('1y', 0) or 0
            if rev_1y > 20:
                score += 40
            elif rev_1y > 10:
                score += 30
            elif rev_1y > 5:
                score += 20
            elif rev_1y > 0:
                score += 10
            
            # 利润增长评分 (0-40分)
            profit_1y = profit_growth.get('1y', 0) or 0
            if profit_1y > 25:
                score += 40
            elif profit_1y > 15:
                score += 30
            elif profit_1y > 8:
                score += 20
            elif profit_1y > 0:
                score += 10
            
            # 增长稳定性评分 (0-20分)
            if revenue_stability and profit_stability:
                avg_stability = (revenue_stability + profit_stability) / 2
                if avg_stability < 0.3:  # 变异系数小于0.3认为很稳定
                    score += 20
                elif avg_stability < 0.5:
                    score += 15
                elif avg_stability < 0.8:
                    score += 10
                elif avg_stability < 1.0:
                    score += 5
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"计算成长可持续性评分失败: {e}")
            return 0
    
    def _determine_growth_trend(self, revenue_growth: Dict, profit_growth: Dict) -> str:
        """判断成长趋势"""
        try:
            rev_rates = [v for v in revenue_growth.values() if v is not None]
            profit_rates = [v for v in profit_growth.values() if v is not None]
            
            if not rev_rates or not profit_rates:
                return "数据不足"
            
            # 计算趋势
            rev_trend = self._calculate_trend(rev_rates)
            profit_trend = self._calculate_trend(profit_rates)
            
            if rev_trend > 0.1 and profit_trend > 0.1:
                return "加速增长"
            elif rev_trend < -0.1 and profit_trend < -0.1:
                return "增长放缓"
            elif abs(rev_trend) < 0.05 and abs(profit_trend) < 0.05:
                return "稳定增长"
            else:
                return "波动增长"
                
        except Exception as e:
            logger.error(f"判断成长趋势失败: {e}")
            return "未知"
    
    def _calculate_trend(self, values: List[float]) -> float:
        """计算数值序列的趋势斜率"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x = list(range(n))
        
        # 简单线性回归计算斜率
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0
    
    def _calculate_roe(self, financial_data: Dict) -> Optional[float]:
        """计算ROE"""
        try:
            fina = financial_data.get("fina_indicator", {})
            return fina.get("roe")
        except:
            return None
    
    def _calculate_roa(self, financial_data: Dict) -> Optional[float]:
        """计算ROA"""
        try:
            fina = financial_data.get("fina_indicator", {})
            return fina.get("roa")
        except:
            return None
    
    def _calculate_roic(self, financial_data: Dict) -> Optional[float]:
        """计算ROIC (投入资本回报率)"""
        try:
            income = financial_data.get("income", {})
            balance = financial_data.get("balance_sheet", {})
            
            net_income = income.get("n_income")
            total_assets = balance.get("total_assets")
            total_liab = balance.get("total_liab")
            
            if not all([net_income, total_assets, total_liab]):
                return None
            
            invested_capital = total_assets - total_liab
            return (net_income / invested_capital) * 100 if invested_capital > 0 else None
            
        except:
            return None
    
    def _calculate_gross_margin(self, financial_data: Dict) -> Optional[float]:
        """计算毛利率"""
        try:
            fina = financial_data.get("fina_indicator", {})
            return fina.get("grossprofit_margin")
        except:
            return None
    
    def _calculate_net_margin(self, financial_data: Dict) -> Optional[float]:
        """计算净利率"""
        try:
            fina = financial_data.get("fina_indicator", {})
            return fina.get("netprofit_margin")
        except:
            return None
    
    def _calculate_operating_margin(self, financial_data: Dict) -> Optional[float]:
        """计算营业利润率"""
        try:
            income = financial_data.get("income", {})
            revenue = income.get("revenue")
            operate_profit = income.get("operate_profit")
            
            if not all([revenue, operate_profit]) or revenue <= 0:
                return None
            
            return (operate_profit / revenue) * 100
            
        except:
            return None
    
    def _calculate_ebitda_margin(self, financial_data: Dict) -> Optional[float]:
        """计算EBITDA利润率"""
        try:
            # 简化计算：营业利润 + 折旧摊销
            income = financial_data.get("income", {})
            revenue = income.get("revenue")
            operate_profit = income.get("operate_profit")
            
            if not all([revenue, operate_profit]) or revenue <= 0:
                return None
            
            # 暂时用营业利润率近似
            return (operate_profit / revenue) * 100
            
        except:
            return None
    
    def _calculate_cash_conversion_ratio(self, financial_data: Dict) -> Optional[float]:
        """计算现金转换率"""
        try:
            income = financial_data.get("income", {})
            cashflow = financial_data.get("cash_flow", {})
            
            net_income = income.get("n_income")
            operating_cf = cashflow.get("n_cashflow_act")
            
            if not all([net_income, operating_cf]) or net_income <= 0:
                return None
            
            return (operating_cf / net_income) * 100
            
        except:
            return None
    
    def _calculate_roe_trend(self, historical_data: List[Dict]) -> str:
        """计算ROE趋势"""
        # 简化实现，实际需要从历史财务指标中计算
        return "稳定"
    
    def _calculate_margin_trend(self, historical_data: List[Dict]) -> str:
        """计算利润率趋势"""
        # 简化实现
        return "稳定"
    
    def _compare_roe_with_industry(self, ts_code: str, roe: float, industry: str) -> Optional[float]:
        """与行业ROE对比"""
        if not roe or not industry:
            return None
        # 简化实现，返回模拟百分位
        return 60.0
    
    def _compare_margin_with_industry(self, ts_code: str, margin: float, industry: str) -> Optional[float]:
        """与行业利润率对比"""
        if not margin or not industry:
            return None
        # 简化实现
        return 55.0
    
    def _calculate_profitability_score(self, roe: float, roa: float, gross_margin: float, net_margin: float) -> float:
        """计算盈利能力综合评分"""
        score = 0
        count = 0
        
        if roe is not None:
            if roe > 20:
                score += 25
            elif roe > 15:
                score += 20
            elif roe > 10:
                score += 15
            elif roe > 5:
                score += 10
            count += 1
        
        if roa is not None:
            if roa > 10:
                score += 25
            elif roa > 7:
                score += 20
            elif roa > 5:
                score += 15
            elif roa > 2:
                score += 10
            count += 1
        
        if gross_margin is not None:
            if gross_margin > 40:
                score += 25
            elif gross_margin > 30:
                score += 20
            elif gross_margin > 20:
                score += 15
            elif gross_margin > 10:
                score += 10
            count += 1
        
        if net_margin is not None:
            if net_margin > 20:
                score += 25
            elif net_margin > 15:
                score += 20
            elif net_margin > 10:
                score += 15
            elif net_margin > 5:
                score += 10
            count += 1
        
        return score / count if count > 0 else 0
    
    def _calculate_quality_score(self, cash_conversion: float, operating_margin: float, roe_trend: str) -> float:
        """计算盈利质量评分"""
        score = 0
        
        # 现金转换率评分
        if cash_conversion is not None:
            if cash_conversion > 100:
                score += 40
            elif cash_conversion > 80:
                score += 30
            elif cash_conversion > 60:
                score += 20
            elif cash_conversion > 40:
                score += 10
        
        # 营业利润率评分
        if operating_margin is not None:
            if operating_margin > 20:
                score += 30
            elif operating_margin > 15:
                score += 25
            elif operating_margin > 10:
                score += 20
            elif operating_margin > 5:
                score += 15
        
        # ROE趋势评分
        if roe_trend == "上升":
            score += 30
        elif roe_trend == "稳定":
            score += 20
        elif roe_trend == "下降":
            score += 10
        
        return min(score, 100)
    
    def _calculate_peg(self, pe_ratio: float, growth_rate: float) -> Optional[float]:
        """计算PEG比率"""
        if not pe_ratio or not growth_rate or growth_rate <= 0:
            return None
        
        return pe_ratio / growth_rate
    
    def _calculate_pe_to_growth_ratio(self, pe_ratio: float, growth_rate: float) -> Optional[float]:
        """计算PE与增长率比值"""
        return self._calculate_peg(pe_ratio, growth_rate)
    
    def _calculate_forward_pe(self, current_pe: float, growth_rate: float) -> Optional[float]:
        """计算前瞻PE"""
        if not current_pe or not growth_rate:
            return None
        
        # 简化计算：假设下一年增长后的PE
        return current_pe / (1 + growth_rate / 100)
    
    def _calculate_fcf_yield(self, ts_code: str) -> Optional[float]:
        """计算自由现金流收益率"""
        # 简化实现
        return None
    
    def _calculate_ev_ebitda(self, ts_code: str) -> Optional[float]:
        """计算EV/EBITDA"""
        # 简化实现
        return None
    
    def _calculate_growth_adjusted_pe(self, pe_ratio: float, growth_metrics: GrowthMetrics) -> Optional[float]:
        """计算成长调整后PE"""
        if not pe_ratio or not growth_metrics.profit_growth_1y:
            return None
        
        # 简化调整：基于增长率调整PE
        adjustment_factor = max(0.5, min(2.0, growth_metrics.profit_growth_1y / 15))
        return pe_ratio * adjustment_factor
    
    def _calculate_quality_adjusted_pb(self, pb_ratio: float, growth_metrics: GrowthMetrics) -> Optional[float]:
        """计算质量调整后PB"""
        if not pb_ratio:
            return None
        
        # 简化调整
        return pb_ratio
    
    def _generate_peg_rating(self, peg_1y: float, peg_3y: float) -> str:
        """生成PEG评级"""
        peg_values = [p for p in [peg_1y, peg_3y] if p is not None]
        if not peg_values:
            return "数据不足"
        
        avg_peg = mean(peg_values)
        
        if avg_peg < 0.5:
            return "严重低估"
        elif avg_peg < 1.0:
            return "低估"
        elif avg_peg < 1.5:
            return "合理"
        elif avg_peg < 2.0:
            return "偏高"
        else:
            return "高估"
    
    def _generate_growth_adjusted_rating(self, adjusted_pe: float, adjusted_pb: float) -> str:
        """生成成长调整评级"""
        # 简化实现
        return "合理"
    
    def _forecast_revenue_growth(self, growth_metrics: GrowthMetrics) -> Optional[float]:
        """预测营收增长率"""
        # 简化实现：基于历史增长率的加权平均
        growth_rates = [
            growth_metrics.revenue_growth_1y,
            growth_metrics.revenue_growth_3y,
            growth_metrics.revenue_growth_5y
        ]
        
        valid_rates = [r for r in growth_rates if r is not None]
        if not valid_rates:
            return None
        
        # 权重：近期更重要
        weights = [0.5, 0.3, 0.2][:len(valid_rates)]
        weighted_avg = sum(rate * weight for rate, weight in zip(valid_rates, weights)) / sum(weights)
        
        return weighted_avg
    
    def _forecast_profit_growth(self, growth_metrics: GrowthMetrics, profitability_metrics: ProfitabilityMetrics) -> Optional[float]:
        """预测利润增长率"""
        # 简化实现
        growth_rates = [
            growth_metrics.profit_growth_1y,
            growth_metrics.profit_growth_3y,
            growth_metrics.profit_growth_5y
        ]
        
        valid_rates = [r for r in growth_rates if r is not None]
        if not valid_rates:
            return None
        
        weights = [0.5, 0.3, 0.2][:len(valid_rates)]
        weighted_avg = sum(rate * weight for rate, weight in zip(valid_rates, weights)) / sum(weights)
        
        return weighted_avg
    
    def _calculate_target_pe(self, growth_metrics: GrowthMetrics, profitability_metrics: ProfitabilityMetrics) -> Optional[float]:
        """计算目标PE"""
        # 简化实现：基于增长率和ROE
        growth_rate = growth_metrics.profit_growth_1y or 10
        roe = profitability_metrics.roe or 15
        
        # 基础PE = 增长率 * ROE调整系数
        base_pe = growth_rate * (1 + roe / 100)
        return max(8, min(50, base_pe))  # 限制在合理范围内
    
    def _get_current_price(self, ts_code: str) -> Optional[float]:
        """获取当前股价"""
        try:
            # 从日线数据获取最新收盘价
            daily_data = list(self.db_handler.get_collection("infrastructure_stock_daily").find({
                "ts_code": ts_code
            }).sort("trade_date", -1).limit(1))
            
            if daily_data:
                return daily_data[0].get("close")
            return None
            
        except Exception as e:
            logger.error(f"获取当前股价失败: {e}")
            return None
    
    def _calculate_target_price(self, current_price: float, current_pe: float, target_pe: float) -> Optional[float]:
        """计算目标价格"""
        if not all([current_price, current_pe, target_pe]) or current_pe <= 0:
            return None
        
        return current_price * (target_pe / current_pe)
    
    def _calculate_beta(self, ts_code: str) -> Optional[float]:
        """计算Beta值"""
        # 简化实现
        return 1.0
    
    def _calculate_volatility(self, ts_code: str) -> Optional[float]:
        """计算波动率"""
        # 简化实现
        return 0.3
    
    def _generate_static_rating(self, static_valuation) -> Tuple[str, float]:
        """生成静态估值评级"""
        # 简化实现
        return "合理", 60.0
    
    def _generate_dynamic_rating(self, growth_metrics: GrowthMetrics, 
                                profitability_metrics: ProfitabilityMetrics, 
                                dynamic_valuation: DynamicValuationMetrics) -> Tuple[str, float]:
        """生成动态估值评级"""
        score = 0
        
        # 成长性评分权重40%
        growth_score = growth_metrics.growth_sustainability_score or 0
        score += growth_score * 0.4
        
        # 盈利质量评分权重30%
        quality_score = profitability_metrics.quality_score or 0
        score += quality_score * 0.3
        
        # PEG评级权重30%
        peg_score = 0
        if dynamic_valuation.peg_1y:
            if dynamic_valuation.peg_1y < 1.0:
                peg_score = 80
            elif dynamic_valuation.peg_1y < 1.5:
                peg_score = 60
            elif dynamic_valuation.peg_1y < 2.0:
                peg_score = 40
            else:
                peg_score = 20
        
        score += peg_score * 0.3
        
        # 生成评级
        if score >= 80:
            rating = "优秀"
        elif score >= 65:
            rating = "良好"
        elif score >= 50:
            rating = "中等"
        elif score >= 35:
            rating = "较差"
        else:
            rating = "差"
        
        return rating, score
    
    def _generate_comprehensive_rating(self, static_score: float, dynamic_score: float) -> str:
        """生成综合评级"""
        # 动态评级权重更高
        comprehensive_score = static_score * 0.3 + dynamic_score * 0.7
        
        if comprehensive_score >= 80:
            return "强烈推荐"
        elif comprehensive_score >= 65:
            return "推荐"
        elif comprehensive_score >= 50:
            return "中性"
        elif comprehensive_score >= 35:
            return "谨慎"
        else:
            return "不推荐"
    
    def _generate_investment_recommendation(self, static_score: float, dynamic_score: float, 
                                           dynamic_valuation: DynamicValuationMetrics) -> Tuple[str, str, str]:
        """生成投资建议"""
        comprehensive_score = static_score * 0.3 + dynamic_score * 0.7
        
        # 投资行动
        if comprehensive_score >= 75:
            action = "买入"
            confidence = "高"
            time_horizon = "长期持有(1-3年)"
        elif comprehensive_score >= 60:
            action = "买入"
            confidence = "中"
            time_horizon = "中期持有(6-18个月)"
        elif comprehensive_score >= 45:
            action = "持有"
            confidence = "中"
            time_horizon = "短期观察(3-6个月)"
        elif comprehensive_score >= 30:
            action = "持有"
            confidence = "低"
            time_horizon = "短期观察(1-3个月)"
        else:
            action = "卖出"
            confidence = "中"
            time_horizon = "短期"
        
        return action, confidence, time_horizon
    
    def _identify_key_risks(self, growth_metrics: GrowthMetrics, 
                           profitability_metrics: ProfitabilityMetrics, 
                           dynamic_valuation: DynamicValuationMetrics) -> List[str]:
        """识别主要风险"""
        risks = []
        
        # 增长风险
        if growth_metrics.growth_sustainability_score and growth_metrics.growth_sustainability_score < 40:
            risks.append("增长可持续性风险")
        
        if growth_metrics.growth_trend == "增长放缓":
            risks.append("增长动能减弱风险")
        
        # 估值风险
        if dynamic_valuation.peg_1y and dynamic_valuation.peg_1y > 2.0:
            risks.append("估值过高风险")
        
        # 盈利质量风险
        if profitability_metrics.cash_conversion_ratio and profitability_metrics.cash_conversion_ratio < 60:
            risks.append("现金流质量风险")
        
        if not risks:
            risks.append("常规市场风险")
        
        return risks
    
    def _identify_catalysts(self, growth_metrics: GrowthMetrics, 
                           profitability_metrics: ProfitabilityMetrics) -> List[str]:
        """识别催化因素"""
        catalysts = []
        
        # 成长催化因素
        if growth_metrics.growth_trend == "加速增长":
            catalysts.append("业绩增长加速")
        
        if growth_metrics.revenue_growth_1y and growth_metrics.revenue_growth_1y > 20:
            catalysts.append("营收高速增长")
        
        # 盈利改善
        if profitability_metrics.roe_trend == "上升":
            catalysts.append("盈利能力提升")
        
        if profitability_metrics.roe and profitability_metrics.roe > 20:
            catalysts.append("高ROE水平")
        
        if not catalysts:
            catalysts.append("基本面稳定")
        
        return catalysts
    
    def _generate_analysis_summary(self, stock_info: Dict, static_valuation, 
                                  growth_metrics: GrowthMetrics, dynamic_valuation: DynamicValuationMetrics, 
                                  comprehensive_rating: str) -> str:
        """生成分析摘要"""
        stock_name = stock_info.get('name', '')
        industry = stock_info.get('industry', '')
        pe_ratio = static_valuation.pe_ratio or 0
        peg = dynamic_valuation.peg_1y or 0
        growth_rate = growth_metrics.profit_growth_1y or 0
        
        summary = f"{stock_name}属于{industry}行业，当前PE为{pe_ratio:.1f}倍，"
        summary += f"1年利润增长率为{growth_rate:.1f}%，PEG比率为{peg:.2f}，"
        summary += f"综合动态估值评级为{comprehensive_rating}。"
        
        return summary
    
    def _generate_recommendation_rationale(self, investment_action: str, 
                                          dynamic_valuation: DynamicValuationMetrics, 
                                          growth_metrics: GrowthMetrics) -> str:
        """生成推荐理由"""
        rationale = f"基于动态估值分析，建议{investment_action}。"
        
        if dynamic_valuation.peg_1y:
            if dynamic_valuation.peg_1y < 1.0:
                rationale += "PEG比率低于1.0，显示良好的成长性价值。"
            elif dynamic_valuation.peg_1y > 2.0:
                rationale += "PEG比率偏高，需谨慎评估估值合理性。"
        
        if growth_metrics.growth_trend == "加速增长":
            rationale += "公司呈现加速增长趋势，具备良好的投资前景。"
        
        return rationale