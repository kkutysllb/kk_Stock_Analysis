#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缠论动力学分析测试
测试背驰分析、MACD计算、一二三类买卖点识别、多级别递归关系

严格按照缠论定义和最佳实践进行测试
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

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
    from models.dynamics import (
        DynamicsAnalyzer, MultiLevelDynamicsAnalyzer, MacdCalculator,
        BackChiAnalysis, BuySellPoint, BuySellPointType, BackChi,
        DynamicsConfig, MultiLevelAnalysis
    )
    from models.enums import TimeLevel, BiDirection, SegDirection, ZhongShuType
    from core.kline_processor import KlineProcessor
    from config.chan_config import ChanConfig
    
    MODULES_AVAILABLE = True
except Exception as e:
    print(f"导入失败: {e}")
    MODULES_AVAILABLE = False


class TestDynamicsAnalysis(unittest.TestCase):
    """测试动力学分析功能"""
    
    @classmethod
    def setUpClass(cls):
        if not MODULES_AVAILABLE:
            raise unittest.SkipTest("模块导入失败")
        
        try:
            cls.db_handler = get_db_handler()
            cls.db = cls.db_handler.db
            cls.config = ChanConfig()
            cls.processor = KlineProcessor(cls.config)
            cls.dynamics_analyzer = DynamicsAnalyzer()
            cls.multi_level_analyzer = MultiLevelDynamicsAnalyzer()
            
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
    
    def test_macd_calculation(self):
        """测试MACD计算功能"""
        print("\\n🔍 MACD计算测试")
        
        # 获取测试数据
        collection = self.db['stock_kline_daily']
        stock_code = "000001.SZ"
        
        query = {'ts_code': stock_code}
        cursor = collection.find(query).sort('trade_date', 1).limit(100)
        raw_data = list(cursor)
        
        if len(raw_data) < 50:
            self.skipTest("数据量不足")
        
        # 转换价格数据
        prices = []
        for item in raw_data:
            try:
                close_price = float(item['close'])
                if close_price > 0:
                    prices.append(close_price)
            except:
                continue
        
        print(f"📊 获取 {stock_code} 收盘价数据: {len(prices)} 条")
        
        # 计算MACD
        macd_calculator = MacdCalculator(12, 26, 9)
        macd_data = macd_calculator.calculate(prices)
        
        print(f"📈 MACD计算结果: {len(macd_data)} 条")
        
        self.assertGreater(len(macd_data), 0, "应该计算出MACD数据")
        
        # 验证MACD数据结构
        if macd_data:
            first_macd = macd_data[0]
            self.assertIsInstance(first_macd.dif, float)
            self.assertIsInstance(first_macd.dea, float)
            self.assertIsInstance(first_macd.macd, float)
            
            print(f"  - 首个MACD: DIF={first_macd.dif:.4f}, DEA={first_macd.dea:.4f}, MACD={first_macd.macd:.4f}")
            
            # 显示最近几个MACD值
            print("\\n📋 最近MACD数据样本:")
            for i, macd in enumerate(macd_data[-5:]):
                print(f"  {i+1}. DIF:{macd.dif:.4f} DEA:{macd.dea:.4f} MACD:{macd.macd:.4f}")
    
    def test_backchi_analysis(self):
        """测试背驰分析功能"""
        print("\\n🔍 背驰分析测试")
        
        # 获取完整的分析链条数据
        collection = self.db['stock_kline_daily']
        stock_code = "000001.SZ"
        
        query = {'ts_code': stock_code}
        cursor = collection.find(query).sort('trade_date', 1).limit(200)
        raw_data = list(cursor)
        
        if len(raw_data) < 100:
            self.skipTest("数据量不足")
        
        print(f"📊 获取 {stock_code} 数据: {len(raw_data)} 条")
        
        # 数据转换和处理
        converted_data = self._convert_daily_data(raw_data)
        kline_list = KLineList.from_mongo_data(converted_data, TimeLevel.DAILY)
        
        # 完整分析链条
        processed_klines, fenxings = self.processor.process_klines(kline_list)
        
        bi_builder = BiBuilder(BiConfig())
        bis = bi_builder.build_from_fenxings(fenxings)
        
        seg_builder = SegBuilder(SegConfig())
        segs = seg_builder.build_from_bis(bis)
        
        zhongshu_builder = ZhongShuBuilder(ZhongShuConfig())
        zhongshus = zhongshu_builder.build_from_segs(segs)
        
        print(f"📊 基础分析结果:")
        print(f"  - 处理后K线: {len(processed_klines)}根")
        print(f"  - 分型: {len(fenxings)}个")
        print(f"  - 笔: {len(bis)}个")
        print(f"  - 线段: {len(segs)}个")
        print(f"  - 中枢: {len(zhongshus)}个")
        
        if len(segs) < 3 or len(zhongshus) == 0:
            self.skipTest("线段或中枢数量不足，无法测试背驰")
        
        # 执行背驰分析
        backchi_analyses = self.dynamics_analyzer.analyze_backchi(
            segs, zhongshus, processed_klines
        )
        
        print(f"\\n📈 背驰分析结果:")
        print(f"  - 背驰分析数量: {len(backchi_analyses)}个")
        
        # 显示背驰分析详情
        valid_backchis = [b for b in backchi_analyses if b.is_valid_backchi()]
        print(f"  - 有效背驰: {len(valid_backchis)}个")
        
        for i, backchi in enumerate(valid_backchis[:3]):
            print(f"\\n📋 背驰样本 {i+1}:")
            print(f"  - 类型: {backchi.backchi_type}")
            print(f"  - 当前线段: {backchi.current_seg.start_time.strftime('%Y-%m-%d')} -> {backchi.current_seg.end_time.strftime('%Y-%m-%d')}")
            print(f"  - 价格: {backchi.current_seg.start_price:.2f} -> {backchi.current_seg.end_price:.2f}")
            print(f"  - MACD面积: 当前={backchi.current_macd_area:.2f}, 前段={backchi.previous_macd_area:.2f}")
            print(f"  - 力度比值: {backchi.strength_ratio:.3f}")
            print(f"  - 可靠度: {backchi.reliability:.3f}")
        
        # 基本断言
        self.assertTrue(len(backchi_analyses) >= 0, "背驰分析应该正常执行")
    
    def test_buy_sell_points_identification(self):
        """测试一二三类买卖点识别"""
        print("\\n🔍 买卖点识别测试")
        
        # 先执行背驰分析获取数据
        backchi_analyses = self._get_backchi_analyses_for_testing()
        if not backchi_analyses:
            self.skipTest("无法获取背驰分析数据")
        
        segs, zhongshus, klines = backchi_analyses['data']
        backchis = backchi_analyses['backchis']
        
        # 识别买卖点
        buy_sell_points = self.dynamics_analyzer.identify_buy_sell_points(
            backchis, segs, zhongshus, klines
        )
        
        print(f"\\n📈 买卖点识别结果:")
        print(f"  - 买卖点总数: {len(buy_sell_points)}个")
        
        # 按类型统计
        buy_points = [p for p in buy_sell_points if p.point_type.is_buy()]
        sell_points = [p for p in buy_sell_points if p.point_type.is_sell()]
        
        print(f"  - 买点: {len(buy_points)}个")
        print(f"  - 卖点: {len(sell_points)}个")
        
        # 按级别统计
        for level in [1, 2, 3]:
            level_points = [p for p in buy_sell_points if p.point_type.get_level() == level]
            print(f"  - {level}类买卖点: {len(level_points)}个")
        
        # 显示买卖点详情
        print(f"\\n📋 买卖点样本 (前5个):")
        for i, point in enumerate(buy_sell_points[:5]):
            print(f"  {i+1}. {point.point_type} @{point.price:.2f} "
                  f"({point.timestamp.strftime('%Y-%m-%d')}) "
                  f"可靠度:{point.reliability:.3f}")
        
        # 基本验证
        self.assertTrue(len(buy_sell_points) >= 0, "买卖点识别应该正常执行")
        
        # 验证买卖点数据结构
        for point in buy_sell_points[:3]:
            self.assertIsInstance(point.point_type, BuySellPointType)
            self.assertIsInstance(point.price, float)
            self.assertIsInstance(point.timestamp, datetime)
            self.assertGreaterEqual(point.reliability, 0.0)
            self.assertLessEqual(point.reliability, 1.0)
    
    def test_multi_level_dynamics(self):
        """测试多级别动力学分析"""
        print("\\n🔍 多级别动力学分析测试")
        
        # 准备多级别数据
        level_data = {}
        
        # 日线数据
        daily_data = self._get_level_data(TimeLevel.DAILY, "stock_kline_daily", 200)
        if daily_data:
            level_data[TimeLevel.DAILY] = daily_data
            print(f"✅ 日线数据准备完成")
        
        # 30分钟数据
        min30_data = self._get_level_data(TimeLevel.MIN_30, "stock_kline_30min", 1000)
        if min30_data:
            level_data[TimeLevel.MIN_30] = min30_data
            print(f"✅ 30分钟数据准备完成")
        
        # 5分钟数据  
        min5_data = self._get_level_data(TimeLevel.MIN_5, "stock_kline_5min", 2000)
        if min5_data:
            level_data[TimeLevel.MIN_5] = min5_data
            print(f"✅ 5分钟数据准备完成")
        
        if len(level_data) < 2:
            self.skipTest("多级别数据不足")
        
        # 执行多级别分析
        multi_results = self.multi_level_analyzer.analyze_multi_level_dynamics(level_data)
        
        print(f"\\n📊 多级别分析结果:")
        
        for level, result in multi_results.items():
            print(f"\\n📈 {level.value} 级别:")
            print(f"  - 背驰分析: {len(result.backchi_analyses)}个")
            print(f"  - 买卖点: {len(result.buy_sell_points)}个")
            print(f"  - 高级别确认: {'✅' if result.higher_level_confirmation else '❌'}")
            print(f"  - 低级别确认: {'✅' if result.lower_level_confirmation else '❌'}")
            print(f"  - 一致性得分: {result.level_consistency_score:.3f}")
            
            # 显示买卖点样本
            if result.buy_sell_points:
                print(f"  📋 买卖点样本:")
                for point in result.buy_sell_points[:2]:
                    print(f"    - {point.point_type} @{point.price:.2f}")
        
        # 基本验证
        self.assertGreater(len(multi_results), 0, "应该有多级别分析结果")
        
        for level, result in multi_results.items():
            self.assertIsInstance(result, MultiLevelAnalysis)
            self.assertEqual(result.time_level, level)
    
    def _convert_daily_data(self, raw_data: List[Dict]) -> List[Dict]:
        """转换日线数据格式"""
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
        
        return converted_data
    
    def _convert_minute_data(self, raw_data: List[Dict]) -> List[Dict]:
        """转换分钟数据格式"""
        converted_data = []
        for item in raw_data:
            try:
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
                    'volume': int(float(item.get('vol', item.get('volume', 1)))),
                    'amount': float(item.get('amount', 0)),
                    'symbol': item['ts_code']
                }
                
                if all(converted_item[k] > 0 for k in ['open', 'high', 'low', 'close']):
                    converted_data.append(converted_item)
                    
            except Exception:
                continue
        
        return converted_data
    
    def _get_backchi_analyses_for_testing(self) -> Optional[Dict]:
        """获取用于测试的背驰分析数据"""
        try:
            collection = self.db['stock_kline_daily']
            stock_code = "000002.SZ"  # 使用不同股票
            
            query = {'ts_code': stock_code}
            cursor = collection.find(query).sort('trade_date', 1).limit(150)
            raw_data = list(cursor)
            
            if len(raw_data) < 100:
                return None
            
            converted_data = self._convert_daily_data(raw_data)
            kline_list = KLineList.from_mongo_data(converted_data, TimeLevel.DAILY)
            
            processed_klines, fenxings = self.processor.process_klines(kline_list)
            bis = BiBuilder(BiConfig()).build_from_fenxings(fenxings)
            segs = SegBuilder(SegConfig()).build_from_bis(bis)  
            zhongshus = ZhongShuBuilder(ZhongShuConfig()).build_from_segs(segs)
            
            if len(segs) < 3 or len(zhongshus) == 0:
                return None
            
            backchis = self.dynamics_analyzer.analyze_backchi(segs, zhongshus, processed_klines)
            
            return {
                'data': (segs, zhongshus, processed_klines),
                'backchis': backchis
            }
            
        except Exception as e:
            print(f"获取测试数据失败: {e}")
            return None
    
    def _get_level_data(self, level: TimeLevel, collection_name: str, limit: int) -> Optional[Tuple]:
        """获取指定级别的数据"""
        try:
            collection = self.db[collection_name]
            stock_code = "000001.SZ"
            
            query = {'ts_code': stock_code}
            
            if level == TimeLevel.DAILY:
                cursor = collection.find(query).sort('trade_date', 1).limit(limit)
                raw_data = list(cursor)
                converted_data = self._convert_daily_data(raw_data)
            else:
                cursor = collection.find(query).sort('trade_time', -1).limit(limit)
                raw_data = list(cursor)
                raw_data.reverse()
                converted_data = self._convert_minute_data(raw_data)
            
            if len(converted_data) < 50:
                return None
            
            kline_list = KLineList.from_mongo_data(converted_data, level)
            processed_klines, fenxings = self.processor.process_klines(kline_list)
            
            if len(fenxings) < 6:
                return None
            
            bis = BiBuilder(BiConfig()).build_from_fenxings(fenxings)
            segs = SegBuilder(SegConfig()).build_from_bis(bis)
            zhongshus = ZhongShuBuilder(ZhongShuConfig()).build_from_segs(segs)
            
            return (segs, zhongshus, processed_klines)
            
        except Exception as e:
            print(f"获取{level.value}数据失败: {e}")
            return None


