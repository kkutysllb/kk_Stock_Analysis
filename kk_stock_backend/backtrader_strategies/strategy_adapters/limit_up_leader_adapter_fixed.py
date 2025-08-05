#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连板龙头策略适配器 - 修复版
完全按照原始接口逻辑重新实现
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class LimitUpLeaderAdapter:
    """连板龙头策略适配器 - 修复版"""
    
    def __init__(self):
        self.strategy_name = "连板龙头策略"
        self.strategy_type = "limit_up"
        self.description = "基于涨跌停数据的真实连板分析"
        self.db_handler = get_global_db_handler()
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           min_limit_times: int = 2,
                           max_limit_times: int = 10,
                           max_open_times: int = 3,
                           min_turnover: float = 5.0,
                           max_turnover: float = 30.0,
                           **kwargs) -> Dict[str, Any]:
        """
        连板龙头策略选股 - 完全按照原始逻辑
        """
        try:
            # 获取最新交易日期
            latest_limit_data = list(self.db_handler.get_collection('limit_list_daily').find({}).sort('trade_date', -1).limit(1))
            if not latest_limit_data:
                return {
                    'strategy_name': self.strategy_name,
                    'error': "找不到涨跌停数据",
                    'total_count': 0,
                    'stocks': []
                }
            
            latest_date = latest_limit_data[0]['trade_date']
            
            # 构建聚合管道 - 完全按照原始逻辑
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
                # 第七步：关联板块涨停数据（简化处理）
                {"$addFields": {
                    "industry_strength": {"$literal": 50},  # 简化处理，固定值
                    "concept_strength": {"$literal": 50}    # 简化处理，固定值
                }},
                
                # 第八步：计算龙头评分
                {"$addFields": {
                    "score": {
                        "$add": [
                            # 连板次数得分：每连板得15分
                            {"$multiply": ["$limit_times", 15]},
                            
                            # 开板惩罚：每开板扣5分
                            {"$multiply": ["$open_times", -5]},
                            
                            # 换手率得分：适中换手率得分，最高20分
                            {"$cond": {
                                "if": {"$and": [
                                    {"$gte": ["$tech_data.turnover_rate", 8]}, 
                                    {"$lte": ["$tech_data.turnover_rate", 20]}
                                ]},
                                "then": 20,
                                "else": {"$cond": {
                                    "if": {"$and": [
                                        {"$gte": ["$tech_data.turnover_rate", 5]}, 
                                        {"$lte": ["$tech_data.turnover_rate", 25]}
                                    ]},
                                    "then": 15,
                                    "else": 10
                                }}
                            }},
                            
                            # 市值得分：大市值更稳定，最高15分
                            {"$cond": {
                                "if": {"$gte": ["$total_mv_yi", 200]},
                                "then": 15,
                                "else": {"$cond": {
                                    "if": {"$gte": ["$total_mv_yi", 100]},
                                    "then": 12,
                                    "else": {"$cond": {
                                        "if": {"$gte": ["$total_mv_yi", 50]},
                                        "then": 8,
                                        "else": 5
                                    }}
                                }}
                            }},
                            
                            # 板块强度得分：简化处理，固定10分
                            10
                        ]
                    },
                    
                    # 判断是否为龙头
                    "is_leader": {
                        "$cond": {
                            "if": {"$and": [
                                {"$gte": ["$limit_times", 3]},
                                {"$lte": ["$open_times", 1]},
                                {"$gte": ["$tech_data.turnover_rate", 8]}
                            ]},
                            "then": True,
                            "else": False
                        }
                    }
                }},
                
                # 第九步：输出字段
                {"$project": {
                    "ts_code": 1,
                    "name": "$stock_info.name",
                    "industry": "$stock_info.industry",
                    "close": "$tech_data.close",
                    "pe": "$tech_data.pe",
                    "pb": "$tech_data.pb",
                    "pct_chg": {"$ifNull": ["$tech_data.pct_chg", 0]},
                    "total_mv": {"$multiply": ["$total_mv_yi", 10000]},  # 转回万元
                    "score": 1,
                    
                    # 连板龙头策略专用字段
                    "limit_times": 1,
                    "open_times": 1,
                    "turnover_rate": "$tech_data.turnover_rate",
                    "amount": "$tech_data.amount",
                    "is_leader": 1,
                    "industry_strength": 1,
                    "concept_strength": 1
                }},
                
                {"$sort": {"score": -1, "limit_times": -1}},
                {"$limit": limit}
            ]
            
            # 执行查询
            collection = self.db_handler.get_collection('limit_list_daily')
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
                    'min_limit_times': min_limit_times,
                    'max_limit_times': max_limit_times,
                    'max_open_times': max_open_times,
                    'min_turnover': min_turnover,
                    'max_turnover': max_turnover
                }
        except Exception as e:
            print(f"❌ 连板龙头策略选股失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'strategy_name': self.strategy_name,
                'error': str(e),
                'total_count': 0,
                'stocks': []
            }
    
    async def _process_results(self, results: List[Dict]) -> List[Dict]:
        """处理查询结果"""
        processed = []
        
        for result in results:
            stock_info = {
                'ts_code': result.get('ts_code'),
                'name': result.get('name', ''),
                'industry': result.get('industry', ''),
                
                # 基础指标
                'close': round(result.get('close') or 0, 2),
                'pe': round(result.get('pe') or 0, 2),
                'pb': round(result.get('pb') or 0, 2),
                'total_mv': round((result.get('total_mv') or 0) / 10000, 2),  # 转换为万元
                'pct_chg': round(result.get('pct_chg') or 0, 2),
                
                # 连板龙头策略专用字段
                'limit_times': result.get('limit_times', 0),
                'open_times': result.get('open_times', 0),
                'turnover_rate': round(result.get('turnover_rate') or 0, 2),
                'amount': round((result.get('amount') or 0) / 100000000, 2),  # 转换为亿元
                'is_leader': result.get('is_leader', False),
                'industry_strength': result.get('industry_strength', 0),
                'concept_strength': result.get('concept_strength', 0),
                
                # 综合评分
                'score': round(result.get('score') or 0, 2),
                
                # 选股理由
                'reason': self._generate_reason(result)
            }
            processed.append(stock_info)
        
        return processed
    
    def _generate_reason(self, result: Dict) -> str:
        """生成选股理由"""
        reasons = []
        
        limit_times = result.get('limit_times', 0)
        open_times = result.get('open_times', 0)
        turnover_rate = result.get('turnover_rate', 0)
        is_leader = result.get('is_leader', False)
        score = result.get('score', 0)
        
        # 连板情况
        if limit_times >= 5:
            reasons.append(f"{limit_times}连板妖股")
        elif limit_times >= 3:
            reasons.append(f"{limit_times}连板强势")
        else:
            reasons.append(f"{limit_times}连板")
        
        # 开板情况
        if open_times == 0:
            reasons.append("未开板")
        elif open_times == 1:
            reasons.append("开板1次")
        else:
            reasons.append(f"开板{open_times}次")
        
        # 换手率
        if turnover_rate >= 20:
            reasons.append(f"高换手{turnover_rate:.1f}%")
        elif turnover_rate >= 10:
            reasons.append(f"活跃换手{turnover_rate:.1f}%")
        else:
            reasons.append(f"换手{turnover_rate:.1f}%")
        
        # 龙头地位
        if is_leader:
            reasons.append("板块龙头")
        
        reasons.append(f"龙头评分{score:.0f}")
        
        return "；".join(reasons)


# 测试函数
async def test_limit_up_leader_adapter():
    """测试连板龙头策略适配器"""
    adapter = LimitUpLeaderAdapter()
    result = await adapter.screen_stocks(limit=5)
    
    print(f"策略名称: {result['strategy_name']}")
    print(f"选股数量: {result['total_count']}")
    
    for i, stock in enumerate(result['stocks'], 1):
        print(f"{i}. {stock['name']} ({stock['ts_code']})")
        print(f"   连板: {stock['limit_times']}次, 开板: {stock['open_times']}次")
        print(f"   评分: {stock['score']}, 理由: {stock['reason']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_limit_up_leader_adapter())