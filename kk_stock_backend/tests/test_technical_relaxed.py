#!/usr/bin/env python3
"""
测试放宽条件后的技术突破策略
"""

import sys
import asyncio
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

from cloud_db_handler import CloudDBHandler

async def test_technical_relaxed():
    """测试放宽条件后的技术突破策略"""
    print("🧪 测试放宽条件后的技术突破策略...")
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
        
        # 放宽条件的筛选
        match_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": 0},
            "total_mv": {"$gte": 500000},  # 5亿市值以上
            "rsi_qfq_12": {"$gte": 45, "$lte": 85},  # RSI 45-85
            "volume_ratio": {"$gte": 1.2},  # 量比 >= 1.2
            "turnover_rate": {"$gte": 1, "$lte": 15},  # 换手率 1-15%
            "$expr": {"$gt": ["$close", "$ma_qfq_20"]}  # 站上20日均线
        }
        
        collection = db_handler.get_collection('stock_factor_pro')
        
        # 检查基础筛选结果
        basic_count = collection.count_documents(match_conditions)
        print(f"🔍 基础筛选条件匹配: {basic_count} 条")
        
        if basic_count > 0:
            # 执行完整的聚合查询
            pipeline = [
                {"$match": match_conditions},
                
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
                
                # 计算评分（新的简化算法）
                {"$addFields": {
                    "score": {
                        "$add": [
                            # 基础分：站上20日线得20分
                            20,
                            
                            # RSI得分：45-85区间，得0-20分
                            {"$multiply": [{"$max": [0, {"$subtract": ["$rsi_qfq_12", 45]}]}, 0.5]},
                            
                            # MACD得分：MACD>0得15分
                            {"$cond": {"if": {"$gt": ["$macd_qfq", 0]}, "then": 15, "else": 0}},
                            
                            # 成交量得分：量比每超过1得10分，最高25分
                            {"$min": [25, {"$multiply": [{"$max": [0, {"$subtract": ["$volume_ratio", 1]}]}, 10]}]},
                            
                            # 涨跌幅得分：涨幅每1%得2分，最高20分
                            {"$min": [20, {"$max": [0, {"$multiply": ["$pct_chg", 2]}]}]}
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
                    "breakthrough_signal": {"$cond": {"if": {"$gte": ["$score", 50]}, "then": True, "else": False}}
                }},
                
                {"$sort": {"score": -1}},
                {"$limit": 10}
            ]
            
            results = list(collection.aggregate(pipeline))
            
            print(f"📊 最终筛选结果: {len(results)} 只股票")
            print("-" * 60)
            
            if results:
                for i, stock in enumerate(results, 1):
                    score = stock.get('score', 0) or 0
                    print(f"{i:2d}. {stock['ts_code']} - {stock.get('name', 'N/A')}")
                    print(f"    行业: {stock.get('industry', 'N/A')}")
                    print(f"    股价: {stock.get('close', 0):.2f}元")
                    print(f"    涨跌幅: {stock.get('pct_chg', 0):.2f}%")
                    print(f"    RSI: {stock.get('rsi_qfq_12', 0):.2f}")
                    print(f"    MACD: {stock.get('macd_qfq', 0):.4f}")
                    print(f"    量比: {stock.get('volume_ratio', 0):.2f}")
                    print(f"    技术评分: {score:.2f}分")
                    print(f"    突破信号: {'✅ 强突破' if stock.get('breakthrough_signal') else '⚠️ 一般'}")
                    print("-" * 40)
            else:
                print("❌ 没有找到符合条件的股票")
        else:
            print("❌ 基础筛选条件没有匹配的股票")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_technical_relaxed())