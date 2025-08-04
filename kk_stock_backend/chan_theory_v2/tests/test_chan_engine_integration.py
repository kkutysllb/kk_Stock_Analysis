#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缠论分析引擎集成测试
测试完整的缠论分析流程：形态学 + 动力学 + 多级别分析

展示缠论v2模块的完整功能和最佳实践应用
"""

import unittest
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

chan_theory_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(chan_theory_root)

try:
    from database.db_handler import get_db_handler
    from models.enums import TimeLevel
    from core.chan_engine import ChanEngine, ChanAnalysisResult, AnalysisLevel, quick_analyze, multi_level_analyze
    from models.dynamics import DynamicsConfig
    from config.chan_config import ChanConfig
    
    MODULES_AVAILABLE = True
except Exception as e:
    print(f"导入失败: {e}")
    MODULES_AVAILABLE = False


class TestChanEngineIntegration(unittest.TestCase):
    """测试缠论分析引擎集成功能"""
    
    @classmethod
    def setUpClass(cls):
        if not MODULES_AVAILABLE:
            raise unittest.SkipTest("模块导入失败")
        
        try:
            cls.db_handler = get_db_handler()
            cls.db = cls.db_handler.db
            cls.chan_engine = ChanEngine()
            
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
    
    def test_basic_analysis(self):
        """测试基础分析功能"""
        print("\\n🔍 基础分析测试")
        
        # 获取测试数据
        data = self._get_daily_data("000001.SZ", 200)
        if not data:
            self.skipTest("无法获取测试数据")
        
        # 执行基础分析
        result = self.chan_engine.analyze(
            data=data,
            symbol="000001.SZ",
            time_level=TimeLevel.DAILY,
            analysis_level=AnalysisLevel.BASIC
        )
        
        # 验证结果
        self.assertIsInstance(result, ChanAnalysisResult)
        self.assertEqual(result.symbol, "000001.SZ")
        self.assertEqual(result.time_level, TimeLevel.DAILY)
        self.assertEqual(result.analysis_level, AnalysisLevel.BASIC)
        
        print(f"📊 基础分析结果:")
        stats = result.get_statistics()
        print(f"  - 原始K线: {stats['klines_count']}根")
        print(f"  - 处理后K线: {stats['processed_klines_count']}根")
        print(f"  - 分型: {stats['fenxings_count']}个")
        print(f"  - 笔: {stats['bis_count']}个")
        print(f"  - 线段: {stats['segs_count']}个")
        print(f"  - 中枢: {stats['zhongshus_count']}个")
        
        # 基础断言
        self.assertGreater(stats['processed_klines_count'], 0)
        if stats['fenxings_count'] > 0:
            self.assertGreater(stats['fenxings_count'], 0)
    
    def test_standard_analysis(self):
        """测试标准分析功能（形态学+动力学）"""
        print("\\n🔍 标准分析测试（形态学+动力学）")
        
        # 获取测试数据
        data = self._get_daily_data("000002.SZ", 250)
        if not data:
            self.skipTest("无法获取测试数据")
        
        # 执行标准分析
        result = self.chan_engine.analyze(
            data=data,
            symbol="000002.SZ",
            time_level=TimeLevel.DAILY,
            analysis_level=AnalysisLevel.STANDARD
        )
        
        print(f"📊 标准分析结果:")
        stats = result.get_statistics()
        print(f"  - 形态学结构: {stats['segs_count']}线段, {stats['zhongshus_count']}中枢")
        print(f"  - 动力学分析: {stats['backchi_count']}背驰, {stats['buy_sell_points_count']}买卖点")
        print(f"  - 买点/卖点: {stats['buy_points_count']}/{stats['sell_points_count']}")
        
        # 显示买卖点详情
        if result.buy_sell_points:
            print(f"\\n📋 买卖点详情:")
            for i, point in enumerate(result.buy_sell_points[:3]):
                print(f"  {i+1}. {point.point_type} @{point.price:.2f} "
                      f"({point.timestamp.strftime('%Y-%m-%d')}) "
                      f"可靠度:{point.reliability:.3f}")
        
        # 获取交易信号
        signals = self.chan_engine.get_trading_signals(result)
        print(f"\\n🎯 交易信号摘要:")
        print(f"  - 总信号数: {signals['summary']['total_signals']}")
        print(f"  - 买入信号: {signals['summary']['buy_signals']}")
        print(f"  - 卖出信号: {signals['summary']['sell_signals']}")
        print(f"  - 高可信度信号: {signals['summary']['high_confidence_signals']}")
        
        # 验证结果
        self.assertEqual(result.analysis_level, AnalysisLevel.STANDARD)
        self.assertTrue(stats['backchi_count'] >= 0)
        self.assertTrue(stats['buy_sell_points_count'] >= 0)
    
    def test_complete_analysis(self):
        """测试完整分析功能"""
        print("\\n🔍 完整分析测试")
        
        # 获取测试数据
        data = self._get_daily_data("000001.SZ", 300)
        if not data:
            self.skipTest("无法获取测试数据")
        
        # 执行完整分析
        result = self.chan_engine.analyze(
            data=data,
            symbol="000001.SZ",
            time_level=TimeLevel.DAILY,
            analysis_level=AnalysisLevel.COMPLETE
        )
        
        print(f"📊 完整分析结果:")
        stats = result.get_statistics()
        
        # 显示综合评估
        print(f"\\n🎯 综合评估:")
        print(f"  - 趋势方向: {stats['trend_direction']}")
        print(f"  - 趋势强度: {stats['trend_strength']:.1%}")
        print(f"  - 风险等级: {stats['risk_level']:.1%}")
        print(f"  - 可信度: {stats['confidence_score']:.1%}")
        print(f"  - 交易建议: {stats['recommended_action']}")
        
        if result.entry_price:
            print(f"  - 建议入场价: {result.entry_price:.2f}")
        if result.stop_loss:
            print(f"  - 止损价: {result.stop_loss:.2f}")
        if result.take_profit:
            print(f"  - 止盈价: {result.take_profit:.2f}")
        
        # 显示分析摘要
        summary = self.chan_engine.get_analysis_summary(result)
        print(f"\\n📋 完整分析摘要:")
        print(summary)
        
        # 验证结果
        self.assertEqual(result.analysis_level, AnalysisLevel.COMPLETE)
        self.assertIsNotNone(result.trend_direction)
        self.assertGreaterEqual(result.trend_strength, 0.0)
        self.assertLessEqual(result.trend_strength, 1.0)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
    
    def test_multi_level_analysis(self):
        """测试多级别分析功能"""
        print("\\n🔍 多级别分析测试")
        
        # 准备多级别数据
        level_data = {}
        
        # 获取日线数据
        daily_data = self._get_daily_data("000001.SZ", 200)
        if daily_data:
            level_data[TimeLevel.DAILY] = daily_data
            print(f"✅ 日线数据: {len(daily_data)} 条")
        
        # 获取30分钟数据
        min30_data = self._get_minute_data("000001.SZ", "stock_kline_30min", 1000)
        if min30_data:
            level_data[TimeLevel.MIN_30] = min30_data
            print(f"✅ 30分钟数据: {len(min30_data)} 条")
        
        # 获取5分钟数据
        min5_data = self._get_minute_data("000001.SZ", "stock_kline_5min", 1500)
        if min5_data:
            level_data[TimeLevel.MIN_5] = min5_data
            print(f"✅ 5分钟数据: {len(min5_data)} 条")
        
        if len(level_data) < 2:
            self.skipTest("多级别数据不足")
        
        # 执行多级别分析
        results = self.chan_engine.analyze_multi_level(level_data, "000001.SZ")
        
        print(f"\\n📊 多级别分析结果:")
        
        for level, result in results.items():
            stats = result.get_statistics()
            print(f"\\n📈 {level.value} 级别:")
            print(f"  - 结构: {stats['segs_count']}线段, {stats['zhongshus_count']}中枢")
            print(f"  - 信号: {stats['buy_sell_points_count']}买卖点")
            print(f"  - 趋势: {stats['trend_direction']} (强度:{stats['trend_strength']:.1%})")
            print(f"  - 一致性得分: {result.level_consistency_score:.3f}")
            
            # 显示最新信号
            latest_signals = result.get_latest_signals(2)
            if latest_signals:
                print(f"  - 最新信号: {latest_signals[0].point_type} @{latest_signals[0].price:.2f}")
        
        # 验证结果
        self.assertGreaterEqual(len(results), 1)
        for level, result in results.items():
            self.assertIsInstance(result, ChanAnalysisResult)
            self.assertEqual(result.symbol, "000001.SZ")
            self.assertEqual(result.time_level, level)
    
    def test_quick_analyze_function(self):
        """测试快速分析便捷函数"""
        print("\\n🔍 快速分析函数测试")
        
        data = self._get_daily_data("000002.SZ", 150)
        if not data:
            self.skipTest("无法获取测试数据")
        
        # 使用便捷函数进行快速分析
        result = quick_analyze(data, "000002.SZ", TimeLevel.DAILY)
        
        self.assertIsInstance(result, ChanAnalysisResult)
        self.assertEqual(result.symbol, "000002.SZ")
        self.assertEqual(result.analysis_level, AnalysisLevel.STANDARD)
        
        stats = result.get_statistics()
        print(f"📊 快速分析结果: {stats['segs_count']}线段, {stats['buy_sell_points_count']}买卖点")
    
    def test_engine_configuration(self):
        """测试引擎配置功能"""
        print("\\n🔍 引擎配置测试")
        
        # 自定义配置
        chan_config = ChanConfig()
        dynamics_config = DynamicsConfig(
            macd_params=(8, 21, 5),  # 自定义MACD参数
            backchi_threshold=0.7,   # 更严格的背驰阈值
        )
        
        # 使用自定义配置创建引擎
        custom_engine = ChanEngine(chan_config, dynamics_config)
        
        self.assertEqual(custom_engine.dynamics_config.macd_params, (8, 21, 5))
        self.assertEqual(custom_engine.dynamics_config.backchi_threshold, 0.7)
        
        print(f"✅ 自定义MACD参数: {custom_engine.dynamics_config.macd_params}")
        print(f"✅ 自定义背驰阈值: {custom_engine.dynamics_config.backchi_threshold}")
    
    def test_analysis_cache(self):
        """测试分析缓存功能"""
        print("\\n🔍 分析缓存测试")
        
        data = self._get_daily_data("000001.SZ", 100)
        if not data:
            self.skipTest("无法获取测试数据")
        
        # 第一次分析
        result1 = self.chan_engine.analyze(data, "000001.SZ", TimeLevel.DAILY)
        
        # 检查缓存
        cache_key = f"000001.SZ_{TimeLevel.DAILY.value}_{AnalysisLevel.STANDARD.value}"
        self.assertIn(cache_key, self.chan_engine._analysis_cache)
        
        # 清空缓存
        self.chan_engine.clear_cache()
        self.assertEqual(len(self.chan_engine._analysis_cache), 0)
        
        print(f"✅ 缓存功能测试通过")
    
    def _get_daily_data(self, stock_code: str, limit: int) -> List[Dict]:
        """获取日线数据"""
        try:
            collection = self.db['stock_kline_daily']
            query = {'ts_code': stock_code}
            cursor = collection.find(query).sort('trade_date', 1).limit(limit)
            raw_data = list(cursor)
            
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
            
        except Exception as e:
            print(f"获取日线数据失败: {e}")
            return []
    
    def _get_minute_data(self, stock_code: str, collection_name: str, limit: int) -> List[Dict]:
        """获取分钟数据"""
        try:
            collection = self.db[collection_name]
            query = {'ts_code': stock_code}
            cursor = collection.find(query).sort('trade_time', -1).limit(limit)
            raw_data = list(cursor)
            raw_data.reverse()  # 转为升序
            
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
            
        except Exception as e:
            print(f"获取分钟数据失败: {e}")
            return []


if __name__ == '__main__':
    print("🔥 缠论分析引擎集成测试")
    print("=" * 60)
    print("📋 测试内容：")
    print("  - 基础分析功能测试")
    print("  - 标准分析功能测试（形态学+动力学）")
    print("  - 完整分析功能测试（含综合评估）")
    print("  - 多级别分析功能测试")
    print("  - 便捷函数测试")
    print("  - 引擎配置测试")
    print("  - 展示完整的缠论v2模块功能")
    print("=" * 60)
    
    unittest.main(verbosity=2)