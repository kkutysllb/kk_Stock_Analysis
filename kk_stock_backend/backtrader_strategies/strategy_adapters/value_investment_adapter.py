#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值投资策略适配器
从API层提取的核心选股逻辑

策略特点：
- 寻找低估值、高ROE、稳定增长的优质股票
- PE < 25, PB < 3, 总市值 > 100亿
- 基于历史财报均值计算综合评分
- 适合长线价值投资
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.global_db import get_global_db_handler


class ValueInvestmentAdapter:
    """价值投资策略适配器"""
    
    def __init__(self):
        self.strategy_name = "价值投资策略"
        self.strategy_type = "fundamental"
        self.description = "寻找低估值、高ROE、稳定增长的优质股票"
        self.db_handler = get_global_db_handler()
        
        # 策略参数
        self.params = {
            # 估值筛选
            'pe_max': 25,           # PE < 25
            'pb_max': 3,            # PB < 3
            'pe_ttm_min': 0,        # 确保TTM市盈率有效
            'total_mv_min': 100000, # 总市值 > 10亿
            
            # ROE要求
            'roe_min': 10,          # ROE >= 10%
            'roe_avg_min': 12,      # 历史ROE均值 >= 12%
            'roe_stable_threshold': 5,  # ROE稳定性要求
            
            # 成长性要求
            'growth_score_min': 60,      # 成长性评分 >= 60
            'profitability_score_min': 70, # 盈利能力评分 >= 70
            
            # 财务健康度
            'debt_ratio_max': 60,        # 资产负债率 <= 60%
            'current_ratio_min': 1.2,    # 流动比率 >= 1.2
            
            # 权重配置
            'technical_weight': 0.1,     # 技术面权重
            'fundamental_weight': 0.8,   # 基本面权重
            'special_weight': 0.1        # 特殊因子权重
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20) -> Dict[str, Any]:
        """
        价值投资策略选股
        
        Args:
            market_cap: 市值范围 (large/mid/small/all)
            stock_pool: 股票池 (all/main/gem/star)
            limit: 返回股票数量
            
        Returns:
            选股结果字典
        """
        try:
            # 构建筛选管道
            pipeline = await self._build_screening_pipeline(market_cap, stock_pool)
            
            # 执行查询
            collection = self.db_handler.get_collection('stock_factor_pro')
            cursor = collection.aggregate(pipeline)
            results = list(cursor)
            
            # 处理结果
            processed_results = await self._process_results(results, limit)
            
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
            print(f"❌ 价值投资策略选股失败: {e}")
            return {
                'strategy_name': self.strategy_name,
                'error': str(e),
                'total_count': 0,
                'stocks': []
            }
    
    async def _build_screening_pipeline(self, market_cap: str, stock_pool: str) -> List[Dict]:
        """构建价值投资筛选管道"""
        pipeline = []
        
        # 获取最新交易日期
        latest_date = await self._get_latest_trade_date()
        
        # 第一阶段：基础筛选条件
        match_conditions = {
            "trade_date": latest_date,
            "pe": {"$gt": 0, "$lte": self.params['pe_max']},
            "pb": {"$gt": 0, "$lte": self.params['pb_max']},
            "pe_ttm": {"$gt": self.params['pe_ttm_min']},
            "total_mv": {"$gt": self.params['total_mv_min']}
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
            resolved_pool = await self._resolve_stock_pool([stock_pool])
            if resolved_pool:
                match_conditions["ts_code"] = {"$in": resolved_pool}
        
        pipeline.extend([
            # 第一步：匹配基础条件
            {"$match": match_conditions},
            
            # 第二步：关联股票基本信息
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            # 第三步：关联历史财务指标
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
                        "roe": {"$exists": True, "$ne": None, "$gt": 0}
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 8},  # 最近8个季度
                    {"$project": {
                        "end_date": 1,
                        "roe": 1,
                        "roe_yearly": 1,
                        "current_ratio": 1,
                        "quick_ratio": 1,
                        "debt_to_assets": 1,
                        "debt_to_eqt": 1,
                        "profit_dedt": 1,
                        "profit_yoy": 1,
                        "netprofit_yoy": 1
                    }}
                ],
                "as": "financial_history"
            }},
            
            # 第四步：过滤财务数据不足的股票
            {"$match": {
                "$expr": {"$gte": [{"$size": "$financial_history"}, 4]}
            }},
            
            # 第五步：计算评分和排序
            await self._add_scoring_fields(),
            
            # 第六步：最终筛选和排序
            {"$match": {
                "avg_roe": {"$gte": self.params['roe_avg_min']},
                "total_score": {"$gte": 70}  # 综合评分要求
            }},
            {"$sort": {"total_score": -1}},
            {"$limit": 100}  # 限制返回数量
        ])
        
        return pipeline
    
    async def _add_scoring_fields(self) -> Dict:
        """添加评分计算字段"""
        return {"$addFields": {
            # 计算ROE均值
            "avg_roe": {
                "$avg": {
                    "$map": {
                        "input": "$financial_history",
                        "as": "fh",
                        "in": {"$ifNull": ["$$fh.roe", 0]}
                    }
                }
            },
            
            # 计算ROE稳定性（标准差）
            "roe_stability": {
                "$stdDevPop": {
                    "$map": {
                        "input": "$financial_history",
                        "as": "fh", 
                        "in": {"$ifNull": ["$$fh.roe", 0]}
                    }
                }
            },
            
            # 计算成长性评分
            "growth_score": {
                "$multiply": [
                    {"$avg": {
                        "$map": {
                            "input": "$financial_history",
                            "as": "fh",
                            "in": {"$ifNull": ["$$fh.profit_yoy", 0]}
                        }
                    }},
                    2  # 权重调整
                ]
            },
            
            # 计算盈利能力评分
            "profitability_score": {
                "$add": [
                    {"$multiply": ["$avg_roe", 3]},  # ROE权重
                    {"$multiply": [{"$ifNull": ["$roe", 0]}, 2]}  # 当前ROE权重
                ]
            },
            
            # 计算综合得分
            "total_score": {
                "$add": [
                    {"$multiply": ["$avg_roe", 4]},      # ROE权重最高
                    {"$multiply": [
                        {"$subtract": [30, {"$ifNull": ["$pe", 30]}]}, 2   # PE估值得分
                    ]},
                    {"$multiply": [
                        {"$subtract": [5, {"$ifNull": ["$pb", 5]}]}, 3     # PB估值得分  
                    ]},
                    {"$ifNull": ["$growth_score", 0]},   # 成长性得分
                    {"$multiply": [
                        {"$subtract": [10, {"$ifNull": ["$roe_stability", 10]}]}, 1  # 稳定性得分
                    ]}
                ]
            }
        }}
    
    async def _process_results(self, results: List[Dict], limit: int) -> List[Dict]:
        """处理查询结果"""
        processed = []
        
        for result in results[:limit]:
            stock_info = {
                'ts_code': result.get('ts_code'),
                'name': result.get('stock_info', {}).get('name', ''),
                'industry': result.get('stock_info', {}).get('industry', ''),
                
                # 估值指标
                'pe': round(result.get('pe', 0), 2),
                'pb': round(result.get('pb', 0), 2),
                'pe_ttm': round(result.get('pe_ttm', 0), 2),
                'total_mv': round(result.get('total_mv', 0) / 10000, 2),  # 转换为亿元
                
                # 盈利指标
                'roe': round(result.get('roe', 0), 2),
                'avg_roe': round(result.get('avg_roe', 0), 2),
                'roe_stability': round(result.get('roe_stability', 0), 2),
                
                # 评分
                'growth_score': round(result.get('growth_score', 0), 1),
                'profitability_score': round(result.get('profitability_score', 0), 1), 
                'total_score': round(result.get('total_score', 0), 1),
                
                # 选股理由
                'reason': self._generate_reason(result)
            }
            processed.append(stock_info)
        
        return processed
    
    def _generate_reason(self, result: Dict) -> str:
        """生成选股理由"""
        reasons = []
        
        avg_roe = result.get('avg_roe', 0)
        pe = result.get('pe', 0)
        pb = result.get('pb', 0)
        total_score = result.get('total_score', 0)
        
        if avg_roe >= 15:
            reasons.append(f"ROE均值{avg_roe:.1f}%优秀")
        elif avg_roe >= 12:
            reasons.append(f"ROE均值{avg_roe:.1f}%良好")
            
        if pe <= 15:
            reasons.append(f"PE{pe:.1f}倍低估")
        elif pe <= 20:
            reasons.append(f"PE{pe:.1f}倍合理")
            
        if pb <= 2:
            reasons.append(f"PB{pb:.1f}倍低估")
        elif pb <= 2.5:
            reasons.append(f"PB{pb:.1f}倍适中")
            
        reasons.append(f"综合评分{total_score:.1f}分")
        
        return "；".join(reasons)
    
    async def _get_latest_trade_date(self) -> str:
        """获取最新交易日期"""
        try:
            collection = self.db_handler.get_collection('stock_factor_pro')
            result = collection.find({}, {"trade_date": 1}).sort("trade_date", -1).limit(1)
            latest = list(result)[0]
            return latest['trade_date']
        except:
            return "20241231"  # 默认日期
    
    async def _resolve_stock_pool(self, stock_pools: List[str]) -> List[str]:
        """解析股票池代码"""
        # 这里需要根据实际的股票池配置来实现
        # 暂时返回空列表，表示不限制股票池
        return []


# 测试函数
async def test_value_investment_adapter():
    """测试价值投资策略适配器"""
    adapter = ValueInvestmentAdapter()
    result = await adapter.screen_stocks(market_cap="all", stock_pool="all", limit=10)
    
    print(f"策略名称: {result['strategy_name']}")
    print(f"选股数量: {result['total_count']}")
    
    for i, stock in enumerate(result['stocks'][:5], 1):
        print(f"{i}. {stock['name']} ({stock['ts_code']})")
        print(f"   PE: {stock['pe']}, PB: {stock['pb']}, ROE: {stock['roe']}%")
        print(f"   评分: {stock['total_score']}, 理由: {stock['reason']}")


if __name__ == "__main__":
    asyncio.run(test_value_investment_adapter())