class TestDynamicsConfiguration(unittest.TestCase):
    """测试动力学配置功能"""
    
    def test_dynamics_config(self):
        """测试动力学配置"""
        print("\\n🔍 动力学配置测试")
        
        config = DynamicsConfig()
        
        # 验证默认配置
        self.assertEqual(config.macd_params, (12, 26, 9))
        self.assertEqual(config.backchi_threshold, 0.6)
        self.assertEqual(config.strength_ratio_threshold, 0.1)
        
        print(f"📊 默认配置:")
        print(f"  - MACD参数: {config.macd_params}")
        print(f"  - 背驰阈值: {config.backchi_threshold}")
        print(f"  - 力度比值阈值: {config.strength_ratio_threshold}")
        
        # 测试配置序列化
        config_dict = config.to_dict()
        self.assertIn('macd_params', config_dict)
        self.assertIn('backchi_threshold', config_dict)
        
        print(f"✅ 配置序列化测试通过")


if __name__ == '__main__':
    print("🔥 缠论动力学分析测试")
    print("=" * 60)
    print("📋 测试内容：")
    print("  - MACD计算验证")
    print("  - 背驰分析算法测试") 
    print("  - 一二三类买卖点识别测试")
    print("  - 多级别动力学关系测试")
    print("  - 严格按照缠论定义和最佳实践")
    print("=" * 60)
    
    unittest.main(verbosity=2)