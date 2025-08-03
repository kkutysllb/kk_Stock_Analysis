#!/usr/bin/env python3
"""
测试完整的成长股筛选管道
"""

import sys
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')
from cloud_db_handler import CloudDBHandler
from datetime import datetime, timedelta

db_handler = CloudDBHandler()

async def _get_latest_trade_date():
    """获取最新交易日期"""
    try:
        latest_record = db_handler.get_collection('stock_factor_pro').find().sort([("trade_date", -1)]).limit(1)
        latest_date = None
        for record in latest_record:
            latest_date = record.get('trade_date')
            break
        
        if not latest_date:
            latest_date = datetime.now().strftime('%Y%m%d')
        
        print(f"📅 最新交易日期: {latest_date}")
        return latest_date
    except Exception as e:
        print(f"❌ 获取最新交易日期失败: {str(e)}")
        return datetime.now().strftime('%Y%m%d')

def test_growth_stock_pipeline():
    """测试完整的成长股筛选管道"""
    print("🔍 测试完整成长股筛选管道...")
    
    # 构建与实际代码相同的管道
    pipeline = []
    
    # 使用同步方式获取最新日期
    latest_date = "20250704"  # 手动设置
    print(f"📅 使用交易日期: {latest_date}")
    
    pipeline.extend([
        # 第一步：联接财务指标数据（最近8个季度）
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
        
        # 第二步：联接基本信息
        {"$lookup": {
            "from": "infrastructure_stock_basic",
            "localField": "ts_code",
            "foreignField": "ts_code",
            "as": "stock_info"
        }},
        {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
        
        # 第三步：计算关键财务指标的多年均值和趋势
        {"$addFields": {
            # 计算EPS连续三年增长率
            "avg_eps_growth": {
                "$avg": {
                    "$map": {
                        "input": {"$slice": ["$fina_indicators.basic_eps_yoy", 0, 12]},
                        "as": "eps_yoy",
                        "in": {"$ifNull": ["$$eps_yoy", 0]}
                    }
                }
            },
            # 计算营收连续三年增长率
            "avg_revenue_growth": {
                "$avg": {
                    "$map": {
                        "input": {"$slice": ["$fina_indicators.or_yoy", 0, 12]},
                        "as": "or_yoy", 
                        "in": {"$ifNull": ["$$or_yoy", 0]}
                    }
                }
            },
            # 计算ROIC均值
            "avg_roic": {
                "$avg": {
                    "$map": {
                        "input": {"$slice": ["$fina_indicators.roic", 0, 8]},
                        "as": "roic",
                        "in": {"$ifNull": ["$$roic", 0]}
                    }
                }
            },
            # 添加股票基本信息
            "name": "$stock_info.name",
            "industry": "$stock_info.industry"
        }},
        
        # 第四步：仅基础匹配，暂时不应用严格筛选
        {"$match": {
            "trade_date": latest_date,
            "fina_indicators.0": {"$exists": True}  # 确保有财务数据
        }},
        
        # 第五步：限制结果数量以便调试
        {"$limit": 5}
    ])
    
    try:
        print(f"🔄 执行聚合管道...")
        results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
        
        print(f"✅ 找到 {len(results)} 只股票")
        
        for i, result in enumerate(results):
            print(f"\n📊 股票 {i+1}: {result.get('name')} ({result.get('ts_code')})")
            print(f"   行业: {result.get('industry')}")
            print(f"   财务数据数量: {len(result.get('fina_indicators', []))}")
            print(f"   📈 计算结果:")
            print(f"      EPS增长率: {result.get('avg_eps_growth')}")
            print(f"      营收增长率: {result.get('avg_revenue_growth')}")
            print(f"      ROIC: {result.get('avg_roic')}")
            
            # 检查原始数据
            fina_indicators = result.get('fina_indicators', [])
            if fina_indicators:
                eps_values = [f.get('basic_eps_yoy') for f in fina_indicators[:3]]
                print(f"      原始EPS数据 (前3个): {eps_values}")
                
    except Exception as e:
        print(f"❌ 管道执行失败: {str(e)}")
        import traceback
        traceback.print_exc()

def test_specific_stock():
    """测试特定股票"""
    print(f"\n🔍 测试特定股票 832982.BJ...")
    
    pipeline = [
        {"$match": {"ts_code": "832982.BJ", "trade_date": "20250704"}},
        {"$lookup": {
            "from": "stock_fina_indicator",
            "let": {"ts_code": "$ts_code"},
            "pipeline": [
                {"$match": {
                    "$expr": {"$eq": ["$ts_code", "$$ts_code"]},
                    "end_date": {"$gte": "20210331"}
                }},
                {"$sort": {"end_date": -1}},
                {"$limit": 12}
            ],
            "as": "fina_indicators"
        }},
        {"$addFields": {
            "fina_count": {"$size": "$fina_indicators"},
            "avg_eps_growth": {
                "$avg": {
                    "$map": {
                        "input": {"$slice": ["$fina_indicators.basic_eps_yoy", 0, 12]},
                        "as": "eps_yoy",
                        "in": {"$ifNull": ["$$eps_yoy", 0]}
                    }
                }
            }
        }}
    ]
    
    try:
        results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
        if results:
            result = results[0]
            print(f"✅ 找到股票: {result.get('ts_code')}")
            print(f"📊 财务数据数量: {result.get('fina_count')}")
            print(f"📈 计算的EPS增长率: {result.get('avg_eps_growth')}")
        else:
            print("❌ 未找到该股票")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def main():
    print("🚀 开始测试完整成长股筛选管道")
    print("=" * 60)
    
    try:
        test_growth_stock_pipeline()
        test_specific_stock()
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 测试完成")

if __name__ == "__main__":
    main()