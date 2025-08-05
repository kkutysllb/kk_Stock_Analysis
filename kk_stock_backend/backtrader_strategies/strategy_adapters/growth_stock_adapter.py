#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成长股策略适配器
从API层提取的核心选股逻辑

策略特点：
- 寻找高成长性、高盈利能力的成长股
- 基于最近12个季度财务数据分析
- 分级筛选：成长性 + 盈利能力 + 财务安全
- 适合中长线成长投资
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.global_db import get_global_db_handler


class GrowthStockAdapter:
    """成长股策略适配器"""
    
    def __init__(self):
        self.strategy_name = "成长股策略"
        self.strategy_type = "growth"
        self.description = "寻找高成长性、高盈利能力的成长股"
        self.db_handler = get_global_db_handler()
        
        # 策略参数
        self.params = {
            # 成长性要求（二选一）
            'eps_growth_min': 10,        # EPS增长率 >= 10%
            'revenue_growth_min': 8,     # 营收增长率 >= 8%
            
            # 盈利能力要求（三选二）
            'roic_min': 6,               # ROIC >= 6%
            'gross_margin_min': 15,      # 毛利率 >= 15%
            'net_margin_min': 5,         # 净利率 >= 5%
            
            # 财务安全要求
            'debt_ratio_max': 80,        # 资产负债率 < 80%
            'quick_ratio_min': 0.5,      # 速动比率 > 0.5
            
            # PEG估值要求
            'peg_min': 0.2,              # PEG > 0.2
            'peg_max': 1.5,              # PEG < 1.5
            
            # 评分权重
            'growth_weight': 0.4,        # 成长性权重 40%
            'profitability_weight': 0.35, # 盈利能力权重 35%
            'innovation_weight': 0.15,   # 创新投入权重 15%
            'safety_weight': 0.1,        # 财务安全权重 10%
            
            # 数据要求
            'quarters_needed': 4,        # 至少需要4个季度数据
            'max_quarters': 12           # 最多分析12个季度
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20) -> Dict[str, Any]:
        """
        成长股策略选股
        
        Args:
            market_cap: 市值范围 (large/mid/small/all)
            stock_pool: 股票池 (all/main/gem/star)
            limit: 返回股票数量
            
        Returns:
            选股结果字典
        """
        try:
            # 构建筛选管道
            pipeline = await self._build_screening_pipeline(market_cap, stock_pool, limit)
            
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
            print(f"❌ 成长股策略选股失败: {e}")
            return {
                'strategy_name': self.strategy_name,
                'error': str(e),
                'total_count': 0,
                'stocks': []
            }
    
    async def _build_screening_pipeline(self, market_cap: str, stock_pool: str, limit: int) -> List[Dict]:
        """构建成长股筛选管道"""
        pipeline = []
        
        # 获取最新交易日期
        latest_date = await self._get_latest_trade_date()
        
        pipeline.extend([
            # 第一步：关联财务指标数据（最近12个季度）
            {"$lookup": {
                "from": "stock_fina_indicator",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$ts_code"]},
                        "end_date": {"$gte": "20210331"}  # 最近3年数据
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": self.params['max_quarters']}
                ],
                "as": "fina_indicators"
            }},
            
            # 第二步：关联股票基本信息
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            # 第三步：计算关键财务指标的均值和趋势
            {"$addFields": {
                # 计算EPS连续增长率
                "avg_eps_growth": {
                    "$avg": {
                        "$map": {
                            "input": {"$slice": ["$fina_indicators.basic_eps_yoy", 0, 12]},
                            "as": "eps_yoy",
                            "in": {"$ifNull": ["$$eps_yoy", 0]}
                        }
                    }
                },
                # 计算营收连续增长率
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
            
            # 第四步：应用筛选条件
            {"$match": await self._build_match_conditions(latest_date, market_cap, stock_pool)},
            
            # 第五步：计算综合评分
            {"$addFields": {
                "score": {
                    "$add": [
                        # 成长性评分 (40%)
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_eps_growth", 0]}, 50]}, 0.4]},
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_revenue_growth", 0]}, 50]}, 0.4]},
                        
                        # 盈利能力评分 (35%)
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_roic", 0]}, 25]}, 0.7]},
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_gross_margin", 0]}, 80]}, 0.25]},
                        {"$multiply": [{"$min": [{"$ifNull": ["$avg_net_margin", 0]}, 40]}, 0.5]},
                        
                        # 创新投入评分 (15%)
                        {"$multiply": [{"$min": [{"$ifNull": ["$latest_rd_rate", 0]}, 15]}, 1]},
                        
                        # 财务安全评分 (10%)
                        {"$cond": {"if": {"$lt": [{"$ifNull": ["$avg_debt_ratio", 100]}, 50]}, "then": 5, "else": 2}},
                        {"$cond": {"if": {"$gt": [{"$ifNull": ["$avg_quick_ratio", 0]}, 1.2]}, "then": 5, "else": 2}},
                        
                        # PEG奖励分
                        {"$cond": {"if": {"$and": [
                            {"$lt": [{"$ifNull": ["$peg_ratio", 999]}, self.params['peg_max']]},
                            {"$gt": [{"$ifNull": ["$peg_ratio", 0]}, self.params['peg_min']]}
                        ]}, "then": 10, "else": 0}}
                    ]
                }
            }},
            
            # 第六步：选择输出字段
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
            
            # 第七步：排序和限制
            {"$sort": {"score": -1}},
            {"$limit": limit}
        ])
        
        return pipeline
    
    async def _build_match_conditions(self, latest_date: str, market_cap: str, stock_pool: str) -> Dict:
        """构建匹配条件"""
        match_conditions = {
            "trade_date": latest_date,
            # 基础条件：确保有财务数据
            "fina_indicators.0": {"$exists": True},
            
            # 核心成长性条件（二选一）
            "$or": [
                {"avg_eps_growth": {"$gte": self.params['eps_growth_min']}},
                {"avg_revenue_growth": {"$gte": self.params['revenue_growth_min']}}
            ],
            
            # 盈利能力条件（三选二）
            "$expr": {
                "$gte": [
                    {"$size": {
                        "$filter": {
                            "input": [
                                {"$gte": [{"$ifNull": ["$avg_roic", 0]}, self.params['roic_min']]},
                                {"$gte": [{"$ifNull": ["$avg_gross_margin", 0]}, self.params['gross_margin_min']]},
                                {"$gte": [{"$ifNull": ["$avg_net_margin", 0]}, self.params['net_margin_min']]}
                            ],
                            "cond": "$$this"
                        }
                    }},
                    2
                ]
            },
            
            # 财务安全基础要求
            "avg_debt_ratio": {"$lt": self.params['debt_ratio_max']},
            "avg_quick_ratio": {"$gt": self.params['quick_ratio_min']},
            
            # 基本估值有效性
            "pe": {"$exists": True, "$ne": None, "$type": "number"},
            "pb": {"$exists": True, "$ne": None, "$type": "number"}
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
        
        return match_conditions
    
    async def _process_results(self, results: List[Dict]) -> List[Dict]:
        """处理查询结果"""
        processed = []
        
        for result in results:
            stock_info = {
                'ts_code': result.get('ts_code'),
                'name': result.get('name', ''),
                'industry': result.get('industry', ''),
                
                # 基础指标
                'close': round(result.get('close', 0), 2),
                'pe': round(result.get('pe', 0), 2),
                'pb': round(result.get('pb', 0), 2),
                'total_mv': round(result.get('total_mv', 0) / 10000, 2),  # 转换为亿元
                'pct_chg': round(result.get('pct_chg', 0), 2),
                
                # 成长性指标
                'avg_eps_growth': result.get('avg_eps_growth', 0),
                'avg_revenue_growth': result.get('avg_revenue_growth', 0),
                
                # 盈利能力指标
                'avg_roic': result.get('avg_roic', 0),
                'avg_gross_margin': result.get('avg_gross_margin', 0),
                'avg_net_margin': result.get('avg_net_margin', 0),
                
                # 估值指标
                'peg_ratio': result.get('peg_ratio', 0),
                
                # 财务安全指标
                'avg_debt_ratio': result.get('avg_debt_ratio', 0),
                'avg_quick_ratio': result.get('avg_quick_ratio', 0),
                
                # 创新指标
                'latest_rd_rate': result.get('latest_rd_rate', 0),
                
                # 综合评分
                'score': round(result.get('score', 0), 1),
                
                # 选股理由
                'reason': self._generate_reason(result)
            }
            processed.append(stock_info)
        
        return processed
    
    def _generate_reason(self, result: Dict) -> str:
        """生成选股理由"""
        reasons = []
        
        eps_growth = result.get('avg_eps_growth', 0)
        revenue_growth = result.get('avg_revenue_growth', 0)
        roic = result.get('avg_roic', 0)
        peg_ratio = result.get('peg_ratio', 0)
        score = result.get('score', 0)
        
        # 成长性亮点
        if eps_growth >= 20:
            reasons.append(f"EPS增长{eps_growth:.1f}%优秀")
        elif eps_growth >= 10:
            reasons.append(f"EPS增长{eps_growth:.1f}%良好")
            
        if revenue_growth >= 15:
            reasons.append(f"营收增长{revenue_growth:.1f}%强劲")
        elif revenue_growth >= 8:
            reasons.append(f"营收增长{revenue_growth:.1f}%稳健")
        
        # 盈利能力亮点
        if roic >= 15:
            reasons.append(f"ROIC{roic:.1f}%优秀")
        elif roic >= 10:
            reasons.append(f"ROIC{roic:.1f}%良好")
        
        # PEG估值亮点
        if 0.5 <= peg_ratio <= 1.0:
            reasons.append(f"PEG{peg_ratio:.1f}合理估值")
        elif 0.2 <= peg_ratio < 0.5:
            reasons.append(f"PEG{peg_ratio:.1f}低估")
        
        reasons.append(f"综合评分{score:.1f}分")
        
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
async def test_growth_stock_adapter():
    """测试成长股策略适配器"""
    adapter = GrowthStockAdapter()
    result = await adapter.screen_stocks(market_cap="all", stock_pool="all", limit=10)
    
    print(f"策略名称: {result['strategy_name']}")
    print(f"选股数量: {result['total_count']}")
    
    for i, stock in enumerate(result['stocks'][:5], 1):
        print(f"{i}. {stock['name']} ({stock['ts_code']})")
        print(f"   EPS增长: {stock['avg_eps_growth']}%, 营收增长: {stock['avg_revenue_growth']}%")
        print(f"   评分: {stock['score']}, 理由: {stock['reason']}")


if __name__ == "__main__":
    asyncio.run(test_growth_stock_adapter())