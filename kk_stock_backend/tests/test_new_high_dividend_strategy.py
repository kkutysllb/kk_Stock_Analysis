#!/usr/bin/env python3
"""
测试修改后的高股息策略查询逻辑
"""

import sys
import asyncio
sys.path.append('/Users/libing/kk_Projects/kk_StockQuant_Analysis/api')

from cloud_db_handler import CloudDBHandler
from datetime import datetime

async def test_new_high_dividend_strategy():
    """测试新的高股息策略查询逻辑"""
    print("🧪 测试新的高股息策略查询逻辑...")
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
        
        # 构建测试聚合管道
        pipeline = [
            # 基础筛选
            {"$match": {
                "trade_date": latest_date,
                "close": {"$gt": 0},
                "total_mv": {"$gt": 0}
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
            
            # 联接近3年财务指标数据
            {"$lookup": {
                "from": "stock_fina_indicator",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}}},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 3}
                ],
                "as": "fina_data_3y"
            }},
            
            # 联接近3年现金流数据
            {"$lookup": {
                "from": "stock_cash_flow",
                "let": {"ts_code": "$ts_code"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}}},
                    {"$sort": {"end_date": -1}},
                    {"$limit": 3}
                ],
                "as": "cashflow_data_3y"
            }},
            
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
                # 计算股息率（近一年）
                "dividend_yield": {
                    "$cond": {
                        "if": {"$and": [
                            {"$gt": [{"$ifNull": ["$fina_data.dv_ttm", 0]}, 0]},
                            {"$gt": [{"$ifNull": ["$close", 0]}, 0]}
                        ]},
                        "then": {"$multiply": [{"$divide": [{"$ifNull": ["$fina_data.dv_ttm", 0]}, {"$ifNull": ["$close", 1]}]}, 100]},
                        "else": 0
                    }
                },
                
                # 计算股息支付率（近3年平均）
                "payout_ratio_3y": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$fina_data_3y"}, 0]},
                        "then": {
                            "$avg": {
                                "$map": {
                                    "input": "$fina_data_3y",
                                    "as": "fina",
                                    "in": {
                                        "$cond": {
                                            "if": {"$and": [
                                                {"$gt": [{"$ifNull": ["$$fina.eps", 0]}, 0]},
                                                {"$gt": [{"$ifNull": ["$$fina.dv_ttm", 0]}, 0]}
                                            ]},
                                            "then": {"$multiply": [{"$divide": [{"$ifNull": ["$$fina.dv_ttm", 0]}, {"$ifNull": ["$$fina.eps", 1]}]}, 100]},
                                            "else": 0
                                        }
                                    }
                                }
                            }
                        },
                        "else": 0
                    }
                },
                
                # 计算分红募资比
                "dividend_fundraising_ratio": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$cashflow_data_3y"}, 0]},
                        "then": {
                            "$let": {
                                "vars": {
                                    "total_dividends": {
                                        "$sum": {
                                            "$map": {
                                                "input": "$cashflow_data_3y",
                                                "as": "cf",
                                                "in": {"$abs": {"$ifNull": ["$$cf.c_pay_div_profit", 0]}}
                                            }
                                        }
                                    },
                                    "total_fundraising": {
                                        "$sum": {
                                            "$map": {
                                                "input": "$cashflow_data_3y",
                                                "as": "cf",
                                                "in": {"$add": [{"$ifNull": ["$$cf.c_recv_cap_contrib", 0]}, {"$ifNull": ["$$cf.c_incr_borrow", 0]}]}
                                            }
                                        }
                                    }
                                },
                                "in": {
                                    "$cond": {
                                        "if": {"$gt": ["$$total_fundraising", 0]},
                                        "then": {"$multiply": [{"$divide": ["$$total_dividends", "$$total_fundraising"]}, 100]},
                                        "else": 0
                                    }
                                }
                            }
                        },
                        "else": 0
                    }
                },
                
                # 计算净现金水平
                "net_cash": {
                    "$cond": {
                        "if": {"$ne": ["$balance_data", None]},
                        "then": {
                            "$subtract": [
                                {"$ifNull": ["$balance_data.money_cap", 0]},
                                {"$add": [{"$ifNull": ["$balance_data.st_borr", 0]}, {"$ifNull": ["$balance_data.lt_borr", 0]}]}
                            ]
                        },
                        "else": 0
                    }
                }
            }},
            
            # 应用筛选条件
            {"$match": {
                "$and": [
                    {"dividend_yield": {"$gte": 3.0}},  # 股息率 >= 3%
                    {"payout_ratio_3y": {"$gte": 40.0}},  # 股息支付率 >= 40%
                    {"dividend_fundraising_ratio": {"$gte": 100.0}},  # 分红募资比 >= 100%
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
                "payout_ratio_3y": 1,
                "dividend_fundraising_ratio": 1,
                "net_cash": 1,
                "roe": "$fina_data.roe",
                "eps": "$fina_data.eps"
            }},
            
            {"$sort": {"dividend_yield": -1}},
            {"$limit": 10}
        ]
        
        print("🔍 执行聚合查询...")
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
                print(f"    股息支付率(3年): {stock.get('payout_ratio_3y', 0):.2f}%")
                print(f"    分红募资比: {stock.get('dividend_fundraising_ratio', 0):.2f}%")
                print(f"    净现金: {stock.get('net_cash', 0):.2f}万元")
                print(f"    ROE: {stock.get('roe', 0):.2f}%")
                print(f"    EPS: {stock.get('eps', 0):.2f}元")
                print("-" * 40)
        else:
            print("❌ 没有找到符合条件的股票")
            print("可能的原因：")
            print("1. 筛选条件过于严格")
            print("2. 数据库中缺少相关财务数据")
            print("3. 字段名称不匹配")
            
            # 检查数据可用性
            print("\n🔍 检查数据可用性...")
            fina_count = db_handler.get_collection('stock_fina_indicator').count_documents({})
            cashflow_count = db_handler.get_collection('stock_cash_flow').count_documents({})
            balance_count = db_handler.get_collection('stock_balance_sheet').count_documents({})
            
            print(f"财务指标数据: {fina_count} 条")
            print(f"现金流数据: {cashflow_count} 条")
            print(f"资产负债表数据: {balance_count} 条")
            
            # 检查字段存在性
            print("\n🔍 检查关键字段...")
            sample_fina = db_handler.get_collection('stock_fina_indicator').find_one({})
            if sample_fina:
                has_dv_ttm = 'dv_ttm' in sample_fina
                has_eps = 'eps' in sample_fina
                has_roe = 'roe' in sample_fina
                print(f"dv_ttm字段存在: {has_dv_ttm}")
                print(f"eps字段存在: {has_eps}")
                print(f"roe字段存在: {has_roe}")
                
                if has_dv_ttm:
                    dv_count = db_handler.get_collection('stock_fina_indicator').count_documents({'dv_ttm': {'$gt': 0}})
                    print(f"有股息数据的记录: {dv_count} 条")
            
            sample_cashflow = db_handler.get_collection('stock_cash_flow').find_one({})
            if sample_cashflow:
                has_div_pay = 'c_pay_div_profit' in sample_cashflow
                has_cap_contrib = 'c_recv_cap_contrib' in sample_cashflow
                print(f"c_pay_div_profit字段存在: {has_div_pay}")
                print(f"c_recv_cap_contrib字段存在: {has_cap_contrib}")
            
            sample_balance = db_handler.get_collection('stock_balance_sheet').find_one({})
            if sample_balance:
                has_money_cap = 'money_cap' in sample_balance
                has_st_borr = 'st_borr' in sample_balance
                has_lt_borr = 'lt_borr' in sample_balance
                print(f"money_cap字段存在: {has_money_cap}")
                print(f"st_borr字段存在: {has_st_borr}")
                print(f"lt_borr字段存在: {has_lt_borr}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_new_high_dividend_strategy())