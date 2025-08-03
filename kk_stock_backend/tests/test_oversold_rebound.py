#!/usr/bin/env python3
"""
测试和优化超跌反弹策略
"""

import sys
import asyncio
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

from cloud_db_handler import CloudDBHandler

async def test_oversold_rebound():
    """测试超跌反弹策略"""
    print("🔍 测试超跌反弹策略...")
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
        
        # 分析超跌反弹策略的核心逻辑
        print(f"\n📊 超跌反弹策略设计思路:")
        print("1. 超跌状态识别: RSI < 30（深度超跌）、连续下跌")
        print("2. 反弹信号确认: 成交量放大、止跌企稳")
        print("3. 估值安全边际: PE、PB相对合理")
        print("4. 技术位支撑: 重要均线、历史低点")
        print("5. 资金关注度: 主力资金开始关注")
        
        # 当前实现的筛选条件
        current_conditions = {
            "trade_date": latest_date,
            "rsi_qfq_12": {"$gte": 20, "$lte": 40},  # RSI 20-40 超跌区域
            "volume_ratio": {"$gte": 1.2},          # 量比 >= 1.2
            "pe": {"$gt": 0, "$lte": 30},            # PE <= 30
            "pb": {"$gt": 0, "$lte": 5}              # PB <= 5
        }
        
        collection = db_handler.get_collection('stock_factor_pro')
        
        # 检查当前条件的匹配数量
        current_count = collection.count_documents(current_conditions)
        print(f"\n🔍 当前筛选条件匹配: {current_count} 条")
        
        # 分析超跌反弹的关键指标
        print(f"\n📈 关键技术指标分析:")
        
        # 1. RSI分布分析
        rsi_ranges = [
            (10, 20, "极度超跌"),
            (20, 30, "深度超跌"),
            (30, 40, "超跌"),
            (40, 50, "偏弱")
        ]
        
        for rsi_min, rsi_max, desc in rsi_ranges:
            count = collection.count_documents({
                "trade_date": latest_date,
                "rsi_qfq_12": {"$gte": rsi_min, "$lte": rsi_max}
            })
            print(f"  RSI {rsi_min}-{rsi_max} ({desc}): {count} 只")
        
        # 2. 连续下跌股票分析
        print(f"\n📉 连续下跌分析:")
        
        # 获取近5个交易日的数据来计算连续下跌
        recent_dates = list(collection.distinct(
            'trade_date',
            {'trade_date': {'$lte': latest_date}}
        ))
        recent_dates.sort(reverse=True)
        recent_dates = recent_dates[:5]  # 最近5个交易日
        
        print(f"  分析交易日: {recent_dates}")
        
        # 优化后的超跌反弹策略条件
        print(f"\n🎯 优化后的超跌反弹策略:")
        
        optimized_conditions = {
            "trade_date": latest_date,
            "close": {"$gt": 0},
            "total_mv": {"$gte": 300000},  # 市值 >= 3亿
            "rsi_qfq_12": {"$gte": 15, "$lte": 35},  # RSI 15-35 超跌区域
            "volume_ratio": {"$gte": 1.5},           # 量比 >= 1.5 (放大)
            "pe": {"$gt": 0, "$lte": 40},            # PE <= 40 (放宽)
            "pb": {"$gt": 0, "$lte": 6},             # PB <= 6 (放宽)
            "turnover_rate": {"$gte": 2, "$lte": 20}  # 换手率 2-20%
        }
        
        # 添加额外的超跌条件
        expr_conditions = [
            {"$lt": ["$close", "$ma_qfq_20"]},     # 低于20日均线
            {"$lt": ["$close", "$ma_qfq_60"]},     # 低于60日均线
        ]
        
        optimized_conditions["$expr"] = {"$and": expr_conditions}
        
        # 检查优化后的条件匹配
        optimized_count = collection.count_documents(optimized_conditions)
        print(f"  优化后筛选条件匹配: {optimized_count} 条")
        
        if optimized_count > 0:
            # 执行完整的聚合查询
            pipeline = [
                {"$match": optimized_conditions},
                
                {"$lookup": {
                    "from": "infrastructure_stock_basic",
                    "localField": "ts_code",
                    "foreignField": "ts_code",
                    "as": "stock_info"
                }},
                {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
                
                {"$match": {
                    "stock_info.name": {"$not": {"$regex": "ST|\\\\*ST", "$options": "i"}}
                }},
                
                # 计算超跌反弹评分
                {"$addFields": {
                    "score": {
                        "$add": [
                            # 基础分：符合超跌条件得20分
                            20,
                            
                            # RSI得分：越低得分越高，15-35区间得0-20分
                            {"$multiply": [{"$subtract": [35, "$rsi_qfq_12"]}, 1]},
                            
                            # 量比得分：量比越高得分越高，最高25分
                            {"$min": [25, {"$multiply": [{"$subtract": ["$volume_ratio", 1]}, 5]}]},
                            
                            # 估值得分：PE越低得分越高，最高15分
                            {"$min": [15, {"$multiply": [{"$divide": [20, "$pe"]}, 3]}]},
                            
                            # 反弹信号得分：当日上涨得10分，横盘得5分
                            {"$cond": {
                                "if": {"$gt": ["$pct_chg", 2]},
                                "then": 15,
                                "else": {"$cond": {
                                    "if": {"$gt": ["$pct_chg", 0]},
                                    "then": 10,
                                    "else": {"$cond": {
                                        "if": {"$gt": ["$pct_chg", -2]},
                                        "then": 5,
                                        "else": 0
                                    }}
                                }}
                            }},
                            
                            # 换手率得分：适中的换手率得分，最高10分
                            {"$cond": {
                                "if": {"$and": [{"$gte": ["$turnover_rate", 3]}, {"$lte": ["$turnover_rate", 8]}]},
                                "then": 10,
                                "else": {"$cond": {
                                    "if": {"$and": [{"$gte": ["$turnover_rate", 2]}, {"$lte": ["$turnover_rate", 15]}]},
                                    "then": 5,
                                    "else": 0
                                }}
                            }}
                        ]
                    }
                }},
                
                {"$project": {
                    "ts_code": 1,
                    "name": "$stock_info.name",
                    "industry": "$stock_info.industry",
                    "close": 1,
                    "pe": 1,
                    "pb": 1,
                    "pct_chg": 1,
                    "total_mv": 1,
                    "rsi_qfq_12": 1,
                    "volume_ratio": 1,
                    "turnover_rate": 1,
                    "ma_qfq_20": 1,
                    "ma_qfq_60": 1,
                    "score": 1,
                    "rebound_signal": {"$cond": {"if": {"$gte": ["$score", 60]}, "then": True, "else": False}}
                }},
                
                {"$sort": {"score": -1}},
                {"$limit": 15}
            ]
            
            results = list(collection.aggregate(pipeline))
            
            print(f"📊 优化后的超跌反弹策略结果: {len(results)} 只股票")
            print("-" * 60)
            
            if results:
                for i, stock in enumerate(results, 1):
                    score = stock.get('score', 0) or 0
                    print(f"{i:2d}. {stock['ts_code']} - {stock.get('name', 'N/A')}")
                    print(f"    行业: {stock.get('industry', 'N/A')}")
                    print(f"    股价: {stock.get('close', 0):.2f}元")
                    print(f"    涨跌幅: {stock.get('pct_chg', 0):.2f}%")
                    print(f"    RSI: {stock.get('rsi_qfq_12', 0):.2f}")
                    print(f"    PE: {stock.get('pe', 0):.2f}")
                    print(f"    量比: {stock.get('volume_ratio', 0):.2f}")
                    print(f"    换手率: {stock.get('turnover_rate', 0):.2f}%")
                    print(f"    超跌反弹评分: {score:.2f}分")
                    print(f"    反弹信号: {'✅ 强反弹' if stock.get('rebound_signal') else '⚠️ 观察'}") 
                    print("-" * 40)
            else:
                print("❌ 没有找到符合条件的股票")
        else:
            print("❌ 优化后的筛选条件没有匹配的股票")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_oversold_rebound())