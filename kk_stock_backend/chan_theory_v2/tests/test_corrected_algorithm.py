#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修正后的完整缠论算法
验证从K线到中枢的完整流程是否产生合理结果
"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(grandparent_dir)
sys.path.append(parent_dir)

from datetime import datetime, timedelta
from api.db_handler import DBHandler

# 使用与现有测试相同的导入方式
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.kline import KLine, KLineList, TimeLevel
from models.bi import Bi, BiList, BiBuilder, BiConfig
from models.seg import Seg, SegList, SegBuilder, SegConfig  
from models.zhongshu import ZhongShu, ZhongShuList, ZhongShuBuilder, ZhongShuConfig
from config.chan_config import ChanConfig
from core.kline_processor import KlineProcessor

def convert_daily_data_to_chan_format(raw_data):
    """转换日线数据为缠论格式"""
    converted_data = []
    
    for item in raw_data:
        try:
            # 解析交易日期
            trade_date_str = str(item['trade_date'])
            timestamp = datetime.strptime(trade_date_str, '%Y%m%d')
            
            converted_item = {
                'timestamp': timestamp,
                'open': float(item['open']),
                'high': float(item['high']),
                'low': float(item['low']),
                'close': float(item['close']),
                'volume': int(float(item['vol'])),  # vol可能是浮点数
                'amount': float(item.get('amount', 0)),
                'symbol': item['ts_code']
            }
            
            # 基本数据验证
            if (converted_item['open'] > 0 and converted_item['high'] > 0 and 
                converted_item['low'] > 0 and converted_item['close'] > 0):
                converted_data.append(converted_item)
                
        except (ValueError, KeyError) as e:
            continue  # 跳过有问题的数据
    
    # 按时间排序
    converted_data.sort(key=lambda x: x['timestamp'])
    return converted_data

def test_stock_with_larger_dataset(stock_code: str, limit: int = 1000):
    """使用更大数据集测试单只股票"""
    print(f"\n=== 测试股票 {stock_code} (数据量: {limit}) ===")
    
    try:
        # 获取数据
        db = DBHandler()
        collection = db.get_collection('stock_kline_daily')
        
        pipeline = [
            {"$match": {"ts_code": stock_code}},
            {"$sort": {"trade_date": -1}},
            {"$limit": limit}
        ]
        
        cursor = collection.aggregate(pipeline)
        raw_data = list(cursor)
        
        if len(raw_data) < 100:
            print(f"❌ 数据量不足: {len(raw_data)} 条")
            return None
        
        # 使用已有的数据转换方法
        converted_data = convert_daily_data_to_chan_format(raw_data)
        
        # 创建K线列表和处理器
        kline_list = KLineList.from_mongo_data(converted_data, TimeLevel.DAILY)
        config = ChanConfig()
        processor = KlineProcessor(config)
        
        print(f"📊 原始K线: {len(kline_list)} 条")
        
        # 步骤1: K线合并处理和分型识别
        processed_klines, fenxings = processor.process_klines(kline_list)
        print(f"📊 处理后K线: {len(processed_klines)} 条 (合并率: {(1-len(processed_klines)/len(kline_list))*100:.1f}%)")
        print(f"📊 分型数量: {len(fenxings)} 个")
        
        if len(fenxings) < 3:
            print("❌ 分型数量不足，跳过后续测试")
            return None
            
    except Exception as e:
        print(f"❌ 数据处理失败: {e}")
        return None
    
    # 测试不同的笔构建配置
    configs = [
        ("默认配置", BiConfig()),
        ("严格模式", BiConfig(fx_check_mode="strict", is_strict=True, allow_equal=False)),
        ("宽松模式", BiConfig(fx_check_mode="loss", is_strict=False, allow_equal=True, min_amplitude_ratio=0.0005)),
    ]
    
    best_result = None
    best_score = 0
    
    for config_name, bi_config in configs:
        print(f"\n--- 测试{config_name} ---")
        
        try:
            # 步骤2: 构建笔
            bi_list = BiList.from_fenxings(fenxings.fenxings, bi_config, TimeLevel.DAILY, processed_klines.klines)
            print(f"📊 笔数量: {len(bi_list)} 个")
            
            if len(bi_list) < 3:
                print("❌ 笔数量不足，跳过线段构建")
                continue
            
            # 步骤3: 构建线段（使用宽松配置）
            seg_config = SegConfig(
                min_bi_count=3,
                min_amplitude_ratio=0.001,
                eigen_fx_check=True,
                build_mode="chan"
            )
            seg_list = SegList.from_bis(bi_list.bis, seg_config)
            print(f"📊 线段数量: {len(seg_list)} 个")
            
            # 步骤4: 构建中枢（使用宽松配置）
            zhongshu_list = ZhongShuList([])  # 初始化空列表
            if len(seg_list) >= 3:
                zhongshu_config = ZhongShuConfig(
                    min_overlap_ratio=0.2,
                    allow_extension=True,
                    mode="loose"
                )
                zhongshu_list = ZhongShuList.from_segs(seg_list.segs, zhongshu_config)
            print(f"📊 中枢数量: {len(zhongshu_list)} 个")
            
            # 计算质量得分
            score = len(bi_list) + len(seg_list) * 2 + len(zhongshu_list) * 5
            print(f"📊 质量得分: {score} (笔:{len(bi_list)} + 线段:{len(seg_list)}*2 + 中枢:{len(zhongshu_list)}*5)")
            
            if score > best_score:
                best_score = score
                best_result = {
                    'config': config_name,
                    'bis': len(bi_list),
                    'segs': len(seg_list),
                    'zhongshus': len(zhongshu_list),
                    'score': score
                }
        except Exception as e:
            print(f"❌ {config_name}配置测试失败: {e}")
            continue
    
    # 总结
    print(f"\n🏆 {stock_code} 最佳结果:")
    if best_result:
        print(f"  配置: {best_result['config']}")
        print(f"  流程: {len(kline_list)}K线 -> {len(fenxings)}分型 -> {best_result['bis']}笔 -> {best_result['segs']}线段 -> {best_result['zhongshus']}中枢")
        print(f"  得分: {best_result['score']}")
    else:
        print("  无有效结果")
    
    return best_result

