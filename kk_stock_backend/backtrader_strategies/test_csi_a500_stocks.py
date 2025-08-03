#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中证A500成分股获取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.cloud_db_handler import CloudDBHandler

def test_csi_a500_stocks():
    """测试获取中证A500成分股"""
    print("🔍 测试中证A500成分股获取...")
    
    db_handler = CloudDBHandler()
    
    try:
        # 1. 检查index_weight集合
        index_collection = db_handler.get_collection('index_weight')
        
        # 查询所有可用指数
        available_indexes = index_collection.distinct('index_code')
        print(f"📋 数据库中可用指数数量: {len(available_indexes)}")
        
        # 检查是否有中证A500
        if '000510.CSI' in available_indexes:
            print("✅ 找到中证A500指数代码: 000510.CSI")
            
            # 先查看数据结构
            sample_doc = index_collection.find_one({'index_code': '000510.CSI'})
            print(f"📋 数据样例: {sample_doc}")
            
            # 获取成分股 - 尝试使用最新日期
            query = {'index_code': '000510.CSI'}
            cursor = index_collection.find(query).sort('trade_date', -1).limit(1000)
            
            csi_a500_stocks = []
            latest_date = None
            
            for doc in cursor:
                current_date = doc.get('trade_date')
                if latest_date is None:
                    latest_date = current_date
                elif current_date != latest_date:
                    break  # 只取最新日期的数据
                    
                if 'con_code' in doc and doc['con_code']:
                    csi_a500_stocks.append(doc['con_code'])
            
            # 去重
            csi_a500_stocks = list(set(csi_a500_stocks))
            
            print(f"📅 最新日期: {latest_date}")
            print(f"📊 中证A500成分股数量: {len(csi_a500_stocks)}")
            if csi_a500_stocks:
                print(f"📝 前10只股票: {csi_a500_stocks[:10]}")
                return csi_a500_stocks
            else:
                print("❌ 未获取到成分股数据")
        else:
            print("❌ 未找到中证A500指数数据")
            print(f"🔍 前20个可用指数: {available_indexes[:20]}")
            
            # 检查类似的指数
            similar_indexes = [idx for idx in available_indexes if '000510' in idx or 'A500' in idx]
            if similar_indexes:
                print(f"🔍 相似指数: {similar_indexes}")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    return []

if __name__ == "__main__":
    stocks = test_csi_a500_stocks()
    print(f"\n🎯 测试完成，获取到 {len(stocks)} 只中证A500成分股")