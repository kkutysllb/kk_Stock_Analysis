#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动量突破策略适配器
从API层提取的核心选股逻辑

策略特点：
- 基于价格动量和技术突破信号
- 重点关注量价配合的突破股票
- 适合短中线趋势跟随
- 使用RSI、MACD、均线等多重技术指标
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class MomentumBreakthroughAdapter:
    """动量突破策略适配器"""
    
    def __init__(self):
        self.strategy_name = "动量突破策略"
        self.strategy_type = "momentum"
        self.description = "基于价格动量和技术突破的选股策略"
        self.db_handler = get_global_db_handler()
        
        # 策略参数
        self.params = {
            # 技术指标参数
            'rsi_min': 50,               # RSI最小值
            'rsi_max': 70,               # RSI最大值
            'volume_ratio_min': 1.5,     # 量比最小值
            'require_macd_golden': True, # 是否要求MACD金叉
            
            # 动量参数
            'period_days': 60,           # 动量计算周期
            'rps_threshold': 80,         # RPS相对强度阈值
            
            # 突破信号参数
            'require_ma_breakthrough': True,  # 要求均线突破
            'min_price': 2.0,           # 最低价格要求
            'max_price': 500.0,         # 最高价格要求
            
            # 评分权重
            'rsi_weight': 0.15,         # RSI权重 15%
            'volume_weight': 0.25,      # 量比权重 25%
            'macd_weight': 0.20,        # MACD权重 20%
            'price_change_weight': 0.15, # 涨跌幅权重 15%
            'breakthrough_weight': 0.15, # 突破信号权重 15%
            'strength_weight': 0.10     # 相对强度权重 10%
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           **kwargs) -> Dict[str, Any]:
        """
        动量突破策略选股
        
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
            print(f"❌ 动量突破策略选股失败: {e}")
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
        """构建动量突破筛选管道"""
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
            
            # 第三步：计算衍生指标
            {"$addFields": {
                # 计算过去N日收益率（简化处理）
                "period_return": {
                    "$multiply": [
                        {"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 
                        {"$divide": [{"$convert": {"input": {"$literal": self.params['period_days']}, "to": "double", "onError": 1}}, 20]}
                    ]
                },
                
                # 计算RPS相对强度评分
                "rps_score": {
                    "$cond": {
                        "if": {"$gt": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 5]},
                        "then": {"$add": [80, {"$multiply": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 2]}]},
                        "else": {"$add": [60, {"$multiply": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 4]}]}
                    }
                },
                
                # EMA近似值（使用移动平均线）
                "ema_20": {"$convert": {"input": "$ma_qfq_20", "to": "double", "onError": 0}},
                "ema_50": {"$convert": {"input": "$ma_qfq_50", "to": "double", "onError": 0}},
                
                # 突破信号判断
                "breakthrough_signal": {
                    "$and": [
                        # 价格突破20日均线
                        {"$gt": [{"$convert": {"input": "$close", "to": "double", "onError": 0}}, {"$convert": {"input": "$ma_qfq_20", "to": "double", "onError": 0}}]},
                        # 20日均线在50日均线之上
                        {"$gt": [{"$convert": {"input": "$ma_qfq_20", "to": "double", "onError": 0}}, {"$convert": {"input": "$ma_qfq_50", "to": "double", "onError": 0}}]},
                        # 量比满足要求
                        {"$gte": [{"$convert": {"input": "$volume_ratio", "to": "double", "onError": 0}}, {"$literal": self.params['volume_ratio_min']}]},
                        # RSI在合理区间
                        {"$gte": [{"$convert": {"input": "$rsi_qfq_12", "to": "double", "onError": 0}}, {"$literal": self.params['rsi_min']}]},
                        {"$lte": [{"$convert": {"input": "$rsi_qfq_12", "to": "double", "onError": 100}}, {"$literal": self.params['rsi_max']}]}
                    ]
                },
                
                # MACD金叉信号
                "macd_golden": {
                    "$and": [
                        {"$gt": [{"$convert": {"input": "$macd_qfq", "to": "double", "onError": 0}}, 0]},
                        {"$gt": [{"$convert": {"input": "$macd_qfq", "to": "double", "onError": 0}}, {"$convert": {"input": "$macd_signal_qfq", "to": "double", "onError": 0}}]}
                    ]
                },
                
                # 综合评分计算
                "score": {
                    "$add": [
                        # RSI权重 (15%)
                        {"$multiply": [
                            {"$subtract": [75, {"$abs": {"$subtract": [{"$convert": {"input": "$rsi_qfq_12", "to": "double", "onError": 50}}, 60]}}]}, 
                            self.params['rsi_weight']
                        ]},
                        
                        # 量比权重 (25%)
                        {"$multiply": [{"$convert": {"input": "$volume_ratio", "to": "double", "onError": 1}}, self.params['volume_weight'] * 100]},
                        
                        # MACD权重 (20%)
                        {"$cond": {"if": {"$gt": [{"$convert": {"input": "$macd_qfq", "to": "double", "onError": 0}}, 0]}, "then": self.params['macd_weight'] * 100, "else": 0}},
                        
                        # 涨跌幅权重 (15%)
                        {"$multiply": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, self.params['price_change_weight'] * 20]},
                        
                        # 突破信号权重 (15%)
                        {"$cond": {"if": "$breakthrough_signal", "then": self.params['breakthrough_weight'] * 100, "else": 0}},
                        
                        # 相对强度权重 (10%)
                        {"$cond": {"if": {"$gt": [{"$convert": {"input": "$pct_chg", "to": "double", "onError": 0}}, 2]}, "then": self.params['strength_weight'] * 100, "else": 0}}
                    ]
                }
            }},
            
            # 第四步：选择输出字段
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
                
                # 动量突破策略专用字段
                "period_return": 1,
                "rps_score": 1,
                "ema_20": 1,
                "ema_50": 1,
                "volume_ratio": 1,
                "rsi": "$rsi_qfq_12",
                "macd": "$macd_qfq",
                "macd_signal": "$macd_signal_qfq",
                "macd_histogram": "$macd_histogram_qfq",
                "breakthrough_signal": 1,
                "macd_golden": 1
            }},
            
            # 第五步：排序和限制
            {"$sort": {"score": -1}},
            {"$limit": limit}
        ])
        
        return pipeline
    
    async def _build_match_conditions(self, latest_date: str, market_cap: str, stock_pool: str) -> Dict:
        """构建匹配条件"""
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": self.params['min_price'], "$lt": self.params['max_price']},  # 价格区间
            "total_mv": {"$gt": 0},  # 有效市值
            "rsi_qfq_12": {"$gte": 30, "$lte": 85},  # 放宽RSI区间
            "volume_ratio": {"$gte": 1.0},  # 基础量比要求
        }
        
        # 应用更严格的技术条件
        if self.params['rsi_min'] > 30 or self.params['rsi_max'] < 85:
            match_conditions["rsi_qfq_12"] = {"$gte": self.params['rsi_min'], "$lte": self.params['rsi_max']}
        
        if self.params['volume_ratio_min'] > 1.0:
            match_conditions["volume_ratio"] = {"$gte": self.params['volume_ratio_min']}
        
        # MACD金叉条件（可选）
        if self.params['require_macd_golden']:
            match_conditions["macd_qfq"] = {"$gt": 0}  # MACD > 0
        
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
                'close': round(result.get('close') or 0, 2),
                'pe': round(result.get('pe') or 0, 2),
                'pb': round(result.get('pb') or 0, 2),
                'total_mv': round((result.get('total_mv') or 0) / 10000, 2),  # 转换为亿元
                'pct_chg': round(result.get('pct_chg') or 0, 2),
                
                # 动量指标
                'period_return': round(result.get('period_return') or 0, 2),
                'rps_score': round(result.get('rps_score') or 0, 1),
                
                # 技术指标
                'rsi': round(result.get('rsi') or 0, 1),
                'volume_ratio': round(result.get('volume_ratio') or 0, 2),
                'macd': round(result.get('macd') or 0, 4),
                'macd_signal': round(result.get('macd_signal') or 0, 4),
                'macd_histogram': round(result.get('macd_histogram') or 0, 4),
                
                # 均线指标
                'ema_20': round(result.get('ema_20') or 0, 2),
                'ema_50': round(result.get('ema_50') or 0, 2),
                
                # 信号指标
                'breakthrough_signal': result.get('breakthrough_signal', False),
                'macd_golden': result.get('macd_golden', False),
                
                # 综合评分
                'score': round(result.get('score') or 0, 1),
                
                # 选股理由
                'reason': self._generate_reason(result)
            }
            processed.append(stock_info)
        
        return processed
    
    def _generate_reason(self, result: Dict) -> str:
        """生成选股理由"""
        reasons = []
        
        pct_chg = result.get('pct_chg', 0)
        volume_ratio = result.get('volume_ratio', 0)
        rsi = result.get('rsi', 0)
        breakthrough_signal = result.get('breakthrough_signal', False)
        macd_golden = result.get('macd_golden', False)
        score = result.get('score', 0)
        
        # 价格动量
        if pct_chg >= 5:
            reasons.append(f"强势上涨{pct_chg:.1f}%")
        elif pct_chg >= 2:
            reasons.append(f"温和上涨{pct_chg:.1f}%")
        elif pct_chg >= 0:
            reasons.append(f"微涨{pct_chg:.1f}%")
        
        # 成交量
        if volume_ratio >= 3:
            reasons.append(f"放量{volume_ratio:.1f}倍")
        elif volume_ratio >= 2:
            reasons.append(f"温和放量{volume_ratio:.1f}倍")
        elif volume_ratio >= 1.5:
            reasons.append(f"小幅放量{volume_ratio:.1f}倍")
        
        # 技术信号
        if breakthrough_signal:
            reasons.append("均线突破信号")
        
        if macd_golden:
            reasons.append("MACD金叉")
        
        if 50 <= rsi <= 70:
            reasons.append(f"RSI{rsi:.0f}适中")
        elif rsi > 70:
            reasons.append(f"RSI{rsi:.0f}强势")
        
        reasons.append(f"动量评分{score:.0f}")
        
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
async def test_momentum_breakthrough_adapter():
    """测试动量突破策略适配器"""
    adapter = MomentumBreakthroughAdapter()
    result = await adapter.screen_stocks(
        market_cap="all", 
        stock_pool="all", 
        limit=10,
        rsi_min=55,
        volume_ratio_min=2.0
    )
    
    print(f"策略名称: {result['strategy_name']}")
    print(f"选股数量: {result['total_count']}")
    
    for i, stock in enumerate(result['stocks'][:5], 1):
        print(f"{i}. {stock['name']} ({stock['ts_code']})")
        print(f"   涨跌幅: {stock['pct_chg']}%, RSI: {stock['rsi']}, 量比: {stock['volume_ratio']}")
        print(f"   评分: {stock['score']}, 理由: {stock['reason']}")


if __name__ == "__main__":
    asyncio.run(test_momentum_breakthrough_adapter())