def test_multiple_stocks_with_various_sizes():
    """测试多只股票不同数据量"""
    print("\n" + "="*60)
    print("🔬 多股票不同数据量完整算法测试")
    print("="*60)
    
    # 测试不同的股票和数据量
    test_cases = [
        ("000001.SZ", 500),
        ("000001.SZ", 1000),
        ("000002.SZ", 500),
        ("600000.SH", 500),
        ("600036.SH", 500),
    ]
    
    all_results = []
    
    for stock_code, limit in test_cases:
        result = test_stock_with_larger_dataset(stock_code, limit)
        if result:
            result['stock'] = stock_code
            result['data_size'] = limit
            all_results.append(result)
    
    # 汇总分析
    print(f"\n" + "="*60)
    print("📊 完整测试汇总")
    print("="*60)
    
    if all_results:
        print("成功构建的案例:")
        for result in all_results:
            print(f"  {result['stock']}({result['data_size']}): {result['bis']}笔->{result['segs']}线段->{result['zhongshus']}中枢 (得分:{result['score']})")
        
        # 统计分析
        avg_bis = sum(r['bis'] for r in all_results) / len(all_results)
        avg_segs = sum(r['segs'] for r in all_results) / len(all_results)
        avg_zhongshus = sum(r['zhongshus'] for r in all_results) / len(all_results)
        
        print(f"\n平均数据:")
        print(f"  平均笔数: {avg_bis:.1f}")
        print(f"  平均线段数: {avg_segs:.1f}")
        print(f"  平均中枢数: {avg_zhongshus:.1f}")
        
        # 找出最佳结果
        best = max(all_results, key=lambda x: x['score'])
        print(f"\n最佳结果: {best['stock']}({best['data_size']}) - 得分:{best['score']}")
        
    else:
        print("❌ 所有测试都未能产生有效的线段和中枢")

