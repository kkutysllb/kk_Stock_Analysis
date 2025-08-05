#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金追踪策略适配器
从API层提取的核心选股逻辑

策略特点：
- 追踪主力资金流向
- 关注大单净流入情况
- 适合跟随资金热点的投资策略
- 基于成交量、资金流向等量化指标
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class FundFlowTrackingAdapter:
    """资金追踪策略适配器"""
    
    def __init__(self):
        self.strategy_name = "资金追踪策略"
        self.strategy_type = "fund_flow"
        self.description = "追踪主力资金流向的选股策略"
        self.db_handler = get_global_db_handler()
        
        # 策略参数
        self.params = {
            # 资金流入要求
            'min_net_amount': 10000000,      # 最小净流入金额（元）>= 1000万
            'min_large_order_ratio': 15.0,   # 最小大单占比 >= 15%
            'min_volume_ratio': 1.5,         # 最小量比 >= 1.5
            
            # 技术指标要求
            'min_turnover_rate': 2.0,        # 最小换手率 >= 2%
            'max_turnover_rate': 25.0,       # 最大换手率 <= 25%
            'rsi_min': 35.0,                 # RSI下限
            'rsi_max': 80.0,                 # RSI上限
            
            # 市值要求
            'min_market_cap': 1000000,       # 最小市值（万元）>= 10亿
            'max_market_cap': 100000000,     # 最大市值（万元）<= 1000亿
            
            # 价格要求
            'min_price': 3.0,                # 最低价格
            'max_price': 200.0,              # 最高价格
            'max_pct_chg': 9.5,              # 最大涨幅（避免涨停板）
            
            # 排除条件
            'exclude_st': True,              # 排除ST股票
            'require_positive_flow': True,   # 要求资金净流入
            
            # 评分权重
            'net_amount_weight': 0.3,        # 净流入金额权重 30%
            'large_order_weight': 0.25,      # 大单占比权重 25%
            'volume_weight': 0.2,            # 成交量权重 20%
            'technical_weight': 0.15,        # 技术指标权重 15%
            'momentum_weight': 0.1,          # 动量权重 10%
            
            # 基础评分
            'base_score': 20,                # 基础分
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           **kwargs) -> Dict[str, Any]:
        """
        资金追踪策略选股
        
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
            print(f"❌ 资金追踪策略选股失败: {e}")
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
        """构建资金追踪筛选管道"""
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
            
            # 第四步：计算资金流向指标
            {"$addFields": {
                # 计算净流入金额（基于成交金额和涨跌幅估算）
                "net_inflow_amount": {
                    "$multiply": [
                        {"$ifNull": ["$amount", 0]},
                        {"$cond": {
                            "if": {"$gt": ["$pct_chg", 0]},
                            "then": {"$multiply": ["$pct_chg", 0.1]},  # 上涨时按比例计算净流入
                            "else": {"$multiply": ["$pct_chg", -0.1]}  # 下跌时为净流出
                        }}
                    ]
                },
                
                # 计算大单占比（基于换手率和成交金额估算）
                "large_order_ratio": {
                    "$cond": {
                        "if": {"$gt": [{"$ifNull": ["$amount", 0]}, 0]},
                        "then": {"$multiply": [
                            {"$min": [{"$ifNull": ["$turnover_rate", 0]}, 20]},
                            0.8
                        ]},
                        "else": 0
                    }
                },
                
                # 计算主力资金净流入率
                "main_fund_ratio": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": ["$pct_chg", 0]},
                            {"$gte": ["$volume_ratio", 1.5]}
                        ]},
                        "then": {"$multiply": ["$pct_chg", 2]},
                        "else": 0
                    }
                },
                
                # 计算资金活跃度
                "fund_activity": {
                    "$multiply": [
                        {"$ifNull": ["$volume_ratio", 1]},
                        {"$ifNull": ["$turnover_rate", 1]},
                        0.1
                    ]
                }
            }},
            
            # 第五步：应用资金流向筛选条件
            {"$match": await self._build_fund_flow_conditions()},
            
            # 第六步：计算资金追踪评分
            {"$addFields": {
                "score": {
                    "$add": [
                        # 基础分
                        self.params['base_score'],
                        
                        # 净流入金额得分：每1000万得5分，最高30分
                        {"$min": [
                            30,
                            {"$multiply": [
                                {"$divide": [{"$max": ["$net_inflow_amount", 0]}, 10000000]},
                                5
                            ]}
                        ]},
                        
                        # 大单占比得分：每5%得5分，最高25分
                        {"$min": [
                            25,
                            {"$multiply": [
                                {"$divide": [{"$max": ["$large_order_ratio", 0]}, 5]},
                                5
                            ]}
                        ]},
                        
                        # 成交量得分：量比权重，最高20分
                        {"$min": [
                            20,
                            {"$multiply": [
                                {"$max": [{"$subtract": ["$volume_ratio", 1]}, 0]},
                                5
                            ]}
                        ]},
                        
                        # 技术指标得分：RSI适中区间得分，最高15分
                        {"$cond": {
                            "if": {"$and": [
                                {"$gte": ["$rsi_qfq_12", 40]},
                                {"$lte": ["$rsi_qfq_12", 70]}
                            ]},
                            "then": 15,
                            "else": {"$cond": {
                                "if": {"$and": [
                                    {"$gte": ["$rsi_qfq_12", 35]},
                                    {"$lte": ["$rsi_qfq_12", 80]}
                                ]},
                                "then": 10,
                                "else": 5
                            }}
                        }},
                        
                        # 动量得分：涨幅权重，最高10分
                        {"$min": [
                            10,
                            {"$multiply": [{"$max": ["$pct_chg", 0]}, 2]}
                        ]}
                    ]
                },
                
                # 判断是否为资金热点
                "is_fund_hotspot": {
                    "$and": [
                        {"$gte": ["$net_inflow_amount", {"$multiply": [self.params['min_net_amount'], 2]}]},
                        {"$gte": ["$large_order_ratio", self.params['min_large_order_ratio']]},
                        {"$gte": ["$volume_ratio", 2.0]}
                    ]
                }
            }},
            
            # 第七步：选择输出字段
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
                
                # 资金追踪专用字段
                "volume": 1,
                "amount": 1,
                "volume_ratio": 1,
                "turnover_rate": 1,
                "rsi": "$rsi_qfq_12",
                "net_inflow_amount": 1,
                "large_order_ratio": 1,
                "main_fund_ratio": 1,
                "fund_activity": 1,
                "is_fund_hotspot": 1
            }},
            
            # 第八步：排序和限制
            {"$sort": {"score": -1, "net_inflow_amount": -1}},
            {"$limit": limit}
        ])
        
        return pipeline
    
    async def _build_match_conditions(self, latest_date: str, market_cap: str, stock_pool: str) -> Dict:
        """构建基础匹配条件"""
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gte": self.params['min_price'], "$lte": self.params['max_price']},
            "total_mv": {"$gte": self.params['min_market_cap']},
            "volume_ratio": {"$gte": self.params['min_volume_ratio']},
            "turnover_rate": {"$gte": self.params['min_turnover_rate'], "$lte": self.params['max_turnover_rate']},
            "rsi_qfq_12": {"$gte": self.params['rsi_min'], "$lte": self.params['rsi_max']},
            "pct_chg": {"$lte": self.params['max_pct_chg']}  # 避免涨停板
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
    
    async def _build_exclusion_conditions(self) -> Dict:
        """构建排除条件"""
        conditions = {}
        
        # 排除ST股票
        if self.params['exclude_st']:
            conditions["stock_info.name"] = {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
        
        return conditions
    
    async def _build_fund_flow_conditions(self) -> Dict:
        """构建资金流向筛选条件"""
        conditions = {}
        
        # 要求资金净流入
        if self.params['require_positive_flow']:
            conditions["net_inflow_amount"] = {"$gte": self.params['min_net_amount']}
        
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
                
                # 成交量指标
                'volume': round(result.get('volume', 0) / 10000, 0),  # 转换为万手
                'amount': round(result.get('amount', 0) / 10000, 2),  # 转换为万元
                'volume_ratio': round(result.get('volume_ratio', 0), 2),
                'turnover_rate': round(result.get('turnover_rate', 0), 2),
                'rsi': round(result.get('rsi', 0), 1),
                
                # 资金流向指标
                'net_inflow_amount': round(result.get('net_inflow_amount', 0) / 10000, 2),  # 转换为万元
                'large_order_ratio': round(result.get('large_order_ratio', 0), 1),
                'main_fund_ratio': round(result.get('main_fund_ratio', 0), 2),
                'fund_activity': round(result.get('fund_activity', 0), 2),
                'is_fund_hotspot': result.get('is_fund_hotspot', False),
                
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
        
        net_inflow = result.get('net_inflow_amount', 0)
        large_order_ratio = result.get('large_order_ratio', 0)
        volume_ratio = result.get('volume_ratio', 0)
        pct_chg = result.get('pct_chg', 0)
        is_fund_hotspot = result.get('is_fund_hotspot', False)
        score = result.get('score', 0)
        
        # 资金流入情况
        if net_inflow >= 50000000:  # 5000万
            reasons.append(f"大幅净流入{net_inflow/10000:.0f}万")
        elif net_inflow >= 20000000:  # 2000万
            reasons.append(f"净流入{net_inflow/10000:.0f}万")
        elif net_inflow > 0:
            reasons.append(f"小幅净流入{net_inflow/10000:.0f}万")
        
        # 大单情况
        if large_order_ratio >= 25:
            reasons.append(f"大单占比{large_order_ratio:.1f}%")
        elif large_order_ratio >= 15:
            reasons.append(f"大单活跃{large_order_ratio:.1f}%")
        
        # 成交量
        if volume_ratio >= 3:
            reasons.append(f"放量{volume_ratio:.1f}倍")
        elif volume_ratio >= 2:
            reasons.append(f"温和放量{volume_ratio:.1f}倍")
        
        # 价格表现
        if pct_chg >= 5:
            reasons.append(f"强势上涨{pct_chg:.1f}%")
        elif pct_chg >= 2:
            reasons.append(f"上涨{pct_chg:.1f}%")
        elif pct_chg > 0:
            reasons.append(f"微涨{pct_chg:.1f}%")
        
        # 热点判断
        if is_fund_hotspot:
            reasons.append("资金热点")
        
        reasons.append(f"资金评分{score:.0f}")
        
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
async def test_fund_flow_tracking_adapter():
    """测试资金追踪策略适配器"""
    adapter = FundFlowTrackingAdapter()
    result = await adapter.screen_stocks(
        market_cap="all", 
        stock_pool="all", 
        limit=10,
        min_net_amount=20000000
    )
    
    print(f"策略名称: {result['strategy_name']}")
    print(f"选股数量: {result['total_count']}")
    
    for i, stock in enumerate(result['stocks'][:5], 1):
        print(f"{i}. {stock['name']} ({stock['ts_code']})")
        print(f"   净流入: {stock['net_inflow_amount']}万, 量比: {stock['volume_ratio']}")
        print(f"   评分: {stock['score']}, 理由: {stock['reason']}")


if __name__ == "__main__":
    asyncio.run(test_fund_flow_tracking_adapter())