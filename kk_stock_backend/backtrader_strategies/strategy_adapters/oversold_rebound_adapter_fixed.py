#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超跌反弹策略适配器 - 修复版
完全按照原始接口逻辑重新实现
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class OversoldReboundAdapter:
    """超跌反弹策略适配器 - 修复版"""
    
    def __init__(self):
        self.strategy_name = "超跌反弹策略"
        self.strategy_type = "rebound"
        self.description = "多维度识别超跌反弹机会的选股策略"
        self.db_handler = get_global_db_handler()
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           rsi_max: float = 35.0,
                           rsi_min: float = 15.0,
                           volume_ratio_min: float = 1.3,
                           pe_max: float = 50.0,
                           pb_max: float = 8.0,
                           **kwargs) -> Dict[str, Any]:
        """
        超跌反弹策略选股 - 完全按照原始逻辑
        """
        try:
            # 获取最新交易日期
            latest_date = await self._get_latest_trade_date()
            
            # 基础筛选条件 - 完全按照原始逻辑
            match_conditions = {
                "trade_date": latest_date,
                "close": {"$gt": 0},
                "total_mv": {"$gte": 300000},              # 市值 >= 3亿
                "rsi_qfq_12": {"$gte": rsi_min, "$lte": rsi_max},  # RSI超跌区域
                "volume_ratio": {"$gte": volume_ratio_min},         # 量比放大
                "pe": {"$gt": 0, "$lte": pe_max},                  # PE合理
                "pb": {"$gt": 0, "$lte": pb_max},                  # PB合理
                "turnover_rate": {"$gte": 1.5, "$lte": 25}        # 换手率适中
            }
            
            # 构建$expr条件：技术位判断
            expr_conditions = [
                {"$lt": ["$close", "$ma_qfq_20"]},     # 低于20日均线
                {"$lt": ["$close", "$ma_qfq_60"]},     # 低于60日均线
            ]
            
            match_conditions["$expr"] = {"$and": expr_conditions}
            
            # 市值筛选
            if market_cap == "large":
                match_conditions["total_mv"] = {"$gte": 5000000}
            elif market_cap == "mid":
                match_conditions["total_mv"] = {"$gte": 1000000, "$lte": 5000000}
            elif market_cap == "small":
                match_conditions["total_mv"] = {"$lte": 1000000}
            else:
                match_conditions["total_mv"] = {"$gte": 300000}  # 最小3亿市值
            
            # 股票池筛选
            if stock_pool != "all":
                resolved_pool = await self._resolve_stock_pool([stock_pool])
                if resolved_pool:
                    match_conditions["ts_code"] = {"$in": resolved_pool}
            
            pipeline = [
                {"$match": match_conditions},
                
                # 联接股票基本信息
                {"$lookup": {
                    "from": "infrastructure_stock_basic",
                    "localField": "ts_code",
                    "foreignField": "ts_code",
                    "as": "stock_info"
                }},
                {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
                
                # 排除ST股票
                {"$match": {
                    "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
                }},
                
                # 计算超跌反弹评分（完全按照原始逻辑的100分制）
                {"$addFields": {
                    "score": {
                        "$add": [
                            # 基础分：符合超跌条件得20分
                            20,
                            
                            # RSI得分：越低得分越高，15-35区间得0-25分
                            {"$multiply": [{"$subtract": [35, "$rsi_qfq_12"]}, 1.25]},
                            
                            # 量比得分：量比越高得分越高，最高20分
                            {"$min": [20, {"$multiply": [{"$subtract": ["$volume_ratio", 1]}, 4]}]},
                            
                            # 估值得分：PE越低得分越高，最高15分
                            {"$min": [15, {"$multiply": [{"$divide": [25, "$pe"]}, 3]}]},
                            
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
                                "if": {"$and": [{"$gte": ["$turnover_rate", 2]}, {"$lte": ["$turnover_rate", 10]}]},
                                "then": 5,
                                "else": 0
                            }}
                        ]
                    }
                }},
                
                # 输出字段 - 按照原始逻辑
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
                    "rebound_signal": {
                        "$cond": {
                            "if": {"$gte": ["$score", 55]},
                            "then": True,
                            "else": False
                        }
                    }
                }},
                
                {"$sort": {"score": -1}},
                {"$limit": limit}
            ]
            
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
                    'rsi_max': rsi_max,
                    'rsi_min': rsi_min,
                    'volume_ratio_min': volume_ratio_min,
                    'pe_max': pe_max,
                    'pb_max': pb_max
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
                
                # 超跌反弹策略专用字段
                'rsi': round(result.get('rsi') or 0, 2),
                'volume_ratio': round(result.get('volume_ratio') or 0, 2),
                'turnover_rate': round(result.get('turnover_rate') or 0, 2),
                'ma_20': round(result.get('ma_20') or 0, 2),
                'ma_60': round(result.get('ma_60') or 0, 2),
                'rebound_signal': result.get('rebound_signal', False),
                
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
        
        rsi = result.get('rsi', 0)
        pct_chg = result.get('pct_chg', 0)
        volume_ratio = result.get('volume_ratio', 0)
        score = result.get('score', 0)
        rebound_signal = result.get('rebound_signal', False)
        
        # 基础超跌条件
        reasons.append("超跌区域")
        
        # RSI状态
        if rsi <= 20:
            reasons.append(f"RSI{rsi:.0f}严重超跌")
        elif rsi <= 30:
            reasons.append(f"RSI{rsi:.0f}超跌")
        
        # 成交量
        if volume_ratio >= 2:
            reasons.append(f"放量{volume_ratio:.1f}倍")
        elif volume_ratio >= 1.5:
            reasons.append(f"温和放量{volume_ratio:.1f}倍")
        
        # 价格表现
        if pct_chg > 3:
            reasons.append(f"强势反弹{pct_chg:.1f}%")
        elif pct_chg > 0:
            reasons.append(f"止跌反弹{pct_chg:.1f}%")
        elif pct_chg > -2:
            reasons.append("跌幅收窄")
        
        # 反弹信号
        if rebound_signal:
            reasons.append("反弹信号确认")
        
        reasons.append(f"反弹评分{score:.0f}")
        
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