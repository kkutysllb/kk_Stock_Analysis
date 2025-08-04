#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试K线合并功能的独立测试脚本
使用单一股票的干净数据，验证K线合并算法的正确性
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from typing import List

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

chan_theory_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(chan_theory_root)

try:
    from database.db_handler import get_db_handler
    from models.kline import KLine, KLineList
    from models.enums import TimeLevel
    from core.kline_processor import KlineProcessor
    from config.chan_config import ChanConfig
    
    MODULES_AVAILABLE = True
except Exception as e:
    print(f"导入失败: {e}")
    MODULES_AVAILABLE = False


class TestKlineMergeOnly(unittest.TestCase):
    """专门测试K线合并功能"""
    
    @classmethod
    def setUpClass(cls):
        if not MODULES_AVAILABLE:
            raise unittest.SkipTest("模块导入失败")
        
        try:
            cls.db_handler = get_db_handler()
            cls.db = cls.db_handler.db
            cls.config = ChanConfig()
            cls.processor = KlineProcessor(cls.config)
            
            cls.db.command('ping')
            print("✅ 数据库连接成功")
            
        except Exception as e:
            raise unittest.SkipTest(f"数据库连接失败: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """测试结束后清理资源"""
        try:
            if hasattr(cls, 'db_handler') and cls.db_handler:
                # 调用析构方法来正确关闭所有连接
                cls.db_handler.__del__()
                print("✅ 数据库连接已关闭")
                
            # 重置全局数据库处理器单例，确保资源完全释放
            from database.db_handler import reset_db_handler
            reset_db_handler()
            print("✅ 数据库处理器单例已重置")
            
        except Exception as e:
            print(f"⚠️ 资源清理时出现异常: {e}")
        finally:
            print("🔒 数据库资源清理完成")
    
    def test_single_stock_clean_data(self):
        """测试单一股票的干净数据"""
        print("\n🔍 单一股票K线合并测试")
        
        # 获取平安银行最近100根K线
        collection = self.db['stock_kline_daily']
        stock_code = "000001.SZ"
        
        # 使用升序排序，确保时间顺序正确
        query = {'ts_code': stock_code}
        cursor = collection.find(query).sort('trade_date', 1).limit(100)  # 改为升序
        raw_data = list(cursor)
        
        if len(raw_data) < 50:
            self.skipTest("数据量不足")
        
        print(f"📊 获取 {stock_code} 数据: {len(raw_data)} 条")
        
        # 转换数据
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
                
                if all(converted_item[k] > 0 for k in ['open', 'high', 'low', 'close']):
                    converted_data.append(converted_item)
                    
            except Exception:
                continue
        
        # 验证时间顺序
        timestamps = [item['timestamp'] for item in converted_data]
        self.assertEqual(timestamps, sorted(timestamps), "输入数据时间顺序应该正确")
        
        # 创建KLineList
        kline_list = KLineList.from_mongo_data(converted_data, TimeLevel.DAILY)
        
        print(f"✅ 创建KLineList: {len(kline_list)}根K线")
        
        # 验证输入数据时间顺序
        input_errors = self.processor._validate_input_data(kline_list)
        if input_errors:
            print(f"⚠️  输入数据问题: {len(input_errors)}个")
            for error in input_errors[:3]:
                print(f"  - {error}")
        else:
            print("✅ 输入数据验证通过")
        
        # 处理K线
        processed_klines, fenxings = self.processor.process_klines(kline_list)
        
        # 验证处理结果
        processing_errors = self.processor.validate_processed_klines(processed_klines)
        
        print(f"📊 处理结果:")
        print(f"  - 原始K线: {len(kline_list)}根")
        print(f"  - 处理后K线: {len(processed_klines)}根") 
        print(f"  - 合并数量: {len(kline_list) - len(processed_klines)}根")
        print(f"  - 合并比例: {(len(kline_list) - len(processed_klines)) / len(kline_list) * 100:.1f}%")
        print(f"  - 分型数量: {len(fenxings)}个")
        print(f"  - 处理错误: {len(processing_errors)}个")
        
        if processing_errors:
            print("⚠️  处理质量问题:")
            for error in processing_errors[:5]:
                print(f"  - {error}")
        else:
            print("✅ 处理质量验证通过")
        
        # 基本断言
        self.assertGreater(len(processed_klines), 0, "应该有处理后的K线")
        self.assertLessEqual(len(processed_klines), len(kline_list), "处理后K线不应增加")
        
        # 严格的质量要求：对于单一股票的干净数据，不应该有时间顺序错误
        time_order_errors = [error for error in processing_errors if "时间顺序错误" in error]
        if time_order_errors:
            print(f"❌ 时间顺序错误: {len(time_order_errors)}个")
            self.assertEqual(len(time_order_errors), 0, f"单一股票数据不应该有时间顺序错误: {time_order_errors[:3]}")
        else:
            print("✅ 时间顺序验证通过")
        
        return processed_klines, fenxings
    
    def test_merge_algorithm_correctness(self):
        """测试合并算法的正确性"""
        print("\n🔧 测试合并算法正确性")
        
        # 处理数据
        processed_klines, fenxings = self.test_single_stock_clean_data()
        
        # 检查缠论合规性
        chan_violations = self.processor.validate_chan_theory_compliance(processed_klines)
        
        print(f"📋 缠论标准验证:")
        print(f"  - 违规项目: {len(chan_violations)}个")
        
        if chan_violations:
            print("⚠️  缠论标准问题:")
            for violation in chan_violations[:5]:
                print(f"  - {violation}")
        else:
            print("✅ 完全符合缠论标准")
        
        # 获取处理统计
        stats = self.processor.get_processing_statistics(
            KLineList([KLine(
                timestamp=datetime.now(),
                open=10, high=11, low=9, close=10.5, volume=1000
            )] * 100),  # 模拟原始数据
            processed_klines,
            fenxings
        )
        
        print(f"📊 处理统计:")
        print(f"  - 处理质量: {stats['processing_quality']}")
        print(f"  - 质量问题数: {stats['quality_issues_count']}")
        print(f"  - 平均合并数: {stats['avg_merge_count']:.2f}")
        print(f"  - 最大合并数: {stats['max_merge_count']}")
        
        # 严格质量要求
        self.assertEqual(len(chan_violations), 0, "应该完全符合缠论标准")
        self.assertIn(stats['processing_quality'], ['excellent', 'good'], 
                     f"处理质量应该优秀: {stats['processing_quality']}")
        
        return stats

if __name__ == '__main__':
    print("🔥 K线合并功能专项测试")
    print("=" * 50)
    print("📋 测试内容：专门验证K线合并算法正确性")
    print("=" * 50)
    
    unittest.main(verbosity=2)