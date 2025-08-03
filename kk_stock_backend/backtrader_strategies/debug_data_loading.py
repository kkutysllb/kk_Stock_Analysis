#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试数据加载问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.cloud_db_handler import CloudDBHandler
from config import DatabaseConfig
import pandas as pd

def test_database_connection():
    """测试数据库连接和基本查询"""
    try:
        print("🔍 测试数据库连接...")
        db_handler = CloudDBHandler()
        db_config = DatabaseConfig()
        
        # 获取集合
        collection = db_handler.get_collection(db_config.factor_collection)
        print(f"✅ 成功获取集合: {db_config.factor_collection}")
        
        # 检查集合中的文档数量
        total_count = collection.count_documents({})
        print(f"📊 集合总文档数: {total_count}")
        
        # 查询一些股票代码
        stock_codes = collection.distinct('ts_code')
        print(f"📈 可用股票数量: {len(stock_codes)}")
        print(f"📈 前10只股票: {stock_codes[:10]}")
        
        # 测试单只股票数据查询
        test_stock = stock_codes[0] if stock_codes else None
        if test_stock:
            print(f"\n🔍 测试股票 {test_stock} 的数据...")
            
            # 查询最近的数据
            query = {'ts_code': test_stock}
            cursor = collection.find(query).sort('trade_date', -1).limit(5)
            recent_data = list(cursor)
            
            print(f"📅 最近5天数据量: {len(recent_data)}")
            if recent_data:
                latest = recent_data[0]
                print(f"📅 最新日期: {latest.get('trade_date', 'N/A')}")
                print(f"💰 收盘价: {latest.get('close', 'N/A')}")
                print(f"📊 成交量: {latest.get('vol', 'N/A')}")
                
                # 检查技术指标字段
                indicators = ['macd_dif_bfq', 'macd_dea_bfq', 'kdj_k_bfq', 'kdj_d_bfq', 'ma_bfq_5', 'ma_bfq_20']
                print(f"\n🔍 技术指标检查:")
                for indicator in indicators:
                    value = latest.get(indicator, 'N/A')
                    print(f"  {indicator}: {value}")
            
            # 测试指定日期范围查询
            print(f"\n🔍 测试2024年数据查询...")
            query_2024 = {
                'ts_code': test_stock,
                'trade_date': {
                    '$gte': '20240101',
                    '$lte': '20241231'
                }
            }
            cursor_2024 = collection.find(query_2024).sort('trade_date', 1)
            data_2024 = list(cursor_2024)
            print(f"📅 2024年数据量: {len(data_2024)}")
            
            if len(data_2024) > 0:
                print(f"📅 2024年第一天: {data_2024[0].get('trade_date', 'N/A')}")
                print(f"📅 2024年最后一天: {data_2024[-1].get('trade_date', 'N/A')}")
            
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def test_enhanced_data_fetch():
    """测试增强数据获取函数"""
    try:
        print("\n🔍 测试EnhancedDataFeed数据获取...")
        
        from data_feed.enhanced_datafeed import _fetch_enhanced_data
        
        # 获取一些测试股票
        db_handler = CloudDBHandler()
        db_config = DatabaseConfig()
        collection = db_handler.get_collection(db_config.factor_collection)
        stock_codes = collection.distinct('ts_code')
        
        if not stock_codes:
            print("❌ 没有可用的股票代码")
            return False
        
        test_stock = stock_codes[0]
        print(f"🔍 测试股票: {test_stock}")
        
        # 测试数据获取
        df = _fetch_enhanced_data(
            stock_code=test_stock,
            start_date='2024-01-01',
            end_date='2024-12-31',
            include_indicators=True
        )
        
        print(f"📊 获取数据行数: {len(df)}")
        if not df.empty:
            print(f"📊 数据列数: {len(df.columns)}")
            print(f"📊 数据列名: {list(df.columns)[:10]}")
            print(f"📅 数据日期范围: {df.index.min()} 到 {df.index.max()}")
            
            # 检查基础字段
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                if field in df.columns:
                    print(f"✅ {field}: {df[field].iloc[-1]}")
                else:
                    print(f"❌ 缺少字段: {field}")
            
            return True
        else:
            print("❌ 获取的数据为空")
            return False
            
    except Exception as e:
        print(f"❌ 增强数据获取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始数据加载调试...")
    
    # 测试数据库连接
    db_ok = test_database_connection()
    
    if db_ok:
        # 测试数据获取
        fetch_ok = test_enhanced_data_fetch()
        
        if fetch_ok:
            print("\n✅ 数据加载测试通过")
        else:
            print("\n❌ 数据获取存在问题")
    else:
        print("\n❌ 数据库连接存在问题")