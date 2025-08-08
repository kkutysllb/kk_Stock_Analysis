#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子分析器 - 智能因子挖掘系统核心模块
基于261个技术因子分析中证A500指数成分股的收益预测能力
"""

import os
import sys
import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import yaml
import logging
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed

# 科学计算库
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from api.global_db import db_handler

# 导入加速模块
try:
    from ..acceleration import create_device_manager, GPUAccelerator
    ACCELERATION_AVAILABLE = True
except ImportError:
    ACCELERATION_AVAILABLE = False

# 导入自定义因子计算器
try:
    from .custom_factor_calculator import CustomFactorCalculator
    CUSTOM_FACTOR_AVAILABLE = True
except ImportError:
    CUSTOM_FACTOR_AVAILABLE = False

warnings.filterwarnings('ignore')

@dataclass
class FactorAnalysisResult:
    """因子分析结果数据类"""
    factor_name: str
    ic_mean: float
    ic_std: float
    ic_ir: float
    rank_ic: float
    t_stat: float
    p_value: float
    significance: bool
    turnover: float
    sharpe_ratio: float
    max_drawdown: float
    analysis_date: datetime
    sample_size: int
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'factor_name': self.factor_name,
            'ic_mean': self.ic_mean,
            'ic_std': self.ic_std,
            'ic_ir': self.ic_ir,
            'rank_ic': self.rank_ic,
            't_stat': self.t_stat,
            'p_value': self.p_value,
            'significance': self.significance,
            'turnover': self.turnover,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'analysis_date': self.analysis_date,
            'sample_size': self.sample_size
        }


class FactorAnalyzer:
    """
    因子分析器
    
    主要功能：
    1. 加载A500成分股的261个技术因子数据
    2. 计算因子与收益率的相关性指标
    3. 因子有效性评估和排序
    4. 因子稳定性分析
    5. 因子正交化处理
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化因子分析器
        
        Args:
            config_path: 配置文件路径
        """
        self.logger = self._setup_logger()
        
        # 加载配置
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "../config/factor_mining_config.yaml")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            self.logger.info(f"✅ 配置文件加载成功: {config_path}")
        except Exception as e:
            self.logger.error(f"❌ 配置文件加载失败: {e}")
            raise
        
        # 初始化组件
        self.db_handler = db_handler
        self.scaler = self._get_scaler()
        self.factor_data = {}
        self.return_data = {}
        self.analysis_results = {}
        
        # 初始化硬件加速
        self.device_manager = None
        self.gpu_accelerator = None
        if ACCELERATION_AVAILABLE:
            try:
                self.device_manager = create_device_manager(self.config)
                if self.device_manager and self.device_manager.device_type:
                    # 只有设备管理器成功初始化才创建GPU加速器
                    self.gpu_accelerator = GPUAccelerator(self.device_manager, self.config.get('acceleration_config', {}))
                    self.logger.info(f"⚡ 硬件加速已启用: {self.device_manager.device_type.upper()}")
                else:
                    self.logger.info("💻 硬件加速未检测到可用设备，使用CPU模式")
            except Exception as e:
                self.logger.warning(f"⚠️ 硬件加速初始化失败，使用CPU模式: {e}")
                self.device_manager = None
                self.gpu_accelerator = None
        else:
            self.logger.info("💻 加速模块未安装，使用CPU计算模式")
        
        # 初始化自定义因子计算器
        self.custom_factor_calculator = None
        if CUSTOM_FACTOR_AVAILABLE:
            try:
                self.custom_factor_calculator = CustomFactorCalculator()
                self.logger.info("🔧 自定义因子计算器已初始化")
            except Exception as e:
                self.logger.warning(f"⚠️ 自定义因子计算器初始化失败: {e}")
        else:
            self.logger.info("⚠️ 自定义因子计算器模块未找到")
        
        # 因子列表 - 从配置文件中获取
        self.factor_fields = self._load_factor_fields()
        
        self.logger.info(f"🚀 因子分析器初始化完成，共{len(self.factor_fields)}个因子")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _get_scaler(self):
        """获取标准化器"""
        scaler_type = self.config['factor_config']['preprocessing']['standardization']
        
        if scaler_type == 'zscore':
            return StandardScaler()
        elif scaler_type == 'minmax':
            return MinMaxScaler()
        elif scaler_type == 'robust':
            return RobustScaler()
        else:
            return StandardScaler()
    
    def _load_factor_fields(self) -> List[str]:
        """
        加载所有因子字段列表（326个）
        优先从factor_mining_config.yaml中获取完整因子列表
        """
        try:
            # 优先从配置文件中加载所有因子
            factor_fields = []
            factor_config = self.config['factor_config']['factor_categories']
            
            # 加载所有类别的因子
            for category, factors in factor_config.items():
                if category == 'custom_derived_factors':
                    # 处理自定义衍生因子
                    for subcategory, subfactors in factors.items():
                        if isinstance(subfactors, dict):
                            factor_fields.extend(list(subfactors.keys()))
                elif isinstance(factors, list):
                    factor_fields.extend(factors)
            
            # 去重并排序，排除索引字段
            factor_fields = sorted(list(set(factor_fields)))
            
            # 排除非因子字段
            exclude_fields = {'trade_date', 'ts_code', '_id'}
            factor_fields = [f for f in factor_fields if f not in exclude_fields]
            
            self.logger.info(f"📊 加载因子字段: {len(factor_fields)}个 (已排除索引字段)")
            basic_count = len([f for f in factor_config.get('basic_factors', []) if f in factor_fields])
            valuation_count = len([f for f in factor_config.get('valuation_factors', []) if f in factor_fields])
            liquidity_count = len([f for f in factor_config.get('liquidity_factors', []) if f in factor_fields])
            technical_count = len([f for f in factor_config.get('technical_factors', []) if f in factor_fields])
            self.logger.info(f"   ├─ 基础因子: {basic_count}个")
            self.logger.info(f"   ├─ 估值因子: {valuation_count}个") 
            self.logger.info(f"   ├─ 流动性因子: {liquidity_count}个")
            self.logger.info(f"   ├─ 技术指标因子: {technical_count}个")
            
            # 统计自定义因子
            custom_count = 0
            if 'custom_derived_factors' in factor_config:
                for subcategory, subfactors in factor_config['custom_derived_factors'].items():
                    if isinstance(subfactors, dict):
                        custom_count += len(subfactors)
            self.logger.info(f"   └─ 自定义衍生因子: {custom_count}个")
            
            # 验证数据库中实际存在的因子
            validated_factors = self._validate_database_factors(factor_fields)
            
            return validated_factors
            
        except Exception as e:
            self.logger.error(f"❌ 配置文件因子加载失败: {e}")
            # 回退到JSON文件加载
            return self._load_from_json_backup()
    
    def _validate_database_factors(self, factor_fields: List[str]) -> List[str]:
        """验证数据库中实际存在的因子字段，只使用stock_factor_pro集合"""
        try:
            # 只从stock_factor_pro集合获取字段
            collection = self.db_handler.get_collection('stock_factor_pro')
            sample_doc = collection.find_one({}, {'_id': 0})
            if not sample_doc:
                self.logger.warning("⚠️ 数据库中没有因子数据")
                return []
            
            # 获取数据库中实际存在的字段
            db_fields = set(sample_doc.keys()) - {'trade_date', 'ts_code', '_id'}
            self.logger.info(f"📊 stock_factor_pro: {len(db_fields)}个因子")
            
            # 分离数据库因子和自定义衍生因子
            db_factors = []
            custom_factors = []
            missing_factors = []
            
            for factor in factor_fields:
                if factor in db_fields:
                    db_factors.append(factor)
                elif self._is_custom_derived_factor(factor):
                    custom_factors.append(factor)
                else:
                    missing_factors.append(factor)
            
            self.logger.info(f"📊 因子验证结果:")
            self.logger.info(f"   ✅ 数据库因子: {len(db_factors)}个")
            self.logger.info(f"   🔧 自定义因子: {len(custom_factors)}个")
            self.logger.info(f"   ❌ 未知因子: {len(missing_factors)}个")
            
            if missing_factors:
                self.logger.warning(f"   未知因子前10个: {missing_factors[:10]}")
            
            # 返回数据库因子 + 自定义因子
            return db_factors + custom_factors
            
        except Exception as e:
            self.logger.error(f"❌ 数据库因子验证失败: {e}")
            return factor_fields  # 失败时返回原列表
    
    def _is_custom_derived_factor(self, factor_name: str) -> bool:
        """判断是否为自定义衍生因子"""
        try:
            custom_factors_config = self.config.get('factor_config', {}).get('factor_categories', {}).get('custom_derived_factors', {})
            
            for subcategory, subfactors in custom_factors_config.items():
                if isinstance(subfactors, dict) and factor_name in subfactors:
                    return True
            return False
        except:
            return False
    
    def _load_from_json_backup(self) -> List[str]:
        """从JSON文件加载技术因子作为备用方案"""
        try:
            factor_file = os.path.join(
                os.path.dirname(__file__), 
                "../../../backtrader_strategies/docs/stock_factor_pro_fields_analysis.json"
            )
            
            import json
            with open(factor_file, 'r', encoding='utf-8') as f:
                factor_analysis = json.load(f)
            
            # 提取所有因子字段名
            factor_fields = []
            # 根据实际JSON文件结构提取因子字段
            factor_categories = ['emotion_fields', 'trend_fields', 'other_fields']
            for category in factor_categories:
                fields = factor_analysis.get(category, [])
                if isinstance(fields, list):
                    factor_fields.extend(fields)
            
            # 去重并排序
            factor_fields = sorted(list(set(factor_fields)))
            
            self.logger.warning(f"⚠️ 使用JSON备用方案，仅加载技术因子: {len(factor_fields)}个")
            return factor_fields
            
        except Exception as e:
            self.logger.error(f"❌ JSON备用方案也失败: {e}")
            # 最后备用方案
            return self._get_backup_factors()
    
    def _get_backup_factors(self) -> List[str]:
        """获取备用因子列表"""
        backup_factors = []
        factor_config = self.config['factor_config']['factor_categories']
        
        for category, factors in factor_config.items():
            if isinstance(factors, list):
                backup_factors.extend(factors)
        
        return backup_factors
    
    def load_a500_universe(self, date: str = None) -> List[str]:
        """
        加载A500指数成分股列表
        
        Args:
            date: 指定日期，默认使用最新日期
            
        Returns:
            A500成分股代码列表
        """
        try:
            collection = self.db_handler.get_collection('index_weight')
            index_code = self.config['data_config']['index_code']
            
            # 查询条件
            query = {'index_code': index_code}
            if date:
                query['trade_date'] = date
            
            # 获取最新日期的成分股
            cursor = collection.find(query).sort('trade_date', -1).limit(500)
            
            stock_codes = []
            latest_date = None
            
            for doc in cursor:
                current_date = doc.get('trade_date')
                if latest_date is None:
                    latest_date = current_date
                elif current_date != latest_date:
                    break
                
                if 'con_code' in doc and doc['con_code']:
                    stock_codes.append(doc['con_code'])
            
            stock_codes = sorted(list(set(stock_codes)))
            self.logger.info(f"📊 加载A500成分股: {len(stock_codes)}只，日期: {latest_date}")
            
            return stock_codes
            
        except Exception as e:
            self.logger.error(f"❌ A500成分股加载失败: {e}")
            return []
    
    def load_factor_data(self, 
                        stock_codes: List[str], 
                        start_date: str, 
                        end_date: str) -> pd.DataFrame:
        """
        加载因子数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            因子数据DataFrame
        """
        try:
            self.logger.info(f"📊 开始加载因子数据: {len(stock_codes)}只股票，{start_date} to {end_date}")
            
            # 1. 加载原始因子数据（未标准化）
            raw_data = self._load_primary_factors_raw(stock_codes, start_date, end_date)
            
            if raw_data.empty:
                self.logger.error("❌ 没有加载到任何因子数据")
                return pd.DataFrame()
            
            # 2. 计算自定义衍生因子（使用原始数据）
            custom_data = self._calculate_custom_factors(raw_data, stock_codes, start_date, end_date)
            
            # 3. 合并自定义因子
            if not custom_data.empty:
                combined_data = raw_data.join(custom_data, how='outer')
                self.logger.info(f"📊 合并数据: 数据库{raw_data.shape[1]}个 + 自定义{custom_data.shape[1]}个 = {combined_data.shape[1]}个")
            else:
                combined_data = raw_data
                self.logger.info(f"📊 最终数据: {raw_data.shape[1]}个 (无自定义因子)")
            
            # 4. 对合并后的数据进行预处理（包括标准化）
            final_data = self._preprocess_factor_data(combined_data)
            self.logger.info(f"📊 数据库因子数据: {final_data.shape[1]}个因子")
            
            return final_data
            
        except Exception as e:
            self.logger.error(f"❌ 因子数据加载失败: {e}")
            return pd.DataFrame()
    
    def _load_primary_factors_raw(self, stock_codes: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """加载原始因子数据 (stock_factor_pro) - 不进行标准化"""
        try:
            collection = self.db_handler.get_collection('stock_factor_pro')
            
            # 批量查询 - 使用优化的批处理大小
            all_data = []
            base_batch_size = self.config.get('factor_config', {}).get('factor_analysis', {}).get('batch_size', 50)
            
            # 根据硬件性能优化批大小
            if self.device_manager and hasattr(self.device_manager, 'get_optimal_batch_size'):
                try:
                    batch_size = self.device_manager.get_optimal_batch_size(
                        base_batch_size, 
                        len(self.factor_fields), 
                        len(stock_codes)
                    )
                except Exception as e:
                    self.logger.warning(f"⚠️ 批大小优化失败，使用默认值: {e}")
                    batch_size = base_batch_size
            else:
                batch_size = base_batch_size
            
            for i in range(0, len(stock_codes), batch_size):
                batch_stocks = stock_codes[i:i+batch_size]
                
                # 转换日期格式 (YYYY-MM-DD -> YYYYMMDD)
                start_date_str = start_date.replace('-', '')
                end_date_str = end_date.replace('-', '')
                
                query = {
                    'ts_code': {'$in': batch_stocks},
                    'trade_date': {
                        '$gte': start_date_str,
                        '$lte': end_date_str
                    }
                }
                
                # 投影 - 只获取需要的字段
                projection = {'_id': 0, 'ts_code': 1, 'trade_date': 1}
                for factor in self.factor_fields:
                    projection[factor] = 1
                
                cursor = collection.find(query, projection)
                batch_data = list(cursor)
                all_data.extend(batch_data)
                
                self.logger.info(f"  批次 {i//batch_size + 1}: 加载了 {len(batch_data)} 条记录")
            
            if not all_data:
                self.logger.warning("⚠️ 未获取到任何因子数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(all_data)
            
            # 重命名字段以保持一致性
            if 'ts_code' in df.columns:
                df = df.rename(columns={'ts_code': 'stock_code'})
            
            # 只做基本的数据清理，不进行标准化
            df = self._basic_data_cleanup(df)
            
            self.logger.info(f"✅ 原始因子数据加载完成: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 原始因子数据加载失败: {e}")
            return pd.DataFrame()
    
    def _load_primary_factors(self, stock_codes: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """加载主要因子数据 (stock_factor_pro)"""
        try:
            collection = self.db_handler.get_collection('stock_factor_pro')
            
            # 批量查询 - 使用优化的批处理大小
            all_data = []
            base_batch_size = self.config.get('factor_config', {}).get('factor_analysis', {}).get('batch_size', 50)
            
            # 根据硬件性能优化批大小
            if self.device_manager and hasattr(self.device_manager, 'get_optimal_batch_size'):
                try:
                    batch_size = self.device_manager.get_optimal_batch_size(
                        base_batch_size, 
                        len(self.factor_fields), 
                        len(stock_codes)
                    )
                except Exception as e:
                    self.logger.warning(f"⚠️ 批大小优化失败，使用默认值: {e}")
                    batch_size = base_batch_size
            else:
                batch_size = base_batch_size
            
            for i in range(0, len(stock_codes), batch_size):
                batch_stocks = stock_codes[i:i+batch_size]
                
                # 转换日期格式 (YYYY-MM-DD -> YYYYMMDD)
                start_date_str = start_date.replace('-', '')
                end_date_str = end_date.replace('-', '')
                
                query = {
                    'ts_code': {'$in': batch_stocks},
                    'trade_date': {
                        '$gte': start_date_str,
                        '$lte': end_date_str
                    }
                }
                
                # 投影 - 只获取需要的字段
                projection = {'_id': 0, 'ts_code': 1, 'trade_date': 1}
                for factor in self.factor_fields:
                    projection[factor] = 1
                
                cursor = collection.find(query, projection)
                batch_data = list(cursor)
                all_data.extend(batch_data)
                
                self.logger.info(f"  批次 {i//batch_size + 1}: 加载了 {len(batch_data)} 条记录")
            
            if not all_data:
                self.logger.warning("⚠️ 未获取到任何因子数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(all_data)
            
            # 重命名字段以保持一致性
            if 'ts_code' in df.columns:
                df = df.rename(columns={'ts_code': 'stock_code'})
            
            # 数据预处理
            df = self._preprocess_factor_data(df)
            
            self.logger.info(f"✅ 主要因子数据加载完成: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 主要因子数据加载失败: {e}")
            return pd.DataFrame()
    
    def _load_mario_factors(self, stock_codes: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """加载Mario因子数据"""
        try:
            mario_data_list = []
            
            # 加载高优先级Mario因子
            high_priority_data = self._load_mario_collection('mario_factors_high_priority', stock_codes, start_date, end_date)
            if not high_priority_data.empty:
                mario_data_list.append(high_priority_data)
            
            # 加载中优先级Mario因子
            medium_priority_data = self._load_mario_collection('mario_factors_medium_priority', stock_codes, start_date, end_date)
            if not medium_priority_data.empty:
                mario_data_list.append(medium_priority_data)
            
            if not mario_data_list:
                self.logger.warning("⚠️ 未加载到任何Mario因子数据")
                return pd.DataFrame()
            
            # 合并Mario因子数据
            mario_df = mario_data_list[0]
            for i in range(1, len(mario_data_list)):
                mario_df = mario_df.join(mario_data_list[i], how='outer')
            
            self.logger.info(f"✅ Mario因子数据加载完成: {mario_df.shape}")
            return mario_df
            
        except Exception as e:
            self.logger.error(f"❌ Mario因子数据加载失败: {e}")
            return pd.DataFrame()
    
    def _load_mario_collection(self, collection_name: str, stock_codes: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """加载单个Mario因子集合"""
        try:
            collection = self.db_handler.get_collection(collection_name)
            
            # 转换日期格式
            start_date_str = start_date.replace('-', '')
            end_date_str = end_date.replace('-', '')
            
            query = {
                'ts_code': {'$in': stock_codes},
                'trade_date': {
                    '$gte': start_date_str,
                    '$lte': end_date_str
                }
            }
            
            # 获取所有数据
            cursor = collection.find(query, {'_id': 0})
            data_list = list(cursor)
            
            if not data_list:
                self.logger.warning(f"⚠️ {collection_name} 集合中没有数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(data_list)
            
            # 重命名字段以保持一致性
            if 'ts_code' in df.columns:
                df = df.rename(columns={'ts_code': 'stock_code'})
            
            # 设置索引
            if 'trade_date' in df.columns and 'stock_code' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                df = df.set_index(['trade_date', 'stock_code'])
            
            self.logger.info(f"📊 {collection_name}: 加载了 {df.shape} 数据")
            return df
            
        except Exception as e:
            self.logger.warning(f"⚠️ {collection_name} 加载失败: {e}")
            return pd.DataFrame()
    
    def _preprocess_factor_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        因子数据预处理
        
        Args:
            df: 原始因子数据
            
        Returns:
            预处理后的因子数据
        """
        try:
            if df.empty:
                return df
            
            # 设置索引（如果还没有设置）
            if not isinstance(df.index, pd.MultiIndex):
                # 处理日期格式：YYYYMMDD -> YYYY-MM-DD
                if 'trade_date' in df.columns:
                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                if 'trade_date' in df.columns and 'stock_code' in df.columns:
                    df = df.set_index(['trade_date', 'stock_code'])
            
            # 数据清洗
            preprocessing_config = self.config['factor_config']['preprocessing']
            
            # 处理异常值
            df = self._handle_outliers(df, preprocessing_config)
            
            # 数据填充
            fill_method = preprocessing_config.get('fill_method', 'forward')
            if fill_method == 'forward':
                df = df.fillna(method='ffill')
            elif fill_method == 'backward':
                df = df.fillna(method='bfill')
            elif fill_method == 'interpolate':
                df = df.interpolate()
            
            # 标准化 - 对所有数值列进行标准化，排除索引列
            factor_columns = [col for col in df.columns if col not in ['trade_date', 'stock_code', '_id']]
            if factor_columns:
                # 在标准化前处理无穷大值和极值
                df = self._clean_numeric_data(df, factor_columns)
                df[factor_columns] = self.scaler.fit_transform(df[factor_columns])
            
            self.logger.info(f"📊 因子数据预处理完成: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 因子数据预处理失败: {e}")
            return df
    
    def _handle_outliers(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """处理异常值"""
        method = config.get('outlier_method', 'mad')
        threshold = config.get('outlier_threshold', 3)
        
        factor_columns = [col for col in df.columns if col in self.factor_fields]
        
        for col in factor_columns:
            if col not in df.columns:
                continue
                
            if method == 'mad':
                # MAD方法
                median = df[col].median()
                mad = np.median(np.abs(df[col] - median))
                lower = median - threshold * mad
                upper = median + threshold * mad
            elif method == 'iqr':
                # IQR方法
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
            else:  # zscore
                # Z-score方法
                mean = df[col].mean()
                std = df[col].std()
                lower = mean - threshold * std
                upper = mean + threshold * std
            
            # 截断处理
            df[col] = df[col].clip(lower=lower, upper=upper)
        
        return df
    
    def _clean_numeric_data(self, df: pd.DataFrame, factor_columns: List[str]) -> pd.DataFrame:
        """
        清理数值数据，处理无穷大值和极值
        
        Args:
            df: 数据DataFrame
            factor_columns: 需要清理的因子列
            
        Returns:
            清理后的DataFrame
        """
        try:
            for col in factor_columns:
                if col not in df.columns:
                    continue
                
                # 1. 替换无穷大值为NaN
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
                
                # 2. 处理极值（超出float64安全范围的值）
                # float64的安全范围大约是 -1.7e308 到 1.7e308
                safe_max = 1e100  # 使用更保守的阈值
                safe_min = -1e100
                
                # 将超出安全范围的值设为NaN
                df.loc[df[col] > safe_max, col] = np.nan
                df.loc[df[col] < safe_min, col] = np.nan
                
                # 3. 检查是否还有无效值
                if pd.isna(df[col]).all():
                    # 如果整列都是无效值，用0填充
                    df[col] = 0.0
                    self.logger.warning(f"⚠️ 因子 {col} 全部为无效值，已用0填充")
                elif pd.isna(df[col]).any():
                    # 有部分无效值，用中位数填充
                    median_value = df[col].median()
                    if pd.isna(median_value):
                        median_value = 0.0
                    df[col] = df[col].fillna(median_value)
                    invalid_ratio = pd.isna(df[col]).sum() / len(df[col])
                    if invalid_ratio > 0.1:  # 如果超过10%的值无效，记录警告
                        self.logger.warning(f"⚠️ 因子 {col} 有 {invalid_ratio:.1%} 的无效值已被填充")
                
                # 4. 最终检查数据类型
                if not pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 数值数据清理失败: {e}")
            # 如果清理失败，至少确保没有无穷大值
            for col in factor_columns:
                if col in df.columns:
                    df[col] = df[col].replace([np.inf, -np.inf], 0.0)
            return df
    
    def calculate_forward_returns(self, 
                                stock_codes: List[str],
                                start_date: str, 
                                end_date: str) -> pd.DataFrame:
        """
        计算前瞻收益率
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            前瞻收益率DataFrame
        """
        try:
            self.logger.info(f"📊 开始计算前瞻收益率")
            
            collection = self.db_handler.get_collection('stock_factor_pro')
            
            # 转换日期格式 (YYYY-MM-DD -> YYYYMMDD)
            start_date_str = start_date.replace('-', '')
            end_date_str = end_date.replace('-', '')
            
            # 查询价格数据
            query = {
                'ts_code': {'$in': stock_codes},
                'trade_date': {
                    '$gte': start_date_str,
                    '$lte': end_date_str
                }
            }
            
            projection = {
                '_id': 0,
                'ts_code': 1,
                'trade_date': 1,
                'close': 1,
                'close_qfq': 1  # 使用前复权价格
            }
            
            cursor = collection.find(query, projection).sort([('ts_code', 1), ('trade_date', 1)])
            price_data = list(cursor)
            
            if not price_data:
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(price_data)
            # 处理日期格式：YYYYMMDD -> YYYY-MM-DD
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            # 重命名字段以保持一致性
            if 'ts_code' in df.columns:
                df = df.rename(columns={'ts_code': 'stock_code'})
            
            # 使用复权价格，如果没有则使用收盘价
            if 'close_qfq' in df.columns and df['close_qfq'].notna().any():
                price_col = 'close_qfq'
            else:
                price_col = 'close'
            
            # 计算各周期前瞻收益率
            forward_periods = self.config['data_config']['forward_returns']
            return_data = []
            
            for stock in stock_codes:
                stock_df = df[df['stock_code'] == stock].copy()
                if stock_df.empty:
                    continue
                
                stock_df = stock_df.sort_values('trade_date')
                stock_df = stock_df.set_index('trade_date')
                
                for period in forward_periods:
                    # 计算前瞻收益率
                    return_col = f'return_{period}d'
                    stock_df[return_col] = stock_df[price_col].pct_change(periods=period).shift(-period)
                
                # 重置索引并添加股票代码
                stock_df = stock_df.reset_index()
                stock_df['stock_code'] = stock
                return_data.append(stock_df)
            
            if not return_data:
                return pd.DataFrame()
            
            result_df = pd.concat(return_data, ignore_index=True)
            
            # 设置多重索引
            result_df = result_df.set_index(['trade_date', 'stock_code'])
            
            self.logger.info(f"✅ 前瞻收益率计算完成: {result_df.shape}")
            return result_df
            
        except Exception as e:
            self.logger.error(f"❌ 前瞻收益率计算失败: {e}")
            return pd.DataFrame()
    
    def calculate_factor_ic(self, 
                          factor_data: pd.DataFrame, 
                          return_data: pd.DataFrame,
                          return_period: int = 20) -> Dict[str, FactorAnalysisResult]:
        """
        计算因子IC指标
        
        Args:
            factor_data: 因子数据
            return_data: 收益率数据
            return_period: 收益率周期
            
        Returns:
            因子分析结果字典
        """
        try:
            self.logger.info(f"📊 开始计算因子IC指标，周期: {return_period}天")
            
            return_col = f'return_{return_period}d'
            if return_col not in return_data.columns:
                self.logger.error(f"❌ 收益率列 {return_col} 不存在")
                return {}
            
            results = {}
            # 只使用实际存在于数据中的因子字段，排除非因子列
            exclude_cols = {'trade_date', 'ts_code', 'stock_code', '_id'}
            factor_columns = [col for col in factor_data.columns 
                            if col not in exclude_cols and 
                            col in self.factor_fields and
                            col != return_col]
            
            self.logger.info(f"📊 可用因子数量: {len(factor_columns)}/{len(self.factor_fields)}")
            
            if not factor_columns:
                self.logger.warning("⚠️ 没有可用的因子数据进行IC计算")
                return {}
            
            # 合并数据
            merged_data = factor_data.join(return_data[return_col], how='inner')
            
            # 使用GPU加速IC计算
            if self.gpu_accelerator and len(factor_columns) > 10:
                try:
                    # 批量GPU计算
                    factor_df = merged_data[factor_columns]
                    return_df = merged_data[[return_col]]
                    
                    ic_results = self.gpu_accelerator.accelerated_ic_calculation(
                        factor_df, return_df
                    )
                    
                    # 转换为FactorAnalysisResult格式
                    for factor in factor_columns:
                        if factor in ic_results.index:
                            ic_value = ic_results.loc[factor, return_col]
                            # 创建简化的结果对象
                            result = FactorAnalysisResult(
                                factor_name=factor,
                                ic_mean=ic_value,
                                ic_std=0.0,  # GPU批量计算暂不计算这些统计量
                                ic_ir=0.0,
                                rank_ic=0.0,
                                t_stat=0.0,
                                p_value=0.0,
                                significance=abs(ic_value) > 0.02,
                                turnover=0.0,
                                sharpe_ratio=0.0,
                                max_drawdown=0.0,
                                analysis_date=datetime.now(),
                                sample_size=len(merged_data)
                            )
                            results[factor] = result
                    
                    self.logger.info(f"⚡ GPU加速IC计算完成: {len(results)}个因子")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ GPU加速失败，回退到CPU计算: {e}")
                    # 回退到原始CPU计算
                    for factor in factor_columns:
                        try:
                            result = self._analyze_single_factor(
                                merged_data, factor, return_col
                            )
                            if result:
                                results[factor] = result
                        except Exception as e:
                            self.logger.warning(f"⚠️ 因子 {factor} 分析失败: {e}")
                            continue
            else:
                # CPU计算 (小批量或无GPU)
                for factor in factor_columns:
                    try:
                        result = self._analyze_single_factor(
                            merged_data, factor, return_col
                        )
                        if result:
                            results[factor] = result
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ 因子 {factor} 分析失败: {e}")
                        continue
            
            self.logger.info(f"✅ 因子IC计算完成，有效因子: {len(results)}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 因子IC计算失败: {e}")
            return {}
    
    def _analyze_single_factor(self, 
                              data: pd.DataFrame, 
                              factor_name: str, 
                              return_col: str) -> Optional[FactorAnalysisResult]:
        """
        分析单个因子
        
        Args:
            data: 合并的数据
            factor_name: 因子名称
            return_col: 收益率列名
            
        Returns:
            因子分析结果
        """
        try:
            # 获取有效数据
            valid_data = data[[factor_name, return_col]].dropna()
            
            if len(valid_data) < 30:  # 最少需要30个观测值
                return None
            
            factor_values = valid_data[factor_name]
            return_values = valid_data[return_col]
            
            # 计算IC指标
            ic_corr, ic_pvalue = pearsonr(factor_values, return_values)
            rank_ic, _ = spearmanr(factor_values, return_values)
            
            # 时间序列IC分析
            ic_series = self._calculate_rolling_ic(data, factor_name, return_col)
            
            if len(ic_series) < 10:
                return None
            
            ic_mean = np.mean(ic_series)
            ic_std = np.std(ic_series)
            ic_ir = ic_mean / ic_std if ic_std > 0 else 0
            
            # t检验
            t_stat, p_value = stats.ttest_1samp(ic_series, 0)
            significance = p_value < 0.05
            
            # 计算其他指标
            turnover = self._calculate_factor_turnover(data, factor_name)
            sharpe_ratio = self._calculate_factor_sharpe(ic_series)
            max_drawdown = self._calculate_max_drawdown(ic_series)
            
            return FactorAnalysisResult(
                factor_name=factor_name,
                ic_mean=ic_mean,
                ic_std=ic_std,
                ic_ir=ic_ir,
                rank_ic=rank_ic,
                t_stat=t_stat,
                p_value=p_value,
                significance=significance,
                turnover=turnover,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                analysis_date=datetime.now(),
                sample_size=len(valid_data)
            )
            
        except Exception as e:
            self.logger.error(f"❌ 因子 {factor_name} 分析失败: {e}")
            return None
    
    def _calculate_rolling_ic(self, 
                             data: pd.DataFrame, 
                             factor_name: str, 
                             return_col: str,
                             window: int = 60) -> np.ndarray:
        """计算滚动IC"""
        try:
            # 按日期分组计算每日IC
            daily_ic = []
            dates = data.index.get_level_values(0).unique().sort_values()
            
            for date in dates:
                try:
                    date_data = data.xs(date, level=0)[[factor_name, return_col]].dropna()
                    
                    if len(date_data) < 10:
                        continue
                    
                    ic, _ = pearsonr(date_data[factor_name], date_data[return_col])
                    if not np.isnan(ic):
                        daily_ic.append(ic)
                        
                except Exception:
                    continue
            
            return np.array(daily_ic)
            
        except Exception as e:
            self.logger.error(f"❌ 滚动IC计算失败: {e}")
            return np.array([])
    
    def _calculate_factor_turnover(self, data: pd.DataFrame, factor_name: str) -> float:
        """计算因子换手率"""
        try:
            # 简化的换手率计算
            return 0.3  # 暂时返回固定值
        except:
            return 0.0
    
    def _calculate_factor_sharpe(self, ic_series: np.ndarray) -> float:
        """计算因子夏普比率"""
        try:
            if len(ic_series) == 0:
                return 0.0
            return np.mean(ic_series) / np.std(ic_series) if np.std(ic_series) > 0 else 0.0
        except:
            return 0.0
    
    def _calculate_max_drawdown(self, ic_series: np.ndarray) -> float:
        """计算最大回撤"""
        try:
            if len(ic_series) == 0:
                return 0.0
            
            cumulative = np.cumsum(ic_series)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max)
            return float(np.min(drawdown))
        except:
            return 0.0
    
    def rank_factors(self, 
                    analysis_results: Dict[str, FactorAnalysisResult],
                    ranking_method: str = 'ic_ir') -> List[Tuple[str, FactorAnalysisResult]]:
        """
        因子排序
        
        Args:
            analysis_results: 因子分析结果
            ranking_method: 排序方法 (ic_ir, ic_mean, significance)
            
        Returns:
            排序后的因子列表
        """
        try:
            if ranking_method == 'ic_ir':
                sorted_factors = sorted(
                    analysis_results.items(),
                    key=lambda x: abs(x[1].ic_ir),
                    reverse=True
                )
            elif ranking_method == 'ic_mean':
                sorted_factors = sorted(
                    analysis_results.items(),
                    key=lambda x: abs(x[1].ic_mean),
                    reverse=True
                )
            elif ranking_method == 'significance':
                # 先按显著性排序，再按IC_IR排序
                sorted_factors = sorted(
                    analysis_results.items(),
                    key=lambda x: (x[1].significance, abs(x[1].ic_ir)),
                    reverse=True
                )
            else:
                sorted_factors = list(analysis_results.items())
            
            self.logger.info(f"📊 因子排序完成，方法: {ranking_method}, 因子数: {len(sorted_factors)}")
            return sorted_factors
            
        except Exception as e:
            self.logger.error(f"❌ 因子排序失败: {e}")
            return list(analysis_results.items())
    
    def run_factor_analysis(self, 
                           start_date: str = None, 
                           end_date: str = None) -> Dict[str, Any]:
        """
        运行完整的因子分析流程
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            分析结果字典
        """
        try:
            self.logger.info("🚀 开始运行完整因子分析流程")
            
            # 使用配置中的默认日期
            if start_date is None:
                start_date = self.config['data_config']['train_period']['start_date']
            if end_date is None:
                end_date = self.config['data_config']['train_period']['end_date']
            
            # 1. 加载A500成分股
            stock_codes = self.load_a500_universe()
            if not stock_codes:
                raise ValueError("未能加载A500成分股")
            
            # 2. 加载因子数据
            factor_data = self.load_factor_data(stock_codes, start_date, end_date)
            if factor_data.empty:
                raise ValueError("未能加载因子数据")
            
            # 3. 计算前瞻收益率
            return_data = self.calculate_forward_returns(stock_codes, start_date, end_date)
            if return_data.empty:
                raise ValueError("未能计算前瞻收益率")
            
            # 4. 计算因子IC指标
            forward_periods = self.config['data_config']['forward_returns']
            all_results = {}
            
            for period in forward_periods:
                self.logger.info(f"📊 分析 {period} 天前瞻收益率")
                period_results = self.calculate_factor_ic(factor_data, return_data, period)
                all_results[f'{period}d'] = period_results
            
            # 5. 因子排序
            ranking_results = {}
            for period, results in all_results.items():
                ranking_results[period] = self.rank_factors(results)
            
            # 6. 保存结果
            self.analysis_results = {
                'factor_analysis': all_results,
                'factor_ranking': ranking_results,
                'metadata': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'stock_count': len(stock_codes),
                    'factor_count': len(self.factor_fields),
                    'analysis_date': datetime.now().isoformat()
                }
            }
            
            self.logger.info("✅ 因子分析流程完成")
            return self.analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ 因子分析流程失败: {e}")
            return {}
    
    def get_top_factors(self, 
                       period: str = '20d', 
                       top_k: int = 50) -> List[str]:
        """
        获取Top因子列表
        
        Args:
            period: 收益率周期
            top_k: 取前K个因子
            
        Returns:
            Top因子名称列表
        """
        try:
            if not self.analysis_results:
                self.logger.warning("⚠️ 请先运行因子分析")
                return []
            
            ranking = self.analysis_results.get('factor_ranking', {}).get(period, [])
            top_factors = [name for name, _ in ranking[:top_k]]
            
            self.logger.info(f"📊 获取Top{top_k}因子: {period}周期")
            return top_factors
            
        except Exception as e:
            self.logger.error(f"❌ 获取Top因子失败: {e}")
            return []


    def _calculate_custom_factors(self, base_data: pd.DataFrame, stock_codes: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """
        计算自定义衍生因子
        
        Args:
            base_data: 基础因子数据（包含OHLCV和技术指标）
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            自定义因子数据DataFrame
        """
        if not self.custom_factor_calculator:
            self.logger.warning("⚠️ 自定义因子计算器未初始化，跳过自定义因子计算")
            return pd.DataFrame()
        
        try:
            custom_data_list = []
            
            # 为每只股票计算自定义因子
            for stock_code in stock_codes:
                # 获取该股票的数据 (索引是 [trade_date, stock_code])
                try:
                    stock_data = base_data.xs(stock_code, level='stock_code')
                except KeyError:
                    self.logger.debug(f"📊 股票{stock_code}在当前时间段数据不存在，跳过自定义因子计算")
                    continue
                
                if stock_data.empty:
                    continue
                
                # 确保有必要的OHLCV字段
                required_fields = ['open', 'high', 'low', 'close', 'vol']
                if not all(field in stock_data.columns for field in required_fields):
                    self.logger.warning(f"⚠️ 股票{stock_code}缺少必要的OHLCV字段，跳过自定义因子计算")
                    continue
                
                # 计算自定义因子
                custom_factors = self.custom_factor_calculator.calculate_all_custom_factors(stock_data)
                
                if custom_factors.empty:
                    continue
                
                # 重建MultiIndex: [trade_date, stock_code]
                custom_factors['stock_code'] = stock_code
                custom_factors = custom_factors.reset_index()
                custom_factors = custom_factors.set_index(['trade_date', 'stock_code'])
                
                custom_data_list.append(custom_factors)
            
            if custom_data_list:
                # 合并所有股票的自定义因子数据
                custom_data = pd.concat(custom_data_list, axis=0)
                successful_stocks = len(custom_data_list)
                missing_stocks = len(stock_codes) - successful_stocks
                self.logger.info(f"🔧 自定义因子计算完成: {custom_data.shape[1]}个因子，{successful_stocks}只股票成功")
                if missing_stocks > 0:
                    self.logger.debug(f"📊 数据统计: {missing_stocks}只股票在当前时间段无数据 (总共{len(stock_codes)}只)")
                return custom_data
            else:
                self.logger.warning("⚠️ 没有计算出任何自定义因子")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"❌ 自定义因子计算失败: {e}")
            return pd.DataFrame()
    
    def _basic_data_cleanup(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基本数据清理，不包含标准化
        
        Args:
            df: 原始数据DataFrame
            
        Returns:
            清理后的DataFrame
        """
        try:
            # 转换日期格式
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'].astype(str), format='%Y%m%d')
            
            # 设置MultiIndex
            if 'trade_date' in df.columns and 'stock_code' in df.columns:
                df = df.set_index(['trade_date', 'stock_code'])
            
            # 转换数值类型
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 删除完全为空的列
            df = df.dropna(how='all', axis=1)
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 基本数据清理失败: {e}")
            return df

