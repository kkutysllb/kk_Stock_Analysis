#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询申万行业分布和价值投资适合的行业
"""

import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from api.global_db import get_global_db_handler

def main():
    """查询申万行业数据"""
    db = get_global_db_handler()
    
    # 查看申万一级行业分布
    pipeline = [
        {'$group': {'_id': {'l1_code': '$l1_code', 'l1_name': '$l1_name'}, 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    
    print("🔍 正在查询申万一级行业分布...")
    l1_industries = list(db.get_collection('index_member_all').aggregate(pipeline))
    
    print('\n📊 申万一级行业分布:')
    for i, industry in enumerate(l1_industries, 1):
        print(f'{i:2d}. {industry["_id"]["l1_name"]} ({industry["_id"]["l1_code"]}): {industry["count"]}只股票')
    
    print('\n🎯 价值投资策略常关注的传统行业:')
    value_industries = ['银行', '保险', '房地产', '钢铁', '煤炭', '石油', '电力', '建筑', '交通运输', '公用事业', '汽车', '机械', '化工']
    found_industries = []
    
    for industry in l1_industries:
        name = industry['_id']['l1_name']
        for target in value_industries:
            if target in name or name in target:
                found_industries.append(industry)
                print(f'✅ {name} ({industry["_id"]["l1_code"]}): {industry["count"]}只股票')
                break
    
    print(f'\n💡 建议: 价值投资策略可以从这{len(found_industries)}个传统行业中筛选股票，而不是从中证A500全行业中选择')
    
    # 查看具体的价值行业股票示例
    print('\n📝 查看银行行业股票示例:')
    bank_stocks = list(db.get_collection('index_member_all').find(
        {'l1_name': {'$regex': '银行'}}, 
        {'ts_code': 1, 'l1_name': 1, 'l2_name': 1, 'l3_name': 1}
    ).limit(10))
    
    for stock in bank_stocks:
        print(f"  {stock['ts_code']} - {stock['l1_name']} > {stock['l2_name']} > {stock['l3_name']}")

def get_value_industry_stocks(limit: int = None) -> List[str]:
    """
    获取价值投资适合的申万行业股票列表
    
    Args:
        limit: 限制返回的股票数量，None表示返回全部
        
    Returns:
        股票代码列表
    """
    db = get_global_db_handler()
    
    # 价值投资重点关注的申万一级行业
    value_industry_names = [
        '银行', '房地产', '钢铁', '煤炭', '石油石化', 
        '公用事业', '交通运输', '建筑装饰', '建筑材料',
        '汽车', '机械设备', '基础化工', '电力设备'
    ]
    
    # 构建查询条件
    query = {'l1_name': {'$in': value_industry_names}}
    
    # 查询股票代码
    projection = {'ts_code': 1, 'l1_name': 1, '_id': 0}
    
    if limit:
        stocks = list(db.get_collection('index_member_all').find(query, projection).limit(limit))
    else:
        stocks = list(db.get_collection('index_member_all').find(query, projection))
    
    # 提取股票代码并去重
    stock_codes = list(set([stock['ts_code'] for stock in stocks if stock.get('ts_code')]))
    
    print(f"📊 从申万价值行业获取 {len(stock_codes)} 只股票")
    
    # 按行业统计
    industry_stats = {}
    for stock in stocks:
        industry = stock.get('l1_name')
        if industry not in industry_stats:
            industry_stats[industry] = 0
        industry_stats[industry] += 1
    
    print("📈 各行业股票数量:")
    for industry, count in sorted(industry_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {industry}: {count}只")
    
    return sorted(stock_codes)

if __name__ == "__main__":
    main()
    
    print("\n" + "="*50)
    print("🎯 测试价值投资股票池获取功能:")
    value_stocks = get_value_industry_stocks(limit=200)
    print(f"前20只股票示例: {value_stocks[:20]}")