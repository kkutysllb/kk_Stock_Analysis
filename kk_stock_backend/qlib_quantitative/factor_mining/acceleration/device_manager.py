"""
设备管理器 - 自动检测和配置硬件加速设备
支持NVIDIA GPU (CUDA)、Apple Silicon (MPS)、CPU
"""

import os
import platform
import logging
from typing import Dict, List, Optional, Tuple, Any
import psutil

class DeviceManager:
    """硬件设备管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化设备管理器
        
        Args:
            config: 加速配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 设备状态
        self.device = None
        self.device_type = None
        self.device_count = 0
        self.available_memory = 0
        
        # 检测并初始化设备
        self._detect_and_initialize_device()
    
    def _detect_and_initialize_device(self):
        """检测并初始化最优设备"""
        device_priority = self.config.get('device_config', {}).get('device_priority', ['cuda', 'mps', 'cpu'])
        
        for device_type in device_priority:
            if self._try_initialize_device(device_type):
                self.device_type = device_type
                break
        
        self.logger.info(f"🚀 已选择设备: {self.device_type}")
        self._log_device_info()
    
    def _try_initialize_device(self, device_type: str) -> bool:
        """尝试初始化指定类型的设备"""
        try:
            if device_type == 'cuda':
                return self._initialize_cuda()
            elif device_type == 'mps':
                return self._initialize_mps()
            elif device_type == 'cpu':
                return self._initialize_cpu()
            else:
                return False
        except Exception as e:
            self.logger.warning(f"⚠️ {device_type.upper()}初始化失败: {e}")
            return False
    
    def _initialize_cuda(self) -> bool:
        """初始化CUDA设备"""
        cuda_config = self.config.get('device_config', {}).get('cuda', {})
        if not cuda_config.get('enabled', True):
            return False
            
        try:
            import torch
            if not torch.cuda.is_available():
                return False
            
            # 检查GPU数量和型号
            device_count = torch.cuda.device_count()
            if device_count == 0:
                return False
            
            # 获取指定的设备ID
            device_ids = cuda_config.get('device_ids', [0])
            valid_device_ids = [i for i in device_ids if i < device_count]
            
            if not valid_device_ids:
                return False
            
            # 设置主设备
            primary_device = valid_device_ids[0]
            torch.cuda.set_device(primary_device)
            self.device = torch.device(f'cuda:{primary_device}')
            self.device_count = len(valid_device_ids)
            
            # 获取显存信息
            total_memory = torch.cuda.get_device_properties(primary_device).total_memory
            self.available_memory = total_memory / (1024**3)  # GB
            
            # 配置内存管理
            if cuda_config.get('allow_growth', True):
                # PyTorch默认就是动态分配，无需特殊设置
                pass
            
            # 混合精度配置
            if cuda_config.get('mixed_precision', True):
                self.mixed_precision = True
            
            self.logger.info(f"✅ CUDA初始化成功: {device_count}张GPU可用")
            for i, device_id in enumerate(valid_device_ids):
                gpu_name = torch.cuda.get_device_name(device_id)
                gpu_memory = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
                self.logger.info(f"   GPU {device_id}: {gpu_name} ({gpu_memory:.1f}GB)")
            
            return True
            
        except ImportError:
            self.logger.warning("⚠️ PyTorch未安装，无法使用CUDA")
            return False
        except Exception as e:
            self.logger.error(f"❌ CUDA初始化失败: {e}")
            return False
    
    def _initialize_mps(self) -> bool:
        """初始化MPS设备 (Apple Silicon)"""
        mps_config = self.config.get('device_config', {}).get('mps', {})
        if not mps_config.get('enabled', True):
            return False
        
        # 检查是否为Mac系统
        if platform.system() != 'Darwin':
            return False
            
        try:
            import torch
            if not torch.backends.mps.is_available():
                return False
            
            self.device = torch.device('mps')
            self.device_count = 1
            
            # 获取系统内存作为参考
            total_memory = psutil.virtual_memory().total / (1024**3)
            memory_fraction = mps_config.get('memory_fraction', 0.7)
            self.available_memory = total_memory * memory_fraction
            
            self.logger.info(f"✅ MPS初始化成功: Apple Silicon GPU")
            self.logger.info(f"   可用内存: {self.available_memory:.1f}GB")
            
            return True
            
        except ImportError:
            self.logger.warning("⚠️ PyTorch MPS支持未安装")
            return False
        except Exception as e:
            self.logger.error(f"❌ MPS初始化失败: {e}")
            return False
    
    def _initialize_cpu(self) -> bool:
        """初始化CPU设备"""
        cpu_config = self.config.get('device_config', {}).get('cpu', {})
        
        try:
            # CPU基本信息 - 不依赖PyTorch
            cpu_count = psutil.cpu_count(logical=True)
            total_memory = psutil.virtual_memory().total / (1024**3)
            self.available_memory = total_memory * 0.8  # 预留20%内存
            self.device_count = 1
            
            # 设置线程数
            n_jobs = cpu_config.get('n_jobs', -1)
            if n_jobs == -1:
                n_jobs = cpu_count
            
            # 尝试设置PyTorch线程数 (如果可用)
            try:
                import torch
                self.device = torch.device('cpu')
                torch.set_num_threads(min(n_jobs, cpu_count))
                self.logger.info(f"   PyTorch CPU后端: 已启用")
            except ImportError:
                self.device = None  # 没有PyTorch，使用纯NumPy/Pandas
                self.logger.info(f"   PyTorch CPU后端: 未安装，使用NumPy/Pandas")
            
            # 设置NumPy线程数
            try:
                import os
                os.environ['OMP_NUM_THREADS'] = str(min(n_jobs, cpu_count))
                os.environ['MKL_NUM_THREADS'] = str(min(n_jobs, cpu_count))
                os.environ['NUMEXPR_NUM_THREADS'] = str(min(n_jobs, cpu_count))
            except:
                pass
            
            self.logger.info(f"✅ CPU初始化成功")
            self.logger.info(f"   CPU核心数: {cpu_count}")
            self.logger.info(f"   使用线程数: {min(n_jobs, cpu_count)}")
            self.logger.info(f"   可用内存: {self.available_memory:.1f}GB")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CPU初始化失败: {e}")
            return False
    
    def _log_device_info(self):
        """记录设备信息"""
        self.logger.info("=" * 60)
        self.logger.info("🖥️  硬件配置信息")
        self.logger.info("=" * 60)
        self.logger.info(f"📱 操作系统: {platform.system()} {platform.release()}")
        self.logger.info(f"🔧 设备类型: {self.device_type.upper()}")
        self.logger.info(f"💾 可用内存: {self.available_memory:.1f}GB")
        self.logger.info(f"🎯 设备数量: {self.device_count}")
        
        if self.device_type == 'cuda':
            self.logger.info(f"⚡ 混合精度: {'启用' if hasattr(self, 'mixed_precision') else '禁用'}")
        
        self.logger.info("=" * 60)
    
    def get_optimal_batch_size(self, base_batch_size: int, factor_count: int, stock_count: int) -> int:
        """
        根据设备性能计算最优批处理大小
        
        Args:
            base_batch_size: 基础批大小
            factor_count: 因子数量
            stock_count: 股票数量
            
        Returns:
            优化后的批大小
        """
        try:
            # 估算内存需求 (GB)
            # 假设每个因子每只股票每天占用8字节 (float64)
            memory_per_batch = base_batch_size * factor_count * 1000 * 8 / (1024**3)  # 1000天数据
            
            # 根据可用内存调整批大小
            if memory_per_batch > self.available_memory * 0.5:  # 不超过50%内存
                scale_factor = (self.available_memory * 0.5) / memory_per_batch
                optimal_batch_size = max(int(base_batch_size * scale_factor), 10)
            else:
                optimal_batch_size = base_batch_size
            
            # 设备类型特定优化
            if self.device_type == 'cuda':
                # GPU可以处理更大的批
                optimal_batch_size = min(optimal_batch_size * 2, stock_count)
            elif self.device_type == 'mps':
                # MPS内存管理较保守
                optimal_batch_size = min(optimal_batch_size, 200)
            
            # 确保批大小在合理范围内
            batch_config = self.config.get('performance_optimization', {}).get('batch_processing', {})
            min_batch = batch_config.get('min_batch_size', 10)
            max_batch = batch_config.get('max_batch_size', 1000)
            
            optimal_batch_size = max(min_batch, min(optimal_batch_size, max_batch))
            
            self.logger.info(f"📊 优化批大小: {base_batch_size} -> {optimal_batch_size}")
            return optimal_batch_size
            
        except Exception as e:
            self.logger.warning(f"⚠️ 批大小优化失败，使用默认值: {e}")
            return base_batch_size
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        return {
            'device': str(self.device) if self.device else None,
            'device_type': self.device_type,
            'device_count': self.device_count,
            'available_memory_gb': self.available_memory,
            'mixed_precision': hasattr(self, 'mixed_precision') and self.mixed_precision
        }
    
    def move_to_device(self, tensor):
        """将张量移动到指定设备"""
        if self.device is not None and hasattr(tensor, 'to'):
            return tensor.to(self.device)
        return tensor
    
    def clear_cache(self):
        """清理设备缓存"""
        try:
            if self.device_type == 'cuda':
                import torch
                torch.cuda.empty_cache()
                self.logger.debug("🧹 CUDA缓存已清理")
            elif self.device_type == 'mps':
                import torch
                if hasattr(torch.mps, 'empty_cache'):
                    torch.mps.empty_cache()
                    self.logger.debug("🧹 MPS缓存已清理")
        except Exception as e:
            self.logger.warning(f"⚠️ 缓存清理失败: {e}")

def create_device_manager(config: Dict[str, Any]) -> DeviceManager:
    """创建设备管理器的工厂函数"""
    return DeviceManager(config.get('acceleration_config', {}))