def analyze_algorithm_bottlenecks():
    """分析算法瓶颈"""
    print(f"\n" + "="*60)
    print("🔍 算法瓶颈分析")
    print("="*60)
    
    # 获取测试数据
    db = DBHandler()
    collection = db.get_collection('stock_kline_daily')
    
    pipeline = [
        {"$match": {"ts_code": "000001.SZ"}},
        {"$sort": {"trade_date": -1}},
        {"$limit": 1000}
    ]
    
    cursor = collection.aggregate(pipeline)
    raw_data = list(cursor)
    
    # 转换数据格式
    converted_data = []
    for item in raw_data:
        try:
            trade_date_str = str(item['trade_date'])
            timestamp = datetime.strptime(trade_date_str, '%Y%m%d')
            
            converted_item = {
                'timestamp': timestamp,
                'open': float(item['open']),
                'high': float(item['high']),
                'low': float(item['low']),
                'close': float(item['close']),
                'volume': int(float(item['vol'])),
                'amount': float(item.get('amount', 0)),
                'symbol': item['ts_code']
            }
            
            if (converted_item['open'] > 0 and converted_item['high'] > 0 and 
                converted_item['low'] > 0 and converted_item['close'] > 0):
                converted_data.append(converted_item)
                
        except (ValueError, KeyError) as e:
            continue
    
    # 按时间排序
    converted_data.sort(key=lambda x: x['timestamp'])
    
    # 创建K线列表和处理器
    kline_list = KLineList.from_mongo_data(converted_data, TimeLevel.DAILY)
    config = ChanConfig()
    processor = KlineProcessor(config)
    
    # 处理K线并识别分型
    processed_klines, fenxings = processor.process_klines(kline_list)
    
    # 分析每个步骤的数据转换
    print(f"📊 步骤分析:")
    print(f"  K线: {len(kline_list)} -> 处理后: {len(processed_klines)} (转换率: {len(processed_klines)/len(kline_list)*100:.1f}%)")
    print(f"  分型: {len(fenxings)} (分型率: {len(fenxings)/len(processed_klines)*100:.1f}%)")
    
    if len(fenxings) == 0:
        print("❌ 没有分型，算法无法继续")
        return
    
    # 分型类型分析
    try:
        tops = fenxings.get_tops()
        bottoms = fenxings.get_bottoms()
        print(f"  分型类型: 顶分型{len(tops)}个, 底分型{len(bottoms)}个")
        
        # 笔分析 - 测试多种配置
        bi_configs = [
            ("超宽松", BiConfig(fx_check_mode="loss", is_strict=False, allow_equal=True, min_amplitude_ratio=0.0001)),
            ("宽松", BiConfig(fx_check_mode="loss", is_strict=False, allow_equal=True, min_amplitude_ratio=0.0005)),
            ("默认", BiConfig()),
            ("严格", BiConfig(fx_check_mode="strict", is_strict=True)),
        ]
        
        print(f"\n📊 笔构建分析:")
        max_bis = 0
        best_bi_list = None
        
        for config_name, bi_config in bi_configs:
            try:
                bi_list = BiList.from_fenxings(fenxings.fenxings, bi_config, TimeLevel.DAILY, processed_klines.klines)
                conversion_rate = len(bi_list)/(len(fenxings)//2)*100 if len(fenxings) > 0 else 0
                print(f"  {config_name}配置: {len(bi_list)}个笔 (转换率: {conversion_rate:.1f}%)")
                
                if len(bi_list) > max_bis:
                    max_bis = len(bi_list)
                    best_bi_list = bi_list
            except Exception as e:
                print(f"  {config_name}配置失败: {e}")
                continue
        
        if best_bi_list is None or len(best_bi_list) < 3:
            print("❌ 笔数量不足，无法构建线段")
            return
        
        # 线段分析 - 核心缠论算法，不能简化
        print(f"\n📊 线段构建分析:")
        seg_configs = [
            ("超宽松", SegConfig(min_bi_count=3, min_amplitude_ratio=0.0001, eigen_fx_check=False, build_mode="def")),
            ("宽松", SegConfig(min_bi_count=3, min_amplitude_ratio=0.001, eigen_fx_check=True, build_mode="chan")),
            ("默认", SegConfig()),
        ]
        
        max_segs = 0
        best_seg_list = None
        
        for config_name, seg_config in seg_configs:
            try:
                seg_list = SegList.from_bis(best_bi_list.bis, seg_config)
                conversion_rate = len(seg_list)/(max(len(best_bi_list)//3, 1))*100
                print(f"  {config_name}配置: {len(seg_list)}个线段 (转换率: {conversion_rate:.1f}%)")
                
                if len(seg_list) > max_segs:
                    max_segs = len(seg_list)
                    best_seg_list = seg_list
            except Exception as e:
                print(f"  {config_name}配置失败: {e}")
                continue
        
        if best_seg_list is None or len(best_seg_list) < 3:
            print("❌ 线段数量不足，无法构建中枢")
            return
        
        # 中枢分析 - 缠论核心，必须完整保留
        print(f"\n📊 中枢构建分析:")
        zhongshu_configs = [
            ("超宽松", ZhongShuConfig(min_overlap_ratio=0.1, allow_extension=True, mode="loose")),
            ("宽松", ZhongShuConfig(min_overlap_ratio=0.3, allow_extension=True, mode="loose")),
            ("默认", ZhongShuConfig()),
        ]
        
        for config_name, zhongshu_config in zhongshu_configs:
            try:
                zhongshu_list = ZhongShuList.from_segs(best_seg_list.segs, zhongshu_config)
                conversion_rate = len(zhongshu_list)/(max(len(best_seg_list)//3, 1))*100
                print(f"  {config_name}配置: {len(zhongshu_list)}个中枢 (转换率: {conversion_rate:.1f}%)")
            except Exception as e:
                print(f"  {config_name}配置失败: {e}")
                continue
                
    except Exception as e:
        print(f"❌ 完整算法分析失败: {e}")
        return

if __name__ == "__main__":
    print("🔬 修正后缠论算法完整测试")
    print("="*60)
    
    # 先分析算法瓶颈
    analyze_algorithm_bottlenecks()
    
    # 再测试多只股票
    test_multiple_stocks_with_various_sizes()
    
    print(f"\n✅ 修正后算法测试完成")