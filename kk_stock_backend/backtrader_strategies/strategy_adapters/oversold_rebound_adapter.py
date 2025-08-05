#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超跌反弹策略适配器
从API层提取的核心选股逻辑

策略特点：
- 专注于超跌后的反弹机会
- 多维度识别超跌反弹股票
- 适合短线反弹操作
- 基于RSI、估值、成交量等综合判断
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class OversoldReboundAdapter:
    """超跌反弹策略适配器"""
    
    def __init__(self):
        self.strategy_name = "超跌反弹策略"
        self.strategy_type = "rebound"
        self.description = "多维度识别超跌反弹机会的选股策略"
        self.db_handler = get_global_db_handler()
        
        # 策略参数
        self.params = {
            # RSI超跌参数
            'rsi_max': 35.0,             # RSI上限：超跌区域
            'rsi_min': 15.0,             # RSI下限：避免极端情况
            
            # 成交量参数
            'volume_ratio_min': 1.3,     # 量比下限：成交量放大
            'turnover_rate_min': 1.5,    # 换手率下限
            'turnover_rate_max': 25.0,   # 换手率上限
            
            # 估值参数
            'pe_max': 50.0,              # PE上限：避免高估值
            'pb_max': 8.0,               # PB上限：避免高估值
            
            # 市值要求
            'min_market_cap': 300000,    # 最小市值（万元）>= 3亿
            
            # 技术位要求
            'require_below_ma20': True,  # 要求低于20日均线
            'require_below_ma60': True,  # 要求低于60日均线
            
            # 排除条件
            'exclude_st': True,          # 排除ST股票
            
            # 评分权重
            'base_score': 20,            # 基础分：符合超跌条件
            'rsi_weight': 1.25,          # RSI权重：越低得分越高
            'volume_weight': 4,          # 量比权重
            'pe_weight': 3,              # PE权重
            'turnover_bonus': 5,         # 换手率奖励分
            
            # 信号阈值
            'rebound_threshold': 55,     # 反弹信号评分阈值
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           **kwargs) -> Dict[str, Any]:
        """
        超跌反弹策略选股
        
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
            print(f"❌ 超跌反弹策略选股失败: {e}")
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
        """构建超跌反弹筛选管道"""
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
            
            # 第三步：排除ST股票
            {"$match": await self._build_exclusion_conditions()},
            
            # 第四步：计算超跌反弹评分
            {"$addFields": {
                "score": {
                    "$add": [
                        # 基础分：符合超跌条件得20分
                        self.params['base_score'],
                        
                        # RSI得分：越低得分越高，15-35区间得0-25分
                        {"$multiply": [
                            {"$subtract": [self.params['rsi_max'], "$rsi_qfq_12"]}, 
                            self.params['rsi_weight']
                        ]},
                        
                        # 量比得分：量比越高得分越高，最高20分
                        {"$min": [
                            20, 
                            {"$multiply": [
                                {"$subtract": ["$volume_ratio", 1]}, 
                                self.params['volume_weight']
                            ]}
                        ]},
                        
                        # 估值得分：PE越低得分越高，最高15分
                        {"$min": [
                            15, 
                            {"$multiply": [
                                {"$divide": [25, "$pe"]}, 
                                self.params['pe_weight']
                            ]}
                        ]},
                        
                        # 反弹信号得分：当日表现评分，最高15分
                        {"$cond": {
                            "if": {"$gt": ["$pct_chg", 3]},
                            "then": 15,
                            "else": {"$cond": {
                                "if": {"$gt": ["$pct_chg", 0]},
                                "then": 10,
                                "else": {"$cond": {
                                    "if": {"$gt": ["$pct_chg", -2]},
                                    "then": 5,
                                    "else": 0
                                }}
                            }}
                        }},
                        
                        # 换手率得分：适中的换手率得分，最高5分
                        {"$cond": {
                            "if": {"$and": [
                                {"$gte": ["$turnover_rate", 2]}, 
                                {"$lte": ["$turnover_rate", 10]}
                            ]},
                            "then": self.params['turnover_bonus'],
                            "else": 0
                        }}
                    ]
                },
                
                # 判断反弹信号
                "rebound_signal": {
                    "$gte": [
                        {"$add": [
                            self.params['base_score'],
                            {"$multiply": [{"$subtract": [self.params['rsi_max'], "$rsi_qfq_12"]}, self.params['rsi_weight']]},
                            {"$min": [20, {"$multiply": [{"$subtract": ["$volume_ratio", 1]}, self.params['volume_weight']]}]},
                            {"$min": [15, {"$multiply": [{"$divide": [25, "$pe"]}, self.params['pe_weight']]}]},
                            {"$cond": {
                                "if": {"$gt": ["$pct_chg", 3]},
                                "then": 15,
                                "else": {"$cond": {
                                    "if": {"$gt": ["$pct_chg", 0]},
                                    "then": 10,
                                    "else": {"$cond": {
                                        "if": {"$gt": ["$pct_chg", -2]},
                                        "then": 5,
                                        "else": 0
                                    }}
                                }}
                            }},
                            {"$cond": {
                                "if": {"$and": [{"$gte": ["$turnover_rate", 2]}, {"$lte": ["$turnover_rate", 10]}]},
                                "then": self.params['turnover_bonus'],
                                "else": 0
                            }}
                        ]},
                        self.params['rebound_threshold']
                    ]
                },
                
                # 计算距离均线的偏离度
                "ma20_deviation": {
                    "$multiply": [
                        {"$divide": [
                            {"$subtract": ["$close", "$ma_qfq_20"]},
                            "$ma_qfq_20"
                        ]},
                        100
                    ]
                },
                
                "ma60_deviation": {
                    "$multiply": [
                        {"$divide": [
                            {"$subtract": ["$close", "$ma_qfq_60"]},
                            "$ma_qfq_60"
                        ]},
                        100
                    ]
                }
            }},
            
            # 第五步：选择输出字段
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
                
                # 超跌反弹策略专用字段
                "rsi": "$rsi_qfq_12",
                "volume_ratio": 1,
                "turnover_rate": 1,
                "ma_20": "$ma_qfq_20",
                "ma_60": "$ma_qfq_60",
                "ma20_deviation": 1,
                "ma60_deviation": 1,
                "rebound_signal": 1
            }},
            
            # 第六步：排序和限制
            {"$sort": {"score": -1}},
            {"$limit": limit}
        ])
        
        return pipeline
    
    async def _build_match_conditions(self, latest_date: str, market_cap: str, stock_pool: str) -> Dict:
        """构建基础匹配条件"""
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": 0},
            "total_mv": {"$gte": self.params['min_market_cap']},              # 市值要求
            "rsi_qfq_12": {"$gte": self.params['rsi_min'], "$lte": self.params['rsi_max']},  # RSI超跌区域
            "volume_ratio": {"$gte": self.params['volume_ratio_min']},         # 量比放大
            "pe": {"$gt": 0, "$lte": self.params['pe_max']},                  # PE合理
            "pb": {"$gt": 0, "$lte": self.params['pb_max']},                  # PB合理
            "turnover_rate": {"$gte": self.params['turnover_rate_min'], "$lte": self.params['turnover_rate_max']}  # 换手率适中
        }
        
        # 构建$expr条件：技术位判断
        expr_conditions = []
        
        if self.params['require_below_ma20']:
            expr_conditions.append({"$lt": ["$close", "$ma_qfq_20"]})     # 低于20日均线
        
        if self.params['require_below_ma60']:
            expr_conditions.append({"$lt": ["$close", "$ma_qfq_60"]})     # 低于60日均线
        
        if expr_conditions:
            match_conditions["$expr"] = {"$and": expr_conditions}
        
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
    
    async def _build_exclusion_conditions(self) -> Dict:
        """构建排除条件"""
        conditions = {}
        
        # 排除ST股票
        if self.params['exclude_st']:
            conditions["stock_info.name"] = {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
        
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
                
                # 技术指标
                'rsi': round(result.get('rsi', 0), 1),
                'volume_ratio': round(result.get('volume_ratio', 0), 2),
                'turnover_rate': round(result.get('turnover_rate', 0), 2),
                
                # 均线指标
                'ma_20': round(result.get('ma_20', 0), 2),
                'ma_60': round(result.get('ma_60', 0), 2),
                'ma20_deviation': round(result.get('ma20_deviation', 0), 2),
                'ma60_deviation': round(result.get('ma60_deviation', 0), 2),
                
                # 信号指标
                'rebound_signal': result.get('rebound_signal', False),
                
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
        
        pct_chg = result.get('pct_chg', 0)
        rsi = result.get('rsi', 0)
        volume_ratio = result.get('volume_ratio', 0)
        pe = result.get('pe', 0)
        ma20_deviation = result.get('ma20_deviation', 0)
        rebound_signal = result.get('rebound_signal', False)
        score = result.get('score', 0)
        
        # 超跌状态
        if rsi <= 20:
            reasons.append(f"RSI{rsi:.0f}严重超跌")
        elif rsi <= 30:
            reasons.append(f"RSI{rsi:.0f}超跌")
        
        # 估值水平
        if pe <= 15:
            reasons.append(f"PE{pe:.1f}低估值")
        elif pe <= 25:
            reasons.append(f"PE{pe:.1f}合理估值")
        
        # 成交量
        if volume_ratio >= 2:
            reasons.append(f"放量{volume_ratio:.1f}倍")
        elif volume_ratio >= 1.5:
            reasons.append(f"温和放量{volume_ratio:.1f}倍")
        
        # 价格表现
        if pct_chg >= 3:
            reasons.append(f"反弹{pct_chg:.1f}%")
        elif pct_chg > 0:
            reasons.append(f"微涨{pct_chg:.1f}%")
        elif pct_chg >= -2:
            reasons.append("企稳")
        
        # 技术位置
        if ma20_deviation <= -10:
            reasons.append(f"距20日线{abs(ma20_deviation):.1f}%")
        
        if rebound_signal:
            reasons.append("反弹信号")
        
        reasons.append(f"超跌评分{score:.0f}")
        
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
async def test_oversold_rebound_adapter():
    """测试超跌反弹策略适配器"""
    adapter = OversoldReboundAdapter()
    result = await adapter.screen_stocks(
        market_cap="all", 
        stock_pool="all", 
        limit=10,
        rsi_max=30
    )
    
    print(f"策略名称: {result['strategy_name']}")
    print(f"选股数量: {result['total_count']}")
    
    for i, stock in enumerate(result['stocks'][:5], 1):
        print(f"{i}. {stock['name']} ({stock['ts_code']})")
        print(f"   涨跌幅: {stock['pct_chg']}%, RSI: {stock['rsi']}, PE: {stock['pe']}")
        print(f"   评分: {stock['score']}, 理由: {stock['reason']}")


if __name__ == "__main__":
    asyncio.run(test_oversold_rebound_adapter())