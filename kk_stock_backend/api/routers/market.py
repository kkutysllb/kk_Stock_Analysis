from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到sys.path以便导入数据库管理器
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from api.cache_middleware import cache_endpoint
from api.global_db import db_handler

router = APIRouter()


# 主要指数配置
MAJOR_INDICES = {
    '000001.SH': {'name': '上证指数', 'market': '上证主板'},
    '399001.SZ': {'name': '深证成指', 'market': '深证主板'}, 
    '399006.SZ': {'name': '创业板指', 'market': '创业板'},
    '000688.SH': {'name': '科创50', 'market': '科创板'},
    '899050.BJ': {'name': '北证50', 'market': '北交所'},
    '000016.SH': {'name': '上证50', 'market': '上证主板'},
    '000300.SH': {'name': '沪深300', 'market': '沪深300'},
    '000905.SH': {'name': '中证500', 'market': '中证500'},
    '000852.SH': {'name': '中证1000', 'market': '中证1000'},
    '399303.SZ': {'name': '国证2000', 'market': '深证主板'},
    # 中小板块指数
    '000510.CSI': {'name': '中证A500', 'market': '中证指数'},
    '000142.SH': {'name': '上证380', 'market': '上证主板'},
    '399010.SZ': {'name': '深证700', 'market': '深证主板'},
    '399020.SZ': {'name': '创业小盘', 'market': '深证主板'},
    '932000.CSI': {'name': '中证2000', 'market': '中证指数'}
}

@cache_endpoint(data_type="market_quote", ttl=300)
@router.get("/quote")
def get_market_quote():
    """基础行情接口"""
    return {"msg": "行情接口示例"}

