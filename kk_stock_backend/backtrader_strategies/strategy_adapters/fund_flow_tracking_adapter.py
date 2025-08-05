#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金追踪策略适配器
从API层提取的核心选股逻辑 - 基于融资融券数据

策略特点：
- 追踪融资买入趋势
- 关注融资余额增长
- 基于融资融券数据的量化分析
- 使用交集查询算法优化性能
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(backend_root)

from api.global_db import get_global_db_handler


class FundFlowTrackingAdapter:
    """资金追踪策略适配器 - 基于融资融券数据"""
    
    def __init__(self):
        self.strategy_name = "资金追踪策略"
        self.strategy_type = "fund_flow"
        self.description = "基于融资融券数据追踪主力资金流向"
        self.db_handler = get_global_db_handler()
        
        # 策略参数 - 与原始接口保持一致
        self.params = {
            'margin_buy_trend_min': 50.0,        # 融资买入趋势最小值
            'margin_balance_growth_min': 50.0,   # 融资余额增长最小值
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           margin_buy_trend_min: float = 50.0,
                           margin_balance_growth_min: float = 50.0,
                           **kwargs) -> Dict[str, Any]:
        """
        资金追踪策略选股 - 使用原始接口的优化交集查询算法
        
        Args:
            market_cap: 市值范围 (large/mid/small/all)
            stock_pool: 股票池 (all/main/gem/star)
            limit: 返回股票数量
            margin_buy_trend_min: 融资买入趋势最小值
            margin_balance_growth_min: 融资余额增长最小值
            
        Returns:
            选股结果字典
        """
        try:
            print(f"🔥 资金追踪策略适配器开始执行")
            print(f"参数: market_cap={market_cap}, stock_pool={stock_pool}, limit={limit}")
            
            # 使用优化的资金追踪筛选逻辑 - 交集查询
            results = await self._optimized_fund_flow_screening(
                market_cap, stock_pool, limit, 
                margin_buy_trend_min, margin_balance_growth_min
            )
            
            return {
                'strategy_name': self.strategy_name,
                'strategy_type': self.strategy_type,
                'total_count': len(results),
                'stocks': results,
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'market_cap': market_cap,
                    'stock_pool': stock_pool,
                    'limit': limit,
                    'margin_buy_trend_min': margin_buy_trend_min,
                    'margin_balance_growth_min': margin_balance_growth_min
                }
            }
            
        except Exception as e:
            print(f"❌ 资金追踪策略选股失败: {e}")
            return {
                'strategy_name': self.strategy_name,
                'strategy_type': self.strategy_type,  # 添加缺失的字段
                'error': str(e),
                'total_count': 0,
                'stocks': [],
                'timestamp': datetime.now().isoformat()
            }

    async def _optimized_fund_flow_screening(self, market_cap: str, stock_pool: str, 
                                           limit: int, margin_buy_trend_min: float,
                                           margin_balance_growth_min: float) -> List[Dict[str, Any]]:
        """优化的资金追踪筛选 - 使用交集查询算法（原始策略逻辑）"""
        try:
            # 步骤1: 并行查询各个条件的TOP股票
            print("🔍 开始并行查询各资金条件...")
            
            # 1.1 融资买入趋势TOP500
            margin_buy_candidates = await self._query_margin_buy_top_stocks(margin_buy_trend_min, 500)
            print(f"融资买入趋势候选: {len(margin_buy_candidates)}只")
            
            # 1.2 融资余额增长TOP500  
            margin_balance_candidates = await self._query_margin_balance_growth_stocks(margin_balance_growth_min, 500)
            print(f"融资余额增长候选: {len(margin_balance_candidates)}只")
            
            # 步骤2: 求交集 (只使用融资买入趋势和融资余额增长两个条件)
            print("🔄 计算候选股票交集...")
            intersection_stocks = set(margin_buy_candidates)
            intersection_stocks &= set(margin_balance_candidates)
            
            print(f"交集结果: {len(intersection_stocks)}只股票")
            
            if not intersection_stocks:
                return []
                
            # 步骤3: 计算最终评分并排序
            print("📊 计算综合评分...")
            scored_results = await self._calculate_final_scores(list(intersection_stocks))
            
            # 返回TOP N结果
            return sorted(scored_results, key=lambda x: x.get('score', 0), reverse=True)[:limit]
            
        except Exception as e:
            print(f"优化资金追踪筛选失败: {str(e)}")
            return []

    async def _query_margin_buy_top_stocks(self, min_trend: float, limit: int = 500) -> List[str]:
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
            
            result = list(self.db_handler.get_collection('margin_detail').aggregate(pipeline))
            return [doc['_id'] for doc in result if doc.get('recent_buy', 0) >= min_trend]
            
        except Exception as e:
            print(f"查询融资买入TOP股票失败: {str(e)}")
            return []

    async def _query_margin_balance_growth_stocks(self, min_growth: float, limit: int = 500) -> List[str]:
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
            
            result = list(self.db_handler.get_collection('margin_detail').aggregate(pipeline))
            return [doc['_id'] for doc in result]
            
        except Exception as e:
            print(f"查询融资余额增长股票失败: {str(e)}")
            return []

    async def _calculate_final_scores(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """计算最终综合评分并获取完整数据（原始策略逻辑）"""
        results = []
        
        for ts_code in stock_codes:
            try:
                # 获取基本信息
                stock_info = self.db_handler.get_collection('infrastructure_stock_basic').find_one(
                    {"ts_code": ts_code},
                    {"name": 1, "industry": 1, "_id": 0}
                )
                
                if not stock_info:
                    continue
                
                # 获取最新价格数据 - 只查询必要字段
                price_data = self.db_handler.get_collection('stock_factor_pro').find_one(
                    {"ts_code": ts_code},
                    {"close": 1, "pct_chg": 1, "total_mv": 1, "_id": 0},
                    sort=[("trade_date", -1)]
                )
                
                # 获取融资融券数据（最近7天）
                margin_cursor = self.db_handler.get_collection('margin_detail').find(
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
                print(f"计算{ts_code}评分失败: {str(e)}")
                continue
        
        return results

    async def _get_latest_trade_date(self) -> str:
        """获取最新交易日"""
        try:
            latest_doc = self.db_handler.get_collection('stock_factor_pro').find_one(
                {},
                {"trade_date": 1, "_id": 0},
                sort=[("trade_date", -1)]
            )
            return latest_doc['trade_date'] if latest_doc else datetime.now().strftime('%Y%m%d')
        except Exception:
            return datetime.now().strftime('%Y%m%d')


if __name__ == "__main__":
    async def test_adapter():
        adapter = FundFlowTrackingAdapter()
        result = await adapter.screen_stocks(limit=10)
        print(f"测试结果: {result}")
    
    asyncio.run(test_adapter())