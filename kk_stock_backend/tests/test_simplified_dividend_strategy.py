#!/usr/bin/env python3
"""
测试简化版高股息策略查询逻辑
"""

import sys
import asyncio
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

from cloud_db_handler import CloudDBHandler

async def test_simplified_dividend_strategy():
    """测试简化版高股息策略查询逻辑"""
    print("🧪 测试简化版高股息策略查询逻辑...")
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
        
        # 构建简化的聚合管道
        pipeline = [
            # 基础筛选
            {"$match": {
                "trade_date": latest_date,
                "close": {"$gt": 0},
                "total_mv": {"$gte": 1000000}  # 总市值 > 10亿
            }},
            
            # 联接股票基本信息
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            # 联接最新财务指标数据
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
            
            # 联接资产负债表数据
            {"$lookup": {
                "from": "stock_balance_sheet",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}}},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 1}
                ],
                "as": "balance_data"
            }},
            {"$unwind": {"path": "$balance_data", "preserveNullAndEmptyArrays": True}},
            
            # 计算关键指标
            {"$addFields": {
                # 计算股息率（使用EPS估算，假设40%分红率）
                "dividend_yield": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": [{"$ifNull": ["$fina_data.eps", 0]}, 0]},
                            {"$gt": [{"$ifNull": ["$close", 0]}, 0]}
                        ]},
                        "then": {"$multiply": [{"$divide": [{"$multiply": [{"$ifNull": ["$fina_data.eps", 0]}, 0.4]}, {"$ifNull": ["$close", 1]}]}, 100]},
                        "else": 0
                    }
                },
                
                # 计算净现金水平
                "net_cash": {
                    "$cond": {
                        "if": {"$ne": ["$balance_data", None]},
                        "then": {"$subtract": [{"$ifNull": ["$balance_data.cash_reser_cb", 0]}, {"$ifNull": ["$balance_data.cb_borr", 0]}]},
                        "else": 0
                    }
                }
            }},
            
            # 应用基础筛选条件
            {"$match": {
                "$and": [
                    {"dividend_yield": {"$gte": 3.0}},  # 股息率 >= 3%
                    {"net_cash": {"$gt": 0}},  # 净现金水平 > 0
                    {"fina_data.roe": {"$gte": 0}},  # ROE >= 0
                    {"fina_data.eps": {"$gt": 0}},  # EPS > 0
                    {"stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}}  # 排除ST股票
                ]
            }},
            
            # 输出字段
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": "$stock_info.industry",
                "close": 1,
                "total_mv": 1,
                "dividend_yield": 1,
                "net_cash": 1,
                "roe": "$fina_data.roe",
                "eps": "$fina_data.eps",
                "debt_to_assets": "$fina_data.debt_to_assets"
            }},
            
            {"$sort": {"dividend_yield": -1}},
            {"$limit": 10}
        ]
        
        print("🔍 执行简化聚合查询...")
        results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
        
        print(f"📊 查询结果: 找到 {len(results)} 只符合条件的股票")
        print("-" * 60)
        
        if results:
            print("符合基础条件的股票:")
            for i, stock in enumerate(results, 1):
                print(f"{i:2d}. {stock['ts_code']} - {stock.get('name', 'N/A')}")
                print(f"    行业: {stock.get('industry', 'N/A')}")
                print(f"    股价: {stock.get('close', 0):.2f}元")
                print(f"    总市值: {stock.get('total_mv', 0):.2f}万元")
                print(f"    股息率: {stock.get('dividend_yield', 0):.2f}%")
                print(f"    净现金: {stock.get('net_cash', 0):.2f}万元")
                print(f"    ROE: {stock.get('roe', 0):.2f}%")
                print(f"    EPS: {stock.get('eps', 0):.2f}元")
                print(f"    资产负债率: {stock.get('debt_to_assets', 0):.2f}%")
                print("-" * 40)
        else:
            print("❌ 没有找到符合条件的股票")
        
        # 单独测试每个条件
        print("\n🔍 单独测试各个筛选条件...")
        
        # 测试股息率条件
        test_pipeline = [
            {"$match": {"trade_date": latest_date, "close": {"$gt": 0}, "total_mv": {"$gte": 1000000}}},
            {"$lookup": {"from": "infrastructure_stock_basic", "localField": "ts_code", "foreignField": "ts_code", "as": "stock_info"}},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": "stock_fina_indicator", "let": {"ts_code": "$ts_code"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}}}, {"$sort": {"end_date": -1}}, {"$limit": 1}], "as": "fina_data"}},
            {"$unwind": {"path": "$fina_data", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {"dividend_yield": {"$cond": {"if": {"$and": [{"$gt": [{"$ifNull": ["$fina_data.eps", 0]}, 0]}, {"$gt": [{"$ifNull": ["$close", 0]}, 0]}]}, "then": {"$multiply": [{"$divide": [{"$multiply": [{"$ifNull": ["$fina_data.eps", 0]}, 0.4]}, {"$ifNull": ["$close", 1]}]}, 100]}, "else": 0}}}},
            {"$match": {"dividend_yield": {"$gte": 3.0}, "fina_data.eps": {"$gt": 0}, "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}}},
            {"$count": "count"}
        ]
        
        dividend_count = list(db_handler.get_collection('stock_factor_pro').aggregate(test_pipeline))
        print(f"股息率 >= 3% 的股票数量: {dividend_count[0]['count'] if dividend_count else 0}")
        
        # 测试净现金条件
        test_pipeline_2 = [
            {"$match": {"trade_date": latest_date, "close": {"$gt": 0}, "total_mv": {"$gte": 1000000}}},
            {"$lookup": {"from": "infrastructure_stock_basic", "localField": "ts_code", "foreignField": "ts_code", "as": "stock_info"}},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": "stock_fina_indicator", "let": {"ts_code": "$ts_code"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}}}, {"$sort": {"end_date": -1}}, {"$limit": 1}], "as": "fina_data"}},
            {"$unwind": {"path": "$fina_data", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": "stock_balance_sheet", "let": {"ts_code": "$ts_code"}, "pipeline": [{"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}}}, {"$sort": {"end_date": -1}}, {"$limit": 1}], "as": "balance_data"}},
            {"$unwind": {"path": "$balance_data", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {"net_cash": {"$cond": {"if": {"$ne": ["$balance_data", None]}, "then": {"$subtract": [{"$ifNull": ["$balance_data.cash_reser_cb", 0]}, {"$ifNull": ["$balance_data.cb_borr", 0]}]}, "else": 0}}}},
            {"$match": {"net_cash": {"$gt": 0}, "fina_data.eps": {"$gt": 0}, "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}}},
            {"$count": "count"}
        ]
        
        cash_count = list(db_handler.get_collection('stock_factor_pro').aggregate(test_pipeline_2))
        print(f"净现金 > 0 的股票数量: {cash_count[0]['count'] if cash_count else 0}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simplified_dividend_strategy())