@router.get("/indices")
@cache_endpoint(data_type='market_indices', ttl=600)  # 缓存10分钟
async def get_market_indices(
    period: str = Query(default="daily", description="数据周期: daily, weekly, monthly"),
    limit: int = Query(default=30, description="获取数据条数")
):
    """
    获取主要指数数据
    
    Args:
        period: 数据周期 (daily/weekly/monthly)
        limit: 获取最近多少条数据
    
    Returns:
        指数数据列表
    """
    try:
        # 根据周期选择集合
        collection_map = {
            'daily': 'index_daily',
            'weekly': 'index_weekly', 
            'monthly': 'index_monthly'
        }
        
        collection_name = collection_map.get(period, 'index_daily')
        collection = db_handler.get_collection(collection_name)
        
        # 获取所有主要指数的最新数据
        indices_data = []
        for ts_code, info in MAJOR_INDICES.items():
            # 获取该指数的最新数据
            cursor = collection.find(
                {'ts_code': ts_code},
                {'_id': 0}
            ).sort('trade_date', -1).limit(limit)
            
            data_list = list(cursor)
            if data_list:
                latest_data = data_list[0]
                indices_data.append({
                    'ts_code': ts_code,
                    'name': info['name'],
                    'market': info['market'],
                    'latest_data': latest_data,
                    'history_data': data_list[:limit] if len(data_list) > 1 else []
                })
        
        return {
            "success": True,
            "data": {
                "period": period,
                "indices": indices_data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指数数据失败: {str(e)}")

@router.get("/dragon-tiger")
@cache_endpoint(data_type='dragon_tiger', ttl=300)  # 缓存5分钟
async def get_dragon_tiger_list(
    trade_date: Optional[str] = Query(default=None, description="交易日期，格式YYYYMMDD"),
    limit: int = Query(default=20, description="获取记录数量")
):
    """
    获取龙虎榜数据
    
    Args:
        trade_date: 交易日期，如果不指定则获取最新交易日
        limit: 获取记录数量
    
    Returns:
        龙虎榜数据
    """
    try:
        collection = db_handler.get_collection('top_list')
        
        # 如果没有指定日期，获取最新交易日期
        if not trade_date:
            latest_record = collection.find_one(
                sort=[('trade_date', -1)],
                projection={'trade_date': 1, '_id': 0}
            )
            if latest_record:
                trade_date = latest_record['trade_date']
            else:
                trade_date = datetime.now().strftime('%Y%m%d')
        
        # 获取指定日期的龙虎榜数据
        cursor = collection.find(
            {'trade_date': trade_date},
            {'_id': 0}
        ).sort([('net_amount', -1)]).limit(limit)
        
        dragon_tiger_list = list(cursor)
        
        # 统计数据
        total_count = collection.count_documents({'trade_date': trade_date})
        
        # 计算总买入和卖出金额
        pipeline = [
            {'$match': {'trade_date': trade_date}},
            {'$group': {
                '_id': None,
                'total_buy': {'$sum': '$l_buy'},
                'total_sell': {'$sum': '$l_sell'},
                'total_net': {'$sum': '$net_amount'}
            }}
        ]
        
        stats_result = list(collection.aggregate(pipeline))
        stats = stats_result[0] if stats_result else {
            'total_buy': 0, 'total_sell': 0, 'total_net': 0
        }
        
        return {
            "success": True,
            "data": {
                "trade_date": trade_date,
                "total_count": total_count,
                "statistics": {
                    "total_buy_amount": stats.get('total_buy', 0),
                    "total_sell_amount": stats.get('total_sell', 0), 
                    "total_net_amount": stats.get('total_net', 0)
                },
                "dragon_tiger_list": dragon_tiger_list,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取龙虎榜数据失败: {str(e)}")

@router.get("/dragon-tiger/summary")
@cache_endpoint(data_type='dragon_tiger_summary', ttl=600)  # 缓存10分钟
async def get_dragon_tiger_summary(
    days: int = Query(default=5, description="统计最近几天的数据")
):
    """
    获取龙虎榜统计摘要
    
    Args:
        days: 统计最近几天的数据
    
    Returns:
        龙虎榜统计摘要
    """
    try:
        collection = db_handler.get_collection('top_list')
        
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y%m%d')
        
        # 获取最近几天的统计
        pipeline = [
            {'$match': {
                'trade_date': {'$gte': start_date, '$lte': end_date}
            }},
            {'$group': {
                '_id': '$trade_date',
                'count': {'$sum': 1},
                'total_amount': {'$sum': '$amount'},
                'total_net': {'$sum': '$net_amount'},
                'avg_change': {'$avg': '$pct_change'}
            }},
            {'$sort': {'_id': -1}}
        ]
        
        daily_stats = list(collection.aggregate(pipeline))
        
        # 获取活跃股票
        active_stocks_pipeline = [
            {'$match': {
                'trade_date': {'$gte': start_date, '$lte': end_date}
            }},
            {'$group': {
                '_id': '$ts_code',
                'name': {'$first': '$name'},
                'count': {'$sum': 1},
                'total_net': {'$sum': '$net_amount'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        active_stocks = list(collection.aggregate(active_stocks_pipeline))
        
        return {
            "success": True,
            "data": {
                "period": f"最近{days}天",
                "daily_statistics": daily_stats,
                "most_active_stocks": active_stocks,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取龙虎榜统计失败: {str(e)}")

@cache_endpoint(data_type="index_detail", ttl=1800)
@router.get("/indices/{ts_code}")
async def get_index_detail(
    ts_code: str,
    period: str = Query(default="daily", description="数据周期"),
    limit: int = Query(default=60, description="获取数据条数")
):
    """
    获取单个指数的详细数据
    
    Args:
        ts_code: 指数代码
        period: 数据周期
        limit: 数据条数
    
    Returns:
        指数详细数据
    """
    try:
        collection_map = {
            'daily': 'index_daily',
            'weekly': 'index_weekly',
            'monthly': 'index_monthly'
        }
        
        collection_name = collection_map.get(period, 'index_daily')
        collection = db_handler.get_collection(collection_name)
        
        cursor = collection.find(
            {'ts_code': ts_code},
            {'_id': 0}
        ).sort('trade_date', -1).limit(limit)
        
        data_list = list(cursor)
        
        if not data_list:
            raise HTTPException(status_code=404, detail=f"未找到指数 {ts_code} 的数据")
        
        # 获取指数信息
        index_info = MAJOR_INDICES.get(ts_code, {'name': ts_code, 'market': '未知'})
        
        return {
            "success": True,
            "data": {
                "ts_code": ts_code,
                "name": index_info['name'],
                "market": index_info['market'],
                "period": period,
                "data": data_list,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指数详情失败: {str(e)}")