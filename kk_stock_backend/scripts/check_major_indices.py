#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询主要宽基指数成分股分布和特征
包括中证A500、沪深300、中证500、中证1000等指数
"""

import sys
import os
from typing import List, Dict, Any
from collections import Counter

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from api.global_db import get_global_db_handler

class MajorIndicesAnalyzer:
    """主要指数分析器"""
    
    def __init__(self):
        self.db = get_global_db_handler()
        
        # 主要指数配置
        self.major_indices = {
            '000510.CSI': '中证A500',
            '000300.SH': '沪深300', 
            '000905.SH': '中证500',
            '000852.SH': '中证1000',
            '399006.SZ': '创业板指',
            '000688.SH': '科创50',
            '000001.SH': '上证指数',
            '399001.SZ': '深证成指'
        }
    
    def get_index_constituents(self, index_code: str, include_weights: bool = False) -> List[Dict]:
        """
        获取指数成分股
        
        Args:
            index_code: 指数代码
            include_weights: 是否包含权重信息
            
        Returns:
            成分股列表
        """
        try:
            collection = self.db.get_collection('index_weight')
            
            # 查询最新的成分股
            query = {'index_code': index_code}
            
            # 获取最新交易日
            latest_doc = collection.find(query).sort('trade_date', -1).limit(1)
            latest_date = None
            
            for doc in latest_doc:
                latest_date = doc.get('trade_date')
                break
            
            if not latest_date:
                print(f"❌ 未找到指数 {index_code} 的成分股数据")
                return []
            
            # 获取最新日期的所有成分股
            query['trade_date'] = latest_date
            projection = {'con_code': 1, 'weight': 1, 'trade_date': 1, '_id': 0}
            
            constituents = list(collection.find(query, projection))
            
            print(f"📊 {self.major_indices.get(index_code, index_code)} 最新成分股数据:")
            print(f"  📅 数据日期: {latest_date}")
            print(f"  📈 成分股数量: {len(constituents)}")
            
            if include_weights and constituents:
                # 按权重排序
                constituents.sort(key=lambda x: x.get('weight', 0), reverse=True)
                
                print(f"  🔝 前10大权重股:")
                for i, stock in enumerate(constituents[:10], 1):
                    weight = stock.get('weight', 0)
                    print(f"    {i:2d}. {stock['con_code']}: {weight:.4f}%")
            
            return constituents
            
        except Exception as e:
            print(f"❌ 获取指数 {index_code} 成分股失败: {e}")
            return []
    
    def analyze_index_overlap(self, index1: str, index2: str) -> Dict[str, Any]:
        """
        分析两个指数的重叠情况
        
        Args:
            index1: 指数1代码
            index2: 指数2代码
            
        Returns:
            重叠分析结果
        """
        constituents1 = self.get_index_constituents(index1)
        constituents2 = self.get_index_constituents(index2)
        
        stocks1 = set([stock['con_code'] for stock in constituents1])
        stocks2 = set([stock['con_code'] for stock in constituents2])
        
        overlap = stocks1.intersection(stocks2)
        
        result = {
            'index1': {'code': index1, 'name': self.major_indices.get(index1, index1), 'count': len(stocks1)},
            'index2': {'code': index2, 'name': self.major_indices.get(index2, index2), 'count': len(stocks2)},
            'overlap_count': len(overlap),
            'overlap_stocks': list(overlap),
            'overlap_ratio1': len(overlap) / len(stocks1) if stocks1 else 0,
            'overlap_ratio2': len(overlap) / len(stocks2) if stocks2 else 0
        }
        
        print(f"\n🔍 指数重叠分析:")
        print(f"  📊 {result['index1']['name']}: {result['index1']['count']}只")
        print(f"  📊 {result['index2']['name']}: {result['index2']['count']}只")
        print(f"  🎯 重叠股票: {result['overlap_count']}只")
        print(f"  📈 重叠比例: {result['overlap_ratio1']:.1%} | {result['overlap_ratio2']:.1%}")
        
        return result
    
    def get_index_industry_distribution(self, index_code: str) -> Dict[str, Any]:
        """
        获取指数的行业分布
        
        Args:
            index_code: 指数代码
            
        Returns:
            行业分布信息
        """
        constituents = self.get_index_constituents(index_code)
        stock_codes = [stock['con_code'] for stock in constituents]
        
        if not stock_codes:
            return {}
        
        # 从申万行业数据获取行业信息
        industry_collection = self.db.get_collection('index_member_all')
        
        # 查询这些股票的行业信息
        query = {'ts_code': {'$in': stock_codes}}
        projection = {'ts_code': 1, 'l1_name': 1, 'l2_name': 1, '_id': 0}
        
        industry_data = list(industry_collection.find(query, projection))
        
        # 统计行业分布
        l1_counter = Counter()
        l2_counter = Counter()
        
        for stock in industry_data:
            l1_name = stock.get('l1_name')
            l2_name = stock.get('l2_name')
            
            if l1_name:
                l1_counter[l1_name] += 1
            if l2_name:
                l2_counter[l2_name] += 1
        
        print(f"\n📊 {self.major_indices.get(index_code, index_code)} 行业分布:")
        print(f"  📈 一级行业分布 (前10):")
        for i, (industry, count) in enumerate(l1_counter.most_common(10), 1):
            ratio = count / len(stock_codes) * 100
            print(f"    {i:2d}. {industry}: {count}只 ({ratio:.1f}%)")
        
        return {
            'index_code': index_code,
            'index_name': self.major_indices.get(index_code, index_code),
            'total_stocks': len(stock_codes),
            'l1_distribution': dict(l1_counter),
            'l2_distribution': dict(l2_counter),
            'stocks_with_industry': len(industry_data),
            'coverage_ratio': len(industry_data) / len(stock_codes) if stock_codes else 0
        }
    
    def compare_all_major_indices(self):
        """比较所有主要指数"""
        print("🎯 主要宽基指数成分股分析")
        print("=" * 80)
        
        # 获取所有指数的成分股数量
        indices_info = {}
        
        for index_code, index_name in self.major_indices.items():
            print(f"\n🔍 分析 {index_name} ({index_code})")
            constituents = self.get_index_constituents(index_code, include_weights=True)
            
            if constituents:
                indices_info[index_code] = {
                    'name': index_name,
                    'count': len(constituents),
                    'stocks': set([stock['con_code'] for stock in constituents])
                }
            else:
                print(f"  ⚠️ 无法获取 {index_name} 的成分股数据")
        
        # 分析重叠情况
        print(f"\n🔍 指数重叠分析:")
        print("-" * 50)
        
        key_indices = ['000510.CSI', '000300.SH', '000905.SH', '000852.SH']
        
        for i, index1 in enumerate(key_indices):
            for index2 in key_indices[i+1:]:
                if index1 in indices_info and index2 in indices_info:
                    self.analyze_index_overlap(index1, index2)
        
        # 行业分布分析
        print(f"\n📊 指数行业分布分析:")
        print("-" * 50)
        
        for index_code in key_indices:
            if index_code in indices_info:
                self.get_index_industry_distribution(index_code)
    
    def get_index_market_cap_distribution(self, index_code: str) -> Dict[str, Any]:
        """
        获取指数的市值分布（需要结合市值数据）
        
        Args:
            index_code: 指数代码
            
        Returns:
            市值分布信息
        """
        constituents = self.get_index_constituents(index_code)
        stock_codes = [stock['con_code'] for stock in constituents]
        
        if not stock_codes:
            return {}
        
        # 从基础数据获取最新市值信息
        try:
            basic_collection = self.db.get_collection('infrastructure_stock_basic')
            
            query = {'ts_code': {'$in': stock_codes}}
            projection = {'ts_code': 1, 'name': 1, 'market': 1, 'list_date': 1, '_id': 0}
            
            basic_data = list(basic_collection.find(query, projection))
            
            # 按市场分布统计
            market_counter = Counter()
            
            for stock in basic_data:
                market = stock.get('market', '未知')
                market_counter[market] += 1
            
            print(f"\n📊 {self.major_indices.get(index_code, index_code)} 市场分布:")
            for market, count in market_counter.most_common():
                ratio = count / len(stock_codes) * 100
                print(f"  {market}: {count}只 ({ratio:.1f}%)")
            
            return {
                'index_code': index_code,
                'market_distribution': dict(market_counter),
                'total_stocks': len(stock_codes),
                'data_coverage': len(basic_data) / len(stock_codes) if stock_codes else 0
            }
            
        except Exception as e:
            print(f"❌ 获取市值分布失败: {e}")
            return {}

def main():
    """主函数"""
    analyzer = MajorIndicesAnalyzer()
    
    print("🚀 主要指数成分股分析工具")
    print("支持的指数:", list(analyzer.major_indices.values()))
    print("=" * 80)
    
    # 执行全面分析
    analyzer.compare_all_major_indices()
    
    # 市场分布分析
    print(f"\n📈 市场分布分析:")
    print("-" * 50)
    
    key_indices = ['000510.CSI', '000300.SH', '000905.SH', '000852.SH']
    for index_code in key_indices:
        analyzer.get_index_market_cap_distribution(index_code)

def get_specific_index_stocks(index_code: str, limit: int = None) -> List[str]:
    """
    获取指定指数的成分股代码列表
    
    Args:
        index_code: 指数代码
        limit: 限制返回数量
        
    Returns:
        股票代码列表
    """
    analyzer = MajorIndicesAnalyzer()
    constituents = analyzer.get_index_constituents(index_code)
    
    stock_codes = [stock['con_code'] for stock in constituents]
    
    if limit:
        stock_codes = stock_codes[:limit]
    
    return stock_codes

if __name__ == "__main__":
    main()
    
    print("\n" + "="*50)
    print("🎯 测试获取中证A500成分股:")
    a500_stocks = get_specific_index_stocks('000510.CSI', limit=20)
    print(f"前20只股票: {a500_stocks}")