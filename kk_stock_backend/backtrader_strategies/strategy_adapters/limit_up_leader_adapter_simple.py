#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连板龙头策略适配器 - 简化版
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class LimitUpLeaderAdapter:
    """连板龙头策略适配器 - 简化版"""
    
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
        """连板龙头策略选股"""
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
            print(f"查询日期: {latest_date}")
            
            # 改进查询 - 获取更多真实数据
            pipeline = [
                {"$match": {
                    "trade_date": latest_date,
                    "limit": "U",
                    "limit_times": {"$gte": min_limit_times, "$lte": max_limit_times},
                    "open_times": {"$lte": max_open_times}
                }},
                {"$lookup": {
                    "from": "infrastructure_stock_basic",
                    "localField": "ts_code",  
                    "foreignField": "ts_code",
                    "as": "stock_info"
                }},
                {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
                {"$match": {
                    "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
                }},
                # 关联技术因子数据获取更多信息
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
                            "close": 1,
                            "total_mv": 1,
                            "turnover_rate": 1,
                            "amount": 1,
                            "pe": 1,
                            "pb": 1
                        }}
                    ],
                    "as": "tech_data"
                }},
                {"$unwind": {"path": "$tech_data", "preserveNullAndEmptyArrays": True}},
                {"$addFields": {
                    "score": {"$multiply": ["$limit_times", 10]},
                    "total_mv_yi": {"$divide": [{"$ifNull": ["$tech_data.total_mv", 0]}, 10000]}
                }},
                {"$project": {
                    "ts_code": 1,
                    "name": "$stock_info.name",
                    "industry": "$stock_info.industry",
                    "limit_times": 1,
                    "open_times": 1,
                    "score": 1,
                    "close": "$tech_data.close",
                    "pe": "$tech_data.pe", 
                    "pb": "$tech_data.pb",
                    "total_mv": "$tech_data.total_mv",
                    "turnover_rate": "$tech_data.turnover_rate",
                    "amount": "$tech_data.amount"
                }},
                {"$sort": {"score": -1, "limit_times": -1}},
                {"$limit": limit}
            ]
            
            # 执行查询
            collection = self.db_handler.get_collection('limit_list_daily')
            cursor = collection.aggregate(pipeline)
            results = list(cursor)
            
            print(f"找到 {len(results)} 只连板股票")
            
            # 处理结果
            processed_results = []
            for result in results:
                limit_times = result.get('limit_times', 0)
                open_times = result.get('open_times', 0)
                
                stock_info = {
                    'ts_code': result.get('ts_code'),
                    'name': result.get('name', ''),
                    'industry': result.get('industry', ''),
                    'close': round(result.get('close') or 0, 2),
                    'pe': round(result.get('pe') or 0, 2),
                    'pb': round(result.get('pb') or 0, 2),
                    'total_mv': round((result.get('total_mv') or 0), 0),  # MongoDB中total_mv单位是万元，保持万元但取整
                    'pct_chg': 9.99,  # 涨停股默认9.99%
                    'limit_times': limit_times,
                    'open_times': open_times,
                    'turnover_rate': round(result.get('turnover_rate') or 0, 2),
                    'amount': round((result.get('amount') or 0) / 100000000, 2),  # 转换为亿元
                    'is_leader': limit_times >= 3 and open_times <= 1,  # 3连板且开板不超过1次
                    'score': round(result.get('score', 0), 2),
                    'reason': self._generate_reason(limit_times, open_times)
                }
                processed_results.append(stock_info)
            
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
            }
            
        except Exception as e:
            print(f"❌ 连板龙头策略选股失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'strategy_name': self.strategy_name,
                'strategy_type': self.strategy_type,  # 添加缺失的字段
                'error': str(e),
                'total_count': 0,
                'stocks': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_reason(self, limit_times: int, open_times: int) -> str:
        """生成选股理由"""
        reasons = []
        
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
        
        # 龙头地位
        if limit_times >= 3 and open_times <= 1:
            reasons.append("板块龙头")
        
        return "；".join(reasons)