# 本地Qwen3-32B模型部署说明

## 🎯 概述

本系统完全基于**本地部署的Qwen3-32B**模型，支持多种部署方式，无需依赖任何在线API服务。

## 📋 支持的部署方式

### 1. **vLLM服务部署** (推荐生产环境)

```bash
# 1. 安装vLLM
pip install vllm

# 2. 启动vLLM服务
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-32B-Instruct \
    --served-model-name Qwen/Qwen2.5-32B-Instruct \
    --host 0.0.0.0 \
    --port 8000

# 3. 验证服务
curl http://localhost:8000/v1/models
```

### 2. **LM Studio部署** (推荐开发调试)

```bash
# 1. 下载并安装LM Studio
# https://lmstudio.ai/

# 2. 在LM Studio中加载Qwen2.5-32B-Instruct模型

# 3. 启动本地服务器 (默认端口1234)

# 4. 验证服务
curl http://localhost:1234/v1/models
```

### 3. **Transformers直接调用**

```python
# 适用于有足够GPU内存的情况
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "Qwen/Qwen2.5-32B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
```

## 🔧 系统配置

### 配置文件示例

```python
# 1. vLLM配置
config = {
    'llm_provider': 'vllm',
    'model_name': 'Qwen/Qwen2.5-32B-Instruct',
    'api_url': 'http://localhost:8000/v1/chat/completions'
}

# 2. LM Studio配置
config = {
    'llm_provider': 'lm_studio',
    'model_name': 'Qwen/Qwen2.5-32B-Instruct',
    'api_url': 'http://localhost:1234/v1/chat/completions'
}

# 3. 本地直接调用配置
config = {
    'llm_provider': 'local_qwen',
    'model_name': 'Qwen/Qwen2.5-32B-Instruct',
    'api_url': 'http://localhost:8000/v1/chat/completions'
}
```

## 🚀 快速启动

### 步骤1：安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 确保安装了PyTorch (GPU支持)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 步骤2：启动模型服务

```bash
# 方式1：使用vLLM (推荐)
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-32B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.8

# 方式2：使用LM Studio
# 打开LM Studio -> 加载模型 -> 启动服务器
```

### 步骤3：测试系统

```bash
# 测试模型服务
curl http://localhost:8000/v1/models

# 或者测试聊天接口
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-32B-Instruct",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## 💡 性能调优建议

### 硬件要求

- **GPU内存**: 至少24GB (RTX 4090/A6000或更高)
- **系统内存**: 至少32GB RAM
- **存储**: SSD存储，至少100GB可用空间

### vLLM优化参数

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-32B-Instruct \
    --tensor-parallel-size 2 \  # 多GPU并行
    --gpu-memory-utilization 0.9 \  # GPU内存使用率
    --max-model-len 4096 \  # 最大序列长度
    --disable-log-stats \  # 禁用统计日志
    --host 0.0.0.0 \
    --port 8000
```

### LM Studio优化

1. 设置合适的上下文长度 (建议4096)
2. 启用GPU加速
3. 调整批处理大小
4. 设置合适的温度参数 (0.7)

## 🔍 故障排除

### 常见问题

1. **模型加载失败**
   ```bash
   # 检查模型是否下载完整
   huggingface-cli download Qwen/Qwen2.5-32B-Instruct
   ```

2. **GPU内存不足**
   ```bash
   # 降低GPU内存使用率
   --gpu-memory-utilization 0.6
   
   # 或使用CPU推理 (较慢)
   --device cpu
   ```

3. **API连接失败**
   ```bash
   # 检查服务是否运行
   curl http://localhost:8000/v1/models
   
   # 检查防火墙设置
   netstat -an | grep :8000
   ```

### 日志调试

```python
import logging
import requests

logging.basicConfig(level=logging.DEBUG)

# 测试API连接
response = requests.get("http://localhost:8000/v1/models")
print(f"API状态: {response.status_code}")
print(f"可用模型: {response.json()}")
```

## 📊 性能监控

### 系统监控脚本

```python
#!/usr/bin/env python3
import requests
import time
import psutil

def monitor_system():
    """监控系统性能"""
    while True:
        # 检查API健康状态
        try:
            response = requests.get("http://localhost:8000/health")
            api_status = "✅" if response.status_code == 200 else "❌"
        except:
            api_status = "❌"
        
        # 系统资源
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        print(f"API状态: {api_status} | CPU: {cpu_percent:.1f}% | 内存: {memory_percent:.1f}%")
        time.sleep(10)

if __name__ == "__main__":
    monitor_system()
```

## 🎯 最佳实践

1. **开发环境**: 使用LM Studio，便于调试和测试
2. **生产环境**: 使用vLLM，性能更好，支持并发
3. **模型管理**: 使用HuggingFace Hub管理模型版本
4. **资源监控**: 定期监控GPU和内存使用情况
5. **备份策略**: 定期备份模型和配置文件

## 📞 技术支持

如果在部署过程中遇到问题，请：

1. 检查日志输出
2. 验证硬件配置
3. 确认网络连接
4. 查看官方文档:
   - [vLLM文档](https://docs.vllm.ai/)
   - [Qwen模型文档](https://github.com/QwenLM/Qwen)
   - [LM Studio文档](https://lmstudio.ai/docs)