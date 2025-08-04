#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高频数据测试 - 5分钟和30分钟行情数据
使用丰富的高频数据验证线段和中枢构建算法优化效果
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

chan_theory_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(chan_theory_root)

try:
    from database.db_handler import get_db_handler
    from models.kline import KLine, KLineList
    from models.fenxing import FenXing, FenXingList
    from models.bi import Bi, BiList, BiBuilder, BiConfig
    from models.seg import Seg, SegList, SegBuilder, SegConfig
    from models.zhongshu import ZhongShu, ZhongShuList, ZhongShuBuilder, ZhongShuConfig
    from models.enums import TimeLevel, BiDirection, SegDirection, ZhongShuType
    from core.kline_processor import KlineProcessor
    from config.chan_config import ChanConfig
    
    MODULES_AVAILABLE = True
except Exception as e:
    print(f"导入失败: {e}")
    MODULES_AVAILABLE = False


class TestHighFreqData(unittest.TestCase):
    """测试高频数据的线段和中枢构建"""
    
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
            
            # 检查高频数据可用性
            cls._check_data_availability()
            
        except Exception as e:
            raise unittest.SkipTest(f"数据库连接失败: {e}")
    
    @classmethod
    def _check_data_availability(cls):
        """检查高频数据可用性"""
        collections = cls.db.list_collection_names()
        
        cls.has_5min = 'stock_kline_5min' in collections
        cls.has_30min = 'stock_kline_30min' in collections
        
        if cls.has_5min:
            count_5min = cls.db['stock_kline_5min'].count_documents({})
            print(f"📊 5分钟数据: {count_5min:,} 条")
        
        if cls.has_30min:
            count_30min = cls.db['stock_kline_30min'].count_documents({})
            print(f"📊 30分钟数据: {count_30min:,} 条")
    
    @classmethod
    def tearDownClass(cls):
        """测试结束后清理资源"""
        try:
            if hasattr(cls, 'db_handler') and cls.db_handler:
                cls.db_handler.__del__()
                print("✅ 数据库连接已关闭")
                
            from database.db_handler import reset_db_handler
            reset_db_handler()
            print("✅ 数据库处理器单例已重置")
            
        except Exception as e:
            print(f"⚠️ 资源清理时出现异常: {e}")
        finally:
            print("🔒 数据库资源清理完成")
    
    def test_5min_data_comprehensive(self):
        """测试5分钟数据的完整分析"""
        if not self.has_5min:
            self.skipTest("5分钟数据不可用")
        
        print("\\n🔍 5分钟数据综合测试")
        
        # 获取5分钟数据
        collection = self.db['stock_kline_5min']
        stock_code = "000001.SZ"
        
        # 获取最近3000条5分钟数据（约10个交易日）
        query = {'ts_code': stock_code}
        cursor = collection.find(query).sort('trade_time', -1).limit(3000)
        raw_data = list(cursor)
        raw_data.reverse()  # 转为升序
        
        if len(raw_data) < 1000:
            self.skipTest(f"5分钟数据量不足: {len(raw_data)}条")
        
        print(f"📊 获取 {stock_code} 5分钟数据: {len(raw_data)} 条")
        
        # 转换数据
        converted_data = self._convert_5min_data(raw_data)
        
        if len(converted_data) < 500:
            self.skipTest(f"有效5分钟数据不足: {len(converted_data)}条")
        
        # 完整处理流水线
        result = self._process_complete_pipeline(converted_data, TimeLevel.MIN_5, "5分钟")
        
        # 验证高频数据的优势
        self.assertGreater(result['segs'], 5, "5分钟数据应该产生更多线段")
        self.assertGreater(result['zhongshus'], 1, "5分钟数据应该产生更多中枢")
        
        return result
    
    def test_30min_data_comprehensive(self):
        """测试30分钟数据的完整分析"""
        if not self.has_30min:
            self.skipTest("30分钟数据不可用")
        
        print("\\n🔍 30分钟数据综合测试")
        
        # 获取30分钟数据
        collection = self.db['stock_kline_30min']
        stock_code = "000001.SZ"
        
        # 获取最近2000条30分钟数据（约2个月）
        query = {'ts_code': stock_code}
        cursor = collection.find(query).sort('trade_time', -1).limit(2000)
        raw_data = list(cursor)
        raw_data.reverse()  # 转为升序
        
        if len(raw_data) < 500:
            self.skipTest(f"30分钟数据量不足: {len(raw_data)}条")
        
        print(f"📊 获取 {stock_code} 30分钟数据: {len(raw_data)} 条")
        
        # 转换数据
        converted_data = self._convert_30min_data(raw_data)
        
        if len(converted_data) < 300:
            self.skipTest(f"有效30分钟数据不足: {len(converted_data)}条")
        
        # 完整处理流水线
        result = self._process_complete_pipeline(converted_data, TimeLevel.MIN_30, "30分钟")
        
        # 验证结果
        self.assertGreater(result['segs'], 3, "30分钟数据应该产生足够的线段")
        self.assertGreaterEqual(result['zhongshus'], 1, "30分钟数据应该产生中枢")
        
        return result
    
    def test_multi_timeframe_comparison(self):
        """测试多时间框架对比"""
        print("\\n📊 多时间框架对比测试")
        
        results = {}
        
        # 测试日线数据（作为基线）
        try:
            daily_result = self._test_daily_baseline()
            results['daily'] = daily_result
            print(f"📈 日线结果: {daily_result['klines']}K线 -> {daily_result['segs']}线段 -> {daily_result['zhongshus']}中枢")
        except Exception as e:
            print(f"⚠️ 日线测试失败: {e}")
        
        # 测试30分钟数据
        if self.has_30min:
            try:
                min30_result = self.test_30min_data_comprehensive()
                results['30min'] = min30_result
                print(f"📈 30分钟结果: {min30_result['klines']}K线 -> {min30_result['segs']}线段 -> {min30_result['zhongshus']}中枢")
            except Exception as e:
                print(f"⚠️ 30分钟测试失败: {e}")
        
        # 测试5分钟数据
        if self.has_5min:
            try:
                min5_result = self.test_5min_data_comprehensive()
                results['5min'] = min5_result
                print(f"📈 5分钟结果: {min5_result['klines']}K线 -> {min5_result['segs']}线段 -> {min5_result['zhongshus']}中枢")
            except Exception as e:
                print(f"⚠️ 5分钟测试失败: {e}")
        
        # 对比分析
        if len(results) >= 2:
            print("\\n📊 时间框架对比分析:")
            for timeframe, result in results.items():
                zhongshu_density = result['zhongshus'] / result['segs'] if result['segs'] > 0 else 0
                print(f"  {timeframe:>8}: 线段{result['segs']:>3}个, 中枢{result['zhongshus']:>3}个, 密度{zhongshu_density:.2f}")
        
        return results
    
    def _convert_5min_data(self, raw_data: List[Dict]) -> List[Dict]:
        """转换5分钟数据格式"""
        converted_data = []
        for item in raw_data:
            try:
                # 5分钟数据使用trade_time字段，格式：'2024-01-02 09:30:00'
                if 'trade_time' in item:
                    timestamp_str = str(item['trade_time'])
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                else:
                    continue
                
                converted_item = {
                    'timestamp': timestamp,
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': int(float(item.get('vol', item.get('volume', 1)))),  # 默认1避免0
                    'amount': float(item.get('amount', 0)),
                    'symbol': item['ts_code']
                }
                
                # 检查价格数据的有效性
                if all(converted_item[k] > 0 for k in ['open', 'high', 'low', 'close']):
                    converted_data.append(converted_item)
                    
            except Exception as e:
                continue
        
        return converted_data
    
    def _convert_30min_data(self, raw_data: List[Dict]) -> List[Dict]:
        """转换30分钟数据格式"""
        converted_data = []
        for item in raw_data:
            try:
                # 30分钟数据使用trade_time字段，格式：'2025-07-10 09:30:00'
                if 'trade_time' in item:
                    timestamp_str = str(item['trade_time'])
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                else:
                    continue
                
                converted_item = {
                    'timestamp': timestamp,
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': int(float(item.get('vol', item.get('volume', 1)))),  # 默认1避免0
                    'amount': float(item.get('amount', 0)),
                    'symbol': item['ts_code']
                }
                
                # 检查价格数据的有效性
                if all(converted_item[k] > 0 for k in ['open', 'high', 'low', 'close']):
                    converted_data.append(converted_item)
                    
            except Exception as e:
                continue
        
        return converted_data
    
    def _process_complete_pipeline(self, converted_data: List[Dict], time_level: TimeLevel, level_name: str) -> Dict:
        """处理完整的缠论分析流水线"""
        # 创建KLineList
        kline_list = KLineList.from_mongo_data(converted_data, time_level)
        
        # K线处理和分型识别
        processed_klines, fenxings = self.processor.process_klines(kline_list)
        
        # 笔构建
        bi_builder = BiBuilder(BiConfig())
        bis = bi_builder.build_from_fenxings(fenxings)
        
        # 线段构建
        seg_builder = SegBuilder(SegConfig())
        segs = seg_builder.build_from_bis(bis)
        
        # 中枢构建
        zhongshu_builder = ZhongShuBuilder(ZhongShuConfig())
        zhongshus = zhongshu_builder.build_from_segs(segs)
        
        # 统计结果
        result = {
            'klines': len(processed_klines),
            'fenxings': len(fenxings),
            'bis': len(bis),
            'segs': len(segs),
            'zhongshus': len(zhongshus),
            'compression_ratio': (len(kline_list) - len(processed_klines)) / len(kline_list) if kline_list else 0
        }
        
        print(f"\\n📊 {level_name}数据处理结果:")
        print(f"  - 原始K线: {len(kline_list)}根")
        print(f"  - 处理后K线: {result['klines']}根")
        print(f"  - 压缩率: {result['compression_ratio']:.1%}")
        print(f"  - 分型: {result['fenxings']}个")
        print(f"  - 笔: {result['bis']}个")
        print(f"  - 线段: {result['segs']}个")
        print(f"  - 中枢: {result['zhongshus']}个")
        
        # 显示质量指标
        if bis:
            avg_bi_strength = sum(bi.strength for bi in bis) / len(bis)
            print(f"  - 平均笔强度: {avg_bi_strength:.3f}")
        
        if segs:
            avg_seg_strength = sum(seg.strength for seg in segs) / len(segs)
            avg_seg_integrity = sum(seg.integrity for seg in segs) / len(segs)
            print(f"  - 平均线段强度: {avg_seg_strength:.3f}")
            print(f"  - 平均线段完整性: {avg_seg_integrity:.3f}")
        
        if zhongshus:
            avg_zs_strength = sum(zs.strength for zs in zhongshus) / len(zhongshus)
            avg_zs_stability = sum(zs.stability for zs in zhongshus) / len(zhongshus)
            print(f"  - 平均中枢强度: {avg_zs_strength:.3f}")
            print(f"  - 平均中枢稳定性: {avg_zs_stability:.3f}")
            
            # 显示中枢样本
            print(f"\\n📋 {level_name}中枢样本 (前3个):")
            for i, zs in enumerate(zhongshus[:3]):
                duration_desc = f"{zs.duration_bars}根K线" if hasattr(zs, 'duration_bars') else ""
                print(f"  {i+1}. 区间:[{zs.low:.2f}-{zs.high:.2f}] "
                      f"中心:{zs.center:.2f} "
                      f"{len(zs.forming_segs)}线段 "
                      f"强度:{zs.strength:.3f} "
                      f"{duration_desc}")
        
        return result
    
    def _test_daily_baseline(self) -> Dict:
        """测试日线数据作为基线"""
        collection = self.db['stock_kline_daily']
        stock_code = "000001.SZ"
        
        query = {'ts_code': stock_code}
        cursor = collection.find(query).sort('trade_date', 1).limit(300)
        raw_data = list(cursor)
        
        # 转换日线数据
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
        
        return self._process_complete_pipeline(converted_data, TimeLevel.DAILY, "日线")


if __name__ == '__main__':
    print("🔥 高频数据缠论分析测试")
    print("=" * 60)
    print("📋 测试内容：")
    print("  - 5分钟数据完整流水线测试")
    print("  - 30分钟数据完整流水线测试")
    print("  - 多时间框架对比分析")
    print("  - 验证优化算法在高频数据下的效果")
    print("=" * 60)
    
    unittest.main(verbosity=2)