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
        
        # 因子列表 - 从数据库字段分析文件中获取
        self.factor_fields = self._load_factor_fields()
        
        self.logger.info(f"🚀 因子分析器初始化完成，共{len(self.factor_fields)}个技术因子")
    
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
        加载261个技术因子字段列表
        从stock_factor_pro_fields_analysis.json中获取
        """
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
            
            self.logger.info(f"📊 加载技术因子字段: {len(factor_fields)}个")
            return factor_fields
            
        except Exception as e:
            self.logger.error(f"❌ 因子字段加载失败: {e}")
            # 使用配置文件中的备用因子列表
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
            
            collection = self.db_handler.get_collection('stock_factor_pro')
            
            # 批量查询
            all_data = []
            batch_size = 50
            
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
            
            self.logger.info(f"✅ 因子数据加载完成: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 因子数据加载失败: {e}")
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
            
            # 设置索引
            # 处理日期格式：YYYYMMDD -> YYYY-MM-DD
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
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
            
            # 标准化
            factor_columns = [col for col in df.columns if col in self.factor_fields]
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
            factor_columns = [col for col in factor_data.columns if col in self.factor_fields]
            
            # 合并数据
            merged_data = factor_data.join(return_data[return_col], how='inner')
            
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


if __name__ == "__main__":
    # 测试代码
    print("🚀 测试因子分析器...")
    
    try:
        analyzer = FactorAnalyzer()
        
        # 运行因子分析
        results = analyzer.run_factor_analysis(
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        if results:
            print("✅ 因子分析测试成功")
            
            # 获取Top20因子
            top_factors = analyzer.get_top_factors(period='20d', top_k=20)
            print(f"📊 Top20因子: {top_factors}")
        else:
            print("❌ 因子分析测试失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()