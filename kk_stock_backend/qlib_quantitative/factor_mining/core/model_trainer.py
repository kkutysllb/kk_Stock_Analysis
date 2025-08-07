#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型训练器 - 基于选择因子的预测模型训练
支持多种机器学习算法，实现模型集成和超参数优化
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
import pickle
import joblib
from dataclasses import dataclass, asdict
import json

# 机器学习库
from sklearn.ensemble import (
    RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor,
    VotingRegressor, StackingRegressor, BaggingRegressor
)
from sklearn.linear_model import (
    LinearRegression, Ridge, Lasso, ElasticNet, 
    RidgeCV, LassoCV, ElasticNetCV
)
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV, 
    RandomizedSearchCV, TimeSeriesSplit
)
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    mean_absolute_percentage_error
)
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# 高级机器学习库
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor

# Optuna超参数优化
try:
    import optuna
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

# 深度学习库
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from qlib_quantitative.factor_mining.core.factor_selector import FactorSelector
from api.global_db import db_handler

warnings.filterwarnings('ignore')

@dataclass
class ModelResult:
    """模型结果数据类"""
    model_name: str
    model_type: str
    selected_factors: List[str]
    train_metrics: Dict[str, float]
    val_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]]
    hyperparameters: Dict[str, Any]
    cross_val_score: float
    model_path: Optional[str]
    training_date: datetime
    training_time: float
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        result = asdict(self)
        result['training_date'] = self.training_date.isoformat()
        return result


