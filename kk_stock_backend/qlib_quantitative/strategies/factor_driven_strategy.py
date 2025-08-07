#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子驱动策略 - 基于挖掘因子和训练模型的智能交易策略
结合因子挖掘结果和机器学习预测模型，实现动态选股和交易信号生成
"""

import os
import sys
import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import yaml
import logging
import pickle
import json
from dataclasses import dataclass

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from qlib_quantitative.factor_mining.core.factor_analyzer import FactorAnalyzer
from qlib_quantitative.factor_mining.core.factor_selector import FactorSelector
from qlib_quantitative.factor_mining.core.model_trainer import ModelTrainer, ModelResult
from api.global_db import db_handler

# Qlib相关
try:
    import qlib
    from qlib.strategy.base import BaseStrategy
    from qlib.data import D
    QLIB_AVAILABLE = True
except ImportError:
    QLIB_AVAILABLE = False
    # 如果qlib不可用，创建一个基础策略类
    class BaseStrategy:
        def generate_trade_decision(self, execute_result=None):
            pass

warnings.filterwarnings('ignore')

@dataclass
class TradingSignal:
    """交易信号数据类"""
    stock_code: str
    signal_type: str  # 'buy', 'sell', 'hold'
    signal_strength: float  # 信号强度 0-1
    predicted_return: float  # 预测收益率
    confidence: float  # 置信度
    factor_scores: Dict[str, float]  # 各因子得分
    model_prediction: float  # 模型预测值
    signal_date: datetime
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'stock_code': self.stock_code,
            'signal_type': self.signal_type,
            'signal_strength': self.signal_strength,
            'predicted_return': self.predicted_return,
            'confidence': self.confidence,
            'factor_scores': self.factor_scores,
            'model_prediction': self.model_prediction,
            'signal_date': self.signal_date.isoformat()
        }


class FactorDrivenStrategy(BaseStrategy):
    """
    因子驱动策略
    
    主要功能：
    1. 基于挖掘因子的股票评分
    2. 机器学习模型预测
    3. 多因子融合选股
    4. 动态交易信号生成
    5. 风险控制和仓位管理
    """
    
    def __init__(self, config_path: str = None, model_name: str = None):
        """
        初始化因子驱动策略
        
        Args:
            config_path: 配置文件路径
            model_name: 使用的模型名称
        """
        if QLIB_AVAILABLE:
            super().__init__()
        
        self.logger = self._setup_logger()
        
        # 加载配置
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "../factor_mining/config/factor_mining_config.yaml"
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            self.logger.info(f"✅ 配置文件加载成功")
        except Exception as e:
            self.logger.error(f"❌ 配置文件加载失败: {e}")
            raise
        
        # 初始化组件
        self.factor_analyzer = FactorAnalyzer(config_path)
        self.factor_selector = FactorSelector(config_path)
        self.model_trainer = ModelTrainer(config_path)
        self.db_handler = db_handler
        
        # 策略状态
        self.selected_factors = []
        self.trained_model = None
        self.model_scaler = None
        self.current_positions = {}
        self.trading_signals = []
        self.model_name = model_name
        
        # 策略参数
        strategy_config = self.config.get('strategy_config', {})
        self.selection_config = strategy_config.get('stock_selection', {})
        self.signal_config = strategy_config.get('trading_signals', {})
        self.freq_config = strategy_config.get('trading_frequency', {})
        
        self.logger.info("🚀 因子驱动策略初始化完成")
    
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
    
    def initialize_strategy(self, 
                          start_date: str = None,
                          end_date: str = None,
                          return_period: int = 20) -> bool:
        """
        初始化策略 - 运行因子挖掘和模型训练
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            return_period: 收益率周期
            
        Returns:
            初始化是否成功
        """
        try:
            self.logger.info("🚀 开始初始化因子驱动策略")
            
            # 1. 运行因子选择
            self.logger.info("📊 运行因子选择...")
            selection_results = self.factor_selector.run_comprehensive_selection(
                start_date, end_date, return_period
            )
            
            if not selection_results:
                self.logger.error("❌ 因子选择失败")
                return False
            
            self.selected_factors = self.factor_selector.get_selected_factors()
            self.logger.info(f"✅ 选择了{len(self.selected_factors)}个有效因子")
            
            # 2. 运行模型训练
            self.logger.info("🤖 运行模型训练...")
            training_results = self.model_trainer.run_comprehensive_training(
                self.selected_factors, start_date, end_date, return_period
            )
            
            if not training_results:
                self.logger.error("❌ 模型训练失败")
                return False
            
            # 3. 选择最佳模型
            if self.model_name and self.model_name in training_results:
                best_model_info = (self.model_name, training_results[self.model_name])
            else:
                best_model_info = self.model_trainer.get_best_model()
            
            if not best_model_info:
                self.logger.error("❌ 未找到可用模型")
                return False
            
            model_name, model_result = best_model_info
            self.logger.info(f"🏆 选择模型: {model_name} (R²: {model_result.val_metrics.get('r2', 0):.4f})")
            
            # 4. 加载最佳模型
            if model_result.model_path and os.path.exists(model_result.model_path):
                with open(model_result.model_path, 'rb') as f:
                    model_package = pickle.load(f)
                
                self.trained_model = model_package['model']
                self.model_scaler = model_package.get('scaler')
                self.model_name = model_name
                
                self.logger.info("✅ 模型加载成功")
            else:
                self.logger.error("❌ 模型文件不存在")
                return False
            
            self.logger.info("✅ 策略初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 策略初始化失败: {e}")
            return False
    
    def load_existing_model(self, model_path: str) -> bool:
        """
        加载已存在的模型
        
        Args:
            model_path: 模型路径
            
        Returns:
            加载是否成功
        """
        try:
            self.logger.info(f"📁 加载模型: {model_path}")
            
            if not os.path.exists(model_path):
                self.logger.error(f"❌ 模型文件不存在: {model_path}")
                return False
            
            with open(model_path, 'rb') as f:
                model_package = pickle.load(f)
            
            self.trained_model = model_package['model']
            self.model_scaler = model_package.get('scaler')
            self.model_name = model_package.get('model_name', 'loaded_model')
            
            # 尝试获取选择的因子
            if 'selected_factors' in model_package:
                self.selected_factors = model_package['selected_factors']
            
            self.logger.info("✅ 模型加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 模型加载失败: {e}")
            return False
    
    def generate_stock_scores(self, 
                            current_date: str,
                            stock_universe: List[str] = None) -> Dict[str, float]:
        """
        生成股票评分
        
        Args:
            current_date: 当前日期
            stock_universe: 股票池，为None时使用A500
            
        Returns:
            {股票代码: 评分}
        """
        try:
            self.logger.info(f"📊 生成股票评分: {current_date}")
            
            if not self.trained_model or not self.selected_factors:
                self.logger.error("❌ 模型或因子未准备好")
                return {}
            
            # 获取股票池
            if stock_universe is None:
                stock_universe = self.factor_analyzer.load_a500_universe(current_date)
            
            if not stock_universe:
                self.logger.warning("⚠️ 股票池为空")
                return {}
            
            # 获取因子数据
            factor_data = self._get_current_factor_data(current_date, stock_universe)
            
            if factor_data.empty:
                self.logger.warning("⚠️ 因子数据为空")
                return {}
            
            # 选择相关因子
            available_factors = [f for f in self.selected_factors if f in factor_data.columns]
            if not available_factors:
                self.logger.warning("⚠️ 无可用因子")
                return {}
            
            factor_subset = factor_data[available_factors].dropna()
            if factor_subset.empty:
                return {}
            
            # 数据预处理
            if self.model_scaler:
                factor_processed = self.model_scaler.transform(factor_subset)
            else:
                factor_processed = factor_subset.values
            
            # 模型预测
            predictions = self.trained_model.predict(factor_processed)
            
            # 生成评分字典
            stock_scores = {}
            for i, stock_code in enumerate(factor_subset.index):
                if isinstance(stock_code, tuple):  # 多重索引
                    stock_code = stock_code[1] if len(stock_code) > 1 else stock_code[0]
                
                stock_scores[stock_code] = float(predictions[i])
            
            self.logger.info(f"✅ 生成了{len(stock_scores)}只股票的评分")
            return stock_scores
            
        except Exception as e:
            self.logger.error(f"❌ 生成股票评分失败: {e}")
            return {}
    
    def _get_current_factor_data(self, 
                               current_date: str, 
                               stock_codes: List[str]) -> pd.DataFrame:
        """获取当前日期的因子数据"""
        try:
            # 计算日期范围（需要一些历史数据用于计算技术指标）
            end_date = current_date
            start_date = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # 加载因子数据
            factor_data = self.factor_analyzer.load_factor_data(stock_codes, start_date, end_date)
            
            if factor_data.empty:
                return pd.DataFrame()
            
            # 获取最新日期的数据
            try:
                current_data = factor_data.xs(current_date, level=0)
                return current_data
            except KeyError:
                # 如果当前日期没有数据，获取最近的数据
                dates = factor_data.index.get_level_values(0).unique()
                latest_date = dates[dates <= current_date].max()
                
                if pd.isna(latest_date):
                    return pd.DataFrame()
                
                return factor_data.xs(latest_date, level=0)
                
        except Exception as e:
            self.logger.error(f"❌ 获取因子数据失败: {e}")
            return pd.DataFrame()
    
    def select_stocks(self, 
                     stock_scores: Dict[str, float],
                     current_date: str = None) -> List[str]:
        """
        基于评分选择股票
        
        Args:
            stock_scores: 股票评分字典
            current_date: 当前日期
            
        Returns:
            选择的股票列表
        """
        try:
            if not stock_scores:
                return []
            
            method = self.selection_config.get('method', 'factor_score')
            top_k = self.selection_config.get('top_k', 50)
            min_score = self.selection_config.get('min_score', 0.6)
            
            if method == 'factor_score':
                # 按评分排序选择
                sorted_stocks = sorted(stock_scores.items(), key=lambda x: x[1], reverse=True)
                
                # 应用最小评分筛选
                qualified_stocks = [(code, score) for code, score in sorted_stocks if score >= min_score]
                
                # 选择前K只
                selected_stocks = [code for code, score in qualified_stocks[:top_k]]
                
            elif method == 'model_predict':
                # 基于模型预测的选择逻辑
                # 可以添加更复杂的选择规则
                sorted_stocks = sorted(stock_scores.items(), key=lambda x: x[1], reverse=True)
                selected_stocks = [code for code, score in sorted_stocks[:top_k]]
            
            else:
                # 默认按评分选择
                sorted_stocks = sorted(stock_scores.items(), key=lambda x: x[1], reverse=True)
                selected_stocks = [code for code, score in sorted_stocks[:top_k]]
            
            self.logger.info(f"📊 选择了{len(selected_stocks)}只股票")
            return selected_stocks
            
        except Exception as e:
            self.logger.error(f"❌ 股票选择失败: {e}")
            return []
    
    def generate_trading_signals(self,
                               selected_stocks: List[str],
                               stock_scores: Dict[str, float],
                               current_date: str) -> List[TradingSignal]:
        """
        生成交易信号
        
        Args:
            selected_stocks: 选择的股票列表
            stock_scores: 股票评分字典
            current_date: 当前日期
            
        Returns:
            交易信号列表
        """
        try:
            self.logger.info(f"🎯 生成交易信号: {current_date}")
            
            signals = []
            entry_threshold = self.signal_config.get('entry_threshold', 0.7)
            exit_threshold = self.signal_config.get('exit_threshold', 0.3)
            
            for stock_code in selected_stocks:
                try:
                    score = stock_scores.get(stock_code, 0)
                    
                    # 判断信号类型
                    if score >= entry_threshold:
                        signal_type = 'buy'
                        signal_strength = min(1.0, score / entry_threshold)
                    elif score <= exit_threshold:
                        signal_type = 'sell'
                        signal_strength = min(1.0, (entry_threshold - score) / (entry_threshold - exit_threshold))
                    else:
                        signal_type = 'hold'
                        signal_strength = 0.5
                    
                    # 计算置信度（基于模型表现）
                    confidence = self._calculate_signal_confidence(stock_code, score)
                    
                    # 创建交易信号
                    signal = TradingSignal(
                        stock_code=stock_code,
                        signal_type=signal_type,
                        signal_strength=signal_strength,
                        predicted_return=score * 100,  # 转换为百分比
                        confidence=confidence,
                        factor_scores={},  # 可以添加详细因子得分
                        model_prediction=score,
                        signal_date=datetime.strptime(current_date, '%Y-%m-%d')
                    )
                    
                    signals.append(signal)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ 生成{stock_code}信号失败: {e}")
                    continue
            
            # 过滤和排序信号
            signals = self._filter_and_rank_signals(signals)
            
            self.logger.info(f"✅ 生成了{len(signals)}个交易信号")
            self.trading_signals.extend(signals)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"❌ 交易信号生成失败: {e}")
            return []
    
    def _calculate_signal_confidence(self, stock_code: str, score: float) -> float:
        """计算信号置信度"""
        try:
            # 基于模型验证集表现和预测值计算置信度
            base_confidence = 0.5
            
            # 基于预测值调整
            score_confidence = min(1.0, abs(score) * 2)
            
            # 如果有历史表现数据，可以进一步调整
            # ...
            
            final_confidence = (base_confidence + score_confidence) / 2
            return max(0.0, min(1.0, final_confidence))
            
        except:
            return 0.5
    
    def _filter_and_rank_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """过滤和排序交易信号"""
        try:
            # 过滤低置信度信号
            min_confidence = 0.3
            filtered_signals = [s for s in signals if s.confidence >= min_confidence]
            
            # 按信号强度和置信度排序
            filtered_signals.sort(
                key=lambda x: (x.signal_strength * x.confidence), 
                reverse=True
            )
            
            return filtered_signals
            
        except Exception as e:
            self.logger.error(f"❌ 信号过滤失败: {e}")
            return signals
    
    def update_positions(self, 
                       signals: List[TradingSignal],
                       current_positions: Dict[str, float]) -> Dict[str, Any]:
        """
        更新仓位建议
        
        Args:
            signals: 交易信号列表
            current_positions: 当前仓位
            
        Returns:
            仓位更新建议
        """
        try:
            self.logger.info("📊 更新仓位建议")
            
            position_changes = []
            new_positions = current_positions.copy()
            
            for signal in signals:
                stock_code = signal.stock_code
                current_weight = current_positions.get(stock_code, 0)
                
                if signal.signal_type == 'buy':
                    # 计算目标仓位
                    target_weight = self._calculate_target_weight(signal)
                    
                    if target_weight > current_weight:
                        change = {
                            'stock_code': stock_code,
                            'action': 'buy',
                            'current_weight': current_weight,
                            'target_weight': target_weight,
                            'change_amount': target_weight - current_weight,
                            'signal_strength': signal.signal_strength,
                            'confidence': signal.confidence
                        }
                        position_changes.append(change)
                        new_positions[stock_code] = target_weight
                
                elif signal.signal_type == 'sell':
                    if current_weight > 0:
                        # 计算减仓比例
                        reduce_ratio = signal.signal_strength * signal.confidence
                        target_weight = current_weight * (1 - reduce_ratio)
                        
                        change = {
                            'stock_code': stock_code,
                            'action': 'sell',
                            'current_weight': current_weight,
                            'target_weight': target_weight,
                            'change_amount': current_weight - target_weight,
                            'signal_strength': signal.signal_strength,
                            'confidence': signal.confidence
                        }
                        position_changes.append(change)
                        new_positions[stock_code] = target_weight
            
            result = {
                'position_changes': position_changes,
                'new_positions': new_positions,
                'total_positions': len([w for w in new_positions.values() if w > 0.01]),
                'total_weight': sum(new_positions.values())
            }
            
            self.current_positions = new_positions
            self.logger.info(f"✅ 生成了{len(position_changes)}个仓位变动建议")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 更新仓位失败: {e}")
            return {}
    
    def _calculate_target_weight(self, signal: TradingSignal) -> float:
        """计算目标权重"""
        try:
            # 基础权重
            base_weight = 0.05  # 5%
            
            # 基于信号强度调整
            signal_multiplier = signal.signal_strength * signal.confidence
            
            # 计算目标权重
            target_weight = base_weight * (1 + signal_multiplier)
            
            # 限制权重范围
            max_weight = 0.10  # 最大10%
            min_weight = 0.02  # 最小2%
            
            return max(min_weight, min(max_weight, target_weight))
            
        except:
            return 0.05
    
    def run_strategy(self, 
                   current_date: str,
                   current_positions: Dict[str, float] = None) -> Dict[str, Any]:
        """
        运行策略主流程
        
        Args:
            current_date: 当前日期
            current_positions: 当前仓位
            
        Returns:
            策略运行结果
        """
        try:
            self.logger.info(f"🚀 运行因子驱动策略: {current_date}")
            
            if current_positions is None:
                current_positions = {}
            
            # 1. 生成股票评分
            stock_scores = self.generate_stock_scores(current_date)
            
            if not stock_scores:
                self.logger.warning("⚠️ 无股票评分，跳过此次运行")
                return {'success': False, 'reason': 'no_scores'}
            
            # 2. 选择股票
            selected_stocks = self.select_stocks(stock_scores, current_date)
            
            # 3. 生成交易信号
            signals = self.generate_trading_signals(selected_stocks, stock_scores, current_date)
            
            # 4. 更新仓位
            position_updates = self.update_positions(signals, current_positions)
            
            # 5. 策略结果
            result = {
                'success': True,
                'date': current_date,
                'stock_scores_count': len(stock_scores),
                'selected_stocks_count': len(selected_stocks),
                'signals_count': len(signals),
                'top_stocks': selected_stocks[:10],  # 前10只股票
                'buy_signals': [s.stock_code for s in signals if s.signal_type == 'buy'],
                'sell_signals': [s.stock_code for s in signals if s.signal_type == 'sell'],
                'position_updates': position_updates,
                'model_name': self.model_name,
                'factor_count': len(self.selected_factors)
            }
            
            self.logger.info(f"✅ 策略运行完成: 评分{len(stock_scores)}只, 选择{len(selected_stocks)}只, 信号{len(signals)}个")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 策略运行失败: {e}")
            return {'success': False, 'reason': str(e)}
    
    def generate_trade_decision(self, execute_result=None):
        """
        生成交易决策 (Qlib接口)
        """
        try:
            if not QLIB_AVAILABLE:
                return {}
            
            # 获取当前日期
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 运行策略
            result = self.run_strategy(current_date)
            
            if not result.get('success', False):
                return {}
            
            # 转换为Qlib格式的交易决策
            trade_decisions = {}
            
            # 买入决策
            for stock_code in result.get('buy_signals', []):
                trade_decisions[stock_code] = 1  # 买入
            
            # 卖出决策
            for stock_code in result.get('sell_signals', []):
                trade_decisions[stock_code] = 0  # 卖出
            
            return trade_decisions
            
        except Exception as e:
            self.logger.error(f"❌ 生成交易决策失败: {e}")
            return {}
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            'strategy_name': 'FactorDrivenStrategy',
            'strategy_type': '因子驱动策略',
            'model_name': self.model_name,
            'selected_factors_count': len(self.selected_factors),
            'selected_factors': self.selected_factors[:10],  # 显示前10个
            'current_positions_count': len([w for w in self.current_positions.values() if w > 0.01]),
            'total_signals': len(self.trading_signals),
            'last_signal_date': self.trading_signals[-1].signal_date.isoformat() if self.trading_signals else None,
            'config': {
                'selection_method': self.selection_config.get('method', 'factor_score'),
                'top_k': self.selection_config.get('top_k', 50),
                'entry_threshold': self.signal_config.get('entry_threshold', 0.7),
                'exit_threshold': self.signal_config.get('exit_threshold', 0.3)
            }
        }


if __name__ == "__main__":
    # 测试代码
    print("🚀 测试因子驱动策略...")
    
    try:
        strategy = FactorDrivenStrategy()
        
        # 初始化策略
        print("📊 初始化策略...")
        success = strategy.initialize_strategy(
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        if success:
            print("✅ 策略初始化成功")
            
            # 运行策略
            print("🎯 运行策略...")
            result = strategy.run_strategy('2024-01-02')
            
            if result.get('success', False):
                print("✅ 策略运行成功")
                print(f"📊 评分股票: {result['stock_scores_count']}")
                print(f"📊 选择股票: {result['selected_stocks_count']}")
                print(f"📊 交易信号: {result['signals_count']}")
                print(f"📊 前5只股票: {result['top_stocks'][:5]}")
            else:
                print(f"❌ 策略运行失败: {result.get('reason', 'unknown')}")
                
            # 获取策略信息
            info = strategy.get_strategy_info()
            print(f"\n📋 策略信息:")
            print(f"  模型: {info['model_name']}")
            print(f"  因子数量: {info['selected_factors_count']}")
            print(f"  当前持仓: {info['current_positions_count']}")
                
        else:
            print("❌ 策略初始化失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()