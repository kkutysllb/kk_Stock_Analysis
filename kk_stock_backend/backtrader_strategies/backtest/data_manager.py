#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理器
负责从数据库加载历史数据，提供统一的数据接口
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.global_db import db_handler
from backtrader_strategies.config import DatabaseConfig


class DataManager:
    """
    数据管理器
    负责加载和管理历史市场数据
    """
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        """
        初始化数据管理器
        
        Args:
            db_config: 数据库配置，如果为None则使用默认配置
        """
        self.db_config = db_config or DatabaseConfig()
        self.db_handler = db_handler
        self.data_cache = {}  # 数据缓存
        self.stock_universe = []  # 股票池
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
    def load_stock_universe(self, index_code: str = "000510.CSI") -> List[str]:
        """
        加载股票池（默认中证A500）
        
        Args:
            index_code: 指数代码
            
        Returns:
            股票代码列表
        """
        try:
            self.logger.info(f"加载股票池: {index_code}")
            
            # 获取指数权重集合
            index_collection = self.db_handler.get_collection('index_weight')
            
            # 查询最新的成分股
            query = {'index_code': index_code}
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
            self.stock_universe = sorted(list(set(stock_codes)))
            
            self.logger.info(f"加载完成，股票数量: {len(self.stock_universe)}")
            return self.stock_universe
            
        except Exception as e:
            self.logger.error(f"加载股票池失败: {e}")
            # 返回一些默认股票用于测试
            self.stock_universe = ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH', '000858.SZ']
            return self.stock_universe
    
    def load_stock_data(self, 
                       stock_code: str, 
                       start_date: str, 
                       end_date: str,
                       include_indicators: bool = True) -> pd.DataFrame:
        """
        加载单只股票的历史数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            include_indicators: 是否包含技术指标
            
        Returns:
            股票历史数据DataFrame
        """
        cache_key = f"{stock_code}_{start_date}_{end_date}_{include_indicators}"
        
        # 检查缓存
        if cache_key in self.data_cache:
            return self.data_cache[cache_key].copy()
        
        try:
            collection = self.db_handler.get_collection(self.db_config.factor_collection)
            
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
                self.logger.warning(f"未找到股票 {stock_code} 在 {start_date} 到 {end_date} 期间的数据")
                return pd.DataFrame()
            
            # 调试输出：检查WR指标是否存在
            if stock_code in ['002003.SZ', '600761.SH'] and data_list:
                sample_data = data_list[0]
                field_mapping = self.db_config.field_mapping
                wr1_source = field_mapping.get('wr1', 'wr1_bfq')
                wr2_source = field_mapping.get('wr2', 'wr_bfq')
                
                print(f"🔍 {stock_code} WR指标检查:")
                print(f"   wr1字段: {wr1_source} ({'存在' if wr1_source in sample_data else '不存在'})")
                print(f"   wr2字段: {wr2_source} ({'存在' if wr2_source in sample_data else '不存在'})")
                if wr1_source in sample_data:
                    print(f"   wr1样本值: {sample_data.get(wr1_source)}")
                if wr2_source in sample_data:
                    print(f"   wr2样本值: {sample_data.get(wr2_source)}")
            
            # 转换为DataFrame
            df = pd.DataFrame(data_list)
            
            # 处理日期列
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            df.set_index('trade_date', inplace=True)
            
            # 字段映射和重命名
            field_mapping = self.db_config.field_mapping
            
            # 基础OHLCV数据和关键字段
            required_fields = {
                'open': field_mapping.get('open', 'open'),
                'high': field_mapping.get('high', 'high'),
                'low': field_mapping.get('low', 'low'),
                'close': field_mapping.get('close', 'close'),
                'volume': field_mapping.get('volume', 'vol'),
                'amount': field_mapping.get('amount', 'amount'),
                'pre_close': field_mapping.get('pre_close', 'pre_close'),  # 前收盘价
                'circ_mv': field_mapping.get('circ_mv', 'circ_mv')          # 流通市值
            }
            
            # 检查并重命名基础字段
            result_df = pd.DataFrame(index=df.index)
            for target_field, source_field in required_fields.items():
                if source_field in df.columns:
                    result_df[target_field] = df[source_field]
                else:
                    self.logger.warning(f"缺少字段: {source_field}")
                    result_df[target_field] = np.nan
            
            # 添加技术指标
            if include_indicators:
                indicator_fields = {
                    'ma5': field_mapping.get('ma5', 'ma_bfq_5'),
                    'ma10': field_mapping.get('ma10', 'ma_bfq_10'),
                    'ma20': field_mapping.get('ma20', 'ma_bfq_20'),
                    'ma60': field_mapping.get('ma60', 'ma_bfq_60'),
                    'ma120': field_mapping.get('ma120', 'ma_bfq_120'),
                    'ma250': field_mapping.get('ma250', 'ma_bfq_250'),
                    'ema5': field_mapping.get('ema5', 'ema_bfq_5'),
                    'ema10': field_mapping.get('ema10', 'ema_bfq_10'),
                    'ema20': field_mapping.get('ema20', 'ema_bfq_20'),
                    'macd_dif': field_mapping.get('macd_dif', 'macd_dif_bfq'),
                    'macd_dea': field_mapping.get('macd_dea', 'macd_dea_bfq'),
                    'macd_macd': field_mapping.get('macd_macd', 'macd_bfq'),
                    'kdj_k': field_mapping.get('kdj_k', 'kdj_k_bfq'),
                    'kdj_d': field_mapping.get('kdj_d', 'kdj_d_bfq'),
                    'kdj_j': field_mapping.get('kdj_j', 'kdj_bfq'),
                    'rsi6': field_mapping.get('rsi6', 'rsi_bfq_6'),
                    'rsi12': field_mapping.get('rsi12', 'rsi_bfq_12'),
                    'rsi24': field_mapping.get('rsi24', 'rsi_bfq_24'),
                    'boll_upper': field_mapping.get('boll_upper', 'boll_upper_bfq'),
                    'boll_mid': field_mapping.get('boll_mid', 'boll_mid_bfq'),
                    'boll_lower': field_mapping.get('boll_lower', 'boll_lower_bfq'),
                    'wr1': field_mapping.get('wr1', 'wr1_bfq'),
                    'wr2': field_mapping.get('wr2', 'wr_bfq'),
                    'turnover_rate': field_mapping.get('turnover_rate', 'turnover_rate'),
                    'volume_ratio': field_mapping.get('volume_ratio', 'volume_ratio'),
                    # volume_ma20 将通过计算得出，不从数据库字段映射
                }
                
                for target_field, source_field in indicator_fields.items():
                    if target_field == 'volume_ma20':
                        continue  # volume_ma20将在后面计算
                    elif isinstance(source_field, str) and source_field in df.columns:
                        result_df[target_field] = df[source_field]
                    else:
                        result_df[target_field] = np.nan
            
            # 数据清理 - 只对必需的价格数据做严格检查
            result_df = result_df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
            
            # 确保数据类型正确
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pre_close', 'circ_mv']
            if include_indicators:
                numeric_columns.extend([
                    'ma5', 'ma10', 'ma20', 'ma60', 'ma120', 'ma250',
                    'ema5', 'ema10', 'ema20',
                    'macd_dif', 'macd_dea', 'macd_macd',
                    'kdj_k', 'kdj_d', 'kdj_j',
                    'rsi6', 'rsi12', 'rsi24',
                    'boll_upper', 'boll_mid', 'boll_lower',
                    'wr1', 'wr2',
                    'turnover_rate', 'volume_ratio', 'volume_ma20'
                ])
            
            for col in numeric_columns:
                if col in result_df.columns:
                    result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
            
            # 最终数据验证
            result_df = result_df.dropna(subset=['open', 'high', 'low', 'close'])
            
            # 调试输出：检查最终WR数据
            if stock_code in ['002003.SZ', '600761.SH'] and not result_df.empty:
                print(f"🔍 {stock_code} 最终WR数据:")
                print(f"   wr1: {result_df['wr1'].iloc[0] if 'wr1' in result_df.columns else 'N/A'}")
                print(f"   wr2: {result_df['wr2'].iloc[0] if 'wr2' in result_df.columns else 'N/A'}")
                print(f"   volume_ma20: {result_df['volume_ma20'].iloc[0] if 'volume_ma20' in result_df.columns else 'N/A'}")
            
            # 计算技术指标
            if include_indicators:
                # 计算20日成交量移动平均
                result_df['volume_ma20'] = result_df['volume'].rolling(window=20, min_periods=1).mean()
                
                # 调试输出：成交量计算完成
                if stock_code in ['002003.SZ', '600761.SH']:
                    print(f"   成交量均线计算完成: 第1天{result_df['volume_ma20'].iloc[0]:.0f}")
            
            # 添加前一日收盘价
            result_df['prev_close'] = result_df['close'].shift(1)
            
            # 计算涨跌幅
            result_df['pct_change'] = result_df['close'].pct_change()
            
            # 合并财务数据
            result_df = self._merge_financial_data(result_df, stock_code, start_date, end_date)
            
            # 添加到缓存
            self.data_cache[cache_key] = result_df.copy()
            
            self.logger.info(f"成功加载股票 {stock_code} 数据: {len(result_df)} 条记录")
            return result_df
            
        except Exception as e:
            self.logger.error(f"加载股票 {stock_code} 数据失败: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def load_market_data(self, 
                        stock_codes: List[str], 
                        start_date: str, 
                        end_date: str,
                        max_stocks: int = 100,
                        strategy_scorer=None) -> Dict[str, pd.DataFrame]:
        """
        批量加载多只股票的历史数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            max_stocks: 最大股票数量
            strategy_scorer: 策略评分函数（可选）
            
        Returns:
            股票代码到数据的映射字典
        """
        market_data = {}
        
        # 如果提供了策略评分函数，使用评分选择股票
        if strategy_scorer and len(stock_codes) > max_stocks:
            self.logger.info(f"使用策略评分选择最优 {max_stocks} 只股票...")
            selected_stocks = self._select_stocks_by_strategy_score(
                stock_codes, start_date, end_date, max_stocks, strategy_scorer
            )
        else:
            # 否则使用分层采样确保不同板块的股票
            selected_stocks = self._select_stocks_by_sampling(stock_codes, max_stocks)
        
        self.logger.info(f"开始加载 {len(selected_stocks)} 只股票的历史数据...")
        
        success_count = 0
        for i, stock_code in enumerate(selected_stocks):
            try:
                df = self.load_stock_data(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    include_indicators=True
                )
                
                if not df.empty and len(df) > 20:  # 至少需要20个交易日的数据
                    market_data[stock_code] = df
                    success_count += 1
                    
                    if (i + 1) % 10 == 0:  # 每10只股票输出一次进度
                        self.logger.info(f"进度: {i+1}/{len(selected_stocks)}, 成功: {success_count}")
                else:
                    self.logger.warning(f"股票 {stock_code} 数据不足，跳过")
                    
            except Exception as e:
                self.logger.error(f"加载股票 {stock_code} 失败: {e}")
                continue
        
        self.logger.info(f"数据加载完成，成功: {success_count}/{len(selected_stocks)}")
        return market_data
    
    def get_trading_dates(self, start_date: str, end_date: str) -> List[str]:
        """
        获取指定期间的交易日列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日列表
        """
        try:
            # 从数据库获取交易日历
            collection = self.db_handler.get_collection(self.db_config.factor_collection)
            
            start_date_str = start_date.replace('-', '')
            end_date_str = end_date.replace('-', '')
            
            # 查询指定期间的所有交易日
            pipeline = [
                {
                    '$match': {
                        'trade_date': {
                            '$gte': start_date_str,
                            '$lte': end_date_str
                        }
                    }
                },
                {
                    '$group': {
                        '_id': '$trade_date'
                    }
                },
                {
                    '$sort': {'_id': 1}
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            trading_dates = []
            
            for doc in cursor:
                date_str = doc['_id']
                formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                trading_dates.append(formatted_date)
            
            self.logger.info(f"获取交易日: {len(trading_dates)} 天")
            return trading_dates
            
        except Exception as e:
            self.logger.error(f"获取交易日失败: {e}")
            # 返回简单的工作日列表作为备选
            date_range = pd.date_range(start_date, end_date, freq='B')  # B表示工作日
            return [date.strftime('%Y-%m-%d') for date in date_range]
    
    def _select_stocks_by_strategy_score(self, stock_codes: List[str], start_date: str, 
                                       end_date: str, max_stocks: int, strategy_scorer) -> List[str]:
        """
        基于策略评分选择股票
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            max_stocks: 最大股票数量
            strategy_scorer: 策略评分函数
            
        Returns:
            选中的股票代码列表
        """
        self.logger.info("正在计算股票策略评分...")
        stock_scores = []
        
        # 获取评分计算的参考日期（开始日期后60天，确保有足够数据）
        from datetime import datetime, timedelta
        score_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=60)).strftime('%Y-%m-%d')
        
        # 扩大数据加载范围以确保有足够的技术指标数据
        score_start_date = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y-%m-%d')
        
        # 为每只股票计算评分
        for i, stock_code in enumerate(stock_codes):
            try:
                # 加载股票数据用于评分（扩大范围以确保技术指标计算正确）
                stock_data_df = self.load_stock_data(stock_code, score_start_date, score_date, include_indicators=True)
                
                if not stock_data_df.empty and len(stock_data_df) > 20:
                    # 获取评分日期的数据
                    score_date_data = self.get_stock_data_on_date(stock_code, score_date, {stock_code: stock_data_df})
                    
                    if score_date_data:
                        # 计算策略评分
                        score = strategy_scorer(stock_code, score_date_data)
                        # 记录所有评分，不管是否满足买入条件
                        stock_scores.append((stock_code, score))
                        if len(stock_scores) <= 10:  # 记录前10个评分用于调试
                            self.logger.info(f"股票 {stock_code} 评分: {score:.2f}")
                    else:
                        self.logger.debug(f"股票 {stock_code} 在 {score_date} 无数据")
                
                if (i + 1) % 50 == 0:
                    self.logger.info(f"评分进度: {i+1}/{len(stock_codes)}")
                
            except Exception as e:
                self.logger.warning(f"股票 {stock_code} 评分失败: {e}")
                import traceback
                self.logger.debug(f"详细错误信息: {traceback.format_exc()}")
                continue
        
        # 按评分排序，选择最高分的股票
        stock_scores.sort(key=lambda x: x[1], reverse=True)
        selected_stocks = [stock_code for stock_code, score in stock_scores[:max_stocks]]
        
        self.logger.info(f"策略评分完成，选择了 {len(selected_stocks)} 只最优股票")
        if stock_scores:
            self.logger.info(f"最高评分: {stock_scores[0][1]:.2f} ({stock_scores[0][0]})")
            if len(stock_scores) > 1:
                self.logger.info(f"最低评分: {stock_scores[-1][1]:.2f} ({stock_scores[-1][0]})")
        
        # 如果选中的股票太少（少于目标的1/4），回退到分层采样
        if len(selected_stocks) < max_stocks // 4:
            self.logger.warning(f"策略评分仅选中 {len(selected_stocks)} 只股票，少于目标的25%，回退到分层采样")
            return self._select_stocks_by_sampling(stock_codes, max_stocks)
        
        return selected_stocks
    
    def _select_stocks_by_sampling(self, stock_codes: List[str], max_stocks: int) -> List[str]:
        """
        分层采样选择股票，确保不同板块的代表性
        
        Args:
            stock_codes: 股票代码列表
            max_stocks: 最大股票数量
            
        Returns:
            选中的股票代码列表
        """
        if len(stock_codes) <= max_stocks:
            return stock_codes
        
        # 按前缀分组（000=深主板, 001=深主板, 002=中小板, 003=创业板, 600-603=沪主板, 688=科创板等）
        stock_groups = {
            '000': [], '001': [], '002': [], '003': [], 
            '600': [], '601': [], '602': [], '603': [], '688': []
        }
        
        for stock_code in stock_codes:
            prefix = stock_code[:3]
            if prefix in stock_groups:
                stock_groups[prefix].append(stock_code)
            else:
                # 其他前缀归入600组
                stock_groups['600'].append(stock_code)
        
        # 计算每组应选择的数量
        selected_stocks = []
        total_stocks = sum(len(stocks) for stocks in stock_groups.values() if stocks)
        
        for prefix, stocks in stock_groups.items():
            if not stocks:
                continue
                
            # 按比例分配，确保每组至少有1只股票（如果该组有股票的话）
            group_quota = max(1, int(len(stocks) / total_stocks * max_stocks))
            group_quota = min(group_quota, len(stocks))
            
            # 均匀采样
            step = len(stocks) // group_quota if group_quota > 0 else 1
            selected_from_group = [stocks[i * step] for i in range(group_quota)]
            selected_stocks.extend(selected_from_group)
            
            if len(selected_stocks) >= max_stocks:
                break
        
        # 如果还没达到目标数量，随机补充
        if len(selected_stocks) < max_stocks:
            remaining_stocks = [s for s in stock_codes if s not in selected_stocks]
            import random
            random.seed(42)  # 固定种子保证可重复性
            additional_stocks = random.sample(
                remaining_stocks, 
                min(max_stocks - len(selected_stocks), len(remaining_stocks))
            )
            selected_stocks.extend(additional_stocks)
        
        return selected_stocks[:max_stocks]
    
    def get_stock_data_on_date(self, 
                              stock_code: str, 
                              date: str, 
                              market_data: Dict[str, pd.DataFrame]) -> Optional[Dict]:
        """
        获取指定股票在指定日期的数据
        
        Args:
            stock_code: 股票代码
            date: 日期
            market_data: 市场数据
            
        Returns:
            股票当日数据字典
        """
        if stock_code not in market_data:
            return None
        
        df = market_data[stock_code]
        
        # 转换日期格式
        try:
            target_date = pd.to_datetime(date)
            
            # 查找最接近的交易日数据
            if target_date in df.index:
                row = df.loc[target_date]
                data_dict = row.to_dict()
                
                # 调试输出
                if stock_code in ['002003.SZ', '600761.SH'] and date in ['2021-01-04', '2021-01-05']:
                    print(f"🔍 {stock_code} {date} 数据字典检查:")
                    print(f"   ma20: {data_dict.get('ma20', 'N/A')} (类型: {type(data_dict.get('ma20'))})")
                    print(f"   ma5: {data_dict.get('ma5', 'N/A')} (类型: {type(data_dict.get('ma5'))})")
                    print(f"   volume_ma20: {data_dict.get('volume_ma20', 'N/A')} (类型: {type(data_dict.get('volume_ma20'))})")
                    print(f"   DataFrame列: {list(df.columns)}")
                    print(f"   DataFrame中ma20值: {row.get('ma20', 'N/A')}")
                
                return data_dict
            else:
                # 找到最近的交易日
                valid_dates = df.index[df.index <= target_date]
                if len(valid_dates) > 0:
                    latest_date = valid_dates.max()
                    row = df.loc[latest_date]
                    return row.to_dict()
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"获取股票 {stock_code} 在 {date} 的数据失败: {e}")
            return None
    
    def validate_data_quality(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        验证数据质量
        
        Args:
            market_data: 市场数据
            
        Returns:
            数据质量报告
        """
        report = {
            'total_stocks': len(market_data),
            'stock_details': {},
            'overall_quality': 'good'
        }
        
        issues = []
        
        for stock_code, df in market_data.items():
            stock_report = {
                'total_days': len(df),
                'missing_data_days': 0,
                'zero_volume_days': 0,
                'abnormal_price_days': 0,
                'quality_score': 100
            }
            
            # 检查缺失数据
            missing_data = df[['open', 'high', 'low', 'close', 'volume']].isnull().any(axis=1).sum()
            stock_report['missing_data_days'] = missing_data
            
            # 检查零成交量
            zero_volume = (df['volume'] == 0).sum()
            stock_report['zero_volume_days'] = zero_volume
            
            # 检查异常价格（如负价格）
            abnormal_price = ((df['open'] <= 0) | (df['high'] <= 0) | 
                            (df['low'] <= 0) | (df['close'] <= 0)).sum()
            stock_report['abnormal_price_days'] = abnormal_price
            
            # 计算质量得分
            total_issues = missing_data + zero_volume + abnormal_price
            if len(df) > 0:
                quality_score = max(0, 100 - (total_issues / len(df)) * 100)
                stock_report['quality_score'] = quality_score
                
                if quality_score < 90:
                    issues.append(f"{stock_code}: 质量得分 {quality_score:.1f}")
            
            report['stock_details'][stock_code] = stock_report
        
        # 整体质量评估
        avg_quality = np.mean([details['quality_score'] for details in report['stock_details'].values()])
        if avg_quality >= 95:
            report['overall_quality'] = 'excellent'
        elif avg_quality >= 90:
            report['overall_quality'] = 'good'
        elif avg_quality >= 80:
            report['overall_quality'] = 'fair'
        else:
            report['overall_quality'] = 'poor'
        
        report['avg_quality_score'] = avg_quality
        report['issues'] = issues
        
        return report
    
    def _merge_financial_data(self, result_df: pd.DataFrame, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """合并财务数据到股票数据中 - 用于选股而非交易信号"""
        try:
            # 获取财务数据集合
            fina_collection = self.db_handler.get_collection(self.db_config.financial_indicator_collection)
            
            # 查询财务数据（获取历史财务数据用于选股）
            from datetime import datetime, timedelta
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            # 向前扩展1年以获取足够的财务数据用于选股
            extended_start = start_dt - timedelta(days=365)
            
            extended_start_str = extended_start.strftime('%Y%m%d')
            
            # 查询逻辑：获取在回测开始前已公告的所有财务数据
            query = {
                'ts_code': stock_code,
                'ann_date': {'$lt': start_date.replace('-', '')}  # 只要回测开始前已公告的数据
            }
            
            # 调试输出
            if stock_code in ['000012.SZ', '002003.SZ']:
                print(f"🔍 {stock_code} 财务查询: {query}")
                # 查看有多少数据
                count = fina_collection.count_documents(query)
                print(f"   匹配财务记录数: {count}")
                # 查看所有数据的ann_date范围
                all_query = {'ts_code': stock_code}
                sample = fina_collection.find(all_query, {'ann_date': 1, 'end_date': 1}).sort('ann_date', -1).limit(3)
                print(f"   最新3条ann_date: {[doc for doc in sample]}")
            
            # 财务指标字段
            financial_fields = {
                'eps': 'eps',
                'bps': 'bps', 
                'roe': 'roe',
                'roa': 'roa_yearly',
                'debt_to_assets': 'debt_to_assets',
                'revenue_ps': 'revenue_ps',
                'netprofit_margin': 'netprofit_margin',
                'assets_turn': 'assets_turn',
                'current_ratio': 'current_ratio',
                'quick_ratio': 'quick_ratio'
            }
            
            # 构建查询字段
            projection = {'ts_code': 1, 'end_date': 1, 'ann_date': 1}
            for alias, field in financial_fields.items():
                projection[field] = 1
            
            cursor = fina_collection.find(query, projection).sort('end_date', -1).limit(1)
            financial_data = list(cursor)
            
            if not financial_data:
                self.logger.debug(f"股票 {stock_code} 无财务数据用于选股")
                # 如果没有财务数据，添加空列
                for alias in financial_fields.keys():
                    result_df[alias] = np.nan
                return result_df
            
            # 获取最新的财务数据（用于整个回测期间的选股）
            latest_financial = financial_data[0]
            
            # 将财务数据填充到所有交易日（因为只用于选股，不需要时间变化）
            for alias, field in financial_fields.items():
                if field in latest_financial:
                    value = latest_financial[field]
                    if value is not None:
                        result_df[alias] = pd.to_numeric(value, errors='coerce')
                    else:
                        result_df[alias] = np.nan
                else:
                    result_df[alias] = np.nan
            
            self.logger.debug(f"股票 {stock_code} 财务数据已加载，用于选股")
            return result_df
            
        except Exception as e:
            self.logger.warning(f"合并财务数据失败 {stock_code}: {e}")
            # 如果合并失败，添加空的财务数据列
            financial_fields = ['eps', 'bps', 'roe', 'roa', 'debt_to_assets', 'revenue_ps', 
                              'netprofit_margin', 'assets_turn', 'current_ratio', 'quick_ratio']
            for field in financial_fields:
                result_df[field] = np.nan
            return result_df
    
    def clear_cache(self):
        """清理数据缓存"""
        self.data_cache.clear()
        self.logger.info("数据缓存已清理")


if __name__ == "__main__":
    # 测试数据管理器
    print("🚀 测试数据管理器...")
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    data_manager = DataManager()
    
    # 测试加载股票池
    stock_universe = data_manager.load_stock_universe()
    print(f"股票池大小: {len(stock_universe)}")
    print(f"前10只股票: {stock_universe[:10]}")
    
    # 测试加载单只股票数据
    if stock_universe:
        test_stock = stock_universe[0]
        df = data_manager.load_stock_data(
            stock_code=test_stock,
            start_date='2024-01-01',
            end_date='2024-12-31',
            include_indicators=True
        )
        
        if not df.empty:
            print(f"\n{test_stock} 数据概览:")
            print(f"数据行数: {len(df)}")
            print(f"数据列数: {len(df.columns)}")
            print(f"日期范围: {df.index.min()} 到 {df.index.max()}")
            print(f"数据列: {list(df.columns)}")
            print("\n最新5天数据:")
            print(df.tail())
    
    print("✅ 数据管理器测试完成")