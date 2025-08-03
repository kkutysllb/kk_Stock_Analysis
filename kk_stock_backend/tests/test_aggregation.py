#!/usr/bin/env python3
"""
测试MongoDB聚合管道
"""

import sys
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')
from cloud_db_handler import CloudDBHandler

db_handler = CloudDBHandler()

def test_simple_aggregation():
    """测试简单的聚合管道"""
    print("🔍 测试简单聚合管道...")
    
    ts_code = "832982.BJ"  # 锦波生物
    
    pipeline = [
        {"$match": {"ts_code": ts_code}},
        {"$lookup": {
            "from": "stock_fina_indicator",
            "let": {"ts_code": "$ts_code"},
            "pipeline": [
                {"$match": {
                    "$expr": {"$eq": ["$ts_code", "$$ts_code"]},
                    "end_date": {"$gte": "20210331"}  # 最近3年数据
                }},
                {"$sort": {"end_date": -1}},
                {"$limit": 12}  # 最近12个季度
            ],
            "as": "fina_indicators"
        }},
        {"$addFields": {
            "fina_count": {"$size": "$fina_indicators"},
            "latest_eps_yoy": {"$arrayElemAt": ["$fina_indicators.basic_eps_yoy", 0]},
            "all_eps_yoy": "$fina_indicators.basic_eps_yoy",
            "avg_eps_growth": {
                "$avg": {
                    "$map": {
                        "input": {"$slice": ["$fina_indicators.basic_eps_yoy", 0, 12]},
                        "as": "eps_yoy",
                        "in": {"$ifNull": ["$$eps_yoy", 0]}
                    }
                }
            }
        }},
        {"$limit": 1}
    ]
    
    try:
        results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
        
        if results:
            result = results[0]
            print(f"✅ 找到股票: {result.get('ts_code')}")
            print(f"📊 财务指标数量: {result.get('fina_count')}")
            print(f"📈 最新EPS增长率: {result.get('latest_eps_yoy')}")
            print(f"📈 平均EPS增长率: {result.get('avg_eps_growth')}")
            
            all_eps_yoy = result.get('all_eps_yoy', [])
            print(f"📈 所有EPS增长率: {all_eps_yoy[:5]}...")  # 只显示前5个
            
            fina_indicators = result.get('fina_indicators', [])
            if fina_indicators:
                print(f"\n📊 财务指标样本 (前2条):")
                for i, fina in enumerate(fina_indicators[:2]):
                    print(f"  {i+1}. 期间: {fina.get('end_date')}")
                    print(f"     EPS增长率: {fina.get('basic_eps_yoy')}")
                    print(f"     营收增长率: {fina.get('or_yoy')}")
                    print(f"     ROIC: {fina.get('roic')}")
        else:
            print("❌ 未找到结果")
            
    except Exception as e:
        print(f"❌ 聚合失败: {str(e)}")

def test_field_calculation():
    """测试字段计算"""
    print(f"\n🔍 测试字段计算...")
    
    # 直接查询财务指标数据
    ts_code = "832982.BJ"
    fina_data = list(db_handler.get_collection('stock_fina_indicator').find({
        "ts_code": ts_code,
        "end_date": {"$gte": "20210331"}
    }).sort("end_date", -1).limit(12))
    
    print(f"📊 找到 {len(fina_data)} 条财务数据")
    
    if fina_data:
        # 手动计算平均值
        eps_yoy_values = [f.get('basic_eps_yoy') for f in fina_data if f.get('basic_eps_yoy') is not None]
        or_yoy_values = [f.get('or_yoy') for f in fina_data if f.get('or_yoy') is not None]
        roic_values = [f.get('roic') for f in fina_data if f.get('roic') is not None]
        
        print(f"✅ EPS增长率数据: {len(eps_yoy_values)} 个有效值")
        print(f"   值: {eps_yoy_values[:5]}...")
        print(f"   平均值: {sum(eps_yoy_values)/len(eps_yoy_values) if eps_yoy_values else 'N/A'}")
        
        print(f"✅ 营收增长率数据: {len(or_yoy_values)} 个有效值")
        print(f"   值: {or_yoy_values[:5]}...")
        print(f"   平均值: {sum(or_yoy_values)/len(or_yoy_values) if or_yoy_values else 'N/A'}")
        
        print(f"✅ ROIC数据: {len(roic_values)} 个有效值")
        print(f"   值: {roic_values[:5]}...")
        print(f"   平均值: {sum(roic_values)/len(roic_values) if roic_values else 'N/A'}")

def main():
    print("🚀 开始测试MongoDB聚合管道")
    print("=" * 60)
    
    try:
        test_simple_aggregation()
        test_field_calculation()
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 测试完成")

if __name__ == "__main__":
    main()