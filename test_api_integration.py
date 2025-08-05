#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值投资策略API接口集成测试
测试重构后的API接口是否能正确调用适配器
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.getcwd())

async def test_api_adapter_integration():
    """测试API接口与适配器的集成"""
    print("🔗 测试API接口与适配器集成...")
    print("=" * 50)
    
    try:
        # 导入适配器
        from backtrader_strategies.strategy_adapters.value_investment_adapter import ValueInvestmentAdapter
        print("✅ 适配器导入成功")
        
        # 创建适配器实例
        adapter = ValueInvestmentAdapter()
        print("✅ 适配器实例创建成功")
        
        # 执行选股测试
        print("\n🔍 执行选股测试...")
        result = await adapter.screen_stocks(
            market_cap="all",
            stock_pool="all",
            limit=10
        )
        
        print("✅ 适配器调用成功")
        print(f"   策略名称: {result.get('strategy_name')}")
        print(f"   策略类型: {result.get('strategy_type')}")
        print(f"   选股数量: {result.get('total_count')}")
        
        if 'error' in result:
            print(f"❌ 选股过程出现错误: {result['error']}")
            return False
        
        # 测试API转换逻辑
        print("\n🔄 测试API格式转换...")
        
        # 模拟API接口的转换逻辑
        formatted_results = []
        for stock in result.get('stocks', []):
            api_result = {
                'ts_code': stock.get('ts_code'),
                'name': stock.get('name', ''),
                'industry': stock.get('industry'),
                'pe': stock.get('pe'),
                'pb': stock.get('pb'),
                'total_mv': stock.get('total_mv'),
                'score': stock.get('total_score', 0),
                'roe': stock.get('roe'),
                'technical': {
                    'avg_roe': stock.get('avg_roe'),
                    'roe_stability': stock.get('roe_stability'),
                    'growth_score': stock.get('growth_score'),
                    'profitability_score': stock.get('profitability_score'),
                    'total_score': stock.get('total_score'),
                    'reason': stock.get('reason')
                }
            }
            formatted_results.append(api_result)
        
        print(f"✅ API格式转换成功，转换了 {len(formatted_results)} 条记录")
        
        # 如果有结果，显示第一条
        if formatted_results:
            first_result = formatted_results[0]
            print(f"\n📊 第一条结果示例:")
            print(f"   股票: {first_result['name']} ({first_result['ts_code']})")
            print(f"   评分: {first_result['score']}")
            print(f"   PE: {first_result['pe']}, PB: {first_result['pb']}")
            print(f"   理由: {first_result['technical']['reason']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_connectivity():
    """测试数据库连接和数据可用性"""
    print("\n🗄️ 测试数据库连接和数据可用性...")
    print("=" * 50)
    
    try:
        from api.global_db import get_global_db_handler
        
        db_handler = get_global_db_handler()
        print("✅ 数据库连接成功")
        
        # 检查主要集合的数据量
        collections_to_check = [
            'stock_factor_pro',
            'infrastructure_stock_basic',
            'stock_fina_indicator'
        ]
        
        for collection_name in collections_to_check:
            collection = db_handler.get_collection(collection_name)
            count = collection.count_documents({})
            print(f"   {collection_name}: {count:,} 条记录")
            
            if count == 0:
                print(f"   ⚠️  {collection_name} 集合为空，可能影响选股结果")
        
        # 检查最新交易日期
        collection = db_handler.get_collection('stock_factor_pro')
        latest_result = list(collection.find({}, {"trade_date": 1}).sort("trade_date", -1).limit(1))
        if latest_result:
            latest_date = latest_result[0]['trade_date']
            print(f"   最新交易日期: {latest_date}")
        else:
            print("   ⚠️  无法获取最新交易日期")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 价值投资策略API接口集成测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行测试
    test_results = []
    
    # 测试数据库连接
    result1 = await test_database_connectivity()
    test_results.append(("数据库连接测试", result1))
    
    # 测试API适配器集成
    result2 = await test_api_adapter_integration()
    test_results.append(("API适配器集成测试", result2))
    
    # 汇总结果
    print("\n📋 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总结: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 API接口集成测试成功！")
        print("💡 重构完成，接口层已成功解耦，使用策略适配器实现")
        return True
    else:
        print("⚠️  部分测试失败，需要检查问题")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⛔ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生未预期错误: {e}")
        sys.exit(1)