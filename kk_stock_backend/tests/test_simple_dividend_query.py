#!/usr/bin/env python3
"""
测试简单的高股息查询逻辑
"""

import sys
import asyncio
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

from cloud_db_handler import CloudDBHandler

async def test_simple_dividend_query():
    """测试简单的高股息查询逻辑"""
    print("🧪 测试简单的高股息查询逻辑...")
    print("=" * 60)
    
    try:
        db_handler = CloudDBHandler()
        
        # 获取最新交易日期
        latest_trade_data = list(db_handler.get_collection('stock_factor_pro').find({}).sort('trade_date', -1).limit(1))
        if not latest_trade_data:
            print("❌ 找不到交易数据")
            return
            
        latest_date = latest_trade_data[0]['trade_date']
        print(f"📅 最新交易日期: {latest_date}")
        
        # 极简查询，只看基础条件
        pipeline = [
            {"$match": {
                "trade_date": latest_date,
                "close": {"$gt": 0},
                "total_mv": {"$gte": 1000000}
            }},
            
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            {"$lookup": {
                "from": "stock_fina_indicator",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}}},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 1}
                ],
                "as": "fina_data"
            }},
            {"$unwind": {"path": "$fina_data", "preserveNullAndEmptyArrays": True}},
            
            {"$addFields": {
                "dividend_yield": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": [{"$ifNull": ["$fina_data.eps", 0]}, 0]},
                            {"$gt": [{"$ifNull": ["$close", 0]}, 0]}
                        ]},
                        "then": {"$multiply": [{"$divide": [{"$multiply": [{"$ifNull": ["$fina_data.eps", 0]}, 0.4]}, {"$ifNull": ["$close", 1]}]}, 100]},
                        "else": 0
                    }
                }
            }},
            
            {"$match": {
                "$and": [
                    {"dividend_yield": {"$gte": 2.0}},
                    {"fina_data.eps": {"$gt": 0}},
                    {"stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}}
                ]
            }},
            
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": "$stock_info.industry",
                "close": 1,
                "total_mv": 1,
                "dividend_yield": 1,
                "eps": "$fina_data.eps",
                "roe": "$fina_data.roe"
            }},
            
            {"$sort": {"dividend_yield": -1}},
            {"$limit": 10}
        ]
        
        print("🔍 执行极简聚合查询...")
        results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
        
        print(f"📊 查询结果: 找到 {len(results)} 只符合条件的股票")
        print("-" * 60)
        
        if results:
            print("符合条件的股票:")
            for i, stock in enumerate(results, 1):
                print(f"{i:2d}. {stock['ts_code']} - {stock.get('name', 'N/A')}")
                print(f"    行业: {stock.get('industry', 'N/A')}")
                print(f"    股价: {stock.get('close', 0):.2f}元")
                print(f"    总市值: {stock.get('total_mv', 0):.2f}万元")
                print(f"    股息率: {stock.get('dividend_yield', 0):.2f}%")
                print(f"    ROE: {stock.get('roe', 0):.2f}%")
                print(f"    EPS: {stock.get('eps', 0):.2f}元")
                print("-" * 40)
        else:
            print("❌ 没有找到符合条件的股票")
            
            # 分步调试
            print("\n🔍 分步调试...")
            
            # 第一步：基础数据
            base_count = db_handler.get_collection('stock_factor_pro').count_documents({
                "trade_date": latest_date,
                "close": {"$gt": 0},
                "total_mv": {"$gte": 1000000}
            })
            print(f"基础交易数据: {base_count} 条")
            
            # 第二步：有财务数据
            pipeline_step2 = [
                {"$match": {"trade_date": latest_date, "close": {"$gt": 0}, "total_mv": {"$gte": 1000000}}},
                {"$lookup": {"from": "stock_fina_indicator", "let": {"ts_code": "$ts_code"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}}}, {"$sort": {"end_date": -1}}, {"$limit": 1}], "as": "fina_data"}},
                {"$unwind": {"path": "$fina_data", "preserveNullAndEmptyArrays": True}},
                {"$match": {"fina_data.eps": {"$gt": 0}}},
                {"$count": "count"}
            ]
            step2_result = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline_step2))
            step2_count = step2_result[0]['count'] if step2_result else 0
            print(f"有财务数据且EPS>0: {step2_count} 条")
            
            # 第三步：计算股息率
            pipeline_step3 = [
                {"$match": {"trade_date": latest_date, "close": {"$gt": 0}, "total_mv": {"$gte": 1000000}}},
                {"$lookup": {"from": "stock_fina_indicator", "let": {"ts_code": "$ts_code"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}}}, {"$sort": {"end_date": -1}}, {"$limit": 1}], "as": "fina_data"}},
                {"$unwind": {"path": "$fina_data", "preserveNullAndEmptyArrays": True}},
                {"$addFields": {"dividend_yield": {"$cond": {"if": {"$and": [{"$gt": [{"$ifNull": ["$fina_data.eps", 0]}, 0]}, {"$gt": [{"$ifNull": ["$close", 0]}, 0]}]}, "then": {"$multiply": [{"$divide": [{"$multiply": [{"$ifNull": ["$fina_data.eps", 0]}, 0.4]}, {"$ifNull": ["$close", 1]}]}, 100]}, "else": 0}}}},
                {"$match": {"dividend_yield": {"$gte": 2.0}, "fina_data.eps": {"$gt": 0}}},
                {"$count": "count"}
            ]
            step3_result = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline_step3))
            step3_count = step3_result[0]['count'] if step3_result else 0
            print(f"股息率>=2%: {step3_count} 条")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_dividend_query())