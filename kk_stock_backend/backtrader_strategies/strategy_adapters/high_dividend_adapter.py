#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高股息策略适配器
从API层提取的核心选股逻辑

策略特点：
- 专注于高股息收益的稳健股票
- 综合考虑股息率、分红稳定性、财务安全性
- 适合追求稳定现金流的价值投资者
- 重点筛选分红能力强、现金流充裕的优质公司
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
    """高股息策略适配器"""
    
    def __init__(self):
        self.strategy_name = "高股息策略"
        self.strategy_type = "dividend"
        self.description = "寻找高股息收益、分红稳定的优质股票"
        self.db_handler = get_global_db_handler()
        
        # 策略参数
        self.params = {
            # 股息要求
            'dividend_yield_min': 2.0,           # 股息率最低要求 >= 2%
            'payout_ratio_min': 20.0,            # 股息支付率最低 >= 20%
            'dividend_fundraising_ratio_min': 30.0, # 分红募资比最低 >= 30%
            
            # 财务安全要求
            'min_market_cap': 1000000,           # 最小市值（万元）>= 10亿
            'max_debt_ratio': 70.0,              # 最大资产负债率 <= 70%
            'min_roe': 5.0,                      # 最小ROE >= 5%
            'min_net_profit_margin': 3.0,       # 最小净利润率 >= 3%
            
            # 现金流要求
            'require_positive_fcf': True,        # 要求正自由现金流
            'min_net_cash': 0,                   # 最小净现金水平
            
            # 排除条件
            'exclude_st': True,                  # 排除ST股票
            'min_years_data': 2,                 # 至少2年数据
            
            # 评分权重
            'dividend_yield_weight': 8,          # 股息率权重
            'payout_ratio_weight': 0.3,         # 股息支付率权重
            'fundraising_ratio_weight': 0.2,    # 分红募资比权重
            'roe_weight': 0.5,                   # ROE权重
            'cash_weight': 2.0,                  # 现金权重
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           **kwargs) -> Dict[str, Any]:
        """
        高股息策略选股
        
        Args:
            market_cap: 市值范围 (large/mid/small/all)
            stock_pool: 股票池 (all/main/gem/star)
            limit: 返回股票数量
            **kwargs: 其他参数
            
        Returns:
            选股结果字典
        """
        try:
            # 更新参数
            self._update_params(kwargs)
            
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
                    'limit': limit,
                    **self.params
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
    
    def _update_params(self, kwargs: Dict[str, Any]):
        """更新策略参数"""
        for key, value in kwargs.items():
            if key in self.params:
                self.params[key] = value
    
    async def _build_screening_pipeline(self, market_cap: str, stock_pool: str, limit: int) -> List[Dict]:
        """构建高股息筛选管道"""
        pipeline = []
        
        # 获取最新交易日期
        latest_date = await self._get_latest_trade_date()
        
        # 构建基础筛选条件
        match_conditions = await self._build_match_conditions(latest_date, market_cap, stock_pool)
        
        pipeline.extend([
            # 第一步：基础筛选
            {"$match": match_conditions},
            
            # 第二步：关联股票基本信息
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            # 第三步：关联最新财务指标数据
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
            
            # 第四步：关联现金流数据
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
            
            # 第五步：关联利润表数据
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
            
            # 第六步：关联资产负债表数据
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
            
            # 第七步：关联近3年现金流数据
            {"$lookup": {
                "from": "stock_cash_flow",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$ts_code", "$$ts_code"]}
                    }},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 3}
                ],
                "as": "cashflow_data_3y"
            }},
            
            # 第八步：计算关键指标
            {"$addFields": {
                # 基础财务指标
                "roe": {"$ifNull": ["$fina_data.roe", 0]},
                "roa": {"$ifNull": ["$fina_data.roa", 0]},
                "eps": {"$ifNull": ["$fina_data.eps", 0]},
                "bps": {"$ifNull": ["$fina_data.bps", 0]},
                
                # 计算股息率（基于EPS估算）
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
                
                # 股息支付率（估算）
                "payout_ratio": {
                    "$literal": 25  # 假设股息支付率为25%
                },
                
                # 计算分红募资比
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
                                        "else": 50  # 默认值
                                    }
                                }
                            }
                        },
                        "else": 0
                    }
                },
                
                # 计算净现金水平
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
                
                # 自由现金流/营收比率
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
                
                # 资产负债率
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
                
                # 净利润率
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
            
            # 第九步：应用高股息策略筛选条件
            {"$match": await self._build_dividend_match_conditions()},
            
            # 第十步：计算综合评分
            {"$addFields": {
                "score": {
                    "$min": [
                        100,  # 最高100分
                        {
                            "$add": [
                                # 股息率权重：最高24分
                                {"$multiply": ["$dividend_yield", self.params['dividend_yield_weight']]},
                                
                                # 股息支付率权重：最高15分
                                {"$multiply": [{"$min": ["$payout_ratio", 50]}, self.params['payout_ratio_weight']]},
                                
                                # 分红募资比权重：最高20分
                                {"$multiply": [{"$min": ["$dividend_fundraising_ratio", 100]}, self.params['fundraising_ratio_weight']]},
                                
                                # 净现金正数加分：最高10分
                                {
                                    "$cond": {
                                        "if": {"$gt": ["$net_cash", 0]},
                                        "then": {"$min": [{"$multiply": [{"$divide": ["$net_cash", 100000]}, self.params['cash_weight']]}, 10]},
                                        "else": 0
                                    }
                                },
                                
                                # ROE权重：最高10分
                                {"$multiply": [{"$min": ["$roe", 20]}, self.params['roe_weight']]},
                                
                                # ROA权重：最高5分
                                {"$multiply": [{"$min": ["$roa", 10]}, 0.5]},
                                
                                # 现金流正数加分：最高5分
                                {
                                    "$cond": {
                                        "if": {"$gt": ["$fcf_revenue_ratio", 0]},
                                        "then": {"$min": [{"$multiply": ["$fcf_revenue_ratio", 0.2]}, 5]},
                                        "else": 0
                                    }
                                },
                                
                                # 净利润率权重：最高5分
                                {"$multiply": [{"$min": ["$net_profit_margin", 20]}, 0.25]},
                                
                                # 低负债率加分：最高6分
                                {
                                    "$cond": {
                                        "if": {"$lt": ["$debt_ratio", 60]},
                                        "then": {"$multiply": [{"$subtract": [60, "$debt_ratio"]}, 0.1]},
                                        "else": 0
                                    }
                                }
                            ]
                        }
                    ]
                }
            }},
            
            # 第十一步：选择输出字段
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
                "dividend_yield": 1,
                "payout_ratio": 1,
                "dividend_fundraising_ratio": 1,
                "net_cash": 1,
                "roe": 1,
                "roa": 1,
                "eps": 1,
                "bps": 1,
                "fcf_revenue_ratio": 1,
                "debt_ratio": 1,
                "net_profit_margin": 1
            }},
            
            # 第十二步：排序和限制
            {"$sort": {"score": -1}},
            {"$limit": limit}
        ])
        
        return pipeline
    
    async def _build_match_conditions(self, latest_date: str, market_cap: str, stock_pool: str) -> Dict:
        """构建基础匹配条件"""
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": 0},  # 有效价格
            "total_mv": {"$gt": 0},  # 有效市值
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
    
    async def _build_dividend_match_conditions(self) -> Dict:
        """构建高股息特有筛选条件"""
        conditions = {
            "$and": [
                # 核心筛选条件
                {"dividend_yield": {"$gte": self.params['dividend_yield_min']}},
                {"eps": {"$gt": 0}},  # 每股收益为正
                
                # 市值筛选
                {"total_mv": {"$gte": self.params['min_market_cap']}},
                
                # 财务安全条件
                {"roe": {"$gte": self.params['min_roe']}},
                {"debt_ratio": {"$lte": self.params['max_debt_ratio']}},
                {"net_profit_margin": {"$gte": self.params['min_net_profit_margin']}},
            ]
        }
        
        # 排除ST股票
        if self.params['exclude_st']:
            conditions["$and"].append({
                "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
            })
        
        # 要求正自由现金流
        if self.params['require_positive_fcf']:
            conditions["$and"].append({
                "fcf_revenue_ratio": {"$gt": 0}
            })
        
        return conditions
    
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
                
                # 股息指标
                'dividend_yield': round(result.get('dividend_yield', 0), 2),
                'payout_ratio': round(result.get('payout_ratio', 0), 1),
                'dividend_fundraising_ratio': round(result.get('dividend_fundraising_ratio', 0), 1),
                
                # 财务指标
                'roe': round(result.get('roe', 0), 2),
                'roa': round(result.get('roa', 0), 2),
                'eps': round(result.get('eps', 0), 2),
                'bps': round(result.get('bps', 0), 2),
                'net_profit_margin': round(result.get('net_profit_margin', 0), 2),
                'debt_ratio': round(result.get('debt_ratio', 0), 1),
                
                # 现金流指标
                'net_cash': round(result.get('net_cash', 0) / 10000, 2),  # 转换为万元
                'fcf_revenue_ratio': round(result.get('fcf_revenue_ratio', 0), 2),
                
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
        
        dividend_yield = result.get('dividend_yield', 0)
        roe = result.get('roe', 0)
        debt_ratio = result.get('debt_ratio', 0)
        net_cash = result.get('net_cash', 0)
        score = result.get('score', 0)
        
        # 股息亮点
        if dividend_yield >= 5:
            reasons.append(f"高股息率{dividend_yield:.1f}%")
        elif dividend_yield >= 3:
            reasons.append(f"股息率{dividend_yield:.1f}%")
        
        # 盈利能力
        if roe >= 15:
            reasons.append(f"ROE{roe:.1f}%优秀")
        elif roe >= 10:
            reasons.append(f"ROE{roe:.1f}%良好")
        
        # 财务安全
        if debt_ratio <= 30:
            reasons.append("低负债率")
        elif debt_ratio <= 50:
            reasons.append("适中负债率")
        
        # 现金状况
        if net_cash > 0:
            reasons.append(f"净现金{net_cash/10000:.1f}万")
        
        reasons.append(f"股息评分{score:.0f}")
        
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
async def test_high_dividend_adapter():
    """测试高股息策略适配器"""
    adapter = HighDividendAdapter()
    result = await adapter.screen_stocks(
        market_cap="all", 
        stock_pool="all", 
        limit=10,
        dividend_yield_min=3.0
    )
    
    print(f"策略名称: {result['strategy_name']}")
    print(f"选股数量: {result['total_count']}")
    
    for i, stock in enumerate(result['stocks'][:5], 1):
        print(f"{i}. {stock['name']} ({stock['ts_code']})")
        print(f"   股息率: {stock['dividend_yield']}%, ROE: {stock['roe']}%")
        print(f"   评分: {stock['score']}, 理由: {stock['reason']}")


if __name__ == "__main__":
    asyncio.run(test_high_dividend_adapter())