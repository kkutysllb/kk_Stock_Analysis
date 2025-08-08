# GPU加速安装指南

本指南介绍如何为因子挖掘系统配置GPU加速环境。

## 🚀 支持的硬件

### NVIDIA GPU
- **RTX 4090** (推荐) - 24GB显存
- **RTX 4080** - 16GB显存  
- **RTX 3090/3080** - 10-24GB显存
- **Tesla V100/A100** (服务器)
- 需要CUDA 11.8+支持

### Apple Silicon
- **M1 Pro/Max/Ultra**
- **M2 Pro/Max/Ultra** 
- **M3 Pro/Max/Ultra**
- 通过Metal Performance Shaders (MPS)加速

## 📦 安装步骤

### 1. NVIDIA GPU环境 (Linux/Windows)

#### 检查GPU状态
```bash
nvidia-smi
```

#### 安装PyTorch (推荐conda)
```bash
# CUDA 12.4版本 (推荐)
conda install pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia

# 或CUDA 11.8版本
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
```

#### 安装GPU加速依赖
```bash
pip install -r requirements-gpu.txt
```

#### 验证GPU安装
```python
import torch
print(f"CUDA可用: {torch.cuda.is_available()}")
print(f"GPU数量: {torch.cuda.device_count()}")
print(f"当前GPU: {torch.cuda.get_device_name(0)}")
```

### 2. Apple Silicon环境 (Mac)

#### 安装PyTorch
```bash
# Apple Silicon优化版本
conda install pytorch torchvision torchaudio -c pytorch
```

#### 安装Mac依赖
```bash
pip install -r requirements-mac.txt
```

#### 验证MPS安装
```python
import torch
print(f"MPS可用: {torch.backends.mps.is_available()}")
```

### 3. CPU环境 (备用)

如果没有GPU或遇到问题：
```bash
pip install -r requirements.txt
```

## ⚡ 性能优化配置

### 配置文件调优
在 `factor_mining_config.yaml` 中调整：

```yaml
acceleration_config:
  device_config:
    # 双4090配置
    cuda:
      device_ids: [0, 1]          # 使用两张卡
      memory_fraction: 0.8        # 每张卡80%内存
      mixed_precision: true       # 混合精度加速
      
    # Mac配置  
    mps:
      memory_fraction: 0.7        # 70%内存
      
  performance_optimization:
    batch_processing:
      adaptive_batch_size: true   # 自适应批大小
      max_batch_size: 1000        # 最大批处理大小
```

### 命令行使用
```bash
# 自动检测最优设备
python run_factor_mining_system.py --index-type csi_a500

# 强制使用CUDA
python run_factor_mining_system.py --index-type csi_a500 --device cuda

# 强制使用MPS (Mac)  
python run_factor_mining_system.py --index-type csi_a500 --device mps

# 禁用GPU
python run_factor_mining_system.py --index-type csi_a500 --disable-gpu

# 自定义批大小
python run_factor_mining_system.py --index-type csi_a500 --batch-size 500
```

## 🔧 故障排除

### 常见问题

1. **PyTorch未安装**
   ```
   No module named 'torch'
   ```
   解决：按上述步骤安装PyTorch

2. **CUDA版本不匹配**
   ```
   CUDA runtime version mismatch
   ```
   解决：重新安装匹配的PyTorch版本

3. **GPU内存不足**
   ```
   CUDA out of memory
   ```
   解决：降低batch_size或memory_fraction

4. **Mac MPS错误**
   ```
   MPS backend not available
   ```
   解决：确保macOS 12.3+和PyTorch 1.12+

### 性能监控
```bash
# 监控GPU使用率
nvidia-smi -l 1

# 监控系统资源
htop

# Python内监控
python -c "
import psutil, GPUtil
print('CPU:', psutil.cpu_percent())
print('Memory:', psutil.virtual_memory().percent, '%')
if GPUtil.getGPUs():
    gpu = GPUtil.getGPUs()[0]
    print(f'GPU: {gpu.load*100:.1f}%, Memory: {gpu.memoryUtil*100:.1f}%')
"
```

## 📈 性能预期

### 双RTX 4090环境
- 因子计算: **10-20x**加速
- IC计算: **15-30x**加速  
- 模型训练: **5-15x**加速
- 内存使用: 减少**50%**

### Apple M系列
- 因子计算: **3-5x**加速
- IC计算: **5-10x**加速
- 模型训练: **2-5x**加速

### 注意事项
- 首次运行会有JIT编译开销
- 小数据集可能CPU更快
- 批大小越大，GPU优势越明显
- 定期清理GPU缓存避免内存泄漏