class ModelTrainer:
    """
    模型训练器
    
    主要功能：
    1. 多种机器学习算法支持
    2. 超参数自动优化
    3. 时间序列交叉验证
    4. 模型集成和Stacking
    5. 模型持久化和管理
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化模型训练器
        
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
        self.factor_selector = FactorSelector(config_path)
        self.db_handler = db_handler
        
        # 模型存储
        self.trained_models = {}
        self.model_results = {}
        
        # 创建模型存储目录
        model_path = self.config['storage_config']['model_storage']['path']
        os.makedirs(model_path, exist_ok=True)
        
        self.logger.info("🚀 模型训练器初始化完成")
    
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
    
    def prepare_training_data(self, 
                            selected_factors: List[str],
                            start_date: str = None,
                            end_date: str = None,
                            return_period: int = 20,
                            test_size: float = 0.2,
                            val_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, 
                                                           pd.Series, pd.Series, pd.Series]:
        """
        准备训练数据
        
        Args:
            selected_factors: 选择的因子列表
            start_date: 开始日期
            end_date: 结束日期
            return_period: 收益率周期
            test_size: 测试集比例
            val_size: 验证集比例
            
        Returns:
            (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        try:
            self.logger.info("📊 开始准备训练数据")
            
            # 使用配置中的默认日期
            if start_date is None:
                start_date = self.config['data_config']['train_period']['start_date']
            if end_date is None:
                end_date = self.config['data_config']['train_period']['end_date']
            
            # 加载A500成分股
            stock_codes = self.factor_selector.factor_analyzer.load_a500_universe()
            
            # 加载因子和收益数据
            factor_data = self.factor_selector.factor_analyzer.load_factor_data(
                stock_codes, start_date, end_date
            )
            return_data = self.factor_selector.factor_analyzer.calculate_forward_returns(
                stock_codes, start_date, end_date
            )
            
            if factor_data.empty or return_data.empty:
                raise ValueError("无法加载数据")
            
            # 选择相关因子
            available_factors = [f for f in selected_factors if f in factor_data.columns]
            if not available_factors:
                raise ValueError("没有可用的选择因子")
            
            self.logger.info(f"可用因子: {len(available_factors)}/{len(selected_factors)}")
            
            # 合并数据
            return_col = f'return_{return_period}d'
            merged_data = factor_data[available_factors].join(return_data[return_col], how='inner')
            merged_data = merged_data.dropna()
            
            if len(merged_data) < 1000:
                self.logger.warning("⚠️ 样本数量较少，可能影响模型效果")
            
            # 特征和目标
            X = merged_data[available_factors]
            y = merged_data[return_col]
            
            # 时间序列划分
            total_samples = len(X)
            train_end = int(total_samples * (1 - test_size - val_size))
            val_end = int(total_samples * (1 - test_size))
            
            X_train = X.iloc[:train_end]
            X_val = X.iloc[train_end:val_end]
            X_test = X.iloc[val_end:]
            
            y_train = y.iloc[:train_end]
            y_val = y.iloc[train_end:val_end]
            y_test = y.iloc[val_end:]
            
            self.logger.info(f"✅ 数据划分完成")
            self.logger.info(f"  训练集: {len(X_train)} 样本")
            self.logger.info(f"  验证集: {len(X_val)} 样本")
            self.logger.info(f"  测试集: {len(X_test)} 样本")
            
            return X_train, X_val, X_test, y_train, y_val, y_test
            
        except Exception as e:
            self.logger.error(f"❌ 数据准备失败: {e}")
            return None, None, None, None, None, None
    
    def train_linear_models(self, 
                          X_train: pd.DataFrame, 
                          y_train: pd.Series,
                          X_val: pd.DataFrame = None,
                          y_val: pd.Series = None) -> Dict[str, ModelResult]:
        """
        训练线性模型
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            X_val: 验证特征
            y_val: 验证目标
            
        Returns:
            模型结果字典
        """
        try:
            self.logger.info("📈 开始训练线性模型")
            results = {}
            
            # 标准化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val) if X_val is not None else None
            
            # 线性回归
            lr = LinearRegression()
            start_time = datetime.now()
            lr.fit(X_train_scaled, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['linear_regression'] = self._evaluate_model(
                lr, X_train_scaled, y_train, X_val_scaled, y_val, 
                'linear_regression', 'linear', X_train.columns.tolist(),
                training_time=training_time, scaler=scaler
            )
            
            # Ridge回归
            ridge = RidgeCV(cv=5, alphas=np.logspace(-6, 2, 50))
            start_time = datetime.now()
            ridge.fit(X_train_scaled, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['ridge'] = self._evaluate_model(
                ridge, X_train_scaled, y_train, X_val_scaled, y_val,
                'ridge', 'linear', X_train.columns.tolist(),
                training_time=training_time, scaler=scaler,
                hyperparams={'alpha': float(ridge.alpha_)}
            )
            
            # Lasso回归
            lasso = LassoCV(cv=5, alphas=np.logspace(-6, 2, 50), max_iter=2000)
            start_time = datetime.now()
            lasso.fit(X_train_scaled, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['lasso'] = self._evaluate_model(
                lasso, X_train_scaled, y_train, X_val_scaled, y_val,
                'lasso', 'linear', X_train.columns.tolist(),
                training_time=training_time, scaler=scaler,
                hyperparams={'alpha': float(lasso.alpha_)}
            )
            
            # ElasticNet回归
            elastic = ElasticNetCV(cv=5, alphas=np.logspace(-6, 2, 20), 
                                 l1_ratio=[0.1, 0.5, 0.7, 0.9], max_iter=2000)
            start_time = datetime.now()
            elastic.fit(X_train_scaled, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['elastic_net'] = self._evaluate_model(
                elastic, X_train_scaled, y_train, X_val_scaled, y_val,
                'elastic_net', 'linear', X_train.columns.tolist(),
                training_time=training_time, scaler=scaler,
                hyperparams={'alpha': float(elastic.alpha_), 'l1_ratio': float(elastic.l1_ratio_)}
            )
            
            self.logger.info(f"✅ 线性模型训练完成: {len(results)}个模型")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 线性模型训练失败: {e}")
            return {}
    
    def train_tree_models(self,
                        X_train: pd.DataFrame,
                        y_train: pd.Series,
                        X_val: pd.DataFrame = None,
                        y_val: pd.Series = None) -> Dict[str, ModelResult]:
        """
        训练树模型
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            X_val: 验证特征
            y_val: 验证目标
            
        Returns:
            模型结果字典
        """
        try:
            self.logger.info("🌳 开始训练树模型")
            results = {}
            
            # 随机森林
            rf = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            start_time = datetime.now()
            rf.fit(X_train, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['random_forest'] = self._evaluate_model(
                rf, X_train, y_train, X_val, y_val,
                'random_forest', 'tree', X_train.columns.tolist(),
                training_time=training_time
            )
            
            # XGBoost
            xgb_model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
            start_time = datetime.now()
            xgb_model.fit(X_train, y_train, 
                         eval_set=[(X_val, y_val)] if X_val is not None else None,
                         verbose=False)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['xgboost'] = self._evaluate_model(
                xgb_model, X_train, y_train, X_val, y_val,
                'xgboost', 'tree', X_train.columns.tolist(),
                training_time=training_time
            )
            
            # LightGBM
            lgb_model = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
            start_time = datetime.now()
            lgb_model.fit(X_train, y_train,
                         eval_set=[(X_val, y_val)] if X_val is not None else None,
                         callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['lightgbm'] = self._evaluate_model(
                lgb_model, X_train, y_train, X_val, y_val,
                'lightgbm', 'tree', X_train.columns.tolist(),
                training_time=training_time
            )
            
            # CatBoost
            try:
                cat_model = CatBoostRegressor(
                    iterations=100,
                    depth=6,
                    learning_rate=0.1,
                    random_seed=42,
                    verbose=False
                )
                start_time = datetime.now()
                cat_model.fit(X_train, y_train,
                             eval_set=(X_val, y_val) if X_val is not None else None,
                             verbose=False)
                training_time = (datetime.now() - start_time).total_seconds()
                
                results['catboost'] = self._evaluate_model(
                    cat_model, X_train, y_train, X_val, y_val,
                    'catboost', 'tree', X_train.columns.tolist(),
                    training_time=training_time
                )
            except Exception as e:
                self.logger.warning(f"⚠️ CatBoost训练失败: {e}")
            
            # 额外树回归器
            et = ExtraTreesRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            start_time = datetime.now()
            et.fit(X_train, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['extra_trees'] = self._evaluate_model(
                et, X_train, y_train, X_val, y_val,
                'extra_trees', 'tree', X_train.columns.tolist(),
                training_time=training_time
            )
            
            self.logger.info(f"✅ 树模型训练完成: {len(results)}个模型")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 树模型训练失败: {e}")
            return {}
    
    def train_neural_models(self,
                          X_train: pd.DataFrame,
                          y_train: pd.Series,
                          X_val: pd.DataFrame = None,
                          y_val: pd.Series = None) -> Dict[str, ModelResult]:
        """
        训练神经网络模型
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            X_val: 验证特征
            y_val: 验证目标
            
        Returns:
            模型结果字典
        """
        try:
            self.logger.info("🧠 开始训练神经网络模型")
            results = {}
            
            # 标准化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val) if X_val is not None else None
            
            # MLP回归器
            mlp = MLPRegressor(
                hidden_layer_sizes=(100, 50),
                activation='relu',
                solver='adam',
                alpha=0.01,
                learning_rate_init=0.001,
                max_iter=500,
                early_stopping=True,
                validation_fraction=0.2,
                random_state=42
            )
            
            start_time = datetime.now()
            mlp.fit(X_train_scaled, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['mlp'] = self._evaluate_model(
                mlp, X_train_scaled, y_train, X_val_scaled, y_val,
                'mlp', 'neural', X_train.columns.tolist(),
                training_time=training_time, scaler=scaler
            )
            
            # PyTorch深度学习模型（如果可用）
            if TORCH_AVAILABLE:
                try:
                    torch_result = self._train_pytorch_model(
                        X_train_scaled, y_train, X_val_scaled, y_val
                    )
                    if torch_result:
                        results['deep_neural'] = torch_result
                except Exception as e:
                    self.logger.warning(f"⚠️ PyTorch模型训练失败: {e}")
            
            self.logger.info(f"✅ 神经网络模型训练完成: {len(results)}个模型")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 神经网络模型训练失败: {e}")
            return {}
    
    def _train_pytorch_model(self, X_train, y_train, X_val=None, y_val=None):
        """训练PyTorch深度学习模型"""
        try:
            if not TORCH_AVAILABLE:
                return None
            
            # 转换为张量
            X_train_tensor = torch.FloatTensor(X_train)
            y_train_tensor = torch.FloatTensor(y_train.values).reshape(-1, 1)
            
            if X_val is not None:
                X_val_tensor = torch.FloatTensor(X_val)
                y_val_tensor = torch.FloatTensor(y_val.values).reshape(-1, 1)
            
            # 定义网络结构
            class DeepNN(nn.Module):
                def __init__(self, input_size):
                    super(DeepNN, self).__init__()
                    self.layers = nn.Sequential(
                        nn.Linear(input_size, 128),
                        nn.ReLU(),
                        nn.Dropout(0.2),
                        nn.Linear(128, 64),
                        nn.ReLU(),
                        nn.Dropout(0.2),
                        nn.Linear(64, 32),
                        nn.ReLU(),
                        nn.Linear(32, 1)
                    )
                
                def forward(self, x):
                    return self.layers(x)
            
            # 创建模型
            model = DeepNN(X_train.shape[1])
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=0.001)
            
            # 训练
            start_time = datetime.now()
            model.train()
            
            for epoch in range(200):
                optimizer.zero_grad()
                outputs = model(X_train_tensor)
                loss = criterion(outputs, y_train_tensor)
                loss.backward()
                optimizer.step()
                
                if epoch % 50 == 0:
                    self.logger.info(f"  Epoch {epoch}, Loss: {loss.item():.6f}")
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # 评估
            model.eval()
            with torch.no_grad():
                train_pred = model(X_train_tensor).numpy()
                train_mse = mean_squared_error(y_train, train_pred)
                train_r2 = r2_score(y_train, train_pred)
                
                if X_val is not None:
                    val_pred = model(X_val_tensor).numpy()
                    val_mse = mean_squared_error(y_val, val_pred)
                    val_r2 = r2_score(y_val, val_pred)
                else:
                    val_mse = val_r2 = 0.0
            
            # 创建结果
            result = ModelResult(
                model_name='deep_neural',
                model_type='neural',
                selected_factors=[],
                train_metrics={'mse': train_mse, 'r2': train_r2},
                val_metrics={'mse': val_mse, 'r2': val_r2},
                test_metrics={},
                feature_importance=None,
                hyperparameters={},
                cross_val_score=0.0,
                model_path=None,
                training_date=datetime.now(),
                training_time=training_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ PyTorch模型训练失败: {e}")
            return None
    
    def train_ensemble_models(self,
                            X_train: pd.DataFrame,
                            y_train: pd.Series,
                            X_val: pd.DataFrame = None,
                            y_val: pd.Series = None,
                            base_models: Dict = None) -> Dict[str, ModelResult]:
        """
        训练集成模型
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            X_val: 验证特征
            y_val: 验证目标
            base_models: 基础模型字典
            
        Returns:
            集成模型结果字典
        """
        try:
            self.logger.info("🎯 开始训练集成模型")
            results = {}
            
            # 基础模型
            if base_models is None:
                base_models = {
                    'rf': RandomForestRegressor(n_estimators=50, random_state=42),
                    'xgb': xgb.XGBRegressor(n_estimators=50, random_state=42),
                    'lgb': lgb.LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
                }
            
            # Voting回归器
            voting_regressor = VotingRegressor(
                estimators=list(base_models.items())
            )
            start_time = datetime.now()
            voting_regressor.fit(X_train, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['voting'] = self._evaluate_model(
                voting_regressor, X_train, y_train, X_val, y_val,
                'voting', 'ensemble', X_train.columns.tolist(),
                training_time=training_time
            )
            
            # Stacking回归器
            try:
                stacking_regressor = StackingRegressor(
                    estimators=list(base_models.items()),
                    final_estimator=Ridge(),
                    cv=3
                )
                start_time = datetime.now()
                stacking_regressor.fit(X_train, y_train)
                training_time = (datetime.now() - start_time).total_seconds()
                
                results['stacking'] = self._evaluate_model(
                    stacking_regressor, X_train, y_train, X_val, y_val,
                    'stacking', 'ensemble', X_train.columns.tolist(),
                    training_time=training_time
                )
            except Exception as e:
                self.logger.warning(f"⚠️ Stacking模型训练失败: {e}")
            
            # Bagging回归器
            bagging_regressor = BaggingRegressor(
                base_estimator=RandomForestRegressor(n_estimators=20, random_state=42),
                n_estimators=10,
                random_state=42,
                n_jobs=-1
            )
            start_time = datetime.now()
            bagging_regressor.fit(X_train, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            results['bagging'] = self._evaluate_model(
                bagging_regressor, X_train, y_train, X_val, y_val,
                'bagging', 'ensemble', X_train.columns.tolist(),
                training_time=training_time
            )
            
            self.logger.info(f"✅ 集成模型训练完成: {len(results)}个模型")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 集成模型训练失败: {e}")
            return {}
    
    def _evaluate_model(self, model, X_train, y_train, X_val=None, y_val=None,
                       model_name='', model_type='', selected_factors=None,
                       training_time=0.0, scaler=None, hyperparams=None):
        """评估模型性能"""
        try:
            # 训练集预测
            train_pred = model.predict(X_train)
            train_metrics = {
                'mse': float(mean_squared_error(y_train, train_pred)),
                'mae': float(mean_absolute_error(y_train, train_pred)),
                'r2': float(r2_score(y_train, train_pred))
            }
            
            # 验证集预测
            val_metrics = {}
            if X_val is not None and y_val is not None:
                val_pred = model.predict(X_val)
                val_metrics = {
                    'mse': float(mean_squared_error(y_val, val_pred)),
                    'mae': float(mean_absolute_error(y_val, val_pred)),
                    'r2': float(r2_score(y_val, val_pred))
                }
            
            # 特征重要性
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                if selected_factors:
                    feature_importance = dict(zip(selected_factors, model.feature_importances_))
            elif hasattr(model, 'coef_'):
                if selected_factors and hasattr(model.coef_, '__len__'):
                    feature_importance = dict(zip(selected_factors, np.abs(model.coef_)))
            
            # 交叉验证得分
            try:
                cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring='neg_mean_squared_error')
                cv_score = float(-np.mean(cv_scores))
            except:
                cv_score = 0.0
            
            # 保存模型
            model_path = self._save_model(model, model_name, scaler)
            
            result = ModelResult(
                model_name=model_name,
                model_type=model_type,
                selected_factors=selected_factors or [],
                train_metrics=train_metrics,
                val_metrics=val_metrics,
                test_metrics={},
                feature_importance=feature_importance,
                hyperparameters=hyperparams or {},
                cross_val_score=cv_score,
                model_path=model_path,
                training_date=datetime.now(),
                training_time=training_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 模型评估失败: {e}")
            return None
    
    def _save_model(self, model, model_name, scaler=None):
        """保存模型"""
        try:
            model_dir = self.config['storage_config']['model_storage']['path']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存模型
            model_filename = f"{model_name}_{timestamp}.pkl"
            model_path = os.path.join(model_dir, model_filename)
            
            # 保存模型和预处理器
            model_package = {
                'model': model,
                'scaler': scaler,
                'model_name': model_name,
                'training_date': datetime.now()
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_package, f)
            
            self.logger.info(f"📁 模型已保存: {model_path}")
            return model_path
            
        except Exception as e:
            self.logger.error(f"❌ 模型保存失败: {e}")
            return None
    
    def run_comprehensive_training(self,
                                 selected_factors: List[str] = None,
                                 start_date: str = None,
                                 end_date: str = None,
                                 return_period: int = 20) -> Dict[str, ModelResult]:
        """
        运行全面的模型训练流程
        
        Args:
            selected_factors: 选择的因子列表
            start_date: 开始日期
            end_date: 结束日期
            return_period: 收益率周期
            
        Returns:
            所有模型结果字典
        """
        try:
            self.logger.info("🚀 开始全面模型训练流程")
            
            # 1. 如果没有提供因子，先运行因子选择
            if selected_factors is None:
                self.logger.info("📊 未提供选择因子，运行因子选择...")
                selection_results = self.factor_selector.run_comprehensive_selection(
                    start_date, end_date, return_period
                )
                if not selection_results:
                    raise ValueError("因子选择失败")
                
                selected_factors = self.factor_selector.get_selected_factors()
                if not selected_factors:
                    raise ValueError("没有选择到有效因子")
            
            self.logger.info(f"🎯 使用{len(selected_factors)}个选择因子进行训练")
            
            # 2. 准备数据
            data_result = self.prepare_training_data(
                selected_factors, start_date, end_date, return_period
            )
            
            if data_result[0] is None:
                raise ValueError("数据准备失败")
            
            X_train, X_val, X_test, y_train, y_val, y_test = data_result
            
            # 3. 训练各类模型
            all_results = {}
            
            # 线性模型
            linear_results = self.train_linear_models(X_train, y_train, X_val, y_val)
            all_results.update(linear_results)
            
            # 树模型
            tree_results = self.train_tree_models(X_train, y_train, X_val, y_val)
            all_results.update(tree_results)
            
            # 神经网络模型
            neural_results = self.train_neural_models(X_train, y_train, X_val, y_val)
            all_results.update(neural_results)
            
            # 集成模型
            ensemble_results = self.train_ensemble_models(X_train, y_train, X_val, y_val)
            all_results.update(ensemble_results)
            
            # 4. 测试集评估
            self.logger.info("📊 进行测试集最终评估...")
            for model_name, result in all_results.items():
                try:
                    # 加载模型进行测试
                    if result.model_path and os.path.exists(result.model_path):
                        with open(result.model_path, 'rb') as f:
                            model_package = pickle.load(f)
                        
                        model = model_package['model']
                        scaler = model_package.get('scaler')
                        
                        # 预测测试集
                        X_test_processed = X_test
                        if scaler:
                            X_test_processed = scaler.transform(X_test)
                        
                        test_pred = model.predict(X_test_processed)
                        
                        # 计算测试指标
                        test_metrics = {
                            'mse': float(mean_squared_error(y_test, test_pred)),
                            'mae': float(mean_absolute_error(y_test, test_pred)),
                            'r2': float(r2_score(y_test, test_pred))
                        }
                        
                        result.test_metrics = test_metrics
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ {model_name} 测试集评估失败: {e}")
            
            # 5. 保存结果
            self.model_results = all_results
            self.trained_models = {name: result for name, result in all_results.items()}
            
            self.logger.info(f"✅ 模型训练流程完成，训练了{len(all_results)}个模型")
            
            # 6. 显示最佳模型
            best_model = self.get_best_model()
            if best_model:
                self.logger.info(f"🏆 最佳模型: {best_model[0]} (验证R²: {best_model[1].val_metrics.get('r2', 0):.4f})")
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"❌ 模型训练流程失败: {e}")
            return {}
    
    def get_best_model(self, metric: str = 'r2') -> Optional[Tuple[str, ModelResult]]:
        """
        获取最佳模型
        
        Args:
            metric: 评估指标 (r2, mse, mae)
            
        Returns:
            (模型名称, 模型结果) 或 None
        """
        try:
            if not self.model_results:
                return None
            
            best_score = None
            best_model = None
            
            for name, result in self.model_results.items():
                if not result.val_metrics:
                    continue
                
                score = result.val_metrics.get(metric, 0)
                
                # R²越大越好，MSE/MAE越小越好
                is_better = False
                if metric == 'r2':
                    is_better = best_score is None or score > best_score
                else:  # mse, mae
                    is_better = best_score is None or score < best_score
                
                if is_better:
                    best_score = score
                    best_model = (name, result)
            
            return best_model
            
        except Exception as e:
            self.logger.error(f"❌ 获取最佳模型失败: {e}")
            return None
    
    def get_model_ranking(self, metric: str = 'r2') -> List[Tuple[str, float]]:
        """
        获取模型排名
        
        Args:
            metric: 评估指标
            
        Returns:
            [(模型名称, 得分), ...] 按得分排序
        """
        try:
            if not self.model_results:
                return []
            
            model_scores = []
            for name, result in self.model_results.items():
                if result.val_metrics:
                    score = result.val_metrics.get(metric, 0)
                    model_scores.append((name, score))
            
            # 排序
            reverse = metric == 'r2'  # R²降序，MSE/MAE升序
            model_scores.sort(key=lambda x: x[1], reverse=reverse)
            
            return model_scores
            
        except Exception as e:
            self.logger.error(f"❌ 获取模型排名失败: {e}")
            return []


if __name__ == "__main__":
    # 测试代码
    print("🚀 测试模型训练器...")
    
    try:
        trainer = ModelTrainer()
        
        # 运行全面训练
        results = trainer.run_comprehensive_training(
            start_date="2023-01-01",
            end_date="2023-12-31",
            return_period=20
        )
        
        if results:
            print("✅ 模型训练测试成功")
            print(f"📊 训练模型数量: {len(results)}")
            
            # 获取最佳模型
            best_model = trainer.get_best_model()
            if best_model:
                print(f"🏆 最佳模型: {best_model[0]}")
                print(f"  验证R²: {best_model[1].val_metrics.get('r2', 0):.4f}")
                print(f"  验证MSE: {best_model[1].val_metrics.get('mse', 0):.6f}")
            
            # 获取模型排名
            ranking = trainer.get_model_ranking()
            print(f"📈 模型排名(按R²):")
            for i, (name, score) in enumerate(ranking[:5], 1):
                print(f"  {i}. {name}: {score:.4f}")
                
        else:
            print("❌ 模型训练测试失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()