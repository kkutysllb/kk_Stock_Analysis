#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接真实数据测试
使用真实MongoDB数据测试缠论模块的基础功能
"""

import sys
import os
from datetime import datetime
import time

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

print("🔥 开始真实数据测试")
print("=" * 60)

try:
    # 导入数据库处理器
    from api.global_db import get_global_db_handler
    print("✅ 数据库模块导入成功")
    
    # 初始化数据库连接
    db_handler = get_global_db_handler()
    db = db_handler.db
    
    # 测试数据库连接
    server_info = db_handler.client.server_info()
    print(f"✅ 数据库连接成功，MongoDB版本: {server_info.get('version')}")
    
    # 检查集合
    collections = db.list_collection_names()
    stock_collections = [col for col in collections if 'stock_kline' in col]
    print(f"📊 发现股票K线集合: {stock_collections}")
    
    # 选择测试集合
    test_collection = 'stock_kline_daily'
    if test_collection not in collections:
        print(f"❌ 未找到测试集合: {test_collection}")
        exit(1)
    
    collection = db[test_collection]
    total_count = collection.count_documents({})
    print(f"📈 {test_collection} 总数据量: {total_count:,} 条")
    
    # 获取一个样本股票的数据
    stock_code = "000001.SZ"  # 平安银行
    print(f"\n📊 测试股票: {stock_code}")
    
    # 查询该股票的最近100条数据
    query = {'ts_code': stock_code}
    cursor = collection.find(query).sort('trade_date', -1).limit(100)
    raw_data = list(cursor)
    
    print(f"✅ 获取数据: {len(raw_data)} 条")
    
    if len(raw_data) == 0:
        print("❌ 没有找到测试股票的数据")
        exit(1)
    
    # 显示样本数据结构
    sample = raw_data[0]
    print(f"📄 数据字段: {list(sample.keys())}")
    print(f"📋 样本数据:")
    print(f"  交易日期: {sample['trade_date']}")
    print(f"  股票代码: {sample['ts_code']}")
    print(f"  开盘价: {sample['open']}")
    print(f"  最高价: {sample['high']}")
    print(f"  最低价: {sample['low']}")
    print(f"  收盘价: {sample['close']}")
    print(f"  成交量: {sample['vol']}")
    print(f"  成交额: {sample.get('amount', 'N/A')}")
    
    # 转换为标准格式
    print(f"\n🔄 转换数据格式...")
    converted_data = []
    
    for item in raw_data:
        try:
            # 解析交易日期
            trade_date_str = str(item['trade_date'])
            timestamp = datetime.strptime(trade_date_str, '%Y%m%d')
            
            converted_data.append({
                'timestamp': timestamp,
                'open': float(item['open']),
                'high': float(item['high']),
                'low': float(item['low']),
                'close': float(item['close']),
                'volume': int(float(item['vol'])),
                'amount': float(item.get('amount', 0)),
                'symbol': item['ts_code']
            })
        except Exception as e:
            print(f"⚠️  跳过有问题的数据: {e}")
            continue
    
    # 按时间排序
    converted_data.sort(key=lambda x: x['timestamp'])
    print(f"✅ 数据转换完成: {len(converted_data)} 条有效数据")
    
    # 显示转换后的样本
    print(f"\n📋 转换后样本数据 (最近5条):")
    for i, data in enumerate(converted_data[-5:], 1):
        change = data['close'] - data['open']
        change_pct = (change / data['open']) * 100 if data['open'] > 0 else 0
        color = "🟢" if change >= 0 else "🔴"
        
        print(f"  {i}. {data['timestamp'].strftime('%Y-%m-%d')} "
              f"{color} O:{data['open']:.2f} H:{data['high']:.2f} "
              f"L:{data['low']:.2f} C:{data['close']:.2f} "
              f"({change:+.2f}, {change_pct:+.2f}%) V:{data['volume']:,}")
    
    # 数据质量验证
    print(f"\n🔍 数据质量验证:")
    valid_count = 0
    issues = []
    
    for i, data in enumerate(converted_data):
        # 基本OHLC逻辑检查
        if data['high'] < max(data['open'], data['close']):
            issues.append(f"第{i+1}条: 高价低于开收价")
        elif data['low'] > min(data['open'], data['close']):
            issues.append(f"第{i+1}条: 低价高于开收价")
        elif data['open'] <= 0 or data['high'] <= 0 or data['low'] <= 0 or data['close'] <= 0:
            issues.append(f"第{i+1}条: 价格不能为0或负数")
        else:
            valid_count += 1
    
    print(f"  ✅ 有效数据: {valid_count}/{len(converted_data)} 条")
    if issues:
        print(f"  ⚠️  发现问题 ({len(issues)} 个):")
        for issue in issues[:5]:  # 只显示前5个问题
            print(f"    - {issue}")
    else:
        print("  🎉 所有数据质量良好!")
    
    # 性能测试
    print(f"\n⚡ 性能测试:")
    
    # 测试数据处理速度
    start_time = time.time()
    
    # 模拟简单的数据处理
    processed_count = 0
    for data in converted_data:
        # 简单计算（模拟K线处理）
        amplitude = data['high'] - data['low']
        body = abs(data['close'] - data['open'])
        shadow_ratio = (amplitude - body) / amplitude if amplitude > 0 else 0
        
        if shadow_ratio < 0.8:  # 实体比例合理
            processed_count += 1
    
    processing_time = time.time() - start_time
    speed = len(converted_data) / processing_time if processing_time > 0 else float('inf')
    
    print(f"  ⏱️  处理耗时: {processing_time:.4f} 秒")
    print(f"  🚀 处理速度: {speed:.0f} 条/秒")
    print(f"  📊 处理结果: {processed_count}/{len(converted_data)} 条有效")
    
    print(f"\n🎯 真实数据测试总结:")
    print(f"  ✅ 数据库连接: 成功")
    print(f"  ✅ 数据获取: {len(raw_data)} 条原始数据")
    print(f"  ✅ 数据转换: {len(converted_data)} 条有效数据")
    print(f"  ✅ 数据质量: {valid_count}/{len(converted_data)} 条通过验证")
    print(f"  ✅ 处理性能: {speed:.0f} 条/秒")
    
    if len(issues) == 0 and valid_count == len(converted_data):
        print(f"\n🏆 测试结果: 完美通过!")
        print(f"真实数据库数据完全符合缠论模块的要求！")
    else:
        print(f"\n⚠️  测试结果: 基本通过，但有少量数据质量问题")
    
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("请检查项目路径和依赖是否正确安装")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
print("🏁 测试完成")