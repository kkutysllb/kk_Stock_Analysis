#!/usr/bin/env python3
"""
测试高股息策略评分计算
"""

import sys
import asyncio
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

from cloud_db_handler import CloudDBHandler

async def test_dividend_scoring():
    """测试高股息策略评分计算"""
    print("🧪 测试高股息策略评分计算...")
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
        
        # 测试评分计算逻辑
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
                },
                "payout_ratio_3y": 40.0,  # 模拟值
                "dividend_fundraising_ratio": 50.0,  # 模拟值
                "net_cash": 5000000,  # 模拟值（万元）
                "roe": {"$ifNull": ["$fina_data.roe", 0]},
                "roa": {"$ifNull": ["$fina_data.roa", 0]},
                "fcf_revenue_ratio": 10.0,  # 模拟值
                "net_profit_margin": 8.0,  # 模拟值
                "debt_ratio": 45.0  # 模拟值
            }},
            
            {"$match": {
                "$and": [
                    {"dividend_yield": {"$gte": 2.0}},
                    {"fina_data.eps": {"$gt": 0}},
                    {"stock_info.name": {"$not": {"$regex": "ST|\\\\*ST", "$options": "i"}}}
                ]
            }},
            
            # 新的评分计算
            {"$addFields": {
                "score": {
                    "$min": [
                        100,  # 最高100分
                        {
                            "$add": [
                                {"$multiply": ["$dividend_yield", 8]},  # 股息率权重：8分/% (最高24分)
                                {"$multiply": [{"$min": ["$payout_ratio_3y", 50]}, 0.3]},  # 股息支付率权重：最高15分
                                {"$multiply": [{"$min": ["$dividend_fundraising_ratio", 100]}, 0.2]},  # 分红募资比权重：最高20分
                                {
                                    "$cond": {
                                        "if": {"$gt": ["$net_cash", 0]},
                                        "then": {"$min": [{"$multiply": [{"$divide": ["$net_cash", 100000]}, 2]}, 10]},  # 净现金正数加分，最高10分
                                        "else": 0
                                    }
                                },
                                {"$multiply": [{"$min": ["$roe", 20]}, 0.5]},  # ROE权重：最高10分
                                {"$multiply": [{"$min": ["$roa", 10]}, 0.5]},  # ROA权重：最高5分
                                {
                                    "$cond": {
                                        "if": {"$gt": ["$fcf_revenue_ratio", 0]},
                                        "then": {"$min": [{"$multiply": ["$fcf_revenue_ratio", 0.2]}, 5]},  # 现金流正数加分，最高5分
                                        "else": 0
                                    }
                                },
                                {"$multiply": [{"$min": ["$net_profit_margin", 20]}, 0.25]},  # 净利润率权重：最高5分
                                {
                                    "$cond": {
                                        "if": {"$lt": ["$debt_ratio", 60]},
                                        "then": {"$multiply": [{"$subtract": [60, "$debt_ratio"]}, 0.1]},  # 低负债率加分，最高6分
                                        "else": 0
                                    }
                                }
                            ]
                        }
                    ]
                }
            }},
            
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "close": 1,
                "dividend_yield": 1,
                "payout_ratio_3y": 1,
                "dividend_fundraising_ratio": 1,
                "net_cash": 1,
                "roe": 1,
                "roa": 1,
                "score": 1
            }},
            
            {"$sort": {"score": -1}},
            {"$limit": 5}
        ]
        
        print("🔍 执行评分测试查询...")
        results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
        
        print(f"📊 查询结果: 找到 {len(results)} 只符合条件的股票")
        print("-" * 60)
        
        if results:
            print("测试评分结果:")
            for i, stock in enumerate(results, 1):
                print(f"{i:2d}. {stock['ts_code']} - {stock.get('name', 'N/A')}")
                print(f"    股价: {stock.get('close', 0):.2f}元")
                print(f"    股息率: {stock.get('dividend_yield', 0):.2f}%")
                print(f"    ROE: {stock.get('roe', 0):.2f}%")
                print(f"    综合得分: {stock.get('score', 0):.2f}分")
                print("-" * 40)
        else:
            print("❌ 没有找到符合条件的股票")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dividend_scoring())