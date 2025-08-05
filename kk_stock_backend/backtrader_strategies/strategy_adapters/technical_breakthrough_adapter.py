#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术突破策略适配器
从API层提取的核心选股逻辑

策略特点：
- 多重技术指标确认突破信号
- 重点关注量价配合的技术突破
- 适合短中线技术操作
- 使用RSI、MACD、均线、成交量等综合指标
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class TechnicalBreakthroughAdapter:
    """技术突破策略适配器"""
    
    def __init__(self):
        self.strategy_name = "技术突破策略"
        self.strategy_type = "technical"
        self.description = "多重技术指标确认的突破选股策略"
        self.db_handler = get_global_db_handler()
        
        # 策略参数
        self.params = {
            # RSI指标参数
            'rsi_min': 45.0,             # RSI下限：确保动能充足
            'rsi_max': 85.0,             # RSI上限：避免超买
            
            # 成交量参数
            'volume_ratio_min': 1.2,     # 量比下限：确保成交量放大
            'turnover_rate_min': 1.0,    # 换手率下限
            'turnover_rate_max': 15.0,   # 换手率上限
            
            # 技术信号参数
            'require_macd_golden': False, # 是否要求MACD金叉
            'require_ma_alignment': False, # 是否要求均线多头排列
            'bollinger_position': 'any',  # 布林带位置要求：upper/middle/any
            
            # 基础要求
            'min_market_cap': 500000,    # 最小市值（万元）>= 5亿
            'exclude_st': True,          # 排除ST股票
            
            # 评分权重
            'base_score': 20,            # 基础分：站上20日线
            'rsi_weight': 0.5,           # RSI权重
            'macd_weight': 15,           # MACD权重
            'volume_weight': 10,         # 成交量权重
            'price_change_weight': 2,    # 涨跌幅权重
            
            # 评分阈值
            'breakthrough_threshold': 70, # 突破信号评分阈值
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           **kwargs) -> Dict[str, Any]:
        """
        技术突破策略选股
        
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
            print(f"❌ 技术突破策略选股失败: {e}")
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
        """构建技术突破筛选管道"""
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
            
            # 第四步：计算技术突破评分
            {"$addFields": {
                "score": {
                    "$add": [
                        # 基础分：站上20日线得20分
                        self.params['base_score'],
                        
                        # RSI得分：45-85区间，得0-20分
                        {"$multiply": [
                            {"$max": [0, {"$subtract": ["$rsi_qfq_12", self.params['rsi_min']]}]}, 
                            self.params['rsi_weight']
                        ]},
                        
                        # MACD得分：MACD>0得15分
                        {"$cond": {
                            "if": {"$gt": ["$macd_qfq", 0]}, 
                            "then": self.params['macd_weight'], 
                            "else": 0
                        }},
                        
                        # 成交量得分：量比每超过1得10分，最高25分
                        {"$min": [
                            25, 
                            {"$multiply": [
                                {"$max": [0, {"$subtract": ["$volume_ratio", 1]}]}, 
                                self.params['volume_weight']
                            ]}
                        ]},
                        
                        # 涨跌幅得分：涨幅每1%得2分，最高20分
                        {"$min": [
                            20, 
                            {"$max": [0, {"$multiply": ["$pct_chg", self.params['price_change_weight']]}]}
                        ]}
                    ]
                },
                
                # 计算均线排列
                "ma_alignment": {
                    "$and": [
                        {"$gt": ["$ma_qfq_5", "$ma_qfq_10"]},       # 5日线 > 10日线
                        {"$gt": ["$ma_qfq_10", "$ma_qfq_20"]}       # 10日线 > 20日线
                    ]
                },
                
                # 计算MACD金叉
                "macd_golden": {
                    "$and": [
                        {"$gt": ["$macd_dif_qfq", "$macd_dea_qfq"]},  # DIF > DEA（金叉）
                        {"$gt": ["$macd_qfq", 0]}                     # MACD柱状线为正
                    ]
                },
                
                # 计算布林带位置
                "bollinger_position": {
                    "$cond": {
                        "if": {"$gte": ["$close", "$boll_upper_qfq"]},
                        "then": "upper",
                        "else": {
                            "$cond": {
                                "if": {"$gte": ["$close", "$boll_mid_qfq"]},
                                "then": "middle",
                                "else": "lower"
                            }
                        }
                    }
                },
                
                # 突破信号判断
                "breakthrough_signal": {
                    "$gte": [{"$add": [
                        self.params['base_score'],
                        {"$multiply": [{"$max": [0, {"$subtract": ["$rsi_qfq_12", self.params['rsi_min']]}]}, self.params['rsi_weight']]},
                        {"$cond": {"if": {"$gt": ["$macd_qfq", 0]}, "then": self.params['macd_weight'], "else": 0}},
                        {"$min": [25, {"$multiply": [{"$max": [0, {"$subtract": ["$volume_ratio", 1]}]}, self.params['volume_weight']]}]},
                        {"$min": [20, {"$max": [0, {"$multiply": ["$pct_chg", self.params['price_change_weight']]}]}]}
                    ]}, self.params['breakthrough_threshold']]
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
                
                # 技术突破策略专用字段
                "rsi": "$rsi_qfq_12",
                "macd": "$macd_qfq",
                "macd_dif": "$macd_dif_qfq",
                "macd_dea": "$macd_dea_qfq",
                "volume_ratio": 1,
                "turnover_rate": 1,
                "ma_5": "$ma_qfq_5",
                "ma_10": "$ma_qfq_10",
                "ma_20": "$ma_qfq_20",
                "ma_60": "$ma_qfq_60",
                "boll_upper": "$boll_upper_qfq",
                "boll_middle": "$boll_mid_qfq",
                "boll_lower": "$boll_lower_qfq",
                "ma_alignment": 1,
                "macd_golden": 1,
                "bollinger_position": 1,
                "breakthrough_signal": 1
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
            "total_mv": {"$gt": 0},
            "rsi_qfq_12": {"$gte": self.params['rsi_min'], "$lte": self.params['rsi_max']},  # RSI动能区间
            "volume_ratio": {"$gte": self.params['volume_ratio_min']},         # 量比放大
            "turnover_rate": {"$gte": self.params['turnover_rate_min'], "$lte": self.params['turnover_rate_max']}  # 换手率适中
        }
        
        # 构建$expr条件列表
        expr_conditions = [
            {"$gt": ["$close", "$ma_qfq_20"]}  # 站上20日均线（基础要求）
        ]
        
        # MACD金叉要求（如果启用）
        if self.params['require_macd_golden']:
            expr_conditions.extend([
                {"$gt": ["$macd_dif_qfq", "$macd_dea_qfq"]},  # DIF > DEA（金叉）
                {"$gt": ["$macd_qfq", 0]}                     # MACD柱状线为正
            ])
        
        # 均线多头排列要求
        if self.params['require_ma_alignment']:
            expr_conditions.extend([
                {"$gt": ["$ma_qfq_5", "$ma_qfq_10"]},       # 5日线 > 10日线
                {"$gt": ["$ma_qfq_10", "$ma_qfq_20"]}       # 10日线 > 20日线
            ])
        
        # 将所有$expr条件合并
        if len(expr_conditions) > 1:
            match_conditions["$expr"] = {"$and": expr_conditions}
        else:
            match_conditions["$expr"] = expr_conditions[0]
        
        # 市值筛选
        if market_cap == "large":
            match_conditions["total_mv"] = {"$gte": 5000000}
        elif market_cap == "mid":
            match_conditions["total_mv"] = {"$gte": 1000000, "$lte": 5000000}
        elif market_cap == "small":
            match_conditions["total_mv"] = {"$lte": 1000000}
        else:
            match_conditions["total_mv"] = {"$gte": self.params['min_market_cap']}  # 最小市值
        
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
                'macd': round(result.get('macd', 0), 4),
                'macd_dif': round(result.get('macd_dif', 0), 4),
                'macd_dea': round(result.get('macd_dea', 0), 4),
                'volume_ratio': round(result.get('volume_ratio', 0), 2),
                'turnover_rate': round(result.get('turnover_rate', 0), 2),
                
                # 均线指标
                'ma_5': round(result.get('ma_5', 0), 2),
                'ma_10': round(result.get('ma_10', 0), 2),
                'ma_20': round(result.get('ma_20', 0), 2),
                'ma_60': round(result.get('ma_60', 0), 2),
                
                # 布林带指标
                'boll_upper': round(result.get('boll_upper', 0), 2),
                'boll_middle': round(result.get('boll_middle', 0), 2),
                'boll_lower': round(result.get('boll_lower', 0), 2),
                'bollinger_position': result.get('bollinger_position', ''),
                
                # 信号指标
                'ma_alignment': result.get('ma_alignment', False),
                'macd_golden': result.get('macd_golden', False),
                'breakthrough_signal': result.get('breakthrough_signal', False),
                
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
        volume_ratio = result.get('volume_ratio', 0)
        rsi = result.get('rsi', 0)
        breakthrough_signal = result.get('breakthrough_signal', False)
        macd_golden = result.get('macd_golden', False)
        ma_alignment = result.get('ma_alignment', False)
        bollinger_position = result.get('bollinger_position', '')
        score = result.get('score', 0)
        
        # 基础突破
        reasons.append("站上20日均线")
        
        # 价格表现
        if pct_chg >= 3:
            reasons.append(f"强势上涨{pct_chg:.1f}%")
        elif pct_chg > 0:
            reasons.append(f"上涨{pct_chg:.1f}%")
        
        # 成交量
        if volume_ratio >= 2:
            reasons.append(f"放量{volume_ratio:.1f}倍")
        elif volume_ratio >= 1.5:
            reasons.append(f"温和放量{volume_ratio:.1f}倍")
        
        # 技术信号
        if ma_alignment:
            reasons.append("均线多头排列")
        
        if macd_golden:
            reasons.append("MACD金叉")
        
        if bollinger_position == "upper":
            reasons.append("突破布林上轨")
        elif bollinger_position == "middle":
            reasons.append("站上布林中轨")
        
        if breakthrough_signal:
            reasons.append("强突破信号")
        
        # RSI状态
        if 50 <= rsi <= 70:
            reasons.append(f"RSI{rsi:.0f}适中")
        elif rsi > 70:
            reasons.append(f"RSI{rsi:.0f}强势")
        
        reasons.append(f"技术评分{score:.0f}")
        
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
async def test_technical_breakthrough_adapter():
    """测试技术突破策略适配器"""
    adapter = TechnicalBreakthroughAdapter()
    result = await adapter.screen_stocks(
        market_cap="all", 
        stock_pool="all", 
        limit=10,
        rsi_min=50,
        require_macd_golden=True
    )
    
    print(f"策略名称: {result['strategy_name']}")
    print(f"选股数量: {result['total_count']}")
    
    for i, stock in enumerate(result['stocks'][:5], 1):
        print(f"{i}. {stock['name']} ({stock['ts_code']})")
        print(f"   涨跌幅: {stock['pct_chg']}%, RSI: {stock['rsi']}, 量比: {stock['volume_ratio']}")
        print(f"   评分: {stock['score']}, 理由: {stock['reason']}")


if __name__ == "__main__":
    asyncio.run(test_technical_breakthrough_adapter())