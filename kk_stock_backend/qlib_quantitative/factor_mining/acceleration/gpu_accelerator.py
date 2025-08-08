"""
GPU加速计算模块
提供因子计算、矩阵运算、机器学习的GPU加速功能
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

class GPUAccelerator:
    """GPU加速计算器"""
    
    def __init__(self, device_manager, config: Dict[str, Any]):
        """
        初始化GPU加速器
        
        Args:
            device_manager: 设备管理器
            config: 加速配置
        """
        self.device_manager = device_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 加速配置
        self.compute_config = config.get('compute_acceleration', {})
        self.performance_config = config.get('performance_optimization', {})
        
        # 初始化计算后端
        self._initialize_backends()
    
    def _initialize_backends(self):
        """初始化计算后端"""
        try:
            # PyTorch后端
            import torch
            self.torch = torch
            self.torch_available = True
            
            # 设置设备
            if self.device_manager.device:
                self.device = self.device_manager.device
            else:
                self.device = torch.device('cpu')
                
        except ImportError:
            self.logger.warning("⚠️ PyTorch未安装，将使用CPU计算")
            self.torch_available = False
            self.device = None
        
        # NumPy优化
        try:
            # 尝试使用优化的BLAS库
            import numpy as np
            self.logger.info(f"📊 NumPy后端: {np.show_config()}")
        except:
            pass
    
    def accelerated_factor_calculation(self, data: pd.DataFrame, 
                                     factor_functions: List[callable],
                                     chunk_size: Optional[int] = None) -> pd.DataFrame:
        """
        加速因子计算
        
        Args:
            data: 输入数据
            factor_functions: 因子计算函数列表
            chunk_size: 分块大小
            
        Returns:
            计算结果
        """
        if data.empty:
            return data
            
        start_time = time.time()
        
        # 确定分块大小
        if chunk_size is None:
            chunk_size = self._get_optimal_chunk_size(data)
        
        # 并行计算配置
        parallel_config = self.performance_config.get('parallelization', {})
        max_workers = parallel_config.get('max_workers', 4)
        
        if self.compute_config.get('factor_computation', {}).get('parallel_factors', True):
            # 并行计算因子
            results = self._parallel_factor_computation(data, factor_functions, chunk_size, max_workers)
        else:
            # 串行计算
            results = self._sequential_factor_computation(data, factor_functions)
        
        computation_time = time.time() - start_time
        self.logger.info(f"⚡ 因子计算完成: {computation_time:.2f}秒")
        
        return results
    
    def _parallel_factor_computation(self, data: pd.DataFrame, 
                                   factor_functions: List[callable],
                                   chunk_size: int, 
                                   max_workers: int) -> pd.DataFrame:
        """并行因子计算"""
        # 数据分块
        chunks = self._split_data_chunks(data, chunk_size)
        
        # 并行处理
        all_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            futures = []
            for i, chunk in enumerate(chunks):
                future = executor.submit(self._compute_chunk_factors, chunk, factor_functions, i)
                futures.append(future)
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        all_results.append(result)
                except Exception as e:
                    self.logger.error(f"❌ 分块计算失败: {e}")
        
        # 合并结果
        if all_results:
            return pd.concat(all_results, ignore_index=True)
        else:
            return data.copy()
    
    def _compute_chunk_factors(self, chunk: pd.DataFrame, 
                             factor_functions: List[callable], 
                             chunk_id: int) -> pd.DataFrame:
        """计算单个数据块的因子"""
        try:
            start_time = time.time()
            
            # 移动数据到GPU (如果可用)
            if self.torch_available and self.device_manager.device_type in ['cuda', 'mps']:
                chunk_tensor = self._dataframe_to_tensor(chunk)
                chunk_tensor = self.device_manager.move_to_device(chunk_tensor)
                
                # GPU计算
                result_tensor = self._gpu_factor_computation(chunk_tensor, factor_functions)
                result = self._tensor_to_dataframe(result_tensor, chunk.index, chunk.columns)
            else:
                # CPU计算
                result = self._cpu_factor_computation(chunk, factor_functions)
            
            computation_time = time.time() - start_time
            self.logger.debug(f"📊 分块{chunk_id}计算完成: {computation_time:.2f}秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 分块{chunk_id}计算失败: {e}")
            return chunk.copy()
        finally:
            # 清理GPU内存
            if self.torch_available:
                self._cleanup_gpu_memory()
    
    def _gpu_factor_computation(self, tensor, factor_functions: List[callable]):
        """GPU因子计算"""
        # 这里实现具体的GPU因子计算逻辑
        # 由于因子计算函数可能很复杂，这里提供一个框架
        
        results = []
        for func in factor_functions:
            try:
                if hasattr(func, 'gpu_compute'):
                    # 如果函数支持GPU计算
                    result = func.gpu_compute(tensor)
                else:
                    # 转换为CPU计算
                    cpu_data = tensor.cpu().numpy()
                    result = func(cpu_data)
                    result = self.torch.from_numpy(result).to(self.device)
                
                results.append(result)
            except Exception as e:
                self.logger.warning(f"⚠️ GPU因子计算失败，回退到CPU: {e}")
                cpu_data = tensor.cpu().numpy()
                result = func(cpu_data)
                result = self.torch.from_numpy(result).to(self.device)
                results.append(result)
        
        return self.torch.stack(results, dim=-1) if results else tensor
    
    def _cpu_factor_computation(self, data: pd.DataFrame, factor_functions: List[callable]) -> pd.DataFrame:
        """CPU因子计算"""
        result = data.copy()
        
        for i, func in enumerate(factor_functions):
            try:
                factor_result = func(data)
                if isinstance(factor_result, pd.Series):
                    result[f'factor_{i}'] = factor_result
                elif isinstance(factor_result, pd.DataFrame):
                    result = pd.concat([result, factor_result], axis=1)
            except Exception as e:
                self.logger.warning(f"⚠️ 因子{i}计算失败: {e}")
        
        return result
    
    def accelerated_ic_calculation(self, factors: pd.DataFrame, 
                                 returns: pd.DataFrame) -> pd.DataFrame:
        """
        加速IC计算
        
        Args:
            factors: 因子数据
            returns: 收益率数据
            
        Returns:
            IC结果
        """
        start_time = time.time()
        
        if self.torch_available and self.device_manager.device_type in ['cuda', 'mps']:
            ic_result = self._gpu_ic_calculation(factors, returns)
        else:
            ic_result = self._cpu_ic_calculation(factors, returns)
        
        computation_time = time.time() - start_time
        self.logger.info(f"⚡ IC计算完成: {computation_time:.2f}秒")
        
        return ic_result
    
    def _gpu_ic_calculation(self, factors: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
        """GPU加速IC计算"""
        try:
            # 转换为张量
            factors_tensor = self.torch.from_numpy(factors.values).float()
            returns_tensor = self.torch.from_numpy(returns.values).float()
            
            # 移动到GPU
            factors_tensor = self.device_manager.move_to_device(factors_tensor)
            returns_tensor = self.device_manager.move_to_device(returns_tensor)
            
            # 计算相关系数矩阵
            # 标准化
            factors_norm = (factors_tensor - factors_tensor.mean(dim=0)) / factors_tensor.std(dim=0)
            returns_norm = (returns_tensor - returns_tensor.mean(dim=0)) / returns_tensor.std(dim=0)
            
            # 计算相关系数
            ic_matrix = self.torch.mm(factors_norm.T, returns_norm) / (factors_tensor.shape[0] - 1)
            
            # 转换回CPU和DataFrame
            ic_result = ic_matrix.cpu().numpy()
            ic_df = pd.DataFrame(ic_result, 
                               index=factors.columns, 
                               columns=returns.columns)
            
            return ic_df
            
        except Exception as e:
            self.logger.warning(f"⚠️ GPU IC计算失败，回退到CPU: {e}")
            return self._cpu_ic_calculation(factors, returns)
    
    def _cpu_ic_calculation(self, factors: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
        """CPU IC计算"""
        # 使用NumPy的优化相关系数计算
        ic_result = np.corrcoef(factors.T, returns.T)
        
        # 提取因子与收益的相关系数部分
        n_factors = factors.shape[1]
        ic_matrix = ic_result[:n_factors, n_factors:]
        
        ic_df = pd.DataFrame(ic_matrix, 
                           index=factors.columns, 
                           columns=returns.columns)
        
        return ic_df
    
    def accelerated_matrix_operations(self, operation: str, *matrices) -> np.ndarray:
        """
        加速矩阵运算
        
        Args:
            operation: 运算类型 ('multiply', 'add', 'subtract', 'inverse', 'svd')
            matrices: 输入矩阵
            
        Returns:
            运算结果
        """
        if not self.torch_available:
            return self._cpu_matrix_operations(operation, *matrices)
        
        try:
            # 转换为张量
            tensors = []
            for matrix in matrices:
                if isinstance(matrix, np.ndarray):
                    tensor = self.torch.from_numpy(matrix).float()
                elif isinstance(matrix, pd.DataFrame):
                    tensor = self.torch.from_numpy(matrix.values).float()
                else:
                    tensor = matrix
                
                tensor = self.device_manager.move_to_device(tensor)
                tensors.append(tensor)
            
            # 执行运算
            if operation == 'multiply':
                result = self.torch.mm(tensors[0], tensors[1])
            elif operation == 'add':
                result = tensors[0] + tensors[1]
            elif operation == 'subtract':
                result = tensors[0] - tensors[1]
            elif operation == 'inverse':
                result = self.torch.inverse(tensors[0])
            elif operation == 'svd':
                U, S, V = self.torch.svd(tensors[0])
                return U.cpu().numpy(), S.cpu().numpy(), V.cpu().numpy()
            else:
                raise ValueError(f"不支持的运算类型: {operation}")
            
            return result.cpu().numpy()
            
        except Exception as e:
            self.logger.warning(f"⚠️ GPU矩阵运算失败，回退到CPU: {e}")
            return self._cpu_matrix_operations(operation, *matrices)
    
    def _cpu_matrix_operations(self, operation: str, *matrices) -> np.ndarray:
        """CPU矩阵运算"""
        arrays = []
        for matrix in matrices:
            if isinstance(matrix, pd.DataFrame):
                arrays.append(matrix.values)
            else:
                arrays.append(np.array(matrix))
        
        if operation == 'multiply':
            return np.dot(arrays[0], arrays[1])
        elif operation == 'add':
            return arrays[0] + arrays[1]
        elif operation == 'subtract':
            return arrays[0] - arrays[1]
        elif operation == 'inverse':
            return np.linalg.inv(arrays[0])
        elif operation == 'svd':
            return np.linalg.svd(arrays[0])
        else:
            raise ValueError(f"不支持的运算类型: {operation}")
    
    def _get_optimal_chunk_size(self, data: pd.DataFrame) -> int:
        """获取最优分块大小"""
        # 基础分块大小
        base_chunk_size = self.compute_config.get('factor_computation', {}).get('chunk_size', 1000)
        
        # 根据数据大小和设备性能调整
        data_size_mb = data.memory_usage(deep=True).sum() / (1024 * 1024)
        
        if self.device_manager.device_type == 'cuda':
            # GPU可以处理更大的块
            optimal_size = min(base_chunk_size * 2, len(data))
        elif self.device_manager.device_type == 'mps':
            # MPS内存较保守
            optimal_size = min(base_chunk_size, len(data))
        else:
            # CPU根据内存调整
            available_memory_mb = self.device_manager.available_memory * 1024
            if data_size_mb > available_memory_mb * 0.5:
                scale_factor = (available_memory_mb * 0.5) / data_size_mb
                optimal_size = max(int(base_chunk_size * scale_factor), 100)
            else:
                optimal_size = base_chunk_size
        
        return min(optimal_size, len(data))
    
    def _split_data_chunks(self, data: pd.DataFrame, chunk_size: int) -> List[pd.DataFrame]:
        """分割数据为块"""
        chunks = []
        for i in range(0, len(data), chunk_size):
            chunk = data.iloc[i:i + chunk_size].copy()
            chunks.append(chunk)
        return chunks
    
    def _dataframe_to_tensor(self, df: pd.DataFrame):
        """DataFrame转换为张量"""
        if not self.torch_available:
            return df.values
        
        # 只选择数值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        numeric_data = df[numeric_columns].fillna(0)
        
        return self.torch.from_numpy(numeric_data.values).float()
    
    def _tensor_to_dataframe(self, tensor, index, columns) -> pd.DataFrame:
        """张量转换为DataFrame"""
        if self.torch_available and hasattr(tensor, 'cpu'):
            array = tensor.cpu().numpy()
        else:
            array = tensor
        
        # 确保维度匹配
        if array.shape[1] > len(columns):
            # 如果结果有更多列，创建新的列名
            new_columns = list(columns) + [f'computed_{i}' for i in range(len(columns), array.shape[1])]
        else:
            new_columns = columns[:array.shape[1]]
        
        return pd.DataFrame(array, index=index[:len(array)], columns=new_columns)
    
    def _cleanup_gpu_memory(self):
        """清理GPU内存"""
        if self.torch_available:
            if hasattr(self.torch.cuda, 'empty_cache'):
                self.torch.cuda.empty_cache()
            elif hasattr(self.torch.mps, 'empty_cache'):
                self.torch.mps.empty_cache()
        
        # 强制垃圾回收
        gc.collect()
    
    def _sequential_factor_computation(self, data: pd.DataFrame, 
                                     factor_functions: List[callable]) -> pd.DataFrame:
        """串行因子计算"""
        return self._cpu_factor_computation(data, factor_functions)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = {
            'device_type': self.device_manager.device_type,
            'device_count': self.device_manager.device_count,
            'available_memory_gb': self.device_manager.available_memory
        }
        
        if self.torch_available and self.device_manager.device_type == 'cuda':
            stats['gpu_memory_allocated'] = self.torch.cuda.memory_allocated() / (1024**3)
            stats['gpu_memory_cached'] = self.torch.cuda.memory_reserved() / (1024**3)
        
        return stats