#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超跌反弹策略适配器 - 简化版
降低筛选条件，确保能找到股票
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class OversoldReboundAdapter:
    """超跌反弹策略适配器 - 简化版"""
    
    def __init__(self):
        self.strategy_name = "超跌反弹策略"
        self.strategy_type = "rebound"
        self.description = "多维度识别超跌反弹机会的选股策略"
        self.db_handler = get_global_db_handler()
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           rsi_max: float = 50.0,  # 放宽RSI上限
                           rsi_min: float = 10.0,
                           volume_ratio_min: float = 1.0,  # 降低量比要求
                           pe_max: float = 100.0,  # 放宽PE限制
                           pb_max: float = 20.0,   # 放宽PB限制
                           **kwargs) -> Dict[str, Any]:
        """超跌反弹策略选股 - 简化筛选条件"""
        try:
            # 获取最新交易日期
            latest_date = await self._get_latest_trade_date()
            print(f"查询日期: {latest_date}")
            
            # 基础筛选条件 - 放宽条件
            match_conditions = {
                "trade_date": latest_date,
                "close": {"$gt": 0},
                "total_mv": {"$gte": 100000},              # 市值 >= 1亿（降低要求）
                "rsi_qfq_12": {"$gte": rsi_min, "$lte": rsi_max},  # RSI区间
                "volume_ratio": {"$gte": volume_ratio_min},         # 量比
                "pe": {"$gt": 0, "$lte": pe_max},                  # PE
                "pb": {"$gt": 0, "$lte": pb_max},                  # PB
                "turnover_rate": {"$gte": 0.5, "$lte": 50}        # 换手率放宽
            }
            
            # 不强制要求低于均线，改为可选
            
            # 市值筛选
            if market_cap == "large":
                match_conditions["total_mv"] = {"$gte": 5000000}
            elif market_cap == "mid":
                match_conditions["total_mv"] = {"$gte": 1000000, "$lte": 5000000}
            elif market_cap == "small":
                match_conditions["total_mv"] = {"$lte": 1000000}
            else:
                match_conditions["total_mv"] = {"$gte": 100000}  # 最小1亿市值
            
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
                
                # 计算超跌反弹评分（简化版）
                {"$addFields": {
                    "score": {
                        "$add": [
                            # 基础分：20分
                            20,
                            
                            # RSI得分：RSI越低得分越高
                            {"$multiply": [{"$subtract": [rsi_max, "$rsi_qfq_12"]}, 1]},
                            
                            # 量比得分：量比越高得分越高，最高20分
                            {"$min": [20, {"$multiply": [{"$subtract": ["$volume_ratio", 1]}, 3]}]},
                            
                            # 当日表现得分
                            {"$cond": {
                                "if": {"$gt": ["$pct_chg", 0]},
                                "then": 10,
                                "else": {"$cond": {
                                    "if": {"$gt": ["$pct_chg", -3]},
                                    "then": 5,
                                    "else": 0
                                }}
                            }}
                        ]
                    }
                }},
                
                # 输出字段
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
                    "rsi": "$rsi_qfq_12",
                    "volume_ratio": 1,
                    "turnover_rate": 1,
                    "ma_20": "$ma_qfq_20",
                    "ma_60": "$ma_qfq_60",
                    "rebound_signal": {
                        "$cond": {
                            "if": {"$gte": ["$score", 40]},  # 降低阈值
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
            
            print(f"找到 {len(results)} 只超跌股票")
            
            # 处理结果
            processed_results = []
            for result in results:
                stock_info = {
                    'ts_code': result.get('ts_code'),
                    'name': result.get('name', ''),
                    'industry': result.get('industry', ''),
                    'close': round(result.get('close') or 0, 2),
                    'pe': round(result.get('pe') or 0, 2),
                    'pb': round(result.get('pb') or 0, 2),
                    'total_mv': round((result.get('total_mv') or 0), 2),
                    'pct_chg': round(result.get('pct_chg') or 0, 2),
                    'rsi': round(result.get('rsi') or 0, 2),
                    'volume_ratio': round(result.get('volume_ratio') or 0, 2),
                    'turnover_rate': round(result.get('turnover_rate') or 0, 2),
                    'ma_20': round(result.get('ma_20') or 0, 2),
                    'ma_60': round(result.get('ma_60') or 0, 2),
                    'rebound_signal': result.get('rebound_signal', False),
                    'score': round(result.get('score') or 0, 2),
                    'reason': self._generate_reason(result)
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
                    'rsi_max': rsi_max,
                    'rsi_min': rsi_min,
                    'volume_ratio_min': volume_ratio_min,
                    'pe_max': pe_max,
                    'pb_max': pb_max
                }
            }
            
        except Exception as e:
            print(f"❌ 超跌反弹策略选股失败: {e}")
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
    
    def _generate_reason(self, result: Dict) -> str:
        """生成选股理由"""
        reasons = []
        
        rsi = result.get('rsi', 0)
        pct_chg = result.get('pct_chg', 0)
        volume_ratio = result.get('volume_ratio', 0)
        score = result.get('score', 0)
        
        # RSI状态
        if rsi <= 30:
            reasons.append(f"RSI{rsi:.0f}超跌")
        elif rsi <= 45:
            reasons.append(f"RSI{rsi:.0f}偏低")
        
        # 成交量
        if volume_ratio >= 1.5:
            reasons.append(f"放量{volume_ratio:.1f}倍")
        
        # 价格表现
        if pct_chg > 0:
            reasons.append(f"上涨{pct_chg:.1f}%")
        elif pct_chg > -3:
            reasons.append("跌幅有限")
        
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
            return "20241231"