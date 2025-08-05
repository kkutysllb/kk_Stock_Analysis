#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连板龙头策略适配器
从API层提取的核心选股逻辑

策略特点：
- 基于涨跌停数据的真实连板分析
- 专注于连续涨停的龙头股票
- 适合短线强势追涨操作
- 重点关注连板稳定性和资金参与度
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class LimitUpLeaderAdapter:
    """连板龙头策略适配器"""
    
    def __init__(self):
        self.strategy_name = "连板龙头策略"
        self.strategy_type = "limit_up"
        self.description = "基于涨跌停数据的连板龙头选股策略"
        self.db_handler = get_global_db_handler()
        
        # 策略参数
        self.params = {
            # 连板要求
            'min_limit_times': 2,        # 最小连板次数
            'max_limit_times': 10,       # 最大连板次数
            'max_open_times': 3,         # 最大开板次数
            
            # 成交量要求
            'min_turnover': 5.0,         # 最小换手率
            'max_turnover': 30.0,        # 最大换手率
            
            # 市值要求
            'min_market_cap': 500000,    # 最小市值（万元）>= 5亿
            'max_market_cap': 50000000,  # 最大市值（万元）<= 500亿
            
            # 排除条件
            'exclude_st': True,          # 排除ST股票
            'exclude_new_stock': True,   # 排除次新股
            
            # 评分权重
            'limit_times_weight': 10,    # 连板次数权重
            'stability_weight': 15,      # 稳定性权重（开板次数越少越好）
            'turnover_weight': 8,        # 换手率权重
            'market_cap_weight': 5,      # 市值权重
            'momentum_weight': 12,       # 动量权重
            
            # 基础评分
            'base_score': 30,            # 基础分
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           **kwargs) -> Dict[str, Any]:
        """
        连板龙头策略选股
        
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
                    **self.params
                }
            }
            
        except Exception as e:
            print(f"❌ 连板龙头策略选股失败: {e}")
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
        """构建连板龙头筛选管道"""
        pipeline = []
        
        # 获取最新涨跌停日期
        latest_date = await self._get_latest_limit_date()
        
        pipeline.extend([
            # 第一步：筛选涨停连板股票
            {"$match": {
                "trade_date": latest_date,
                "limit": "U",  # 涨停
                "limit_times": {"$gte": self.params['min_limit_times'], "$lte": self.params['max_limit_times']},
                "open_times": {"$lte": self.params['max_open_times']}
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
            {"$match": await self._build_exclusion_conditions()},
            
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
                    }}
                ],
                "as": "factor_data"
            }},
            {"$unwind": {"path": "$factor_data", "preserveNullAndEmptyArrays": True}},
            
            # 第五步：应用市值和换手率筛选
            {"$match": await self._build_technical_conditions(market_cap, stock_pool)},
            
            # 第六步：计算连板龙头评分
            {"$addFields": {
                "score": {
                    "$add": [
                        # 基础分
                        self.params['base_score'],
                        
                        # 连板次数得分：每连板1次得10分
                        {"$multiply": ["$limit_times", self.params['limit_times_weight']]},
                        
                        # 稳定性得分：开板次数越少得分越高，最高15分
                        {"$subtract": [
                            self.params['stability_weight'],
                            {"$multiply": ["$open_times", 5]}
                        ]},
                        
                        # 换手率得分：适中的换手率得分，最高15分
                        {"$cond": {
                            "if": {"$and": [
                                {"$gte": [{"$ifNull": ["$factor_data.turnover_rate", 0]}, self.params['min_turnover']]},
                                {"$lte": [{"$ifNull": ["$factor_data.turnover_rate", 0]}, self.params['max_turnover']]}
                            ]},
                            "then": {"$multiply": [
                                {"$min": [{"$ifNull": ["$factor_data.turnover_rate", 0]}, 20]},
                                0.75
                            ]},
                            "else": 0
                        }},
                        
                        # 市值得分：中等市值得分最高，最高5分
                        {"$cond": {
                            "if": {"$and": [
                                {"$gte": [{"$ifNull": ["$factor_data.total_mv", 0]}, 1000000]},
                                {"$lte": [{"$ifNull": ["$factor_data.total_mv", 0]}, 10000000]}
                            ]},
                            "then": self.params['market_cap_weight'],
                            "else": 2
                        }},
                        
                        # 动量得分：基于首次涨停到现在的表现，最高12分
                        {"$cond": {
                            "if": {"$gte": ["$limit_times", 3]},
                            "then": self.params['momentum_weight'],
                            "else": {"$multiply": ["$limit_times", 4]}
                        }}
                    ]
                },
                
                # 计算龙头强度指标
                "leader_strength": {
                    "$multiply": [
                        "$limit_times",
                        {"$subtract": [4, "$open_times"]},  # 开板次数越少强度越高
                        {"$divide": [{"$ifNull": ["$factor_data.turnover_rate", 1]}, 10]}
                    ]
                },
                
                # 判断是否为强势龙头
                "is_strong_leader": {
                    "$and": [
                        {"$gte": ["$limit_times", 3]},
                        {"$lte": ["$open_times", 1]},
                        {"$gte": [{"$ifNull": ["$factor_data.turnover_rate", 0]}, 8]}
                    ]
                }
            }},
            
            # 第七步：选择输出字段
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": "$stock_info.industry",
                "trade_date": 1,
                "score": 1,
                
                # 连板相关字段
                "limit_times": 1,
                "open_times": 1,
                "first_time": 1,
                "last_time": 1,
                "leader_strength": 1,
                "is_strong_leader": 1,
                
                # 技术因子字段
                "close": "$factor_data.close",
                "pct_chg": "$factor_data.pct_chg",
                "volume": "$factor_data.volume",
                "amount": "$factor_data.amount",
                "turnover_rate": "$factor_data.turnover_rate",
                "total_mv": "$factor_data.total_mv",
                "pe": "$factor_data.pe",
                "pb": "$factor_data.pb"
            }},
            
            # 第八步：排序和限制
            {"$sort": {"score": -1, "limit_times": -1, "open_times": 1}},
            {"$limit": limit}
        ])
        
        return pipeline
    
    async def _build_exclusion_conditions(self) -> Dict:
        """构建排除条件"""
        conditions = {}
        
        # 排除ST股票
        if self.params['exclude_st']:
            conditions["stock_info.name"] = {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
        
        return conditions
    
    async def _build_technical_conditions(self, market_cap: str, stock_pool: str) -> Dict:
        """构建技术条件"""
        conditions = {
            # 换手率要求
            "factor_data.turnover_rate": {
                "$gte": self.params['min_turnover'], 
                "$lte": self.params['max_turnover']
            },
            
            # 基础市值要求
            "factor_data.total_mv": {"$gte": self.params['min_market_cap']}
        }
        
        # 市值筛选
        if market_cap == "large":
            conditions["factor_data.total_mv"] = {"$gte": 5000000}
        elif market_cap == "mid":
            conditions["factor_data.total_mv"] = {"$gte": 1000000, "$lte": 5000000}
        elif market_cap == "small":
            conditions["factor_data.total_mv"] = {"$lte": 1000000}
        
        # 股票池筛选
        if stock_pool != "all":
            # 这里可以根据需要添加股票池筛选逻辑
            pass
        
        return conditions
    
    async def _process_results(self, results: List[Dict]) -> List[Dict]:
        """处理查询结果"""
        processed = []
        
        for result in results:
            stock_info = {
                'ts_code': result.get('ts_code'),
                'name': result.get('name', ''),
                'industry': result.get('industry', ''),
                'trade_date': result.get('trade_date'),
                
                # 基础指标
                'close': round(result.get('close', 0), 2),
                'pct_chg': round(result.get('pct_chg', 0), 2),
                'pe': round(result.get('pe', 0), 2),
                'pb': round(result.get('pb', 0), 2),
                'total_mv': round(result.get('total_mv', 0) / 10000, 2),  # 转换为亿元
                
                # 成交量指标
                'volume': round(result.get('volume', 0) / 10000, 0),  # 转换为万手
                'amount': round(result.get('amount', 0) / 10000, 2),  # 转换为万元
                'turnover_rate': round(result.get('turnover_rate', 0), 2),
                
                # 连板指标
                'limit_times': result.get('limit_times', 0),
                'open_times': result.get('open_times', 0),
                'first_time': result.get('first_time', ''),
                'last_time': result.get('last_time', ''),
                'leader_strength': round(result.get('leader_strength', 0), 2),
                'is_strong_leader': result.get('is_strong_leader', False),
                
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
        
        limit_times = result.get('limit_times', 0)
        open_times = result.get('open_times', 0)
        turnover_rate = result.get('turnover_rate', 0)
        is_strong_leader = result.get('is_strong_leader', False)
        leader_strength = result.get('leader_strength', 0)
        score = result.get('score', 0)
        
        # 连板强度
        if limit_times >= 5:
            reasons.append(f"{limit_times}连板超强")
        elif limit_times >= 3:
            reasons.append(f"{limit_times}连板强势")
        else:
            reasons.append(f"{limit_times}连板")
        
        # 稳定性
        if open_times == 0:
            reasons.append("无开板稳定")
        elif open_times == 1:
            reasons.append("1次开板较稳定")
        else:
            reasons.append(f"{open_times}次开板")
        
        # 资金参与
        if turnover_rate >= 20:
            reasons.append(f"换手率{turnover_rate:.1f}%活跃")
        elif turnover_rate >= 10:
            reasons.append(f"换手率{turnover_rate:.1f}%适中")
        
        # 龙头地位
        if is_strong_leader:
            reasons.append("强势龙头")
        elif leader_strength >= 10:
            reasons.append("龙头地位")
        
        reasons.append(f"连板评分{score:.0f}")
        
        return "；".join(reasons)
    
    async def _get_latest_limit_date(self) -> str:
        """获取最新涨跌停数据日期"""
        try:
            collection = self.db_handler.get_collection('limit_list_daily')
            result = collection.find({}, {"trade_date": 1}).sort("trade_date", -1).limit(1)
            latest = list(result)[0]
            return latest['trade_date']
        except:
            return "20241231"  # 默认日期


# 测试函数
async def test_limit_up_leader_adapter():
    """测试连板龙头策略适配器"""
    adapter = LimitUpLeaderAdapter()
    result = await adapter.screen_stocks(
        market_cap="all", 
        stock_pool="all", 
        limit=10,
        min_limit_times=2
    )
    
    print(f"策略名称: {result['strategy_name']}")
    print(f"选股数量: {result['total_count']}")
    
    for i, stock in enumerate(result['stocks'][:5], 1):
        print(f"{i}. {stock['name']} ({stock['ts_code']})")
        print(f"   连板: {stock['limit_times']}次, 开板: {stock['open_times']}次")
        print(f"   评分: {stock['score']}, 理由: {stock['reason']}")


if __name__ == "__main__":
    asyncio.run(test_limit_up_leader_adapter())