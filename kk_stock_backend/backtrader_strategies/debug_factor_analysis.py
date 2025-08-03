#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试因子分析问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.cloud_db_handler import CloudDBHandler

def debug_historical_data():
    """调试历史数据获取"""
    print("🔍 开始调试历史数据获取...")
    
    db_handler = CloudDBHandler()
    collection = db_handler.get_collection('stock_factor_pro')
    
    # 查询更长时间段的数据
    start_date = '20200101'  # 扩展到2020年
    end_date = '20241231'
    
    query = {
        'trade_date': {
            '$gte': start_date,
            '$lte': end_date
        }
    }
    
    # 先查询总数
    total_count = collection.count_documents(query)
    print(f"📊 符合条件的总记录数: {total_count}")
    
    # 获取少量样本查看结构
    sample_cursor = collection.find(query).limit(50)  # 增加样本数量
    samples = list(sample_cursor)
    
    if samples:
        print(f"\n📝 数据结构示例:")
        sample = samples[0]
        for key, value in sample.items():
            print(f"  {key}: {value} ({type(value).__name__})")
        
        # 检查股票分布
        stock_codes = set()
        for record in samples:
            stock_code = record.get('ts_code')
            if stock_code:
                stock_codes.add(stock_code)
        
        print(f"\n📈 样本中的股票:")
        for code in list(stock_codes)[:5]:
            print(f"  {code}")
        
        # 检查日期分布
        dates = set()
        for record in samples:
            trade_date = record.get('trade_date')
            if trade_date:
                dates.add(trade_date)
        
        print(f"\n📅 样本中的日期:")
        sorted_dates = sorted(list(dates))
        if len(sorted_dates) > 10:
            print(f"  {sorted_dates[0]} ... {sorted_dates[-1]} (共{len(sorted_dates)}个)")
            print(f"  最早10个: {sorted_dates[:10]}")
            print(f"  最晚10个: {sorted_dates[-10:]}")
        else:
            for date in sorted_dates:
                print(f"  {date}")
        
        # 检查关键字段
        print(f"\n🔍 关键字段检查:")
        close_values = [r.get('close') for r in samples if r.get('close')]
        ma_values = [r.get('ma_hfq_20') for r in samples if r.get('ma_hfq_20')]
        rsi_values = [r.get('rsi_bfq_12') for r in samples if r.get('rsi_bfq_12')]
        
        print(f"  close字段: {len(close_values)}/{len(samples)} 条有效")
        print(f"  ma_hfq_20字段: {len(ma_values)}/{len(samples)} 条有效")
        print(f"  rsi_bfq_12字段: {len(rsi_values)}/{len(samples)} 条有效")
        
        if close_values:
            print(f"  close样例: {close_values[:3]}")
        if ma_values:
            print(f"  ma_hfq_20样例: {ma_values[:3]}")
        if rsi_values:
            print(f"  rsi_bfq_12样例: {rsi_values[:3]}")
    
    else:
        print("❌ 未找到任何样本数据")
    
    # 测试按股票分组
    print(f"\n🔄 测试股票分组...")
    projection = {
        'ts_code': 1,
        'trade_date': 1,
        'close': 1,
        'ma_hfq_20': 1,
        'rsi_bfq_12': 1
    }
    
    cursor = collection.find(query, projection).limit(1000)  # 增加样本
    test_data = list(cursor)
    
    if test_data:
        # 按股票分组
        stock_groups = {}
        for record in test_data:
            stock_code = record.get('ts_code')
            if stock_code:
                if stock_code not in stock_groups:
                    stock_groups[stock_code] = []
                stock_groups[stock_code].append(record)
        
        print(f"📈 分组结果: {len(stock_groups)} 只股票")
        
        # 检查每只股票的记录数
        valid_count = 0
        for stock_code, records in stock_groups.items():
            record_count = len(records)
            if record_count >= 10:
                valid_count += 1
                if valid_count <= 3:
                    print(f"  {stock_code}: {record_count} 条记录")
                    # 检查日期排序
                    dates = [r.get('trade_date') for r in records if r.get('trade_date')]
                    if dates:
                        sorted_dates = sorted(dates)
                        print(f"    日期范围: {sorted_dates[0]} - {sorted_dates[-1]}")
        
        print(f"🎯 有效股票 (>=10条记录): {valid_count}")
    
    # 专门检查日期分布
    print("\n🔍 专门检查日期分布...")
    date_cursor = collection.find(query, {'trade_date': 1}).limit(2000)
    all_dates = [doc.get('trade_date') for doc in date_cursor if doc.get('trade_date')]
    unique_dates = sorted(list(set(all_dates)))
    
    if unique_dates:
        print(f"📅 唯一日期数量: {len(unique_dates)}")
        if len(unique_dates) > 20:
            print(f"📅 最早20个日期: {unique_dates[:20]}")
            print(f"📅 最晚20个日期: {unique_dates[-20:]}")
        else:
            print(f"📅 所有日期: {unique_dates}")
        
        # 检查特定股票的历史数据
        print("\n🎯 检查特定股票的历史数据...")
        test_stock = '000001.SZ'
        stock_query = {
            'ts_code': test_stock,
            'trade_date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        
        stock_cursor = collection.find(stock_query, {'trade_date': 1, 'close': 1}).sort('trade_date', 1)
        stock_data = list(stock_cursor)
        
        if stock_data:
            print(f"📊 股票 {test_stock} 历史记录数: {len(stock_data)}")
            if len(stock_data) > 10:
                print(f"🔍 前5条: {[(d['trade_date'], d.get('close')) for d in stock_data[:5]]}")
                print(f"🔍 后5条: {[(d['trade_date'], d.get('close')) for d in stock_data[-5:]]}")
            else:
                print(f"🔍 所有记录: {[(d['trade_date'], d.get('close')) for d in stock_data]}")
        else:
            print(f"❌ 股票 {test_stock} 无历史数据")
    
    else:
        print("❌ 未获取到任何日期数据")
        
    print("\n✅ 调试完成")

if __name__ == "__main__":
    debug_historical_data()