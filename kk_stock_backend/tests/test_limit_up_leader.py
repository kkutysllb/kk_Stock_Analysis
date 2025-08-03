#!/usr/bin/env python3
"""
测试和设计连板龙头策略
"""

import sys
import asyncio
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

from cloud_db_handler import CloudDBHandler

async def test_limit_up_leader():
    """测试连板龙头策略"""
    print("🚀 测试连板龙头策略...")
    print("=" * 60)
    
    try:
        db_handler = CloudDBHandler()
        
        # 获取最新交易日期
        latest_trade_data = list(db_handler.get_collection('limit_list_daily').find({}).sort('trade_date', -1).limit(1))
        if not latest_trade_data:
            print("❌ 找不到涨跌停数据")
            return
            
        latest_date = latest_trade_data[0]['trade_date']
        print(f"📅 最新交易日期: {latest_date}")
        
        print(f"\n📊 连板龙头策略设计思路:")
        print("1. 连板确认: 连板次数>=2，且当日涨停")
        print("2. 龙头识别: 在连板天梯中排名靠前")
        print("3. 板块热度: 所属板块涨停股数量多，资金净流入大")
        print("4. 封板强度: 开板次数少，成交额大，换手率适中")
        print("5. 风险控制: 避免过高连板数，关注机构参与")
        
        # 1. 分析当日涨停连板情况
        limit_up_conditions = {
            "trade_date": latest_date,
            "limit": "U",  # 涨停
            "limit_times": {"$gte": 2}  # 连板次数>=2
        }
        
        limit_up_stocks = list(db_handler.get_collection('limit_list_daily').find(limit_up_conditions))
        print(f"\n🔍 当日涨停连板股票: {len(limit_up_stocks)} 只")
        
        if limit_up_stocks:
            # 按连板次数分组统计
            limit_stats = {}
            for stock in limit_up_stocks:
                times = stock.get('limit_times', 0)
                if times not in limit_stats:
                    limit_stats[times] = 0
                limit_stats[times] += 1
            
            print("连板次数分布:")
            for times in sorted(limit_stats.keys()):
                print(f"  {times}连板: {limit_stats[times]} 只")
        
        # 2. 分析板块热度
        sector_conditions = {
            "trade_date": latest_date,
            "up_nums": {"$gte": 3}  # 板块涨停数>=3
        }
        
        hot_sectors = list(db_handler.get_collection('limit_cpt_list').find(sector_conditions).sort('up_nums', -1).limit(10))
        print(f"\n🔥 热门板块 (涨停股>=3):")
        for i, sector in enumerate(hot_sectors, 1):
            print(f"{i:2d}. {sector.get('concept', 'N/A')} - {sector.get('up_nums', 0)}只涨停")
        
        # 3. 分析资金流向热点
        money_flow_conditions = {
            "trade_date": latest_date,
            "net_amount": {"$gt": 0}  # 净流入>0
        }
        
        money_flow_hot = list(db_handler.get_collection('money_flow_industry').find(money_flow_conditions).sort('net_amount', -1).limit(10))
        print(f"\n💰 资金流入热点行业:")
        for i, industry in enumerate(money_flow_hot, 1):
            net_amount = industry.get('net_amount', 0) / 10000  # 转换为万元
            print(f"{i:2d}. {industry.get('industry', 'N/A')} - {net_amount:.2f}万元")
        
        # 4. 设计连板龙头策略的聚合查询
        print(f"\n🎯 设计连板龙头策略聚合查询...")
        
        # 主要基于涨跌停数据，关联其他数据源
        pipeline = [
            # 第一步：筛选涨停连板股票
            {"$match": {
                "trade_date": latest_date,
                "limit": "U",                    # 涨停
                "limit_times": {"$gte": 2, "$lte": 10},  # 2-10连板
                "open_times": {"$lte": 3}        # 开板次数<=3次
            }},
            
            # 第二步：关联股票基本信息
            {"$lookup": {
                "from": "infrastructure_stock_basic",
                "localField": "ts_code",
                "foreignField": "ts_code",
                "as": "stock_info"
            }},
            {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
            
            # 第三步：关联技术因子数据（获取市值、成交额等）
            {"$lookup": {
                "from": "stock_factor_pro",
                "let": {"stock_code": "$ts_code", "date": "$trade_date"},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$ts_code", "$$stock_code"]},
                                {"$eq": ["$trade_date", "$$date"]}
                            ]
                        }
                    }},
                    {"$project": {
                        "total_mv": 1,
                        "turnover_rate": 1,
                        "amount": 1,
                        "pe": 1,
                        "pb": 1
                    }}
                ],
                "as": "tech_data"
            }},
            {"$unwind": {"path": "$tech_data", "preserveNullAndEmptyArrays": True}},
            
            # 第四步：关联板块涨停数据
            {"$lookup": {
                "from": "limit_cpt_list",
                "let": {"date": "$trade_date", "industry": "$industry"},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$trade_date", "$$date"]},
                                {"$eq": ["$concept", "$$industry"]}
                            ]
                        }
                    }},
                    {"$project": {
                        "up_nums": 1,
                        "cons_nums": 1
                    }}
                ],
                "as": "sector_data"
            }},
            {"$unwind": {"path": "$sector_data", "preserveNullAndEmptyArrays": True}},
            
            # 第五步：计算连板龙头评分
            {"$addFields": {
                "score": {
                    "$add": [
                        # 连板次数得分：2-6连板得分递增，超过6连板得分递减
                        {"$cond": {
                            "if": {"$lte": ["$limit_times", 6]},
                            "then": {"$multiply": ["$limit_times", 8]},  # 2连16分，6连48分
                            "else": {"$subtract": [60, {"$multiply": [{"$subtract": ["$limit_times", 6]}, 5]}]}  # 7连55分，递减
                        }},
                        
                        # 封板强度得分：开板次数越少得分越高，最高20分
                        {"$subtract": [20, {"$multiply": [{"$ifNull": ["$open_times", 0]}, 5]}]},
                        
                        # 板块热度得分：板块涨停股数越多得分越高，最高20分
                        {"$min": [20, {"$multiply": [{"$ifNull": ["$sector_data.up_nums", 0]}, 2]}]},
                        
                        # 市值得分：中等市值得分较高，最高15分
                        {"$cond": {
                            "if": {"$and": [
                                {"$gte": [{"$ifNull": ["$tech_data.total_mv", 0]}, 500000]},  # >=50亿
                                {"$lte": [{"$ifNull": ["$tech_data.total_mv", 0]}, 2000000]}   # <=200亿
                            ]},
                            "then": 15,
                            "else": {"$cond": {
                                "if": {"$gte": [{"$ifNull": ["$tech_data.total_mv", 0]}, 200000]},  # >=20亿
                                "then": 10,
                                "else": 5
                            }}
                        }},
                        
                        # 换手率得分：适中换手率得分高，最高10分
                        {"$cond": {
                            "if": {"$and": [
                                {"$gte": [{"$ifNull": ["$tech_data.turnover_rate", 0]}, 8]},    # >=8%
                                {"$lte": [{"$ifNull": ["$tech_data.turnover_rate", 0]}, 20]}    # <=20%
                            ]},
                            "then": 10,
                            "else": 5
                        }}
                    ]
                }
            }},
            
            # 第六步：输出关键字段
            {"$project": {
                "ts_code": 1,
                "name": "$stock_info.name",
                "industry": 1,
                "limit_times": 1,
                "open_times": 1,
                "first_time": 1,
                "last_time": 1,
                "close": 1,
                "pct_chg": 1,
                "amount": "$tech_data.amount",
                "total_mv": "$tech_data.total_mv",
                "turnover_rate": "$tech_data.turnover_rate",
                "pe": "$tech_data.pe",
                "pb": "$tech_data.pb",
                "sector_up_nums": "$sector_data.up_nums",
                "score": 1,
                "leader_signal": {
                    "$cond": {
                        "if": {"$gte": ["$score", 70]},
                        "then": True,
                        "else": False
                    }
                }
            }},
            
            {"$sort": {"score": -1}},
            {"$limit": 15}
        ]
        
        results = list(db_handler.get_collection('limit_list_daily').aggregate(pipeline))
        
        print(f"📊 连板龙头策略筛选结果: {len(results)} 只")
        print("-" * 60)
        
        if results:
            for i, stock in enumerate(results, 1):
                score = stock.get('score', 0) or 0
                print(f"{i:2d}. {stock['ts_code']} - {stock.get('name', 'N/A')}")
                print(f"    行业: {stock.get('industry', 'N/A')}")
                print(f"    连板次数: {stock.get('limit_times', 0)}连板")
                print(f"    开板次数: {stock.get('open_times', 0)}次")
                print(f"    涨跌幅: {stock.get('pct_chg', 0):.2f}%")
                print(f"    成交额: {(stock.get('amount', 0) or 0) / 10000:.2f}万元")
                print(f"    总市值: {(stock.get('total_mv', 0) or 0) / 10000:.2f}万元")
                print(f"    换手率: {stock.get('turnover_rate', 0):.2f}%")
                print(f"    板块涨停数: {stock.get('sector_up_nums', 0)}只")
                print(f"    龙头评分: {score:.2f}分")
                print(f"    龙头信号: {'🔥 强龙头' if stock.get('leader_signal') else '⚠️ 观察'}")
                print("-" * 40)
        else:
            print("❌ 没有找到符合条件的连板龙头股票")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_limit_up_leader())