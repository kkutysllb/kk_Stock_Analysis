#!/usr/bin/env python3
"""
测试技术突破策略
"""

import sys
import asyncio
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

from cloud_db_handler import CloudDBHandler

async def test_technical_breakthrough_strategy():
    """测试技术突破策略"""
    print("🧪 测试技术突破策略...")
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
        
        # 测试技术突破策略的筛选逻辑
        pipeline = [
            {"$match": {
                "trade_date": latest_date,
                "close": {"$gt": 0},
                "total_mv": {"$gte": 500000},
                "rsi_qfq_12": {"$gte": 50, "$lte": 80},
                "volume_ratio": {"$gte": 1.5},
                "turnover_rate": {"$gte": 1, "$lte": 15},
                "$expr": {"$gt": ["$close", "$ma_qfq_20"]}
            }},
            
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            {"$match": {
                "stock_info.name": {"$not": {"$regex": "ST|\\*ST", "$options": "i"}}
            }},
            
            # 计算技术突破评分
            {"$addFields": {
                "bollinger_score": {
                    "$cond": {
                        "if": {"$gt": ["$close", "$boll_upper_qfq"]},
                        "then": 25,
                        "else": {
                            "$cond": {
                                "if": {"$gt": ["$close", "$boll_mid_qfq"]},
                                "then": 15,
                                "else": 5
                            }
                        }
                    }
                },
                "ma_alignment_score": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": ["$ma_qfq_5", "$ma_qfq_10"]},
                            {"$gt": ["$ma_qfq_10", "$ma_qfq_20"]},
                            {"$gt": ["$ma_qfq_20", "$ma_qfq_60"]}
                        ]},
                        "then": 20,
                        "else": {
                            "$cond": {
                                "if": {"$and": [
                                    {"$gt": ["$ma_qfq_5", "$ma_qfq_10"]},
                                    {"$gt": ["$ma_qfq_10", "$ma_qfq_20"]}
                                ]},
                                "then": 12,
                                "else": 5
                            }
                        }
                    }
                },
                "macd_score": {
                    "$add": [
                        {"$cond": {"if": {"$gt": ["$macd_dif_qfq", "$macd_dea_qfq"]}, "then": 10, "else": 0}},
                        {"$cond": {"if": {"$gt": ["$macd_qfq", 0]}, "then": 8, "else": 0}},
                        {"$cond": {"if": {"$gt": ["$macd_dif_qfq", 0]}, "then": 5, "else": 0}}
                    ]
                },
                "rsi_score": {
                    "$cond": {
                        "if": {"$and": [{"$gte": ["$rsi_qfq_12", 50]}, {"$lte": ["$rsi_qfq_12", 70]}]},
                        "then": {"$multiply": [{"$subtract": ["$rsi_qfq_12", 50]}, 0.5]},
                        "else": 3
                    }
                },
                "volume_score": {
                    "$min": [15, {"$multiply": [{"$subtract": ["$volume_ratio", 1]}, 6]}]
                },
                "momentum_score": {
                    "$cond": {
                        "if": {"$gt": ["$pct_chg", 5]},
                        "then": 10,
                        "else": {
                            "$cond": {
                                "if": {"$gt": ["$pct_chg", 2]},
                                "then": 6,
                                "else": {"$cond": {"if": {"$gte": ["$pct_chg", 0]}, "then": 3, "else": 0}}
                            }
                        }
                    }
                },
                "score": {
                    "$add": [
                        "$bollinger_score",
                        "$ma_alignment_score", 
                        "$macd_score",
                        "$rsi_score",
                        "$volume_score",
                        "$momentum_score"
                    ]
                }
            }},
            
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": "$stock_info.industry",
                "close": 1,
                "pct_chg": 1,
                "rsi_qfq_12": 1,
                "macd_qfq": 1,
                "volume_ratio": 1,
                "score": 1,
                "breakthrough_signal": {"$cond": {"if": {"$gte": ["$score", 70]}, "then": True, "else": False}}
            }},
            
            {"$sort": {"score": -1}},
            {"$limit": 10}
        ]
        
        print("🔍 执行技术突破策略查询...")
        results = list(db_handler.get_collection('stock_factor_pro').aggregate(pipeline))
        
        print(f"📊 查询结果: 找到 {len(results)} 只符合条件的股票")
        print("-" * 60)
        
        if results:
            print("技术突破策略筛选结果:")
            for i, stock in enumerate(results, 1):
                print(f"{i:2d}. {stock['ts_code']} - {stock.get('name', 'N/A')}")
                print(f"    行业: {stock.get('industry', 'N/A')}")
                print(f"    股价: {stock.get('close', 0):.2f}元")
                print(f"    涨跌幅: {stock.get('pct_chg', 0):.2f}%")
                print(f"    RSI: {stock.get('rsi_qfq_12', 0):.2f}")
                print(f"    MACD: {stock.get('macd_qfq', 0):.4f}")
                print(f"    量比: {stock.get('volume_ratio', 0):.2f}")
                score = stock.get('score', 0) or 0
                print(f"    技术评分: {score:.2f}分")
                print(f"    突破信号: {'✅ 强突破' if stock.get('breakthrough_signal') else '⚠️ 一般'}")
                print("-" * 40)
        else:
            print("❌ 没有找到符合条件的股票")
            
            # 分步调试
            print("\n🔍 分步调试...")
            
            base_count = db_handler.get_collection('stock_factor_pro').count_documents({
                "trade_date": latest_date,
                "close": {"$gt": 0},
                "total_mv": {"$gte": 500000}
            })
            print(f"基础数据: {base_count} 条")
            
            rsi_count = db_handler.get_collection('stock_factor_pro').count_documents({
                "trade_date": latest_date,
                "rsi_qfq_12": {"$gte": 50, "$lte": 80}
            })
            print(f"RSI 50-80区间: {rsi_count} 条")
            
            volume_count = db_handler.get_collection('stock_factor_pro').count_documents({
                "trade_date": latest_date,
                "volume_ratio": {"$gte": 1.5}
            })
            print(f"量比>=1.5: {volume_count} 条")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_technical_breakthrough_strategy())