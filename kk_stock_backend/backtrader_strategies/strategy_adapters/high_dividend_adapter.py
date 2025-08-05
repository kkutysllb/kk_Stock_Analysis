#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高股息策略适配器 - 性能优化版本
将复杂计算从MongoDB聚合管道移到Python层，避免查询超时

策略特点：
- 专注于高股息收益的稳健股票
- 基础数据用简单查询获取
- 复杂计算在Python层完成
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.global_db import get_global_db_handler


class HighDividendAdapter:
    """高股息策略适配器 - 性能优化版"""
    
    def __init__(self):
        self.strategy_name = "高股息策略"
        self.strategy_type = "dividend"
        self.description = "寻找高股息收益、分红稳定的优质股票（优化版）"
        self.db_handler = get_global_db_handler()
        
        # 筛选参数（放宽条件）
        self.params = {
            'pe_max': 100,
            'pb_max': 20,
            'total_mv_min': 500000,   # 50亿最小市值
            'eps_min': 0.05,          # 最小EPS
            'dividend_yield_min': 1.0, # 最小股息率
        }
    
    async def screen_stocks(self,
                           market_cap: str = "all",
                           stock_pool: str = "all", 
                           limit: int = 20,
                           **kwargs) -> Dict[str, Any]:
        """
        高股息策略选股 - 优化版
        
        Args:
            market_cap: 市值范围 (large/mid/small/all)
            stock_pool: 股票池 (all/main/gem/star)
            limit: 返回股票数量
            **kwargs: 其他参数
            
        Returns:
            选股结果字典
        """
        try:
            # 步骤1：获取基础股票数据（简单查询）
            basic_stocks = await self._get_basic_stocks(market_cap, stock_pool, limit * 5)
            
            if not basic_stocks:
                return self._empty_result()
            
            # 步骤2：获取财务数据（批量查询）
            enriched_stocks = await self._enrich_financial_data(basic_stocks)
            
            # 步骤3：Python层计算和筛选
            processed_stocks = await self._calculate_and_filter(enriched_stocks, limit)
            
            return {
                'strategy_name': self.strategy_name,
                'strategy_type': self.strategy_type,
                'total_count': len(processed_stocks),
                'stocks': processed_stocks,
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'market_cap': market_cap,
                    'stock_pool': stock_pool,
                    'limit': limit
                }
            }
            
        except Exception as e:
            print(f"❌ 高股息策略选股失败: {e}")
            return {
                'strategy_name': self.strategy_name,
                'strategy_type': self.strategy_type,
                'error': str(e),
                'total_count': 0,
                'stocks': [],
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_basic_stocks(self, market_cap: str, stock_pool: str, pre_limit: int) -> List[Dict]:
        """获取基础股票数据 - 简单快速查询"""
        try:
            # 获取最新交易日期
            latest_date = await self._get_latest_trade_date()
            
            # 基础筛选条件
            match_conditions = {
                "trade_date": latest_date,
                "close": {"$gt": 2.0},  # 价格>2元
                "total_mv": {"$gt": 500000},  # 市值>50亿
                "pe": {"$gt": 0, "$lt": 100},  # 合理PE
                "pb": {"$gt": 0, "$lt": 20}    # 合理PB
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
            
            # 简单管道：只获取基础数据和股票信息
            pipeline = [
                {"$match": match_conditions},
                
                # 只联接股票基本信息
                {"$lookup": {
                    "from": "infrastructure_stock_basic",
                    "localField": "ts_code",
                    "foreignField": "ts_code",
                    "as": "stock_info"
                }},
                {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
                
                # 过滤ST股票
                {"$match": {
                    "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
                }},
                
                {"$project": {
                    "ts_code": 1,
                    "name": "$stock_info.name",
                    "industry": "$stock_info.industry",
                    "close": 1,
                    "pe": 1,
                    "pb": 1,
                    "pct_chg": 1,
                    "total_mv": 1,
                    "vol": 1,
                    "amount": 1
                }},
                
                {"$sort": {"total_mv": -1}},  # 按市值排序
                {"$limit": pre_limit}
            ]
            
            collection = self.db_handler.get_collection('stock_factor_pro')
            cursor = collection.aggregate(pipeline)
            return list(cursor)
            
        except Exception as e:
            print(f"获取基础股票数据失败: {e}")
            return []
    
    async def _enrich_financial_data(self, stocks: List[Dict]) -> List[Dict]:
        """批量获取财务数据"""
        if not stocks:
            return []
        
        ts_codes = [stock['ts_code'] for stock in stocks]
        
        try:
            # 批量获取财务指标
            fina_collection = self.db_handler.get_collection('stock_fina_indicator')
            fina_pipeline = [
                {"$match": {"ts_code": {"$in": ts_codes}}},
                {"$sort": {"ts_code": 1, "end_date": -1}},
                {"$group": {
                    "_id": "$ts_code",
                    "latest": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$latest"}}
            ]
            fina_data = {item['ts_code']: item for item in fina_collection.aggregate(fina_pipeline)}
            
            # 批量获取现金流数据
            cash_collection = self.db_handler.get_collection('stock_cash_flow')
            cash_pipeline = [
                {"$match": {"ts_code": {"$in": ts_codes}}},
                {"$sort": {"ts_code": 1, "end_date": -1}},
                {"$group": {
                    "_id": "$ts_code",
                    "latest": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$latest"}}
            ]
            cash_data = {item['ts_code']: item for item in cash_collection.aggregate(cash_pipeline)}
            
            # 合并数据
            for stock in stocks:
                ts_code = stock['ts_code']
                stock['fina_data'] = fina_data.get(ts_code, {})
                stock['cash_data'] = cash_data.get(ts_code, {})
            
            return stocks
            
        except Exception as e:
            print(f"获取财务数据失败: {e}")
            return stocks
    
    async def _calculate_and_filter(self, stocks: List[Dict], limit: int) -> List[Dict]:
        """在Python层计算指标并筛选"""
        calculated_stocks = []
        
        for stock in stocks:
            try:
                # 计算各项指标
                metrics = self._calculate_dividend_metrics(stock)
                
                # 应用筛选条件
                if self._meets_criteria(metrics):
                    # 计算综合评分
                    metrics['score'] = self._calculate_score(metrics)
                    calculated_stocks.append(metrics)
                    
            except Exception as e:
                print(f"处理股票 {stock.get('ts_code')} 失败: {e}")
                continue
        
        # 按评分排序并返回top N
        calculated_stocks.sort(key=lambda x: x['score'], reverse=True)
        return calculated_stocks[:limit]
    
    def _calculate_dividend_metrics(self, stock: Dict) -> Dict:
        """计算股息相关指标"""
        fina = stock.get('fina_data', {})
        cash = stock.get('cash_data', {})
        
        # 基础数据
        eps = fina.get('eps', 0) or 0
        close = stock.get('close', 0) or 0
        roe = fina.get('roe', 0) or 0
        roa = fina.get('roa', 0) or 0
        roic = fina.get('roic', 0) or 0  # 投入资本回报率
        debt_to_assets = fina.get('debt_to_assets', 0) or 0  # 资产负债率
        
        # 银行业特殊处理：ROIC通常为空，使用ROE估算
        industry = stock.get('industry', '')
        if roic == 0 and industry in ['银行', '保险', '金融']:
            # 对于金融业，使用ROE作为ROIC的代理指标
            roic = roe * 0.8 if roe > 0 else 0
        
        # 分红相关
        dividend_paid = abs(cash.get('c_pay_dist_dpcp_int_exp', 0) or 0)  # 分红支出
        net_profit = fina.get('profit_dedt', 0) or 0  # 净利润
        financing_inflow = cash.get('stot_cash_in_fnc_act', 0) or 0  # 筹资流入
        
        # 计算股息率（估算：EPS * 40%分红率 / 股价）
        dividend_yield = 0
        if eps > 0 and close > 0:
            estimated_dividend = eps * 0.4  # 假设40%分红率
            dividend_yield = (estimated_dividend / close) * 100
        
        # 计算股息支付率（分红/净利润）
        payout_ratio = 0
        if dividend_paid > 0 and net_profit > 0:
            payout_ratio = min(100, (dividend_paid / net_profit) * 100)
        
        # 计算分红募资比（分红/筹资流入）
        dividend_fundraising_ratio = 0
        if dividend_paid > 0 and financing_inflow > 0:
            dividend_fundraising_ratio = min(200, (dividend_paid / financing_inflow) * 100)
        
        # 估算净现金（简化）
        total_mv = stock.get('total_mv', 0) or 0
        net_cash = total_mv / 100  # 简化估算
        
        # 净利润率（ROE的一半，简化估算）
        net_profit_margin = roe * 0.5 if roe > 0 else 10
        
        return {
            'ts_code': stock.get('ts_code'),
            'name': stock.get('name', ''),
            'industry': stock.get('industry', ''),
            'close': round(close, 2),
            'pe': round(stock.get('pe', 0) or 0, 2),
            'pb': round(stock.get('pb', 0) or 0, 2),
            'pct_chg': round(stock.get('pct_chg', 0) or 0, 2),
            'total_mv': round(total_mv / 10000, 2),  # 转换为亿元
            
            # 股息指标
            'dividend_yield': round(dividend_yield, 2),
            'payout_ratio': round(payout_ratio, 2),
            'dividend_fundraising_ratio': round(dividend_fundraising_ratio, 2),
            'net_cash': round(net_cash, 2),
            'roe': round(roe, 2),
            'roa': round(roa, 2) if roa else 0,
            'roic': round(roic, 2) if roic else 0,  # ROIC%
            'debt_ratio': round(debt_to_assets, 2) if debt_to_assets else 0,  # 资产负债率%
            'eps': round(eps, 2),
            'net_profit_margin': round(net_profit_margin, 2),
            
            # 选股理由
            'reason': self._generate_reason({
                'dividend_yield': dividend_yield,
                'roe': roe,
                'payout_ratio': payout_ratio
            })
        }
    
    def _meets_criteria(self, metrics: Dict) -> bool:
        """检查是否满足筛选条件"""
        return (
            metrics['eps'] > self.params['eps_min'] and
            metrics['total_mv'] >= self.params['total_mv_min'] / 10000 and  # 已转换为亿元
            metrics['dividend_yield'] >= self.params['dividend_yield_min'] and
            metrics['pe'] > 0 and metrics['pe'] < self.params['pe_max'] and
            metrics['pb'] > 0 and metrics['pb'] < self.params['pb_max']
        )
    
    def _calculate_score(self, metrics: Dict) -> float:
        """计算综合评分"""
        score = 0
        
        # 股息率权重 40%
        score += metrics['dividend_yield'] * 8
        
        # ROE权重 20%
        score += min(metrics['roe'], 20) * 2
        
        # 市值稳定性 20%
        score += min(metrics['total_mv'] / 10, 10)  # 最高10分
        
        # 分红稳定性 20%
        if metrics['payout_ratio'] > 20:
            score += min(metrics['payout_ratio'] / 5, 10)
        
        # 基础分 20分
        score += 20
        
        return round(score, 1)
    
    def _generate_reason(self, metrics: Dict) -> str:
        """生成选股理由"""
        reasons = []
        
        dividend_yield = metrics.get('dividend_yield', 0)
        roe = metrics.get('roe', 0)
        payout_ratio = metrics.get('payout_ratio', 0)
        
        if dividend_yield >= 5:
            reasons.append(f"高股息率{dividend_yield:.1f}%")
        elif dividend_yield >= 3:
            reasons.append(f"股息率{dividend_yield:.1f}%")
        
        if roe >= 15:
            reasons.append(f"高ROE{roe:.1f}%")
        elif roe >= 10:
            reasons.append(f"ROE{roe:.1f}%")
        
        if payout_ratio >= 50:
            reasons.append("高分红比例")
        elif payout_ratio >= 20:
            reasons.append("稳定分红")
        
        return "；".join(reasons) if reasons else "财务稳健"
    
    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'strategy_name': self.strategy_name,
            'strategy_type': self.strategy_type,
            'total_count': 0,
            'stocks': [],
            'timestamp': datetime.now().isoformat(),
            'parameters': {}
        }
    
    async def _get_latest_trade_date(self) -> str:
        """获取最新交易日期"""
        try:
            collection = self.db_handler.get_collection('stock_factor_pro')
            result = collection.find_one({}, {"trade_date": 1}, sort=[("trade_date", -1)])
            return result['trade_date'] if result else "20241230"
        except:
            return "20241230"
    
    async def _resolve_stock_pool(self, pools: List[str]) -> List[str]:
        """解析股票池"""
        # 简化实现，实际应该查询股票池配置
        return []