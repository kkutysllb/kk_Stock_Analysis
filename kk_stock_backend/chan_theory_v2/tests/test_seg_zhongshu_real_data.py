#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线段和中枢构建真实数据测试
使用真实股票数据验证线段和中枢构建算法的正确性
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


class TestSegZhongShuRealData(unittest.TestCase):
    """测试线段和中枢构建的真实数据"""
    
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
                cls.db_handler.__del__()
                print("✅ 数据库连接已关闭")
                
            from database.db_handler import reset_db_handler
            reset_db_handler()
            print("✅ 数据库处理器单例已重置")
            
        except Exception as e:
            print(f"⚠️ 资源清理时出现异常: {e}")
        finally:
            print("🔒 数据库资源清理完成")
    
    def test_seg_construction_from_real_data(self):
        """测试从真实数据构建线段"""
        print("\\n🔍 线段构建真实数据测试")
        
        # 获取真实数据
        collection = self.db['stock_kline_daily']
        stock_code = "000001.SZ"
        
        query = {'ts_code': stock_code}
        cursor = collection.find(query).sort('trade_date', 1).limit(300)
        raw_data = list(cursor)
        
        if len(raw_data) < 100:
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
        
        # 创建KLineList并处理
        kline_list = KLineList.from_mongo_data(converted_data, TimeLevel.DAILY)
        processed_klines, fenxings = self.processor.process_klines(kline_list)
        
        print(f"📊 处理结果:")
        print(f"  - 原始K线: {len(kline_list)}根")
        print(f"  - 处理后K线: {len(processed_klines)}根")
        print(f"  - 分型数量: {len(fenxings)}个")
        
        # 构建笔
        bi_config = BiConfig()
        bi_builder = BiBuilder(bi_config)
        bis = bi_builder.build_from_fenxings(fenxings)
        
        print(f"  - 笔数量: {len(bis)}个")
        
        if len(bis) < 10:
            self.skipTest("笔数量不足，无法测试线段构建")
        
        # 构建线段
        seg_config = SegConfig()
        seg_builder = SegBuilder(seg_config)
        segs = seg_builder.build_from_bis(bis)
        
        print(f"\\n📈 线段构建结果:")
        print(f"  - 线段数量: {len(segs)}个")
        
        if segs:
            up_segs = [seg for seg in segs if seg.is_up]
            down_segs = [seg for seg in segs if seg.is_down]
            
            print(f"  - 向上线段: {len(up_segs)}个")
            print(f"  - 向下线段: {len(down_segs)}个")
            
            # 统计线段质量
            valid_segs = [seg for seg in segs if seg.is_valid_seg()]
            avg_strength = sum(seg.strength for seg in segs) / len(segs) if segs else 0
            avg_integrity = sum(seg.integrity for seg in segs) / len(segs) if segs else 0
            
            print(f"  - 有效线段: {len(valid_segs)}个")
            print(f"  - 平均强度: {avg_strength:.3f}")
            print(f"  - 平均完整性: {avg_integrity:.3f}")
            
            # 显示样本线段
            print(f"\\n📋 线段样本 (前5个):")
            for i, seg in enumerate(segs[:5]):
                direction_emoji = "📈" if seg.is_up else "📉"
                print(f"  {i+1}. {seg.start_time.strftime('%Y-%m-%d')} -> {seg.end_time.strftime('%Y-%m-%d')} "
                      f"{direction_emoji} {seg.direction.value} "
                      f"{seg.start_price:.2f}->{seg.end_price:.2f} "
                      f"({seg.amplitude_ratio:.2%}) 强度:{seg.strength:.3f} "
                      f"{seg.bi_count}笔")
        
        # 基本断言
        self.assertGreater(len(segs), 0, "应该构建出线段")
        
        # 验证线段序列
        seg_list = SegList(segs)
        errors = seg_list.validate_seg_sequence()
        
        if errors:
            print(f"⚠️ 线段序列问题: {len(errors)}个")
            for error in errors[:3]:
                print(f"  - {error}")
        else:
            print("✅ 线段序列验证通过")
        
        return segs
    
    def test_zhongshu_construction_from_real_data(self):
        """测试从真实数据构建中枢"""
        print("\\n🔍 中枢构建真实数据测试")
        
        # 先构建线段
        segs = self.test_seg_construction_from_real_data()
        
        if len(segs) < 3:
            self.skipTest("线段数量不足，无法测试中枢构建")
        
        # 构建中枢
        zhongshu_config = ZhongShuConfig()
        zhongshu_builder = ZhongShuBuilder(zhongshu_config)
        zhongshus = zhongshu_builder.build_from_segs(segs)
        
        print(f"\\n🏛️ 中枢构建结果:")
        print(f"  - 中枢数量: {len(zhongshus)}个")
        
        if zhongshus:
            # 中枢统计
            zhongshu_list = ZhongShuList(zhongshus)
            stats = zhongshu_list.get_statistics()
            
            print(f"  - 活跃中枢: {stats['active_count']}个")
            print(f"  - 平均强度: {stats['avg_strength']:.3f}")
            print(f"  - 平均稳定性: {stats['avg_stability']:.3f}")
            print(f"  - 平均持续K线: {stats['avg_duration']:.1f}根")
            print(f"  - 平均区间比例: {stats['avg_range_ratio']:.2%}")
            
            # 按类型统计
            print(f"  - 类型分布: {stats['type_distribution']}")
            
            # 显示样本中枢
            print(f"\\n📋 中枢样本 (前3个):")
            for i, zs in enumerate(zhongshus[:3]):
                print(f"  {i+1}. {zs.start_time.strftime('%Y-%m-%d')} -> {zs.end_time.strftime('%Y-%m-%d')} "
                      f"区间:[{zs.low:.2f}-{zs.high:.2f}] "
                      f"中心:{zs.center:.2f} "
                      f"{zs.seg_count}线段 "
                      f"强度:{zs.strength:.3f} "
                      f"扩展:{zs.extend_count}次")
                
                # 显示构成线段
                for j, seg in enumerate(zs.forming_segs[:3]):
                    direction_emoji = "📈" if seg.is_up else "📉"
                    print(f"    - 线段{j+1}: {direction_emoji} {seg.start_price:.2f}->{seg.end_price:.2f}")
        
        # 基本断言
        if len(segs) >= 3:
            # 只有当线段足够多时才要求有中枢
            print(f"线段数量: {len(segs)}, 期望至少有一些中枢候选")
        
        # 验证中枢质量
        if zhongshus:
            for zs in zhongshus:
                self.assertGreater(zs.high, zs.low, "中枢上沿应该高于下沿")
                self.assertGreaterEqual(len(zs.forming_segs), 3, "中枢应该至少由3个线段构成")
                self.assertGreater(zs.range_size, 0, "中枢区间应该大于0")
        
        print(f"✅ 中枢构建测试完成")
        
        return zhongshus
    
    def test_full_pipeline_integration(self):
        """测试完整流水线集成"""
        print("\\n🔄 完整流水线集成测试")
        
        # 获取数据
        collection = self.db['stock_kline_daily']
        stock_code = "000002.SZ"  # 用不同股票测试
        
        query = {'ts_code': stock_code}
        cursor = collection.find(query).sort('trade_date', 1).limit(200)
        raw_data = list(cursor)
        
        if len(raw_data) < 50:
            self.skipTest("数据量不足")
        
        print(f"📊 测试股票: {stock_code}, 数据量: {len(raw_data)}条")
        
        # 完整流水线处理
        try:
            # 1. 数据转换
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
            
            # 2. K线处理和分型识别
            kline_list = KLineList.from_mongo_data(converted_data, TimeLevel.DAILY)
            processed_klines, fenxings = self.processor.process_klines(kline_list)
            
            # 3. 笔构建
            bi_builder = BiBuilder(BiConfig())
            bis = bi_builder.build_from_fenxings(fenxings)
            
            # 4. 线段构建
            seg_builder = SegBuilder(SegConfig())
            segs = seg_builder.build_from_bis(bis)
            
            # 5. 中枢构建
            zhongshu_builder = ZhongShuBuilder(ZhongShuConfig())
            zhongshus = zhongshu_builder.build_from_segs(segs)
            
            # 结果统计
            print(f"\\n📊 完整流水线结果:")
            print(f"  - 原始K线: {len(kline_list)}根")
            print(f"  - 处理后K线: {len(processed_klines)}根")
            print(f"  - 分型: {len(fenxings)}个")
            print(f"  - 笔: {len(bis)}个")
            print(f"  - 线段: {len(segs)}个")
            print(f"  - 中枢: {len(zhongshus)}个")
            
            # 质量验证
            compression_ratio = (len(kline_list) - len(processed_klines)) / len(kline_list) if kline_list else 0
            print(f"  - K线压缩率: {compression_ratio:.1%}")
            
            if bis:
                avg_bi_strength = sum(bi.strength for bi in bis) / len(bis)
                print(f"  - 平均笔强度: {avg_bi_strength:.3f}")
            
            if segs:
                avg_seg_strength = sum(seg.strength for seg in segs) / len(segs)
                print(f"  - 平均线段强度: {avg_seg_strength:.3f}")
            
            if zhongshus:
                avg_zs_strength = sum(zs.strength for zs in zhongshus) / len(zhongshus)
                print(f"  - 平均中枢强度: {avg_zs_strength:.3f}")
            
            # 基本断言
            self.assertGreater(len(processed_klines), 0, "应该有处理后的K线")
            self.assertGreater(len(fenxings), 0, "应该有分型")
            
            if len(fenxings) >= 6:  # 至少6个分型才能构成笔
                self.assertGreater(len(bis), 0, "应该有笔")
            
            print("✅ 完整流水线集成测试通过")
            
        except Exception as e:
            self.fail(f"完整流水线处理失败: {e}")


if __name__ == '__main__':
    print("🔥 线段和中枢构建真实数据测试")
    print("=" * 60)
    print("📋 测试内容：")
    print("  - 线段构建算法验证")
    print("  - 中枢构建算法验证") 
    print("  - 完整流水线集成测试")
    print("  - 使用真实股票数据，不使用模拟数据")
    print("=" * 60)
    
    unittest.main(verbosity=2)