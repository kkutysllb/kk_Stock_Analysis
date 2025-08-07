#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子选择器 - 基于机器学习的智能因子选择
结合统计方法和机器学习算法，从261个技术因子中筛选出最有效的预测因子
"""

import os
import sys
import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
import yaml
import logging
from dataclasses import dataclass
import json

# 机器学习库
from sklearn.feature_selection import (
    SelectKBest, SelectPercentile, SelectFpr, SelectFdr, SelectFwe,
    RFE, RFECV, SelectFromModel, VarianceThreshold
)
from sklearn.feature_selection import (
    f_regression, mutual_info_regression, chi2, f_classif
)
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import LassoCV, RidgeCV, ElasticNetCV
from sklearn.svm import SVR
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb

# 统计库
from scipy import stats
from scipy.stats import normaltest, jarque_bera
import seaborn as sns
import matplotlib.pyplot as plt

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from qlib_quantitative.factor_mining.core.factor_analyzer import FactorAnalyzer, FactorAnalysisResult

warnings.filterwarnings('ignore')

@dataclass
class FactorSelectionResult:
    """因子选择结果数据类"""
    method: str
    selected_factors: List[str]
    factor_scores: Dict[str, float]
    selection_metrics: Dict[str, float]
    cross_val_score: float
    feature_importance: Optional[Dict[str, float]]
    selection_date: datetime
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'method': self.method,
            'selected_factors': self.selected_factors,
            'factor_scores': self.factor_scores,
            'selection_metrics': self.selection_metrics,
            'cross_val_score': self.cross_val_score,
            'feature_importance': self.feature_importance,
            'selection_date': self.selection_date.isoformat()
        }


class FactorSelector:
    """
    因子选择器
    
    主要功能：
    1. 基于统计指标的因子筛选
    2. 基于机器学习的因子选择
    3. 多种选择算法的集成
    4. 因子重要性评估
    5. 因子稳定性验证
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化因子选择器
        
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
            self.logger.info(f"✅ 配置文件加载成功")
        except Exception as e:
            self.logger.error(f"❌ 配置文件加载失败: {e}")
            raise
        
        # 初始化组件
        self.factor_analyzer = FactorAnalyzer(config_path)
        self.selection_results = {}
        self.selected_factors = []
        
        self.logger.info("🚀 因子选择器初始化完成")
    
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
    
    def statistical_factor_selection(self, 
                                   factor_analysis_results: Dict[str, FactorAnalysisResult],
                                   selection_criteria: Dict[str, Any] = None) -> FactorSelectionResult:
        """
        基于统计指标的因子选择
        
        Args:
            factor_analysis_results: 因子分析结果
            selection_criteria: 选择标准
            
        Returns:
            因子选择结果
        """
        try:
            self.logger.info("📊 开始统计因子选择")
            
            # 默认选择标准
            if selection_criteria is None:
                selection_criteria = {
                    'min_ic_ir': 0.5,      # 最小IC_IR
                    'min_ic_mean': 0.02,   # 最小IC均值
                    'max_p_value': 0.05,   # 最大p值
                    'min_significance': True, # 必须显著
                    'top_k': 50            # 选择前K个
                }
            
            selected_factors = []
            factor_scores = {}
            
            # 筛选条件
            for factor_name, result in factor_analysis_results.items():
                # IC_IR筛选
                if abs(result.ic_ir) < selection_criteria.get('min_ic_ir', 0):
                    continue
                
                # IC均值筛选  
                if abs(result.ic_mean) < selection_criteria.get('min_ic_mean', 0):
                    continue
                
                # 显著性筛选
                if selection_criteria.get('min_significance', False) and not result.significance:
                    continue
                
                # p值筛选
                if result.p_value > selection_criteria.get('max_p_value', 1.0):
                    continue
                
                # 计算综合得分
                score = abs(result.ic_ir) * 0.4 + abs(result.ic_mean) * 0.3 + \
                       result.sharpe_ratio * 0.2 + (1 - result.p_value) * 0.1
                
                selected_factors.append(factor_name)
                factor_scores[factor_name] = score
            
            # 按得分排序，选择Top K
            top_k = selection_criteria.get('top_k', len(selected_factors))
            sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
            
            final_factors = [name for name, score in sorted_factors[:top_k]]
            final_scores = {name: score for name, score in sorted_factors[:top_k]}
            
            # 计算选择指标
            selection_metrics = {
                'total_factors': len(factor_analysis_results),
                'passed_criteria': len(selected_factors),
                'final_selected': len(final_factors),
                'selection_ratio': len(final_factors) / len(factor_analysis_results),
                'avg_ic_ir': np.mean([factor_analysis_results[f].ic_ir for f in final_factors]),
                'avg_ic_mean': np.mean([factor_analysis_results[f].ic_mean for f in final_factors]),
                'significant_ratio': sum([factor_analysis_results[f].significance for f in final_factors]) / len(final_factors)
            }
            
            result = FactorSelectionResult(
                method='statistical',
                selected_factors=final_factors,
                factor_scores=final_scores,
                selection_metrics=selection_metrics,
                cross_val_score=0.0,  # 统计方法不需要交叉验证
                feature_importance=None,
                selection_date=datetime.now()
            )
            
            self.logger.info(f"✅ 统计因子选择完成: {len(final_factors)}个因子")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 统计因子选择失败: {e}")
            return FactorSelectionResult(
                method='statistical',
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def ml_factor_selection(self, 
                          X: pd.DataFrame, 
                          y: pd.Series,
                          method: str = 'rfecv',
                          n_features: int = 50) -> FactorSelectionResult:
        """
        基于机器学习的因子选择
        
        Args:
            X: 因子数据
            y: 目标变量
            method: 选择方法 (rfecv, selectkbest, lasso, xgboost, etc.)
            n_features: 选择的因子数量
            
        Returns:
            因子选择结果
        """
        try:
            self.logger.info(f"🤖 开始机器学习因子选择: {method}")
            
            if X.empty or y.empty:
                raise ValueError("输入数据为空")
            
            # 数据预处理
            X_clean, y_clean = self._clean_data_for_ml(X, y)
            
            if len(X_clean) < 100:
                self.logger.warning("⚠️ 样本数量过少，可能影响选择效果")
            
            # 根据方法选择因子
            if method == 'rfecv':
                result = self._rfecv_selection(X_clean, y_clean, n_features)
            elif method == 'selectkbest':
                result = self._selectkbest_selection(X_clean, y_clean, n_features)
            elif method == 'lasso':
                result = self._lasso_selection(X_clean, y_clean, n_features)
            elif method == 'xgboost':
                result = self._xgboost_selection(X_clean, y_clean, n_features)
            elif method == 'lightgbm':
                result = self._lightgbm_selection(X_clean, y_clean, n_features)
            elif method == 'random_forest':
                result = self._random_forest_selection(X_clean, y_clean, n_features)
            elif method == 'mutual_info':
                result = self._mutual_info_selection(X_clean, y_clean, n_features)
            else:
                raise ValueError(f"不支持的选择方法: {method}")
            
            self.logger.info(f"✅ {method} 因子选择完成: {len(result.selected_factors)}个因子")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 机器学习因子选择失败: {e}")
            return FactorSelectionResult(
                method=method,
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def _clean_data_for_ml(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """清理机器学习数据"""
        # 移除缺失值
        valid_idx = y.notna() & X.notna().all(axis=1)
        X_clean = X[valid_idx].copy()
        y_clean = y[valid_idx].copy()
        
        # 移除无变化的特征
        var_threshold = VarianceThreshold(threshold=0.01)
        X_clean = pd.DataFrame(
            var_threshold.fit_transform(X_clean),
            columns=X_clean.columns[var_threshold.get_support()],
            index=X_clean.index
        )
        
        return X_clean, y_clean
    
    def _rfecv_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> FactorSelectionResult:
        """递归特征消除交叉验证"""
        try:
            # 使用随机森林作为基础估计器
            estimator = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
            
            # RFECV
            selector = RFECV(
                estimator=estimator,
                min_features_to_select=min(n_features, len(X.columns)),
                cv=5,
                scoring='neg_mean_squared_error',
                n_jobs=-1
            )
            
            X_selected = selector.fit_transform(X, y)
            selected_features = X.columns[selector.support_].tolist()
            
            # 计算特征重要性
            feature_importance = {}
            if hasattr(selector.estimator_, 'feature_importances_'):
                importances = selector.estimator_.feature_importances_
                for i, feature in enumerate(selected_features):
                    feature_importance[feature] = float(importances[i])
            
            # 交叉验证得分
            cv_scores = cross_val_score(estimator, X_selected, y, cv=5, scoring='neg_mean_squared_error')
            cv_score = float(-np.mean(cv_scores))
            
            # 因子得分（使用重要性）
            factor_scores = feature_importance.copy()
            
            # 选择指标
            selection_metrics = {
                'optimal_features': int(selector.n_features_),
                'cv_score': cv_score,
                'cv_std': float(np.std(cv_scores))
            }
            
            return FactorSelectionResult(
                method='rfecv',
                selected_factors=selected_features,
                factor_scores=factor_scores,
                selection_metrics=selection_metrics,
                cross_val_score=cv_score,
                feature_importance=feature_importance,
                selection_date=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ RFECV选择失败: {e}")
            return FactorSelectionResult(
                method='rfecv',
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def _selectkbest_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> FactorSelectionResult:
        """SelectKBest特征选择"""
        try:
            # 使用f_regression评分函数
            selector = SelectKBest(score_func=f_regression, k=min(n_features, len(X.columns)))
            X_selected = selector.fit_transform(X, y)
            
            selected_features = X.columns[selector.get_support()].tolist()
            scores = selector.scores_
            
            # 因子得分
            factor_scores = {}
            for i, feature in enumerate(selected_features):
                idx = X.columns.get_loc(feature)
                factor_scores[feature] = float(scores[idx])
            
            # 交叉验证
            estimator = RandomForestRegressor(n_estimators=50, random_state=42)
            cv_scores = cross_val_score(estimator, X_selected, y, cv=5, scoring='neg_mean_squared_error')
            cv_score = float(-np.mean(cv_scores))
            
            selection_metrics = {
                'avg_score': float(np.mean(scores)),
                'cv_score': cv_score
            }
            
            return FactorSelectionResult(
                method='selectkbest',
                selected_factors=selected_features,
                factor_scores=factor_scores,
                selection_metrics=selection_metrics,
                cross_val_score=cv_score,
                feature_importance=None,
                selection_date=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ SelectKBest选择失败: {e}")
            return FactorSelectionResult(
                method='selectkbest',
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def _lasso_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> FactorSelectionResult:
        """Lasso回归特征选择"""
        try:
            # LassoCV
            lasso = LassoCV(cv=5, random_state=42, n_jobs=-1, max_iter=1000)
            lasso.fit(X, y)
            
            # 获取非零系数的特征
            non_zero_coef = np.abs(lasso.coef_) > 1e-5
            selected_features = X.columns[non_zero_coef].tolist()
            
            # 如果选择的特征太多，按系数绝对值排序选择top n
            if len(selected_features) > n_features:
                coef_abs = np.abs(lasso.coef_[non_zero_coef])
                sorted_idx = np.argsort(coef_abs)[::-1][:n_features]
                selected_features = [selected_features[i] for i in sorted_idx]
            
            # 因子得分（系数绝对值）
            factor_scores = {}
            for feature in selected_features:
                idx = X.columns.get_loc(feature)
                factor_scores[feature] = float(np.abs(lasso.coef_[idx]))
            
            # 交叉验证得分
            cv_score = float(-lasso.score(X[selected_features], y))
            
            selection_metrics = {
                'alpha': float(lasso.alpha_),
                'n_iter': int(lasso.n_iter_),
                'cv_score': cv_score
            }
            
            return FactorSelectionResult(
                method='lasso',
                selected_factors=selected_features,
                factor_scores=factor_scores,
                selection_metrics=selection_metrics,
                cross_val_score=cv_score,
                feature_importance=None,
                selection_date=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Lasso选择失败: {e}")
            return FactorSelectionResult(
                method='lasso',
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def _xgboost_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> FactorSelectionResult:
        """XGBoost特征选择"""
        try:
            # XGBoost模型
            xgb_model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
            
            xgb_model.fit(X, y)
            
            # 获取特征重要性
            importance = xgb_model.feature_importances_
            feature_importance = dict(zip(X.columns, importance))
            
            # 选择top n特征
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            selected_features = [name for name, score in sorted_features[:n_features]]
            factor_scores = {name: float(score) for name, score in sorted_features[:n_features]}
            
            # 交叉验证
            cv_scores = cross_val_score(xgb_model, X[selected_features], y, cv=5, scoring='neg_mean_squared_error')
            cv_score = float(-np.mean(cv_scores))
            
            selection_metrics = {
                'avg_importance': float(np.mean(importance)),
                'cv_score': cv_score
            }
            
            return FactorSelectionResult(
                method='xgboost',
                selected_factors=selected_features,
                factor_scores=factor_scores,
                selection_metrics=selection_metrics,
                cross_val_score=cv_score,
                feature_importance=feature_importance,
                selection_date=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ XGBoost选择失败: {e}")
            return FactorSelectionResult(
                method='xgboost',
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def _lightgbm_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> FactorSelectionResult:
        """LightGBM特征选择"""
        try:
            # LightGBM模型
            lgb_model = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
            
            lgb_model.fit(X, y)
            
            # 获取特征重要性
            importance = lgb_model.feature_importances_
            feature_importance = dict(zip(X.columns, importance))
            
            # 选择top n特征
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            selected_features = [name for name, score in sorted_features[:n_features]]
            factor_scores = {name: float(score) for name, score in sorted_features[:n_features]}
            
            # 交叉验证
            cv_scores = cross_val_score(lgb_model, X[selected_features], y, cv=5, scoring='neg_mean_squared_error')
            cv_score = float(-np.mean(cv_scores))
            
            selection_metrics = {
                'avg_importance': float(np.mean(importance)),
                'cv_score': cv_score
            }
            
            return FactorSelectionResult(
                method='lightgbm',
                selected_factors=selected_features,
                factor_scores=factor_scores,
                selection_metrics=selection_metrics,
                cross_val_score=cv_score,
                feature_importance=feature_importance,
                selection_date=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ LightGBM选择失败: {e}")
            return FactorSelectionResult(
                method='lightgbm',
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def _random_forest_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> FactorSelectionResult:
        """随机森林特征选择"""
        try:
            # 随机森林模型
            rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            rf_model.fit(X, y)
            
            # 获取特征重要性
            importance = rf_model.feature_importances_
            feature_importance = dict(zip(X.columns, importance))
            
            # 选择top n特征
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            selected_features = [name for name, score in sorted_features[:n_features]]
            factor_scores = {name: float(score) for name, score in sorted_features[:n_features]}
            
            # 交叉验证
            cv_scores = cross_val_score(rf_model, X[selected_features], y, cv=5, scoring='neg_mean_squared_error')
            cv_score = float(-np.mean(cv_scores))
            
            selection_metrics = {
                'avg_importance': float(np.mean(importance)),
                'cv_score': cv_score
            }
            
            return FactorSelectionResult(
                method='random_forest',
                selected_factors=selected_features,
                factor_scores=factor_scores,
                selection_metrics=selection_metrics,
                cross_val_score=cv_score,
                feature_importance=feature_importance,
                selection_date=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ 随机森林选择失败: {e}")
            return FactorSelectionResult(
                method='random_forest',
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def _mutual_info_selection(self, X: pd.DataFrame, y: pd.Series, n_features: int) -> FactorSelectionResult:
        """互信息特征选择"""
        try:
            # 计算互信息
            mutual_info_scores = mutual_info_regression(X, y, random_state=42)
            
            # 选择top n特征
            feature_scores = dict(zip(X.columns, mutual_info_scores))
            sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
            selected_features = [name for name, score in sorted_features[:n_features]]
            factor_scores = {name: float(score) for name, score in sorted_features[:n_features]}
            
            # 交叉验证
            estimator = RandomForestRegressor(n_estimators=50, random_state=42)
            cv_scores = cross_val_score(estimator, X[selected_features], y, cv=5, scoring='neg_mean_squared_error')
            cv_score = float(-np.mean(cv_scores))
            
            selection_metrics = {
                'avg_mutual_info': float(np.mean(mutual_info_scores)),
                'cv_score': cv_score
            }
            
            return FactorSelectionResult(
                method='mutual_info',
                selected_factors=selected_features,
                factor_scores=factor_scores,
                selection_metrics=selection_metrics,
                cross_val_score=cv_score,
                feature_importance=None,
                selection_date=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ 互信息选择失败: {e}")
            return FactorSelectionResult(
                method='mutual_info',
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def ensemble_factor_selection(self, 
                                 X: pd.DataFrame, 
                                 y: pd.Series,
                                 methods: List[str] = None,
                                 n_features: int = 50,
                                 vote_threshold: float = 0.3) -> FactorSelectionResult:
        """
        集成因子选择
        
        Args:
            X: 因子数据
            y: 目标变量
            methods: 选择方法列表
            n_features: 选择的因子数量
            vote_threshold: 投票阈值
            
        Returns:
            集成选择结果
        """
        try:
            self.logger.info("🎯 开始集成因子选择")
            
            if methods is None:
                methods = ['xgboost', 'lightgbm', 'random_forest', 'lasso', 'selectkbest']
            
            # 运行各种方法
            method_results = {}
            for method in methods:
                try:
                    result = self.ml_factor_selection(X, y, method, n_features * 2)  # 选择更多候选
                    method_results[method] = result
                    self.logger.info(f"  ✅ {method}: {len(result.selected_factors)}个因子")
                except Exception as e:
                    self.logger.warning(f"  ⚠️ {method} 失败: {e}")
                    continue
            
            if not method_results:
                raise ValueError("所有方法都失败了")
            
            # 统计投票结果
            factor_votes = {}
            factor_scores_sum = {}
            
            for method, result in method_results.items():
                for factor in result.selected_factors:
                    factor_votes[factor] = factor_votes.get(factor, 0) + 1
                    factor_scores_sum[factor] = factor_scores_sum.get(factor, 0) + \
                                              result.factor_scores.get(factor, 0)
            
            # 计算投票比例和平均得分
            n_methods = len(method_results)
            factor_vote_ratios = {f: votes/n_methods for f, votes in factor_votes.items()}
            factor_avg_scores = {f: score/factor_votes[f] for f, score in factor_scores_sum.items()}
            
            # 按投票比例和平均得分筛选
            qualified_factors = []
            for factor, vote_ratio in factor_vote_ratios.items():
                if vote_ratio >= vote_threshold:
                    qualified_factors.append((factor, vote_ratio, factor_avg_scores[factor]))
            
            # 排序选择
            qualified_factors.sort(key=lambda x: (x[1], x[2]), reverse=True)
            selected_factors = [f[0] for f in qualified_factors[:n_features]]
            
            # 最终得分
            final_scores = {}
            for factor, vote_ratio, avg_score in qualified_factors[:n_features]:
                final_scores[factor] = vote_ratio * 0.7 + (avg_score / max(factor_avg_scores.values())) * 0.3
            
            # 交叉验证最终结果
            estimator = RandomForestRegressor(n_estimators=100, random_state=42)
            cv_scores = cross_val_score(estimator, X[selected_factors], y, cv=5, scoring='neg_mean_squared_error')
            cv_score = float(-np.mean(cv_scores))
            
            # 选择指标
            selection_metrics = {
                'n_methods': n_methods,
                'vote_threshold': vote_threshold,
                'qualified_factors': len(qualified_factors),
                'final_selected': len(selected_factors),
                'avg_vote_ratio': np.mean([f[1] for f in qualified_factors[:n_features]]),
                'cv_score': cv_score
            }
            
            result = FactorSelectionResult(
                method='ensemble',
                selected_factors=selected_factors,
                factor_scores=final_scores,
                selection_metrics=selection_metrics,
                cross_val_score=cv_score,
                feature_importance=None,
                selection_date=datetime.now()
            )
            
            self.logger.info(f"✅ 集成因子选择完成: {len(selected_factors)}个因子")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 集成因子选择失败: {e}")
            return FactorSelectionResult(
                method='ensemble',
                selected_factors=[],
                factor_scores={},
                selection_metrics={},
                cross_val_score=0.0,
                feature_importance=None,
                selection_date=datetime.now()
            )
    
    def run_comprehensive_selection(self, 
                                  start_date: str = None,
                                  end_date: str = None,
                                  return_period: int = 20) -> Dict[str, FactorSelectionResult]:
        """
        运行全面的因子选择流程
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            return_period: 收益率周期
            
        Returns:
            选择结果字典
        """
        try:
            self.logger.info("🚀 开始全面因子选择流程")
            
            # 1. 运行因子分析
            analysis_results = self.factor_analyzer.run_factor_analysis(start_date, end_date)
            if not analysis_results:
                raise ValueError("因子分析失败")
            
            # 2. 获取因子分析结果
            period_key = f'{return_period}d'
            factor_analysis = analysis_results['factor_analysis'].get(period_key, {})
            
            if not factor_analysis:
                # 如果当前周期没有结果，尝试使用其他周期的结果
                self.logger.warning(f"⚠️ 未找到{return_period}天周期的因子分析结果，尝试使用其他周期")
                
                # 查找可用的周期
                available_periods = [k for k, v in analysis_results['factor_analysis'].items() if v]
                if available_periods:
                    period_key = available_periods[0]  # 使用第一个可用周期
                    factor_analysis = analysis_results['factor_analysis'][period_key]
                    self.logger.info(f"✅ 使用{period_key}周期的因子分析结果")
                else:
                    raise ValueError(f"所有周期都没有有效的因子分析结果")
            
            # 3. 统计因子选择
            statistical_result = self.statistical_factor_selection(factor_analysis)
            
            # 4. 准备机器学习数据
            # 加载A500成分股
            stock_codes = self.factor_analyzer.load_a500_universe()
            
            # 使用配置中的默认日期
            if start_date is None:
                start_date = self.config['data_config']['train_period']['start_date']
            if end_date is None:
                end_date = self.config['data_config']['train_period']['end_date']
                
            # 加载因子数据
            factor_data = self.factor_analyzer.load_factor_data(stock_codes, start_date, end_date)
            return_data = self.factor_analyzer.calculate_forward_returns(stock_codes, start_date, end_date)
            
            if factor_data.empty or return_data.empty:
                raise ValueError("无法加载机器学习数据")
            
            # 合并数据
            return_col = f'return_{return_period}d'
            merged_data = factor_data.join(return_data[return_col], how='inner')
            
            X = merged_data[self.factor_analyzer.factor_fields].dropna()
            y = merged_data[return_col].loc[X.index]
            
            # 5. 集成机器学习选择
            ensemble_result = self.ensemble_factor_selection(X, y, n_features=50)
            
            # 6. 保存结果
            results = {
                'statistical': statistical_result,
                'ensemble': ensemble_result
            }
            
            self.selection_results = results
            
            # 7. 选择最佳结果作为最终结果
            if ensemble_result.cross_val_score > 0:
                self.selected_factors = ensemble_result.selected_factors
            else:
                self.selected_factors = statistical_result.selected_factors
            
            self.logger.info(f"✅ 全面因子选择完成，最终选择{len(self.selected_factors)}个因子")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 全面因子选择失败: {e}")
            return {}
    
    def get_selected_factors(self, method: str = 'best') -> List[str]:
        """
        获取选择的因子
        
        Args:
            method: 选择方法 ('best', 'statistical', 'ensemble')
            
        Returns:
            选择的因子列表
        """
        try:
            if method == 'best':
                return self.selected_factors
            elif method in self.selection_results:
                return self.selection_results[method].selected_factors
            else:
                self.logger.warning(f"⚠️ 方法 {method} 不存在，返回默认结果")
                return self.selected_factors
                
        except Exception as e:
            self.logger.error(f"❌ 获取选择因子失败: {e}")
            return []


if __name__ == "__main__":
    # 测试代码
    print("🚀 测试因子选择器...")
    
    try:
        selector = FactorSelector()
        
        # 运行全面选择
        results = selector.run_comprehensive_selection(
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        if results:
            print("✅ 因子选择测试成功")
            
            # 获取选择的因子
            selected_factors = selector.get_selected_factors()
            print(f"📊 最终选择因子: {len(selected_factors)}个")
            print(f"前10个因子: {selected_factors[:10]}")
        else:
            print("❌ 因子选择测试失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()