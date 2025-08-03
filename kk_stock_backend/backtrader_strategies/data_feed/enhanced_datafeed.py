#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强数据源模块
基于MongoDB数据库的backtrader数据源适配器
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import backtrader as bt

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.global_db import db_handler
from backtrader_strategies.config import DatabaseConfig


class EnhancedDataFeed(bt.feeds.PandasData):
    """
    增强数据源类
    基于MongoDB数据的backtrader数据源
    """
    
    # 定义数据列映射
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
        # 技术指标列
        ('ma5', 'ma5'),
        ('ma20', 'ma20'),
        ('ma60', 'ma60'),
        ('macd_dif', 'macd_dif'),
        ('macd_dea', 'macd_dea'),
        ('kdj_k', 'kdj_k'),
        ('kdj_d', 'kdj_d'),
        ('rsi', 'rsi'),
        ('turnover_rate', 'turnover_rate'),
        ('volume_ratio', 'volume_ratio'),
    )


def _fetch_enhanced_data(
    stock_code: str,
    start_date: str,
    end_date: str,
    include_indicators: bool = True
) -> pd.DataFrame:
    """
    从数据库获取增强股票数据
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        include_indicators: 是否包含技术指标
        
    Returns:
        包含股票数据的DataFrame
    """
    try:
        # 初始化数据库连接
        # 使用全局数据库处理器
        db_config = DatabaseConfig()
        collection = db_handler.get_collection(db_config.factor_collection)
        
        # 转换日期格式
        start_date_str = start_date.replace('-', '')
        end_date_str = end_date.replace('-', '')
        
        # 构建查询条件
        query = {
            'ts_code': stock_code,
            'trade_date': {
                '$gte': start_date_str,
                '$lte': end_date_str
            }
        }
        
        # 查询数据
        cursor = collection.find(query).sort('trade_date', 1)
        data_list = list(cursor)
        
        if not data_list:
            print(f"⚠️  未找到股票 {stock_code} 在 {start_date} 到 {end_date} 期间的数据")
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(data_list)
        
        # 处理日期列
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df.set_index('trade_date', inplace=True)
        
        # 字段映射和重命名
        field_mapping = db_config.field_mapping
        
        # 基础OHLCV数据
        required_fields = {
            'open': field_mapping.get('open', 'open'),
            'high': field_mapping.get('high', 'high'),
            'low': field_mapping.get('low', 'low'),
            'close': field_mapping.get('close', 'close'),
            'volume': field_mapping.get('volume', 'vol')
        }
        
        # 检查并重命名基础字段
        result_df = pd.DataFrame(index=df.index)
        for target_field, source_field in required_fields.items():
            if source_field in df.columns:
                result_df[target_field] = df[source_field]
            else:
                print(f"⚠️  缺少字段: {source_field}")
                result_df[target_field] = np.nan
        
        # 添加技术指标
        if include_indicators:
            indicator_fields = {
                'ma5': field_mapping.get('ma5', 'ma_bfq_5'),
                'ma20': field_mapping.get('ma20', 'ma_bfq_20'),
                'ma60': field_mapping.get('ma60', 'ma_bfq_60'),
                'macd_dif': field_mapping.get('macd_dif', 'macd_dif_bfq'),
                'macd_dea': field_mapping.get('macd_dea', 'macd_dea_bfq'),
                'kdj_k': field_mapping.get('kdj_k', 'kdj_k_bfq'),
                'kdj_d': field_mapping.get('kdj_d', 'kdj_d_bfq'),
                'rsi': field_mapping.get('rsi6', 'rsi_bfq_6'),
                'turnover_rate': field_mapping.get('turnover_rate', 'turnover_rate'),
                'volume_ratio': field_mapping.get('volume_ratio', 'volume_ratio'),
            }
            
            for target_field, source_field in indicator_fields.items():
                if source_field in df.columns:
                    result_df[target_field] = df[source_field]
                else:
                    result_df[target_field] = np.nan
        
        # 数据清理
        result_df = result_df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        
        # 确保数据类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        if include_indicators:
            numeric_columns.extend(['ma5', 'ma20', 'ma60', 'macd_dif', 'macd_dea', 
                                  'kdj_k', 'kdj_d', 'rsi', 'turnover_rate', 'volume_ratio'])
        
        for col in numeric_columns:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
        
        # 最终数据验证
        result_df = result_df.dropna(subset=['open', 'high', 'low', 'close'])
        
        print(f"✅ 成功获取股票 {stock_code} 数据: {len(result_df)} 条记录")
        return result_df
        
    except Exception as e:
        print(f"❌ 获取股票 {stock_code} 数据失败: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_stock_universe() -> List[str]:
    """
    获取股票池（中证A500成分股）
    
    Returns:
        股票代码列表
    """
    try:
        # 使用全局数据库处理器
        
        # 获取index_weight集合
        index_collection = db_handler.get_collection('index_weight')
        
        # 查询中证A500最新成分股
        query = {'index_code': '000510.CSI'}
        cursor = index_collection.find(query).sort('trade_date', -1).limit(1000)
        
        stock_codes = []
        latest_date = None
        
        for doc in cursor:
            current_date = doc.get('trade_date')
            if latest_date is None:
                latest_date = current_date
            elif current_date != latest_date:
                break  # 只取最新日期的数据
                
            if 'con_code' in doc and doc['con_code']:
                stock_codes.append(doc['con_code'])
        
        # 去重并排序
        stock_codes = sorted(list(set(stock_codes)))
        
        print(f"✅ 获取中证A500成分股: {len(stock_codes)} 只")
        return stock_codes
        
    except Exception as e:
        print(f"❌ 获取股票池失败: {e}")
        # 返回一些默认股票用于测试
        return ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH', '000858.SZ']


def create_data_feeds(
    stock_codes: List[str],
    start_date: str,
    end_date: str,
    max_stocks: int = 50
) -> Dict[str, EnhancedDataFeed]:
    """
    创建多只股票的数据源
    
    Args:
        stock_codes: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        max_stocks: 最大股票数量
        
    Returns:
        股票代码到数据源的映射字典
    """
    data_feeds = {}
    
    # 限制股票数量
    selected_stocks = stock_codes[:max_stocks]
    
    print(f"🔄 开始创建 {len(selected_stocks)} 只股票的数据源...")
    
    for i, stock_code in enumerate(selected_stocks):
        try:
            # 获取股票数据
            df = _fetch_enhanced_data(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                include_indicators=True
            )
            
            if not df.empty and len(df) > 20:  # 至少需要20个交易日的数据
                # 创建数据源
                data_feed = EnhancedDataFeed(dataname=df)
                data_feeds[stock_code] = data_feed
                
                print(f"✅ [{i+1}/{len(selected_stocks)}] {stock_code}: {len(df)} 条数据")
            else:
                print(f"⚠️  [{i+1}/{len(selected_stocks)}] {stock_code}: 数据不足，跳过")
                
        except Exception as e:
            print(f"❌ [{i+1}/{len(selected_stocks)}] {stock_code}: 创建数据源失败 - {e}")
            continue
    
    print(f"🎯 成功创建 {len(data_feeds)} 只股票的数据源")
    return data_feeds


if __name__ == "__main__":
    # 测试数据获取
    print("🚀 测试增强数据源...")
    
    # 测试单只股票数据获取
    test_stock = "000001.SZ"
    df = _fetch_enhanced_data(
        stock_code=test_stock,
        start_date="2024-01-01",
        end_date="2024-12-31",
        include_indicators=True
    )
    
    if not df.empty:
        print(f"\n📊 {test_stock} 数据概览:")
        print(f"  数据行数: {len(df)}")
        print(f"  数据列数: {len(df.columns)}")
        print(f"  日期范围: {df.index.min()} 到 {df.index.max()}")
        print(f"  数据列: {list(df.columns)}")
        print(f"\n最新5天数据:")
        print(df.tail())
    
    # 测试股票池获取
    print(f"\n🔍 测试股票池获取...")
    stock_universe = get_stock_universe()
    print(f"股票池大小: {len(stock_universe)}")
    print(f"前10只股票: {stock_universe[:10]}")