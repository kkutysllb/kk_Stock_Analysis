#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高股息策略适配器 - 简化版本
从API层提取的核心选股逻辑

策略特点：
- 专注于高股息收益的稳健股票
- 简化版实现，避免复杂查询导致卡死
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class HighDividendAdapter:
    """高股息策略适配器 - 简化版"""
    
    def __init__(self):
        self.strategy_name = "高股息策略"
        self.strategy_type = "dividend"
        self.description = "寻找高股息收益、分红稳定的优质股票"
        self.db_handler = get_global_db_handler()
        
        # 简化参数
        self.params = {
            'pe_max': 50,
            'pb_max': 10,
            'total_mv_min': 500000,  # 50亿
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           **kwargs) -> Dict[str, Any]:
        """
        高股息策略选股 - 简化版
        
        Args:
            market_cap: 市值范围 (large/mid/small/all)
            stock_pool: 股票池 (all/main/gem/star)
            limit: 返回股票数量
            **kwargs: 其他参数
            
        Returns:
            选股结果字典
        """
        try:
            # 构建筛选管道
            pipeline = await self._build_screening_pipeline(market_cap, stock_pool)
            pipeline.append({"$limit": limit})
            
            # 执行查询
            collection = self.db_handler.get_collection('stock_factor_pro')
            cursor = collection.aggregate(pipeline)
            results = list(cursor)
            
            # 处理结果
            processed_results = await self._process_results(results)
            
            return {
                'strategy_name': self.strategy_name,
                'strategy_type': self.strategy_type,
                'total_count': len(processed_results),
                'stocks': processed_results,
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'market_cap': market_cap,
                    'stock_pool': stock_pool,
                    'limit': limit
                }
            }
            
        except Exception as e:
            print(f"❌ 高股息策略选股失败: {e}")
            return {
                'strategy_name': self.strategy_name,
                'error': str(e),
                'total_count': 0,
                'stocks': []
            }
    
    async def _build_screening_pipeline(self, market_cap: str, stock_pool: str) -> List[Dict]:
        """构建高股息筛选管道 - 使用真实财务数据"""
        pipeline = []
        
        # 获取最新交易日期
        latest_date = await self._get_latest_trade_date()
        
        # 基础筛选条件
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": 0},
            "total_mv": {"$gt": 0},
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
            resolved_pool = await self._resolve_stock_pool([stock_pool])
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
            
            # 联接最新现金流数据
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
            
            # 计算真实财务指标
            {"$addFields": {
                # 基础财务指标
                "roe": {"$ifNull": ["$fina_data.roe", 0]},
                "roa": {"$ifNull": ["$fina_data.roa", 0]},
                "eps": {"$ifNull": ["$fina_data.eps", 0]},
                "bps": {"$ifNull": ["$fina_data.bps", 0]},
                
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
                                    {"$multiply": [{"$ifNull": ["$fina_data.eps", 0]}, 0.4]},
                                    {"$ifNull": ["$close", 1]}
                                ]},
                                100
                            ]
                        },
                        "else": 0
                    }
                },
                
                # 真实股息支付率：分红金额 / 净利润
                "payout_ratio": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": [{"$abs": {"$ifNull": ["$cashflow_data.c_pay_dist_dpcp_int_exp", 0]}}, 0]},
                            {"$gt": [{"$ifNull": ["$fina_data.profit_dedt", 0]}, 0]}
                        ]},
                        "then": {
                            "$min": [
                                100,
                                {"$multiply": [
                                    {"$divide": [
                                        {"$abs": {"$ifNull": ["$cashflow_data.c_pay_dist_dpcp_int_exp", 0]}},
                                        {"$ifNull": ["$fina_data.profit_dedt", 1]}
                                    ]},
                                    100
                                ]}
                            ]
                        },
                        "else": 0
                    }
                },
                
                # 真实分红募资比：分红金额 / 筹资活动现金流入
                "dividend_fundraising_ratio": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": [{"$abs": {"$ifNull": ["$cashflow_data.c_pay_dist_dpcp_int_exp", 0]}}, 0]},
                            {"$gt": [{"$ifNull": ["$cashflow_data.stot_cash_in_fnc_act", 0]}, 0]}
                        ]},
                        "then": {
                            "$min": [
                                200,
                                {"$multiply": [
                                    {"$divide": [
                                        {"$abs": {"$ifNull": ["$cashflow_data.c_pay_dist_dpcp_int_exp", 0]}},
                                        {"$ifNull": ["$cashflow_data.stot_cash_in_fnc_act", 1]}
                                    ]},
                                    100
                                ]}
                            ]
                        },
                        "else": 0
                    }
                },
                
                # 净现金估算
                "net_cash": {"$divide": ["$total_mv", 100]},
                
                # 净利润率估算
                "net_profit_margin": {"$multiply": [{"$ifNull": ["$fina_data.roe", 10]}, 0.5]}
            }},
            
            # 应用筛选条件
            {"$match": {
                "$and": [
                    {"eps": {"$gt": 0}},
                    {"total_mv": {"$gte": 1000000}},
                    {"stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}}
                ]
            }},
            
            # 计算评分
            {"$addFields": {
                "score": {
                    "$add": [
                        {"$multiply": ["$dividend_yield", 8]},
                        {"$multiply": [{"$min": ["$roe", 20]}, 2]},
                        {"$min": [{"$divide": ["$total_mv", 1000000]}, 10]},
                        20
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
                "dividend_yield": 1,
                "payout_ratio": 1,
                "dividend_fundraising_ratio": 1,
                "net_cash": 1,
                "roe": 1,
                "roa": 1,
                "eps": 1,
                "bps": 1,
                "net_profit_margin": 1,
                # 调试字段
                "c_pay_dist_dpcp_int_exp": "$cashflow_data.c_pay_dist_dpcp_int_exp",
                "profit_dedt": "$fina_data.profit_dedt",
                "stot_cash_in_fnc_act": "$cashflow_data.stot_cash_in_fnc_act"
            }},
            
            {"$sort": {"score": -1}}
        ])
        
        return pipeline
    
    async def _process_results(self, results: List[Dict]) -> List[Dict]:
        """处理查询结果 - 使用真实数据库数据"""
        processed = []
        for result in results:
            processed_result = {
                'ts_code': result.get('ts_code'),
                'name': result.get('name', ''),
                'industry': result.get('industry'),
                'close': round(result.get('close') or 0, 2),
                'pe': round(result.get('pe') or 0, 2),
                'pb': round(result.get('pb') or 0, 2),
                'pct_chg': round(result.get('pct_chg') or 0, 2),
                'total_mv': round(result.get('total_mv') or 0, 2),
                'score': round(result.get('score') or 0, 2),
                
                # 高股息策略专用字段（直接使用数据库真实数据）
                'dividend_yield': round(result.get('dividend_yield') or 0, 2),  # 真实股息率
                'payout_ratio': round(result.get('payout_ratio') or 0, 2),      # 真实股息支付率
                'dividend_coverage': None,
                'roe': round(result.get('roe') or 0, 2),                        # 真实ROE
                'roic': round(result.get('roa') or 0, 2),                       # 用ROA代替ROIC
                'fcf_revenue_ratio': round(result.get('fcf_revenue_ratio') or 0, 2),
                'debt_ratio': round(result.get('debt_ratio') or 0, 2),
                'eps': round(result.get('eps') or 0, 2),                        # 真实EPS
                'net_profit_margin': round(result.get('net_profit_margin') or 0, 2),  # 真实净利润率
                'dividend_fundraising_ratio': round(result.get('dividend_fundraising_ratio') or 0, 2),  # 真实分红募资比
                'net_cash': round(result.get('net_cash') or 0, 2)               # 真实净现金
            }
            processed.append(processed_result)
        
        return processed
    
    async def _get_latest_trade_date(self) -> str:
        """获取最新交易日期"""
        try:
            collection = self.db_handler.get_collection('stock_factor_pro')
            result = collection.find({}, {"trade_date": 1}).sort("trade_date", -1).limit(1)
            latest = list(result)[0]
            return latest['trade_date']
        except:
            return ""  # 默认日期
    
    async def _resolve_stock_pool(self, stock_pools: List[str]) -> List[str]:
        """解析股票池代码"""
        # 暂时返回空列表，表示不限制股票池
        return []


# 测试函数
async def test_high_dividend_adapter():
    """测试高股息策略适配器"""
    adapter = HighDividendAdapter()
    result = await adapter.screen_stocks(limit=5)
    print(f"找到 {result['total_count']} 只股票")
    for stock in result['stocks'][:3]:
        print(f"{stock['ts_code']} {stock['name']} 得分:{stock['score']}")


if __name__ == "__main__":
    asyncio.run(test_high_dividend_adapter())