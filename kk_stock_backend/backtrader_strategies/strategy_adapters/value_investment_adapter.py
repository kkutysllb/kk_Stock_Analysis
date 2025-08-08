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
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(os.path.dirname(current_dir))  # 到 kk_stock_backend
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

try:
    from api.global_db import get_global_db_handler
except ImportError as e:
    print(f"❌ 无法导入数据库处理器: {e}")
    print(f"当前路径: {current_dir}")
    print(f"后端根目录: {backend_root}")
    print(f"Python路径: {sys.path[:3]}...")
    raise ImportError("无法导入全局数据库处理器，请检查项目路径配置")


class ValueInvestmentAdapter:
    """价值投资策略适配器"""
    
    def __init__(self):
        self.strategy_name = "价值投资策略"
        self.strategy_type = "fundamental"
        self.description = "寻找低估值、高ROE、稳定增长的优质股票"
        self.db_handler = get_global_db_handler()
        
        # 策略参数 - 适配全市场选股，放宽部分条件以获得足够候选股票
        self.params = {
            # 估值筛选 - 适度放宽以适应全市场
            'pe_max': 35,           # PE < 35 (放宽)
            'pb_max': 5,            # PB < 5 (放宽)
            'pe_ttm_min': 0,        # 确保TTM市盈率有效
            'total_mv_min': 50000,  # 总市值 > 5亿 (降低门槛)
            
            # ROE要求 - 保持核心价值投资理念但适度放宽
            'roe_min': 8,           # ROE >= 8% (适度放宽)
            'roe_avg_min': 10,      # 历史ROE均值 >= 10% (适度放宽)
            'roe_stable_threshold': 8,  # ROE稳定性要求 (放宽)
            
            # 成长性要求 - 降低评分要求以增加候选
            'growth_score_min': 40,      # 成长性评分 >= 40 (放宽)
            'profitability_score_min': 50, # 盈利能力评分 >= 50 (放宽)
            
            # 财务健康度 - 保持基本要求
            'debt_ratio_max': 70,        # 资产负债率 <= 70% (适度放宽)
            'current_ratio_min': 1.0,    # 流动比率 >= 1.0 (适度放宽)
            
            # 权重配置
            'technical_weight': 0.1,     # 技术面权重
            'fundamental_weight': 0.8,   # 基本面权重
            'special_weight': 0.1        # 特殊因子权重
        }
    
    async def screen_stocks(self,
                           trade_date: str = None,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20) -> Dict[str, Any]:
        """
        价值投资策略选股
        
        Args:
            trade_date: 交易日期（回测系统使用）
            market_cap: 市值范围 (large/mid/small/all)
            stock_pool: 股票池 (all/main/gem/star/shenwan_value)
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
                'strategy_type': self.strategy_type,  # 添加缺失的字段
                'error': str(e),
                'total_count': 0,
                'stocks': [],
                'timestamp': datetime.now().isoformat()
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
        if stock_pool == "shenwan_value":
            # 申万传统价值行业股票池（向后兼容）
            shenwan_value_stocks = await self._get_shenwan_value_stocks()
            if shenwan_value_stocks:
                match_conditions["ts_code"] = {"$in": shenwan_value_stocks}
        elif stock_pool != "all":
            resolved_pool = await self._resolve_stock_pool([stock_pool])
            if resolved_pool:
                match_conditions["ts_code"] = {"$in": resolved_pool}
        # stock_pool == "all" 时不添加股票池限制，使用全市场选股
        
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
            
            # 第六步：计算综合评分（按优先级加权）
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
            
            # 第七步：应用价值投资核心筛选条件（与原始API逻辑一致）
            {"$match": {
                "avg_roe": {"$gte": 10},           # ROE均值 > 10%（最高优先级）
                "avg_current_ratio": {"$gte": 1.2}, # 流动比率 > 1.2（高现金流）
                "avg_debt_ratio": {"$lte": 60},     # 资产负债率 < 60%（低负债）
                "avg_profit_growth": {"$gte": 5}    # 利润增长率 > 5%（业绩超预期）
            }},
            
            # 第八步：输出字段（与原始API一致）
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": "$stock_info.industry",
                "close": 1,
                "pe": 1,
                "pb": 1,
                "pct_chg": {"$ifNull": ["$pct_chg", 0]},
                "total_mv": {"$ifNull": ["$total_mv", 0]},
                "roe": 1,
                "avg_roe": {"$round": ["$avg_roe", 2]},
                "avg_roe_yearly": {"$round": ["$avg_roe_yearly", 2]},
                "avg_current_ratio": {"$round": ["$avg_current_ratio", 2]},
                "avg_debt_ratio": {"$round": ["$avg_debt_ratio", 2]},
                "avg_profit_growth": {"$round": ["$avg_profit_growth", 2]},
                "value_score": {"$round": ["$value_score", 2]},
                "financial_periods": {"$size": "$financial_history"},
                "stock_info": 1,
                "financial_history": 1
            }},
            
            # 第九步：按价值评分排序
            {"$sort": {"value_score": -1}},
            {"$limit": 100}  # 限制返回数量
        ])
        
        return pipeline
    
    async def _process_results(self, results: List[Dict], limit: int) -> List[Dict]:
        """处理查询结果 - 与原始API输出格式保持一致"""
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
                'close': result.get('close', 0),
                'pct_chg': result.get('pct_chg', 0),
                'total_mv': round(result.get('total_mv', 0), 2),  # 保持万元单位
                
                # 财务指标（与原始逻辑一致）
                'roe': result.get('roe', 0),
                'avg_roe': round(result.get('avg_roe', 0), 2),
                'avg_roe_yearly': round(result.get('avg_roe_yearly', 0), 2),
                'avg_current_ratio': round(result.get('avg_current_ratio', 0), 2),
                'avg_debt_ratio': round(result.get('avg_debt_ratio', 0), 2),
                'avg_profit_growth': round(result.get('avg_profit_growth', 0), 2),
                
                # 评分（使用value_score作为主评分）
                'total_score': round(result.get('value_score', 0), 2),
                'growth_score': round(result.get('avg_profit_growth', 0), 1),
                'profitability_score': round(result.get('avg_roe', 0) * 4, 1),  # 基于ROE计算
                
                # 财务数据期数
                'financial_periods': result.get('financial_periods', len(result.get('financial_history', []))),
                
                # 选股理由
                'reason': self._generate_reason(result)
            }
            processed.append(stock_info)
        
        return processed
    
    def _generate_reason(self, result: Dict) -> str:
        """生成选股理由 - 基于价值投资四大核心指标"""
        reasons = []
        
        avg_roe = result.get('avg_roe', 0)
        avg_current_ratio = result.get('avg_current_ratio', 0)
        avg_debt_ratio = result.get('avg_debt_ratio', 0)
        avg_profit_growth = result.get('avg_profit_growth', 0)
        pe = result.get('pe', 0)
        pb = result.get('pb', 0)
        value_score = result.get('value_score', 0)
        
        # ROE评价
        if avg_roe >= 15:
            reasons.append(f"ROE均值{avg_roe:.1f}%优秀")
        elif avg_roe >= 10:
            reasons.append(f"ROE均值{avg_roe:.1f}%良好")
        
        # 现金流评价
        if avg_current_ratio >= 2.0:
            reasons.append(f"流动比率{avg_current_ratio:.1f}高现金流")
        elif avg_current_ratio >= 1.2:
            reasons.append(f"流动比率{avg_current_ratio:.1f}现金流良好")
            
        # 负债评价
        if avg_debt_ratio <= 40:
            reasons.append(f"负债率{avg_debt_ratio:.1f}%低负债")
        elif avg_debt_ratio <= 60:
            reasons.append(f"负债率{avg_debt_ratio:.1f}%负债适中")
            
        # 增长评价
        if avg_profit_growth >= 15:
            reasons.append(f"利润增长{avg_profit_growth:.1f}%高增长")
        elif avg_profit_growth >= 5:
            reasons.append(f"利润增长{avg_profit_growth:.1f}%稳定增长")
            
        # 估值评价
        if pe <= 15:
            reasons.append(f"PE{pe:.1f}倍低估")
        elif pe <= 20:
            reasons.append(f"PE{pe:.1f}倍合理")
            
        if pb <= 2:
            reasons.append(f"PB{pb:.1f}倍低估")
        elif pb <= 2.5:
            reasons.append(f"PB{pb:.1f}倍适中")
            
        reasons.append(f"价值评分{value_score:.1f}分")
        
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
    
    async def _get_shenwan_value_stocks(self) -> List[str]:
        """
        获取申万传统价值行业股票池（向后兼容）
        
        Returns:
            申万传统价值行业股票代码列表
        """
        try:
            # 价值投资重点关注的申万一级行业（与DataManager保持一致）
            value_industry_names = [
                '银行', '房地产', '钢铁', '煤炭', '石油石化', 
                '公用事业', '交通运输', '建筑装饰', '建筑材料',
                '汽车', '机械设备', '基础化工', '电力设备'
            ]
            
            # 获取申万行业成分股集合
            industry_collection = self.db_handler.get_collection('index_member_all')
            
            # 查询股票代码 - 获取所有价值行业股票
            projection = {'ts_code': 1, '_id': 0}
            stocks = []
            
            for industry in value_industry_names:
                query = {'l1_name': industry}
                industry_stocks = list(industry_collection.find(query, projection))
                stocks.extend(industry_stocks)
            
            # 提取股票代码并去重
            stock_codes = list(set([stock['ts_code'] for stock in stocks if stock.get('ts_code')]))
            
            return sorted(stock_codes)
            
        except Exception as e:
            print(f"❌ 获取申万传统价值行业股票池失败: {e}")
            return []

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