#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果存储管理器 - 因子挖掘结果的数据库存储
负责将因子分析、选择、模型训练和策略运行结果存储到MongoDB
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
import yaml
import logging
import json
from dataclasses import asdict

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from api.global_db import db_handler
from qlib_quantitative.factor_mining.core.factor_analyzer import FactorAnalysisResult
from qlib_quantitative.factor_mining.core.factor_selector import FactorSelectionResult
from qlib_quantitative.factor_mining.core.model_trainer import ModelResult


class ResultStorage:
    """
    结果存储管理器
    
    主要功能：
    1. 因子分析结果存储
    2. 因子选择结果存储
    3. 模型训练结果存储
    4. 策略运行结果存储
    5. 历史结果查询和管理
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化结果存储管理器
        
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
        
        # 初始化数据库连接
        self.db_handler = db_handler
        
        # 集合名称配置
        storage_config = self.config['storage_config']['collections']
        self.collections = {
            'factors': storage_config['factors'],
            'models': storage_config['models'],
            'results': storage_config['results'],
            'evaluations': storage_config['evaluations']
        }
        
        # 确保集合存在
        self._ensure_collections()
        
        self.logger.info("🚀 结果存储管理器初始化完成")
    
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
    
    def _ensure_collections(self):
        """确保集合存在"""
        try:
            for collection_name in self.collections.values():
                collection = self.db_handler.get_collection(collection_name)
                # 检查集合是否存在，如果不存在会自动创建
                collection.count_documents({})
            
            self.logger.info("✅ 数据库集合检查完成")
        except Exception as e:
            self.logger.error(f"❌ 数据库集合检查失败: {e}")
    
    def save_factor_analysis_results(self, 
                                   analysis_results: Dict[str, Dict[str, FactorAnalysisResult]],
                                   metadata: Dict[str, Any] = None) -> str:
        """
        保存因子分析结果
        
        Args:
            analysis_results: 因子分析结果
            metadata: 元数据
            
        Returns:
            保存的文档ID
        """
        try:
            self.logger.info("💾 保存因子分析结果")
            
            # 转换结果格式
            formatted_results = {}
            for period, results in analysis_results.items():
                formatted_results[period] = {}
                for factor_name, result in results.items():
                    formatted_results[period][factor_name] = result.to_dict()
            
            # 创建文档
            document = {
                'type': 'factor_analysis',
                'results': formatted_results,
                'metadata': metadata or {},
                'created_at': datetime.now(),
                'version': '1.0'
            }
            
            # 保存到数据库
            collection = self.db_handler.get_collection(self.collections['results'])
            result = collection.insert_one(document)
            
            self.logger.info(f"✅ 因子分析结果已保存: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"❌ 保存因子分析结果失败: {e}")
            return ""
    
    def save_factor_selection_results(self,
                                    selection_results: Dict[str, FactorSelectionResult],
                                    metadata: Dict[str, Any] = None) -> str:
        """
        保存因子选择结果
        
        Args:
            selection_results: 因子选择结果
            metadata: 元数据
            
        Returns:
            保存的文档ID
        """
        try:
            self.logger.info("💾 保存因子选择结果")
            
            # 转换结果格式
            formatted_results = {}
            for method, result in selection_results.items():
                formatted_results[method] = result.to_dict()
            
            # 创建文档
            document = {
                'type': 'factor_selection',
                'results': formatted_results,
                'metadata': metadata or {},
                'created_at': datetime.now(),
                'version': '1.0'
            }
            
            # 保存到数据库
            collection = self.db_handler.get_collection(self.collections['results'])
            result = collection.insert_one(document)
            
            self.logger.info(f"✅ 因子选择结果已保存: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"❌ 保存因子选择结果失败: {e}")
            return ""
    
    def save_model_training_results(self,
                                  training_results: Dict[str, ModelResult],
                                  metadata: Dict[str, Any] = None) -> str:
        """
        保存模型训练结果
        
        Args:
            training_results: 模型训练结果
            metadata: 元数据
            
        Returns:
            保存的文档ID
        """
        try:
            self.logger.info("💾 保存模型训练结果")
            
            # 转换结果格式
            formatted_results = {}
            for model_name, result in training_results.items():
                formatted_results[model_name] = result.to_dict()
            
            # 创建文档
            document = {
                'type': 'model_training',
                'results': formatted_results,
                'metadata': metadata or {},
                'created_at': datetime.now(),
                'version': '1.0'
            }
            
            # 保存到数据库
            collection = self.db_handler.get_collection(self.collections['models'])
            result = collection.insert_one(document)
            
            self.logger.info(f"✅ 模型训练结果已保存: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"❌ 保存模型训练结果失败: {e}")
            return ""
    
    def save_strategy_results(self,
                            strategy_result: Dict[str, Any],
                            metadata: Dict[str, Any] = None) -> str:
        """
        保存策略运行结果
        
        Args:
            strategy_result: 策略运行结果
            metadata: 元数据
            
        Returns:
            保存的文档ID
        """
        try:
            self.logger.info("💾 保存策略运行结果")
            
            # 创建文档
            document = {
                'type': 'strategy_execution',
                'result': strategy_result,
                'metadata': metadata or {},
                'created_at': datetime.now(),
                'version': '1.0'
            }
            
            # 保存到数据库
            collection = self.db_handler.get_collection(self.collections['results'])
            result = collection.insert_one(document)
            
            self.logger.info(f"✅ 策略运行结果已保存: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"❌ 保存策略运行结果失败: {e}")
            return ""
    
    def save_factor_importance(self,
                             factor_importance: Dict[str, float],
                             model_name: str,
                             period: str,
                             metadata: Dict[str, Any] = None) -> str:
        """
        保存因子重要性
        
        Args:
            factor_importance: 因子重要性字典
            model_name: 模型名称
            period: 预测周期
            metadata: 元数据
            
        Returns:
            保存的文档ID
        """
        try:
            self.logger.info("💾 保存因子重要性")
            
            # 创建文档
            document = {
                'type': 'factor_importance',
                'model_name': model_name,
                'period': period,
                'factor_importance': factor_importance,
                'metadata': metadata or {},
                'created_at': datetime.now(),
                'version': '1.0'
            }
            
            # 保存到数据库
            collection = self.db_handler.get_collection(self.collections['factors'])
            result = collection.insert_one(document)
            
            self.logger.info(f"✅ 因子重要性已保存: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"❌ 保存因子重要性失败: {e}")
            return ""
    
    def get_latest_factor_analysis(self, 
                                 period: str = '20d',
                                 limit: int = 1) -> List[Dict[str, Any]]:
        """
        获取最新的因子分析结果
        
        Args:
            period: 预测周期
            limit: 返回数量限制
            
        Returns:
            因子分析结果列表
        """
        try:
            collection = self.db_handler.get_collection(self.collections['results'])
            
            query = {'type': 'factor_analysis'}
            cursor = collection.find(query).sort('created_at', -1).limit(limit)
            
            results = []
            for doc in cursor:
                # 提取指定周期的结果
                if period in doc.get('results', {}):
                    results.append({
                        'id': str(doc['_id']),
                        'period': period,
                        'results': doc['results'][period],
                        'metadata': doc.get('metadata', {}),
                        'created_at': doc['created_at']
                    })
            
            self.logger.info(f"📊 获取了{len(results)}个因子分析结果")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 获取因子分析结果失败: {e}")
            return []
    
    def get_latest_model_results(self, 
                               model_type: str = None,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最新的模型训练结果
        
        Args:
            model_type: 模型类型筛选
            limit: 返回数量限制
            
        Returns:
            模型结果列表
        """
        try:
            collection = self.db_handler.get_collection(self.collections['models'])
            
            query = {'type': 'model_training'}
            cursor = collection.find(query).sort('created_at', -1).limit(limit)
            
            results = []
            for doc in cursor:
                doc_results = doc.get('results', {})
                
                # 如果指定了模型类型，进行筛选
                if model_type:
                    filtered_results = {
                        name: result for name, result in doc_results.items()
                        if result.get('model_type') == model_type
                    }
                    if not filtered_results:
                        continue
                    doc_results = filtered_results
                
                results.append({
                    'id': str(doc['_id']),
                    'results': doc_results,
                    'metadata': doc.get('metadata', {}),
                    'created_at': doc['created_at']
                })
            
            self.logger.info(f"📊 获取了{len(results)}个模型训练结果")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 获取模型训练结果失败: {e}")
            return []
    
    def get_factor_performance_history(self, 
                                     factor_name: str,
                                     days: int = 30) -> List[Dict[str, Any]]:
        """
        获取因子历史表现
        
        Args:
            factor_name: 因子名称
            days: 历史天数
            
        Returns:
            因子历史表现列表
        """
        try:
            collection = self.db_handler.get_collection(self.collections['results'])
            
            # 计算查询起始日期
            start_date = datetime.now() - pd.Timedelta(days=days)
            
            query = {
                'type': 'factor_analysis',
                'created_at': {'$gte': start_date}
            }
            
            cursor = collection.find(query).sort('created_at', -1)
            
            history = []
            for doc in cursor:
                results = doc.get('results', {})
                
                # 查找包含指定因子的结果
                for period, factors in results.items():
                    if factor_name in factors:
                        factor_data = factors[factor_name]
                        history.append({
                            'date': doc['created_at'],
                            'period': period,
                            'factor_name': factor_name,
                            'ic_mean': factor_data.get('ic_mean', 0),
                            'ic_ir': factor_data.get('ic_ir', 0),
                            'significance': factor_data.get('significance', False),
                            'sharpe_ratio': factor_data.get('sharpe_ratio', 0)
                        })
            
            self.logger.info(f"📊 获取了{factor_name}的{len(history)}条历史记录")
            return history
            
        except Exception as e:
            self.logger.error(f"❌ 获取因子历史表现失败: {e}")
            return []
    
    def get_best_models_summary(self, 
                              top_k: int = 10,
                              metric: str = 'r2') -> List[Dict[str, Any]]:
        """
        获取最佳模型汇总
        
        Args:
            top_k: 返回前K个模型
            metric: 评估指标
            
        Returns:
            最佳模型汇总列表
        """
        try:
            collection = self.db_handler.get_collection(self.collections['models'])
            
            query = {'type': 'model_training'}
            cursor = collection.find(query).sort('created_at', -1)
            
            all_models = []
            for doc in cursor:
                results = doc.get('results', {})
                created_at = doc['created_at']
                
                for model_name, model_data in results.items():
                    val_metrics = model_data.get('val_metrics', {})
                    if metric in val_metrics:
                        all_models.append({
                            'model_name': model_name,
                            'model_type': model_data.get('model_type', ''),
                            'metric_value': val_metrics[metric],
                            'train_r2': model_data.get('train_metrics', {}).get('r2', 0),
                            'val_r2': val_metrics.get('r2', 0),
                            'test_r2': model_data.get('test_metrics', {}).get('r2', 0),
                            'cv_score': model_data.get('cross_val_score', 0),
                            'training_time': model_data.get('training_time', 0),
                            'created_at': created_at,
                            'document_id': str(doc['_id'])
                        })
            
            # 排序并取前K个
            reverse = metric == 'r2'  # R²降序，其他升序
            all_models.sort(key=lambda x: x['metric_value'], reverse=reverse)
            
            best_models = all_models[:top_k]
            
            self.logger.info(f"📊 获取了前{len(best_models)}个最佳模型")
            return best_models
            
        except Exception as e:
            self.logger.error(f"❌ 获取最佳模型汇总失败: {e}")
            return []
    
    def cleanup_old_results(self, days: int = 30) -> int:
        """
        清理旧的结果记录
        
        Args:
            days: 保留天数
            
        Returns:
            删除的记录数
        """
        try:
            self.logger.info(f"🗑️ 清理{days}天前的旧结果")
            
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            query = {'created_at': {'$lt': cutoff_date}}
            
            total_deleted = 0
            
            # 清理各个集合
            for collection_name in self.collections.values():
                collection = self.db_handler.get_collection(collection_name)
                result = collection.delete_many(query)
                total_deleted += result.deleted_count
                
                self.logger.info(f"  {collection_name}: 删除了{result.deleted_count}条记录")
            
            self.logger.info(f"✅ 总共删除了{total_deleted}条旧记录")
            return total_deleted
            
        except Exception as e:
            self.logger.error(f"❌ 清理旧结果失败: {e}")
            return 0
    
    def export_results_to_json(self, 
                             result_type: str,
                             output_path: str,
                             days: int = 7) -> bool:
        """
        导出结果到JSON文件
        
        Args:
            result_type: 结果类型
            output_path: 输出路径
            days: 导出天数
            
        Returns:
            导出是否成功
        """
        try:
            self.logger.info(f"📤 导出{result_type}结果到{output_path}")
            
            # 确定集合
            if result_type in ['factor_analysis', 'factor_selection', 'strategy_execution']:
                collection = self.db_handler.get_collection(self.collections['results'])
            elif result_type == 'model_training':
                collection = self.db_handler.get_collection(self.collections['models'])
            elif result_type == 'factor_importance':
                collection = self.db_handler.get_collection(self.collections['factors'])
            else:
                raise ValueError(f"不支持的结果类型: {result_type}")
            
            # 查询数据
            start_date = datetime.now() - pd.Timedelta(days=days)
            query = {
                'type': result_type,
                'created_at': {'$gte': start_date}
            }
            
            cursor = collection.find(query).sort('created_at', -1)
            
            # 转换数据
            results = []
            for doc in cursor:
                # 移除_id字段并转换日期
                doc_dict = dict(doc)
                doc_dict.pop('_id', None)
                
                # 转换datetime对象为字符串
                if 'created_at' in doc_dict:
                    doc_dict['created_at'] = doc_dict['created_at'].isoformat()
                
                results.append(doc_dict)
            
            # 保存到文件
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"✅ 导出完成: {len(results)}条记录")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 导出结果失败: {e}")
            return False
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息
        """
        try:
            stats = {
                'collections': {},
                'total_documents': 0,
                'storage_size_mb': 0,
                'latest_update': None
            }
            
            for name, collection_name in self.collections.items():
                collection = self.db_handler.get_collection(collection_name)
                
                # 文档数量
                count = collection.count_documents({})
                stats['collections'][name] = {
                    'collection_name': collection_name,
                    'document_count': count
                }
                stats['total_documents'] += count
                
                # 最新更新时间
                if count > 0:
                    latest_doc = collection.find().sort('created_at', -1).limit(1)
                    latest_doc = list(latest_doc)
                    if latest_doc:
                        latest_time = latest_doc[0].get('created_at')
                        if latest_time and (stats['latest_update'] is None or latest_time > stats['latest_update']):
                            stats['latest_update'] = latest_time
            
            # 格式化最新更新时间
            if stats['latest_update']:
                stats['latest_update'] = stats['latest_update'].isoformat()
            
            self.logger.info(f"📊 存储统计: {stats['total_documents']}个文档")
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 获取存储统计失败: {e}")
            return {}


if __name__ == "__main__":
    # 测试代码
    print("🚀 测试结果存储管理器...")
    
    try:
        storage = ResultStorage()
        
        # 获取存储统计
        stats = storage.get_storage_statistics()
        print("📊 存储统计:")
        for name, info in stats['collections'].items():
            print(f"  {name}: {info['document_count']}个文档")
        
        print(f"总文档数: {stats['total_documents']}")
        print(f"最新更新: {stats['latest_update']}")
        
        # 获取最新模型结果
        model_results = storage.get_latest_model_results(limit=3)
        print(f"\n📊 最新模型结果: {len(model_results)}条")
        
        # 获取最佳模型汇总
        best_models = storage.get_best_models_summary(top_k=5)
        print(f"\n🏆 最佳模型:")
        for i, model in enumerate(best_models[:3], 1):
            print(f"  {i}. {model['model_name']} (R²: {model['val_r2']:.4f})")
        
        print("✅ 结果存储管理器测试成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()