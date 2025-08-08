#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能因子挖掘系统完整运行脚本
整合因子分析、选择、模型训练、策略执行和结果存储的完整流程
"""

import os
import sys
import argparse
import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qlib_quantitative.factor_mining.core.factor_analyzer import FactorAnalyzer
from qlib_quantitative.factor_mining.core.factor_selector import FactorSelector
from qlib_quantitative.factor_mining.core.model_trainer import ModelTrainer
from qlib_quantitative.factor_mining.storage.result_storage import ResultStorage
from qlib_quantitative.strategies.factor_driven_strategy import FactorDrivenStrategy
# 尝试导入可视化模块，如果失败则使用占位符
try:
    from qlib_quantitative.factor_mining.visualization.factor_reporter import FactorReporter
    VISUALIZATION_AVAILABLE = True
except ImportError:
    # 如果可视化模块不可用，创建一个占位符类
    class FactorReporter:
        def __init__(self, *args, **kwargs):
            pass
        def generate_comprehensive_report(self, *args, **kwargs):
            return {}
    VISUALIZATION_AVAILABLE = False


class FactorMiningSystem:
    """
    智能因子挖掘系统
    
    支持不同指数成分股的因子挖掘系统
    - 中证A500、申万行业、其他指数
    - 按指数类型分别存储和分析
    """
    
    def __init__(self, config_path: str = None, index_type: str = "csi_a500", 
                 device: str = "auto", disable_gpu: bool = False, batch_size: int = None):
        """
        初始化因子挖掘系统
        
        Args:
            config_path: 配置文件路径
            index_type: 指数类型 (csi_a500, sw_industry, csi300, etc.)
            device: 计算设备类型
            disable_gpu: 是否禁用GPU
            batch_size: 批处理大小覆盖
        """
        # 指数类型配置
        self.index_type = index_type
        self.index_config = self._get_index_config(index_type)
        
        # 硬件配置
        self.device_preference = device
        self.disable_gpu = disable_gpu
        self.batch_size_override = batch_size
        
        self.logger = self._setup_logger()
        
        # 加载配置
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "factor_mining/config/factor_mining_config.yaml"
            )
        
        self.config_path = config_path
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                
            # 根据指数类型调整配置
            self._adjust_config_for_index()
            
            self.logger.info(f"✅ 配置文件加载成功: {config_path}")
            self.logger.info(f"📊 指数类型: {self.index_config['name']} ({self.index_type})")
        except Exception as e:
            self.logger.error(f"❌ 配置文件加载失败: {e}")
            raise
        
        # 初始化组件
        self.factor_analyzer = None
        self.factor_selector = None
        self.model_trainer = None
        self.result_storage = None
        self.strategy = None
        self.reporter = None
        
        # 运行结果
        self.results = {}
        
        self.logger.info(f"🚀 因子挖掘系统初始化完成 - {self.index_config['name']}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # 文件处理器
            try:
                log_dir = "logs"
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"factor_mining_{datetime.now().strftime('%Y%m%d')}.log")
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"⚠️ 无法创建日志文件: {e}")
        
        return logger
    
    def _get_index_config(self, index_type: str) -> Dict[str, Any]:
        """获取指数配置信息"""
        index_configs = {
            "csi_a500": {
                "name": "中证A500指数",
                "code": "000510.CSI", 
                "collection": "index_weight",
                "filter": {"index_code": "000510.CSI"},
                "stock_count": 500,
                "description": "中证A500指数成分股"
            },
            "csi300": {
                "name": "沪深300指数",
                "code": "000300.SH",
                "collection": "index_weight", 
                "filter": {"index_code": "000300.SH"},
                "stock_count": 300,
                "description": "沪深300指数成分股"
            },
            "csi500": {
                "name": "中证500指数",
                "code": "000905.SH",
                "collection": "index_weight",
                "filter": {"index_code": "000905.SH"}, 
                "stock_count": 500,
                "description": "中证500指数成分股"
            },
            "csi1000": {
                "name": "中证1000指数",
                "code": "000852.SH", 
                "collection": "index_weight",
                "filter": {"index_code": "000852.SH"},
                "stock_count": 1000,
                "description": "中证1000指数成分股"
            },
            "sw_food": {
                "name": "申万食品饮料行业",
                "code": "SW_FOOD",
                "collection": "index_member_all",
                "filter": {"l1_name": "食品饮料"},
                "stock_count": 100,
                "description": "申万食品饮料行业成分股"
            },
            "sw_tech": {
                "name": "申万电子行业", 
                "code": "SW_TECH",
                "collection": "index_member_all",
                "filter": {"l1_name": "电子"},
                "stock_count": 200,
                "description": "申万电子行业成分股"
            },
            "sw_pharma": {
                "name": "申万医药生物行业",
                "code": "SW_PHARMA", 
                "collection": "index_member_all",
                "filter": {"l1_name": "医药生物"},
                "stock_count": 150,
                "description": "申万医药生物行业成分股"
            },
            "sw_auto": {
                "name": "申万汽车行业",
                "code": "SW_AUTO",
                "collection": "index_member_all", 
                "filter": {"l1_name": "汽车"},
                "stock_count": 80,
                "description": "申万汽车行业成分股"
            },
            "sw_metal": {
                "name": "申万有色金属行业",
                "code": "SW_METAL",
                "collection": "index_member_all",
                "filter": {"l1_name": "有色金属"},
                "stock_count": 120,
                "description": "申万有色金属行业成分股"
            },
            "custom": {
                "name": "自定义股票池",
                "code": "CUSTOM",
                "collection": "custom_universe",
                "filter": {},
                "stock_count": 0,
                "description": "自定义股票池"
            }
        }
        
        return index_configs.get(index_type, index_configs["csi_a500"])
    
    def _adjust_config_for_index(self):
        """根据指数类型调整配置"""
        # 调整数据配置
        self.config['data_config']['stock_universe'] = self.index_type
        self.config['data_config']['index_code'] = self.index_config['code']
        
        # 调整硬件加速配置
        self._adjust_hardware_config()
        
        # 调整存储配置 - 按指数类型分别存储
        original_collections = self.config['storage_config']['collections'].copy()
        
        # 为每个集合添加指数前缀
        for key, collection_name in original_collections.items():
            self.config['storage_config']['collections'][key] = f"{self.index_type}_{collection_name}"
        
        # 调整输出路径
        if 'output_config' not in self.config:
            self.config['output_config'] = {}
        
        self.config['output_config']['base_path'] = f"results/factor_mining/{self.index_type}"
        self.config['output_config']['report_prefix'] = f"{self.index_config['name']}_"
    
    def _adjust_hardware_config(self):
        """调整硬件加速配置"""
        if 'acceleration_config' not in self.config:
            return
            
        # 处理设备偏好
        if self.device_preference != "auto":
            # 强制指定设备
            if self.device_preference == "cuda":
                self.config['acceleration_config']['device_config']['device_priority'] = ["cuda"]
            elif self.device_preference == "mps":
                self.config['acceleration_config']['device_config']['device_priority'] = ["mps"]
            elif self.device_preference == "cpu":
                self.config['acceleration_config']['device_config']['device_priority'] = ["cpu"]
        
        # 禁用GPU
        if self.disable_gpu:
            self.config['acceleration_config']['device_config']['device_priority'] = ["cpu"]
            self.config['acceleration_config']['device_config']['cuda']['enabled'] = False
            self.config['acceleration_config']['device_config']['mps']['enabled'] = False
        
        # 覆盖批处理大小
        if self.batch_size_override:
            if 'factor_config' not in self.config:
                self.config['factor_config'] = {}
            if 'factor_analysis' not in self.config['factor_config']:
                self.config['factor_config']['factor_analysis'] = {}
            
            self.config['factor_config']['factor_analysis']['batch_size'] = self.batch_size_override
            
            # 同时调整性能优化配置
            if 'performance_optimization' in self.config['acceleration_config']:
                batch_config = self.config['acceleration_config']['performance_optimization'].get('batch_processing', {})
                batch_config['min_batch_size'] = min(self.batch_size_override, batch_config.get('min_batch_size', 10))
                batch_config['max_batch_size'] = max(self.batch_size_override, batch_config.get('max_batch_size', 1000))
    
    def initialize_components(self):
        """初始化系统组件"""
        try:
            self.logger.info("🔧 初始化系统组件...")
            
            # 初始化各组件
            self.factor_analyzer = FactorAnalyzer(self.config_path)
            self.factor_selector = FactorSelector(self.config_path)
            self.model_trainer = ModelTrainer(self.config_path)
            self.result_storage = ResultStorage(self.config_path)
            self.strategy = FactorDrivenStrategy(self.config_path)
            self.reporter = FactorReporter()
            
            self.logger.info("✅ 系统组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 系统组件初始化失败: {e}")
            raise
    
    def run_factor_analysis(self, 
                          start_date: str = None, 
                          end_date: str = None) -> Dict[str, Any]:
        """
        运行因子分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            因子分析结果
        """
        try:
            self.logger.info("📊 开始运行因子分析...")
            
            if not self.factor_analyzer:
                self.initialize_components()
            
            # 使用配置中的默认日期
            if start_date is None:
                start_date = self.config['data_config']['train_period']['start_date']
            if end_date is None:
                end_date = self.config['data_config']['train_period']['end_date']
            
            # 运行因子分析
            analysis_results = self.factor_analyzer.run_factor_analysis(start_date, end_date)
            
            if not analysis_results:
                raise ValueError("因子分析失败")
            
            # 保存结果
            metadata = {
                'start_date': start_date,
                'end_date': end_date,
                'analysis_type': 'comprehensive',
                'system_version': '1.0',
                'index_type': self.index_type,
                'index_name': self.index_config['name'],
                'index_code': self.index_config['code'],
                'stock_count': self.index_config['stock_count']
            }
            
            doc_id = self.result_storage.save_factor_analysis_results(
                analysis_results['factor_analysis'], metadata
            )
            
            self.results['factor_analysis'] = {
                'results': analysis_results,
                'doc_id': doc_id,
                'metadata': metadata
            }
            
            self.logger.info("✅ 因子分析完成")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ 因子分析失败: {e}")
            return {}
    
    def run_factor_selection(self,
                           start_date: str = None,
                           end_date: str = None,
                           return_period: int = 20) -> Dict[str, Any]:
        """
        运行因子选择
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            return_period: 收益率周期
            
        Returns:
            因子选择结果
        """
        try:
            self.logger.info("🎯 开始运行因子选择...")
            
            if not self.factor_selector:
                self.initialize_components()
            
            # 运行因子选择
            selection_results = self.factor_selector.run_comprehensive_selection(
                start_date, end_date, return_period
            )
            
            if not selection_results:
                raise ValueError("因子选择失败")
            
            # 保存结果
            metadata = {
                'start_date': start_date,
                'end_date': end_date,
                'return_period': return_period,
                'selection_type': 'comprehensive',
                'system_version': '1.0',
                'index_type': self.index_type,
                'index_name': self.index_config['name'],
                'index_code': self.index_config['code']
            }
            
            doc_id = self.result_storage.save_factor_selection_results(
                selection_results, metadata
            )
            
            self.results['factor_selection'] = {
                'results': selection_results,
                'doc_id': doc_id,
                'metadata': metadata
            }
            
            # 获取选择的因子
            selected_factors = self.factor_selector.get_selected_factors()
            self.logger.info(f"✅ 因子选择完成，选择了{len(selected_factors)}个因子")
            
            return selection_results
            
        except Exception as e:
            self.logger.error(f"❌ 因子选择失败: {e}")
            return {}
    
    def run_model_training(self,
                         selected_factors: List[str] = None,
                         start_date: str = None,
                         end_date: str = None,
                         return_period: int = 20) -> Dict[str, Any]:
        """
        运行模型训练
        
        Args:
            selected_factors: 选择的因子列表
            start_date: 开始日期
            end_date: 结束日期
            return_period: 收益率周期
            
        Returns:
            模型训练结果
        """
        try:
            self.logger.info("🤖 开始运行模型训练...")
            
            if not self.model_trainer:
                self.initialize_components()
            
            # 如果没有提供因子，使用因子选择结果
            if selected_factors is None:
                if 'factor_selection' in self.results:
                    selected_factors = self.factor_selector.get_selected_factors()
                else:
                    # 运行因子选择
                    self.run_factor_selection(start_date, end_date, return_period)
                    selected_factors = self.factor_selector.get_selected_factors()
            
            if not selected_factors:
                raise ValueError("没有可用的选择因子")
            
            # 运行模型训练
            training_results = self.model_trainer.run_comprehensive_training(
                selected_factors, start_date, end_date, return_period
            )
            
            if not training_results:
                raise ValueError("模型训练失败")
            
            # 保存结果
            metadata = {
                'selected_factors_count': len(selected_factors),
                'selected_factors': selected_factors[:20],  # 保存前20个因子
                'start_date': start_date,
                'end_date': end_date,
                'return_period': return_period,
                'training_type': 'comprehensive',
                'system_version': '1.0'
            }
            
            doc_id = self.result_storage.save_model_training_results(
                training_results, metadata
            )
            
            # 保存因子重要性
            best_model = self.model_trainer.get_best_model()
            if best_model and best_model[1].feature_importance:
                self.result_storage.save_factor_importance(
                    best_model[1].feature_importance,
                    best_model[0],
                    f'{return_period}d',
                    metadata
                )
            
            self.results['model_training'] = {
                'results': training_results,
                'doc_id': doc_id,
                'metadata': metadata,
                'best_model': best_model
            }
            
            model_count = len(training_results)
            best_model_name = best_model[0] if best_model else "无"
            best_r2 = best_model[1].val_metrics.get('r2', 0) if best_model else 0
            
            self.logger.info(f"✅ 模型训练完成，训练了{model_count}个模型")
            self.logger.info(f"🏆 最佳模型: {best_model_name} (R²: {best_r2:.4f})")
            
            return training_results
            
        except Exception as e:
            self.logger.error(f"❌ 模型训练失败: {e}")
            return {}
    
    def run_strategy_execution(self,
                             current_date: str = None,
                             model_name: str = None) -> Dict[str, Any]:
        """
        运行策略执行
        
        Args:
            current_date: 当前日期
            model_name: 指定模型名称
            
        Returns:
            策略执行结果
        """
        try:
            self.logger.info("🎯 开始运行策略执行...")
            
            if not self.strategy:
                self.initialize_components()
            
            # 使用默认日期
            if current_date is None:
                current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 初始化策略
            if not self.strategy.trained_model:
                # 检查是否有训练结果
                if 'model_training' in self.results and self.results['model_training']['results']:
                    # 使用最佳模型或指定模型
                    training_results = self.results['model_training']['results']
                    
                    if model_name and model_name in training_results:
                        model_result = training_results[model_name]
                    else:
                        best_model = self.results['model_training'].get('best_model')
                        if not best_model:
                            raise ValueError("没有可用的训练模型")
                        model_result = best_model[1]
                    
                    # 加载模型
                    if not self.strategy.load_existing_model(model_result.model_path):
                        raise ValueError("模型加载失败")
                    
                    # 设置选择的因子
                    self.strategy.selected_factors = model_result.selected_factors
                else:
                    # 重新初始化策略
                    success = self.strategy.initialize_strategy()
                    if not success:
                        raise ValueError("策略初始化失败")
            
            # 运行策略
            strategy_result = self.strategy.run_strategy(current_date)
            
            if not strategy_result.get('success', False):
                raise ValueError(f"策略执行失败: {strategy_result.get('reason', 'unknown')}")
            
            # 保存结果
            metadata = {
                'current_date': current_date,
                'model_name': self.strategy.model_name,
                'factor_count': len(self.strategy.selected_factors),
                'execution_type': 'single_date',
                'system_version': '1.0'
            }
            
            doc_id = self.result_storage.save_strategy_results(strategy_result, metadata)
            
            self.results['strategy_execution'] = {
                'result': strategy_result,
                'doc_id': doc_id,
                'metadata': metadata
            }
            
            self.logger.info("✅ 策略执行完成")
            self.logger.info(f"📊 选择股票: {strategy_result['selected_stocks_count']}")
            self.logger.info(f"📊 交易信号: {strategy_result['signals_count']}")
            
            return strategy_result
            
        except Exception as e:
            self.logger.error(f"❌ 策略执行失败: {e}")
            return {}
    
    def run_complete_pipeline(self,
                            start_date: str = None,
                            end_date: str = None,
                            return_period: int = 20,
                            execute_strategy: bool = True) -> Dict[str, Any]:
        """
        运行完整的因子挖掘流水线
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            return_period: 收益率周期
            execute_strategy: 是否执行策略
            
        Returns:
            完整运行结果
        """
        try:
            self.logger.info("🚀 开始运行完整因子挖掘流水线")
            
            # 记录开始时间
            start_time = datetime.now()
            
            # 初始化组件
            self.initialize_components()
            
            # 1. 因子分析
            self.logger.info("=" * 60)
            self.logger.info("第1步: 因子分析")
            self.logger.info("=" * 60)
            
            factor_analysis_results = self.run_factor_analysis(start_date, end_date)
            if not factor_analysis_results:
                raise ValueError("因子分析阶段失败")
            
            # 2. 因子选择
            self.logger.info("=" * 60)
            self.logger.info("第2步: 因子选择")
            self.logger.info("=" * 60)
            
            factor_selection_results = self.run_factor_selection(start_date, end_date, return_period)
            if not factor_selection_results:
                raise ValueError("因子选择阶段失败")
            
            # 3. 模型训练
            self.logger.info("=" * 60)
            self.logger.info("第3步: 模型训练")
            self.logger.info("=" * 60)
            
            selected_factors = self.factor_selector.get_selected_factors()
            model_training_results = self.run_model_training(
                selected_factors, start_date, end_date, return_period
            )
            if not model_training_results:
                raise ValueError("模型训练阶段失败")
            
            # 4. 策略执行（可选）
            strategy_result = {}
            if execute_strategy:
                self.logger.info("=" * 60)
                self.logger.info("第4步: 策略执行")
                self.logger.info("=" * 60)
                
                strategy_result = self.run_strategy_execution()
                if not strategy_result:
                    self.logger.warning("⚠️ 策略执行失败，但不影响整体流程")
            
            # 计算总耗时
            total_time = (datetime.now() - start_time).total_seconds()
            
            # 汇总结果
            pipeline_result = {
                'success': True,
                'total_time_seconds': total_time,
                'start_date': start_date,
                'end_date': end_date,
                'return_period': return_period,
                'stages': {
                    'factor_analysis': {
                        'success': bool(factor_analysis_results),
                        'factor_count': len(self.factor_analyzer.factor_fields),
                        'doc_id': self.results.get('factor_analysis', {}).get('doc_id', '')
                    },
                    'factor_selection': {
                        'success': bool(factor_selection_results),
                        'selected_factors_count': len(selected_factors),
                        'doc_id': self.results.get('factor_selection', {}).get('doc_id', '')
                    },
                    'model_training': {
                        'success': bool(model_training_results),
                        'models_count': len(model_training_results),
                        'best_model': self.results.get('model_training', {}).get('best_model', [None, None])[0],
                        'doc_id': self.results.get('model_training', {}).get('doc_id', '')
                    },
                    'strategy_execution': {
                        'success': bool(strategy_result),
                        'executed': execute_strategy,
                        'doc_id': self.results.get('strategy_execution', {}).get('doc_id', '')
                    }
                },
                'system_version': '1.0',
                'execution_date': datetime.now().isoformat()
            }
            
            # 保存管道执行结果
            pipeline_metadata = {
                'pipeline_type': 'complete',
                'execution_time_seconds': total_time,
                'system_version': '1.0'
            }
            
            pipeline_doc_id = self.result_storage.save_strategy_results(
                pipeline_result, pipeline_metadata
            )
            
            self.results['pipeline'] = {
                'result': pipeline_result,
                'doc_id': pipeline_doc_id
            }
            
            # 6. 生成可视化报告
            self.logger.info("============================================================")
            self.logger.info("第6步: 生成分析报告")
            self.logger.info("============================================================")
            
            try:
                if VISUALIZATION_AVAILABLE:
                    self.logger.info("📊 开始生成综合分析报告...")
                    
                    report_files = self.reporter.generate_comprehensive_report(
                        factor_analysis_results=factor_analysis_results,
                        model_results=model_training_results,
                        strategy_results=strategy_result,
                        report_title=f"因子挖掘综合分析报告 ({start_date} 至 {end_date})"
                    )
                else:
                    self.logger.warning("⚠️ 可视化模块不可用，跳过报告生成")
                    report_files = {}
                
                if report_files:
                    self.logger.info("✅ 综合分析报告生成完成")
                    for report_type, file_path in report_files.items():
                        self.logger.info(f"📄 {report_type.upper()}报告: {file_path}")
                    
                    # 添加报告信息到结果中
                    pipeline_result['reports'] = {
                        'success': True,
                        'files': report_files,
                        'generation_time': datetime.now().isoformat()
                    }
                else:
                    self.logger.warning("⚠️ 报告生成部分失败")
                    pipeline_result['reports'] = {
                        'success': False,
                        'error': 'Report generation failed'
                    }
                    
            except Exception as e:
                self.logger.error(f"❌ 报告生成失败: {e}")
                pipeline_result['reports'] = {
                    'success': False,
                    'error': str(e)
                }
            
            self.logger.info("=" * 60)
            self.logger.info("✅ 完整流水线执行成功")
            self.logger.info("=" * 60)
            self.logger.info(f"📊 总耗时: {total_time:.1f}秒")
            self.logger.info(f"📊 分析因子: {len(self.factor_analyzer.factor_fields)}个")
            self.logger.info(f"📊 选择因子: {len(selected_factors)}个")
            self.logger.info(f"📊 训练模型: {len(model_training_results)}个")
            if execute_strategy and strategy_result:
                self.logger.info(f"📊 策略信号: {strategy_result.get('signals_count', 0)}个")
            
            return pipeline_result
            
        except Exception as e:
            self.logger.error(f"❌ 完整流水线执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_date': datetime.now().isoformat()
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # 存储统计
            storage_stats = self.result_storage.get_storage_statistics() if self.result_storage else {}
            
            # 组件状态
            component_status = {
                'factor_analyzer': self.factor_analyzer is not None,
                'factor_selector': self.factor_selector is not None,
                'model_trainer': self.model_trainer is not None,
                'result_storage': self.result_storage is not None,
                'strategy': self.strategy is not None
            }
            
            # 最新结果
            latest_results = {}
            if self.result_storage:
                try:
                    latest_results = {
                        'factor_analysis': len(self.result_storage.get_latest_factor_analysis(limit=1)),
                        'model_results': len(self.result_storage.get_latest_model_results(limit=1)),
                        'best_models': len(self.result_storage.get_best_models_summary(top_k=3))
                    }
                except:
                    latest_results = {'error': 'failed_to_fetch'}
            
            status = {
                'system_initialized': all(component_status.values()),
                'components': component_status,
                'storage_stats': storage_stats,
                'latest_results': latest_results,
                'current_results': {
                    'stages_completed': list(self.results.keys()),
                    'total_stages': len(self.results)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"❌ 获取系统状态失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能因子挖掘系统')
    
    # 基本参数
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--start-date', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--return-period', type=int, default=20, help='收益率周期（天）')
    
    # 指数类型参数
    parser.add_argument('--index-type', type=str, default='csi_a500',
                       choices=['csi_a500', 'csi300', 'csi500', 'csi1000', 'sw_food', 'sw_tech', 'sw_pharma', 'sw_auto', 'sw_metal', 'custom'],
                       help='指数类型: csi_a500(中证A500), csi300(沪深300), csi500(中证500), csi1000(中证1000), sw_food(申万食品), sw_tech(申万电子), sw_pharma(申万医药), sw_auto(申万汽车), sw_metal(申万有色金属), custom(自定义)')
    parser.add_argument('--list-indices', action='store_true', help='显示支持的指数类型')
    
    # 运行模式
    parser.add_argument('--mode', type=str, choices=['complete', 'analysis', 'selection', 'training', 'strategy'], 
                       default='complete', help='运行模式')
    parser.add_argument('--no-strategy', action='store_true', help='不执行策略')
    
    # 硬件加速参数
    parser.add_argument('--device', type=str, choices=['auto', 'cuda', 'mps', 'cpu'], 
                       default='auto', help='指定计算设备: auto(自动检测), cuda(NVIDIA GPU), mps(Apple Silicon), cpu(CPU)')
    parser.add_argument('--disable-gpu', action='store_true', help='禁用GPU加速，强制使用CPU')
    parser.add_argument('--batch-size', type=int, help='覆盖配置文件中的批处理大小')
    
    # 其他参数
    parser.add_argument('--model-name', type=str, help='指定模型名称')
    parser.add_argument('--current-date', type=str, help='当前日期（策略执行用）')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    
    args = parser.parse_args()
    
    try:
        # 显示支持的指数类型
        if args.list_indices:
            print("📊 支持的指数类型:")
            indices = {
                'csi_a500': '中证A500指数 (500只成分股)',
                'csi300': '沪深300指数 (300只成分股)', 
                'csi500': '中证500指数 (500只成分股)',
                'csi1000': '中证1000指数 (1000只成分股)',
                'sw_food': '申万食品饮料行业',
                'sw_tech': '申万电子行业',
                'sw_pharma': '申万医药生物行业', 
                'sw_auto': '申万汽车行业',
                'sw_metal': '申万有色金属行业',
                'custom': '自定义股票池'
            }
            for code, desc in indices.items():
                print(f"  {code:10s} - {desc}")
            return
        
        # 创建系统实例 
        system = FactorMiningSystem(
            config_path=args.config, 
            index_type=args.index_type,
            device=args.device,
            disable_gpu=args.disable_gpu,
            batch_size=args.batch_size
        )
        
        # 显示系统状态
        if args.status:
            status = system.get_system_status()
            print("📊 系统状态:")
            print(f"  系统初始化: {status['system_initialized']}")
            print(f"  存储文档数: {status.get('storage_stats', {}).get('total_documents', 0)}")
            print(f"  已完成阶段: {status['current_results']['stages_completed']}")
            return
        
        # 根据模式运行
        if args.mode == 'complete':
            # 完整流水线
            result = system.run_complete_pipeline(
                start_date=args.start_date,
                end_date=args.end_date,
                return_period=args.return_period,
                execute_strategy=not args.no_strategy
            )
            
        elif args.mode == 'analysis':
            # 仅因子分析
            result = system.run_factor_analysis(args.start_date, args.end_date)
            
        elif args.mode == 'selection':
            # 仅因子选择
            result = system.run_factor_selection(args.start_date, args.end_date, args.return_period)
            
        elif args.mode == 'training':
            # 仅模型训练
            result = system.run_model_training(None, args.start_date, args.end_date, args.return_period)
            
        elif args.mode == 'strategy':
            # 仅策略执行
            result = system.run_strategy_execution(args.current_date, args.model_name)
        
        # 显示结果摘要
        if result:
            print("\n" + "="*60)
            print("✅ 执行完成")
            print("="*60)
            
            if args.mode == 'complete':
                success = result.get('success', False)
                print(f"状态: {'成功' if success else '失败'}")
                if success:
                    print(f"总耗时: {result['total_time_seconds']:.1f}秒")
                    stages = result.get('stages', {})
                    for stage_name, stage_info in stages.items():
                        status = '✅' if stage_info.get('success', False) else '❌'
                        print(f"  {stage_name}: {status}")
                else:
                    print(f"错误: {result.get('error', 'unknown')}")
            else:
                print(f"模式: {args.mode}")
                print(f"结果: {'成功' if result else '失败'}")
        else:
            print("❌ 执行失败")
        
    except Exception as e:
        print(f"❌ 系统运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()