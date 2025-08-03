#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取工具
负责从数据库获取股票的多时间周期数据
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
from pymongo import MongoClient

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from api.db_handler import DBHandler


class DataFetcher:
    """数据获取器"""
    
    def __init__(self, db_config: Optional[Dict] = None):
        """
        初始化数据获取器
        
        Args:
            db_config: 数据库配置
        """
        self.logger = logging.getLogger(__name__)
        self.db_handler = DBHandler()
        
    def get_daily_data(self, stock_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        获取日线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日线数据DataFrame
        """
        try:
            # 直接从stock_kline_daily集合获取日线数据
            collection = self.db_handler.get_collection('stock_kline_daily')
            
            # 构建查询条件
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            query = {
                'ts_code': stock_code,
                'trade_date': {
                    '$gte': start_date_str,
                    '$lte': end_date_str
                }
            }
            
            # 查询数据
            cursor = collection.find(query).sort('trade_date', 1)
            data = list(cursor)
            
            if not data:
                self.logger.debug(f"未找到股票 {stock_code} 的日线数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 数据处理
            df = self._process_daily_data(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取日线数据时发生错误: {e}")
            return pd.DataFrame()
    
    def get_weekly_data(self, stock_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        获取周线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            周线数据DataFrame
        """
        try:
            # 尝试从stock_kline_weekly集合获取周线数据
            collection = self.db_handler.get_collection('stock_kline_weekly')
            
            # 构建查询条件
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            query = {
                'ts_code': stock_code,
                'trade_date': {
                    '$gte': start_date_str,
                    '$lte': end_date_str
                }
            }
            
            # 查询数据
            cursor = collection.find(query).sort('trade_date', 1)
            data = list(cursor)
            
            if not data:
                self.logger.debug(f"未找到股票 {stock_code} 的周线数据，尝试从日线数据合成")
                return self._synthesize_weekly_from_daily(stock_code, start_date, end_date)
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 数据处理
            df = self._process_weekly_data(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取周线数据时发生错误: {e}")
            return pd.DataFrame()
    
    def get_monthly_data(self, stock_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        获取月线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            月线数据DataFrame
        """
        try:
            # 尝试从stock_kline_monthly集合获取月线数据
            collection = self.db_handler.get_collection('stock_kline_monthly')
            
            # 构建查询条件
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            query = {
                'ts_code': stock_code,
                'trade_date': {
                    '$gte': start_date_str,
                    '$lte': end_date_str
                }
            }
            
            # 查询数据
            cursor = collection.find(query).sort('trade_date', 1)
            data = list(cursor)
            
            if not data:
                self.logger.debug(f"未找到股票 {stock_code} 的月线数据，尝试从日线数据合成")
                return self._synthesize_monthly_from_daily(stock_code, start_date, end_date)
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 数据处理
            df = self._process_monthly_data(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取月线数据时发生错误: {e}")
            return pd.DataFrame()
    
    def get_factor_data(self, stock_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        获取技术因子数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            技术因子数据DataFrame
        """
        try:
            # 直接从stock_factor_pro集合获取技术因子数据
            collection = self.db_handler.get_collection('stock_factor_pro')
            
            # 构建查询条件
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            query = {
                'ts_code': stock_code,
                'trade_date': {
                    '$gte': start_date_str,
                    '$lte': end_date_str
                }
            }
            
            # 查询数据
            cursor = collection.find(query).sort('trade_date', 1)
            data = list(cursor)
            
            if not data:
                self.logger.debug(f"未找到股票 {stock_code} 的技术因子数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 数据处理
            df = self._process_factor_data(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取技术因子数据时发生错误: {e}")
            return pd.DataFrame()
    
    def get_stock_basic_info(self, stock_code: str) -> Dict:
        """
        获取股票基本信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票基本信息字典
        """
        try:
            query = {'ts_code': stock_code}
            collection = self.db_handler.get_collection('infrastructure_stock_basic')
            data = list(collection.find(query).limit(1))
            
            if data:
                return data[0]
            else:
                return {'ts_code': stock_code, 'name': stock_code}
                
        except Exception as e:
            self.logger.error(f"获取股票基本信息时发生错误: {e}")
            return {'ts_code': stock_code, 'name': stock_code}
    
    def _process_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理日线数据"""
        if df.empty:
            return df
        
        # 如果trade_date不在索引中，设置为索引
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            df.set_index('trade_date', inplace=True)
        
        # 确保数值列为浮点型
        numeric_columns = ['open', 'high', 'low', 'close', 'vol', 'amount', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 重命名列以保持一致性
        column_mapping = {
            'vol': 'volume',
            'amount': 'turnover'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # 排序
        df.sort_index(inplace=True)
        
        # 去除重复数据
        df = df[~df.index.duplicated(keep='last')]
        
        return df
    
    def _process_weekly_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理周线数据"""
        return self._process_daily_data(df)  # 处理逻辑相同
    
    def _process_monthly_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理月线数据"""
        return self._process_daily_data(df)  # 处理逻辑相同
    
    def _process_factor_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理技术因子数据"""
        if df.empty:
            return df
        
        # 如果trade_date不在索引中，设置为索引
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            df.set_index('trade_date', inplace=True)
        
        # 确保数值列为浮点型
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 排序
        df.sort_index(inplace=True)
        
        # 去除重复数据
        df = df[~df.index.duplicated(keep='last')]
        
        return df
    
    def _synthesize_weekly_from_daily(self, stock_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """从日线数据合成周线数据"""
        daily_data = self.get_daily_data(stock_code, start_date, end_date)
        
        if daily_data.empty:
            return pd.DataFrame()
        
        # 按周聚合
        weekly_data = daily_data.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'turnover': 'sum'
        }).dropna()
        
        return weekly_data
    
    def _synthesize_monthly_from_daily(self, stock_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """从日线数据合成月线数据"""
        daily_data = self.get_daily_data(stock_code, start_date, end_date)
        
        if daily_data.empty:
            return pd.DataFrame()
        
        # 按月聚合
        monthly_data = daily_data.resample('ME').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'turnover': 'sum'
        }).dropna()
        
        return monthly_data
    
    def validate_data_quality(self, data: pd.DataFrame, data_type: str) -> Dict:
        """验证数据质量"""
        if data.empty:
            return {
                'is_valid': False,
                'errors': ['数据为空'],
                'warnings': []
            }
        
        errors = []
        warnings = []
        
        # 检查必要字段
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            errors.append(f"缺少必要字段: {missing_columns}")
        
        # 检查数据完整性
        if len(data) < 10:
            warnings.append(f"数据量较少，只有{len(data)}条记录")
        
        # 检查数据逻辑性
        if not missing_columns:
            # 高价应该 >= 低价
            invalid_high_low = data[data['high'] < data['low']]
            if not invalid_high_low.empty:
                errors.append(f"发现{len(invalid_high_low)}条高价低于低价的异常数据")
            
            # 开盘价和收盘价应该在高低价之间
            invalid_open = data[(data['open'] > data['high']) | (data['open'] < data['low'])]
            if not invalid_open.empty:
                warnings.append(f"发现{len(invalid_open)}条开盘价超出高低价范围的数据")
            
            invalid_close = data[(data['close'] > data['high']) | (data['close'] < data['low'])]
            if not invalid_close.empty:
                warnings.append(f"发现{len(invalid_close)}条收盘价超出高低价范围的数据")
            
            # 检查成交量
            zero_volume = data[data['volume'] <= 0]
            if not zero_volume.empty:
                warnings.append(f"发现{len(zero_volume)}条零成交量数据")
        
        # 检查数据连续性
        date_gaps = self._check_date_gaps(data.index, data_type)
        if date_gaps:
            warnings.append(f"发现{len(date_gaps)}个日期缺口")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'data_count': len(data),
            'date_range': {
                'start': data.index.min(),
                'end': data.index.max()
            }
        }
    
    def _check_date_gaps(self, date_index: pd.DatetimeIndex, data_type: str) -> List:
        """检查日期缺口"""
        if len(date_index) < 2:
            return []
        
        gaps = []
        
        # 根据数据类型确定期望的时间间隔
        if data_type == 'daily':
            expected_freq = pd.Timedelta(days=1)
            max_gap = pd.Timedelta(days=7)  # 允许周末和节假日
        elif data_type == 'weekly':
            expected_freq = pd.Timedelta(weeks=1)
            max_gap = pd.Timedelta(weeks=2)
        elif data_type == 'monthly':
            expected_freq = pd.Timedelta(days=30)
            max_gap = pd.Timedelta(days=45)
        else:
            return gaps
        
        for i in range(1, len(date_index)):
            gap = date_index[i] - date_index[i-1]
            if gap > max_gap:
                gaps.append({
                    'start': date_index[i-1],
                    'end': date_index[i],
                    'gap_days': gap.days
                })
        
        return gaps
    
    def get_market_index_data(self, index_code: str = '000001.SH', 
                             start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """
        获取市场指数数据
        
        Args:
            index_code: 指数代码，默认为上证指数
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指数数据DataFrame
        """
        try:
            if start_date is None:
                start_date = datetime.now() - timedelta(days=365)
            if end_date is None:
                end_date = datetime.now()
            
            query = {
                'ts_code': index_code,
                'trade_date': {
                    '$gte': start_date.strftime('%Y%m%d'),
                    '$lte': end_date.strftime('%Y%m%d')
                }
            }
            
            collection = self.db_handler.get_collection('index_kline_daily')
            data = list(collection.find(query))
            
            if not data:
                self.logger.warning(f"未找到指数 {index_code} 的数据")
                return pd.DataFrame()
            
            # 转换为DataFrame并处理
            df = pd.DataFrame(data)
            df = self._process_daily_data(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取指数数据时发生错误: {e}")
            return pd.DataFrame()