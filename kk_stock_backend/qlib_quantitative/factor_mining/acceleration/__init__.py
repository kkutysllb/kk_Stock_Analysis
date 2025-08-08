"""
因子挖掘加速模块
提供GPU/CPU/MPS硬件加速支持
"""

from .device_manager import DeviceManager, create_device_manager
from .gpu_accelerator import GPUAccelerator

__all__ = [
    'DeviceManager',
    'create_device_manager', 
    'GPUAccelerator'
]