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
            self.stock_universe = []
            return self.stock_universe
    
    def load_all_market_universe(self) -> List[str]:
        """
        加载全市场股票池
        注意：此方法只提供基础数据源，具体的筛选、评分、选股由策略适配器负责
        
        Returns:
            全市场股票代码列表（基础数据源，不做任何筛选）
        """
        try:
            self.logger.info(f"加载全市场基础股票池")
            
            # 获取全市场股票（从股票基本信息表获取所有有效股票）
            stock_basic_collection = self.db_handler.get_collection('infrastructure_stock_basic')
            
            # 查询所有A股市场股票
            query = {
                'market': {'$in': ['主板', '中小板', '创业板', '科创板']},  # A股市场
            }
            projection = {'ts_code': 1, '_id': 0}
            
            cursor = stock_basic_collection.find(query, projection)
            stock_codes = [doc['ts_code'] for doc in cursor if doc.get('ts_code')]
            
            # 基本过滤：只保留正常的A股代码格式
            filtered_stock_codes = []
            for code in stock_codes:
                if code and (code.endswith('.SZ') or code.endswith('.SH')):
                    filtered_stock_codes.append(code)
            
            stock_codes = sorted(filtered_stock_codes)
            
            self.logger.info(f"全市场基础股票池加载完成，总数量: {len(stock_codes)}只股票")
            self.logger.info("📝 注意：数据管理器仅提供基础数据源，具体选股、评分、调仓由策略适配器负责")
            
            # 更新股票池
            self.stock_universe = stock_codes
            
            return self.stock_universe
            
        except Exception as e:
            self.logger.error(f"加载全市场基础股票池失败: {e}")
            # 如果数据库查询失败，这是系统问题，不应该降级
            raise e
    
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
                # 需要加载的技术指标字段（基于全量数据库字段映射） 
                indicator_field_names = [
                    # ==================== 基础市场数据 ====================
                    'change', 'pct_chg', 'adj_factor',
                    
                    # ==================== 复权价格数据 ====================
                    'open_hfq', 'high_hfq', 'low_hfq', 'close_hfq',
                    'open_qfq', 'high_qfq', 'low_qfq', 'close_qfq',
                    
                    # ==================== 市值和估值指标 ====================
                    'total_mv', 'circ_mv', 'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm',
                    'dv_ratio', 'dv_ttm', 'total_share', 'float_share', 'free_share',
                    
                    # ==================== 成交量和流动性指标 ====================
                    'turnover_rate', 'turnover_rate_f', 'volume_ratio',
                    
                    # ==================== 移动平均线系列 ====================
                    # 简单移动平均(SMA) - 不复权
                    'ma5', 'ma10', 'ma20', 'ma30', 'ma60', 'ma90', 'ma250',  # 移除ma120(不存在)
                    # 简单移动平均(SMA) - 后复权  
                    'ma5_hfq', 'ma10_hfq', 'ma20_hfq', 'ma30_hfq', 'ma60_hfq', 'ma90_hfq', 'ma250_hfq',
                    # 简单移动平均(SMA) - 前复权
                    'ma5_qfq', 'ma10_qfq', 'ma20_qfq', 'ma30_qfq', 'ma60_qfq', 'ma90_qfq', 'ma250_qfq',
                    # 指数移动平均(EMA) - 不复权
                    'ema5', 'ema10', 'ema20', 'ema30', 'ema60', 'ema90', 'ema250',
                    # 指数移动平均(EMA) - 后复权
                    'ema5_hfq', 'ema10_hfq', 'ema20_hfq', 'ema30_hfq', 'ema60_hfq', 'ema90_hfq', 'ema250_hfq',
                    # 指数移动平均(EMA) - 前复权  
                    'ema5_qfq', 'ema10_qfq', 'ema20_qfq', 'ema30_qfq', 'ema60_qfq', 'ema90_qfq', 'ema250_qfq',
                    # EXPMA指数移动平均
                    'expma12', 'expma50', 'expma12_hfq', 'expma50_hfq', 'expma12_qfq', 'expma50_qfq',
                    
                    # ==================== RSI相对强弱指标系列 ====================
                    'rsi6', 'rsi12', 'rsi24',
                    'rsi6_hfq', 'rsi12_hfq', 'rsi24_hfq',
                    'rsi6_qfq', 'rsi12_qfq', 'rsi24_qfq',
                    
                    # ==================== MACD指标系列 ====================
                    'macd_dif', 'macd_dea', 'macd_macd',
                    'macd_dif_hfq', 'macd_dea_hfq', 'macd_macd_hfq',
                    'macd_dif_qfq', 'macd_dea_qfq', 'macd_macd_qfq',
                    
                    # ==================== 布林带指标系列 ====================
                    'boll_upper', 'boll_mid', 'boll_lower',
                    'boll_upper_hfq', 'boll_mid_hfq', 'boll_lower_hfq',
                    'boll_upper_qfq', 'boll_mid_qfq', 'boll_lower_qfq',
                    
                    # ==================== KDJ随机指标系列 ====================
                    'kdj_k', 'kdj_d', 'kdj_j',
                    'kdj_k_hfq', 'kdj_d_hfq', 'kdj_j_hfq',
                    'kdj_k_qfq', 'kdj_d_qfq', 'kdj_j_qfq',
                    
                    # ==================== 威廉指标系列 ====================
                    'wr', 'wr1',
                    'wr_hfq', 'wr1_hfq',
                    'wr_qfq', 'wr1_qfq',
                    
                    # ==================== BIAS乖离率指标系列 ====================
                    'bias1', 'bias2', 'bias3',
                    'bias1_hfq', 'bias2_hfq', 'bias3_hfq',
                    'bias1_qfq', 'bias2_qfq', 'bias3_qfq',
                    
                    # ==================== DMI趋向指标系列 ====================
                    'dmi_pdi', 'dmi_mdi', 'dmi_adx', 'dmi_adxr',
                    'dmi_pdi_hfq', 'dmi_mdi_hfq', 'dmi_adx_hfq', 'dmi_adxr_hfq',
                    'dmi_pdi_qfq', 'dmi_mdi_qfq', 'dmi_adx_qfq', 'dmi_adxr_qfq',
                    
                    # ==================== BRAR人气意愿指标系列 ====================
                    'brar_ar', 'brar_br',
                    'brar_ar_hfq', 'brar_br_hfq',
                    'brar_ar_qfq', 'brar_br_qfq',
                    
                    # ==================== 其他重要技术指标 ====================
                    'cci', 'cci_hfq', 'cci_qfq',                      # CCI商品通道指数
                    'atr', 'atr_hfq', 'atr_qfq',                      # ATR真实波幅
                    'roc', 'roc_hfq', 'roc_qfq',                      # ROC变动率
                    'mtm', 'mtm_hfq', 'mtm_qfq',                      # MTM动量指标
                    'psy', 'psy_hfq', 'psy_qfq',                      # PSY心理线
                    'psyma', 'psyma_hfq', 'psyma_qfq',                # PSYMA心理线移动平均
                    'obv', 'obv_hfq', 'obv_qfq',                      # OBV累积能量
                    'emv', 'emv_hfq', 'emv_qfq',                      # EMV简易波动
                    'mfi', 'mfi_hfq', 'mfi_qfq',                      # MFI资金流量
                    'vr', 'vr_hfq', 'vr_qfq',                         # VR成交量变异率
                    'mass', 'mass_hfq', 'mass_qfq',                   # MASS梅斯线
                    'ma_mass', 'ma_mass_hfq', 'ma_mass_qfq',          # MA_MASS梅斯线移动平均
                    'cr', 'cr_hfq', 'cr_qfq',                         # CR指标
                    'asi', 'asit', 'asi_hfq', 'asit_hfq', 'asi_qfq', 'asit_qfq', # ASI振动升降指标
                    'trix', 'trix_hfq', 'trix_qfq',                   # TRIX三重指数平滑
                    'dpo', 'dpo_hfq', 'dpo_qfq',                      # DPO去趋势价格震荡
                    'bbi', 'bbi_hfq', 'bbi_qfq',                      # BBI多空指标
                    
                    # ==================== 高级技术指标 ====================
                    'dfma_dif', 'dfma_difma',                         # DFMA动态平均
                    'dfma_dif_hfq', 'dfma_difma_hfq',
                    'dfma_dif_qfq', 'dfma_difma_qfq',
                    'ktn_upper', 'ktn_mid', 'ktn_down',               # KTN肯特纳通道
                    'ktn_upper_hfq', 'ktn_mid_hfq', 'ktn_down_hfq',
                    'ktn_upper_qfq', 'ktn_mid_qfq', 'ktn_down_qfq',
                    'taq_up', 'taq_mid', 'taq_down',                  # TAQ抛物线指标
                    'taq_up_hfq', 'taq_mid_hfq', 'taq_down_hfq',
                    'taq_up_qfq', 'taq_mid_qfq', 'taq_down_qfq',
                    'xsii_td1', 'xsii_td2', 'xsii_td3', 'xsii_td4',  # XSII小时四度空间指标
                    'xsii_td1_hfq', 'xsii_td2_hfq', 'xsii_td3_hfq', 'xsii_td4_hfq',
                    'xsii_td1_qfq', 'xsii_td2_qfq', 'xsii_td3_qfq', 'xsii_td4_qfq',
                    
                    # ==================== 涨跌统计指标 ====================
                    'updays', 'downdays', 'topdays', 'lowdays',
                ]
                
                # 使用field_mapping加载指标数据
                for target_field in indicator_field_names:
                    if target_field == 'volume_ma20':
                        continue  # volume_ma20将在后面计算
                    
                    # 从field_mapping获取实际数据库字段名
                    source_field = field_mapping.get(target_field, target_field)
                    
                    if source_field in df.columns:
                        result_df[target_field] = df[source_field]
                    else:
                        # 如果字段不存在，设为NaN并记录警告
                        result_df[target_field] = np.nan
                        if target_field not in ['wr1', 'wr2']:  # 兼容性字段不警告
                            self.logger.debug(f"技术指标字段 {target_field} ({source_field}) 不存在")
            
            # 数据清理 - 只对必需的价格数据做严格检查
            result_df = result_df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
            
            # 确保数据类型正确
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pre_close', 'circ_mv']
            if include_indicators:
                # 添加所有技术指标字段
                numeric_columns.extend(indicator_field_names)
                numeric_columns.append('volume_ma20')  # 添加计算字段
            
            for col in numeric_columns:
                if col in result_df.columns:
                    result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
            
            # 最终数据验证
            result_df = result_df.dropna(subset=['open', 'high', 'low', 'close'])
            
           
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
            return [date.strftime('%Y%m%d') for date in date_range]
    
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
        # 统一使用%Y%m%d格式
        start_date_fmt = start_date.replace('-', '') if '-' in start_date else start_date
        score_date = (datetime.strptime(start_date_fmt, '%Y%m%d') + timedelta(days=60)).strftime('%Y%m%d')
        
        # 扩大数据加载范围以确保有足够的技术指标数据
        score_start_date = (datetime.strptime(start_date_fmt, '%Y%m%d') - timedelta(days=60)).strftime('%Y%m%d')
        
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
            # 统一使用%Y%m%d格式
            start_date_fmt = start_date.replace('-', '') if '-' in start_date else start_date
            start_dt = datetime.strptime(start_date_fmt, '%Y%m%d')
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
            
            # 财务指标字段映射 - 基于数据库因子综合报告的全量财务字段
            financial_fields = {
                # ==================== 每股指标 ====================
                'eps': 'eps',                          # 每股收益
                'diluted2_eps': 'diluted2_eps',        # 稀释每股收益
                'dt_eps': 'dt_eps',                    # 扣非每股收益
                'bvps': 'bps',                         # 每股净资产
                'cfps': 'cfps',                        # 每股现金流
                'ocfps': 'ocfps',                      # 每股经营现金流
                'revenue_ps': 'revenue_ps',            # 每股营收
                'total_revenue_ps': 'total_revenue_ps', # 每股营业总收入
                'capital_rese_ps': 'capital_rese_ps',  # 每股资本公积
                'surplus_rese_ps': 'surplus_rese_ps',  # 每股盈余公积
                'undist_profit_ps': 'undist_profit_ps', # 每股未分配利润
                'retainedps': 'retainedps',            # 每股留存收益
                
                # ==================== 盈利能力指标 ====================
                'roe': 'roe',                          # 净资产收益率
                'roe_waa': 'roe_waa',                  # 加权平均净资产收益率
                'roe_dt': 'roe_dt',                    # 扣非净资产收益率
                'roe_avg': 'roe_avg',                  # 平均净资产收益率
                'roe_yearly': 'roe_yearly',            # 年化净资产收益率
                'roa_dp': 'roa_dp',                    # 总资产报酬率
                'roa_yearly': 'roa_yearly',            # 年化总资产收益率
                'netprofit_margin': 'netprofit_margin', # 销售净利率
                # 注意: grossprofit_margin字段在数据库中不存在，已移除
                # 'grossprofit_margin': 'grossprofit_margin', # 销售毛利率
                'profit_to_gr': 'profit_to_gr',        # 净利润/营业总收入
                'profit_to_op': 'profit_to_op',        # 净利润/营业利润
                
                # ==================== 营运能力指标 ====================
                'assets_turn': 'assets_turn',          # 资产周转率
                'total_fa_trun': 'total_fa_trun',      # 固定资产周转率
                
                # ==================== 偿债能力指标 ====================
                'debt_to_assets': 'debt_to_assets',    # 资产负债率
                'debt_to_eqt': 'debt_to_eqt',          # 产权比率
                'eqt_to_debt': 'eqt_to_debt',          # 权益乘数
                'assets_to_eqt': 'assets_to_eqt',      # 资产权益比
                # 注意: current_ratio, quick_ratio字段在数据库中不存在，已移除
                # 'current_ratio': 'current_ratio',    # 流动比率
                # 'quick_ratio': 'quick_ratio',        # 速动比率
                'ocf_to_debt': 'ocf_to_debt',          # 经营现金流量对负债比率
                'op_to_debt': 'op_to_debt',            # 营业利润对负债比率
                
                # ==================== 现金流指标 ====================
                'ocf_to_profit': 'ocf_to_profit',      # 经营现金净流量对净利润比率
                'ocf_to_opincome': 'ocf_to_opincome',  # 经营现金净流量对营业收入比率
                'ocf_to_or': 'ocf_to_or',              # 经营现金净流量营业收入比
                
                # ==================== 成长能力指标 ====================
                'revenue_yoy': 'or_yoy',               # 营业收入同比增长率
                'profit_yoy': 'netprofit_yoy',         # 净利润同比增长率
                'dt_netprofit_yoy': 'dt_netprofit_yoy', # 扣非净利润同比增长率
                'eps_yoy': 'basic_eps_yoy',            # 每股收益同比增长率
                'dt_eps_yoy': 'dt_eps_yoy',            # 扣非每股收益同比增长率
                'bps_yoy': 'bps_yoy',                  # 每股净资产同比增长率
                'cfps_yoy': 'cfps_yoy',                # 每股经营现金流同比增长率
                'roe_yoy': 'roe_yoy',                  # ROE同比变化
                'assets_yoy': 'assets_yoy',            # 资产同比增长率
                'equity_yoy': 'equity_yoy',            # 股东权益同比增长率
                'ebt_yoy': 'ebt_yoy',                  # 利润总额同比增长率
                'op_yoy': 'op_yoy',                    # 营业利润同比增长率
                'ocf_yoy': 'ocf_yoy',                  # 经营现金流同比增长率
                
                # ==================== 季度指标 ====================
                'q_eps': 'q_eps',                      # 单季每股收益
                'q_roe': 'q_roe',                      # 单季ROE
                'q_dt_roe': 'q_dt_roe',                # 单季扣非ROE
                'q_netprofit_margin': 'q_netprofit_margin', # 单季销售净利率
                'q_netprofit_yoy': 'q_netprofit_yoy',  # 单季净利润同比
                'q_netprofit_qoq': 'q_netprofit_qoq',  # 单季净利润环比
                'q_profit_yoy': 'q_profit_yoy',        # 单季利润同比
                'q_profit_qoq': 'q_profit_qoq',        # 单季利润环比
                'q_profit_to_gr': 'q_profit_to_gr',    # 单季净利润/营业总收入
                'q_dtprofit': 'q_dtprofit',            # 单季扣非净利润
                'q_dtprofit_to_profit': 'q_dtprofit_to_profit', # 单季扣非净利润/净利润
                'q_opincome': 'q_opincome',            # 单季营业收入
                'q_investincome': 'q_investincome',    # 单季投资收益
                'q_investincome_to_ebt': 'q_investincome_to_ebt', # 单季投资收益/利润总额
                'q_opincome_to_ebt': 'q_opincome_to_ebt', # 单季营业收入/利润总额
                
                # ==================== 其他财务指标 ====================
                'op_income': 'op_income',              # 营业收入
                'profit_dedt': 'profit_dedt',          # 利润总额
                'retained_earnings': 'retained_earnings', # 留存收益
                'fixed_assets': 'fixed_assets',        # 固定资产
                'non_op_profit': 'non_op_profit',      # 营业外收支净额
                'valuechange_income': 'valuechange_income', # 公允价值变动收益
                'investincome_of_ebt': 'investincome_of_ebt', # 投资收益/利润总额
                'opincome_of_ebt': 'opincome_of_ebt',  # 营业收入/利润总额
                'n_op_profit_of_ebt': 'n_op_profit_of_ebt', # 营业外收支净额/利润总额
                'dtprofit_to_profit': 'dtprofit_to_profit', # 扣非净利润/净利润
                'nop_to_ebt': 'nop_to_ebt',            # 营业外收支净额/利润总额
                'op_of_gr': 'op_of_gr',                # 营业利润/营业总收入
                'op_to_ebt': 'op_to_ebt',              # 营业利润/利润总额
                # 注意: adminexp_of_gr字段在数据库中不存在，暂时移除
                # 'adminexp_of_gr': 'adminexp_of_gr',  # 管理费用/营业总收入
                'extra_item': 'extra_item',            # 非经常性损益
                'npta': 'npta',                        # 总资产净利润
                'dp_assets_to_eqt': 'dp_assets_to_eqt', # 带息负债/全部投入资本
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
                              'netprofit_margin', 'assets_turn']  # 移除不存在的字段
            for field in financial_fields:
                result_df[field] = np.nan
            return result_df
    
    def clear_cache(self):
        """清理数据缓存"""
        self.data_cache.clear()
        self.logger.info("数据缓存已清理")
    
    def load_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载指数数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指数数据DataFrame
        """
        try:
            collection = self.db_handler.get_collection(self.db_config.index_daily_collection)
            
            query = {
                'ts_code': index_code,
                'trade_date': {
                    '$gte': start_date.replace('-', ''),
                    '$lte': end_date.replace('-', '')
                }
            }
            
            cursor = collection.find(query).sort('trade_date', 1)
            data = list(cursor)
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            df.set_index('trade_date', inplace=True)
            
            # 应用字段映射
            field_mapping = self.db_config.field_mapping
            mapped_data = {}
            for target_field, source_field in field_mapping.items():
                if target_field.startswith('idx_') and source_field in df.columns:
                    mapped_data[target_field] = df[source_field]
            
            result_df = pd.DataFrame(mapped_data)
            return result_df
            
        except Exception as e:
            self.logger.error(f"加载指数 {index_code} 数据失败: {e}")
            return pd.DataFrame()
    
    def load_money_flow_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载资金流向数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            资金流向数据DataFrame
        """
        try:
            collection = self.db_handler.get_collection(self.db_config.money_flow_collection)
            
            query = {
                'ts_code': stock_code,
                'trade_date': {
                    '$gte': start_date.replace('-', ''),
                    '$lte': end_date.replace('-', '')
                }
            }
            
            cursor = collection.find(query).sort('trade_date', 1)
            data = list(cursor)
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            df.set_index('trade_date', inplace=True)
            
            # 应用字段映射
            field_mapping = self.db_config.field_mapping
            mapped_data = {}
            money_flow_fields = [k for k in field_mapping.keys() if any(
                prefix in k for prefix in ['buy_', 'sell_', 'net_mf_']
            )]
            
            for target_field in money_flow_fields:
                source_field = field_mapping[target_field]
                if source_field in df.columns:
                    mapped_data[target_field] = df[source_field]
            
            result_df = pd.DataFrame(mapped_data)
            return result_df
            
        except Exception as e:
            self.logger.error(f"加载股票 {stock_code} 资金流向数据失败: {e}")
            return pd.DataFrame()
    
    def load_dividend_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载分红数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            分红数据DataFrame
        """
        try:
            collection = self.db_handler.get_collection(self.db_config.dividend_collection)
            
            query = {
                'ts_code': stock_code,
                'end_date': {
                    '$gte': start_date.replace('-', ''),
                    '$lte': end_date.replace('-', '')
                }
            }
            
            cursor = collection.find(query).sort('end_date', 1)
            data = list(cursor)
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            if 'end_date' in df.columns:
                df['end_date'] = pd.to_datetime(df['end_date'], format='%Y%m%d')
                df.set_index('end_date', inplace=True)
            
            # 应用字段映射
            field_mapping = self.db_config.field_mapping
            mapped_data = {}
            dividend_fields = [k for k in field_mapping.keys() if k.startswith('div_') or k in ['cash_div', 'stk_div']]
            
            for target_field in dividend_fields:
                source_field = field_mapping[target_field]
                if source_field in df.columns:
                    mapped_data[target_field] = df[source_field]
            
            result_df = pd.DataFrame(mapped_data)
            return result_df
            
        except Exception as e:
            self.logger.error(f"加载股票 {stock_code} 分红数据失败: {e}")
            return pd.DataFrame()
    
    def load_margin_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载融资融券数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            融资融券数据DataFrame
        """
        try:
            collection = self.db_handler.get_collection(self.db_config.margin_detail_collection)
            
            query = {
                'ts_code': stock_code,
                'trade_date': {
                    '$gte': start_date.replace('-', ''),
                    '$lte': end_date.replace('-', '')
                }
            }
            
            cursor = collection.find(query).sort('trade_date', 1)
            data = list(cursor)
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            df.set_index('trade_date', inplace=True)
            
            # 应用字段映射
            field_mapping = self.db_config.field_mapping
            mapped_data = {}
            margin_fields = ['rzye', 'rzmre', 'rzche', 'rqye', 'rqmcl', 'rqchl']
            
            for target_field in margin_fields:
                source_field = field_mapping.get(target_field, target_field)
                if source_field in df.columns:
                    mapped_data[target_field] = df[source_field]
            
            result_df = pd.DataFrame(mapped_data)
            return result_df
            
        except Exception as e:
            self.logger.error(f"加载股票 {stock_code} 融资融券数据失败: {e}")
            return pd.DataFrame()
    
    def load_trading_calendar(self, start_date: str, end_date: str, exchange: str = 'SSE') -> pd.DataFrame:
        """
        加载交易日历数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所代码
            
        Returns:
            交易日历DataFrame
        """
        try:
            collection = self.db_handler.get_collection(self.db_config.trading_calendar_collection)
            
            query = {
                'exchange': exchange,
                'cal_date': {
                    '$gte': start_date.replace('-', ''),
                    '$lte': end_date.replace('-', '')
                }
            }
            
            cursor = collection.find(query).sort('cal_date', 1)
            data = list(cursor)
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df['cal_date'] = pd.to_datetime(df['cal_date'], format='%Y%m%d')
            df.set_index('cal_date', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"加载交易日历数据失败: {e}")
            return pd.DataFrame()
