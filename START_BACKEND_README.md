# 🚀 KK股票量化分析系统后端启动脚本使用指南

## 📋 概述

`start_backend.sh` 是一个功能强大的后端服务管理脚本，专为 **KK股票量化分析系统后端** 设计。该脚本基于 `Python 3.11 + FastAPI + Uvicorn` 架构，提供完整的开发、生产和部署解决方案，支持全局路径配置和灵活的环境管理。

## ✨ 主要功能

### 🌍 全局路径配置
- **智能路径检测** - 自动检测项目根目录和子目录结构
- **环境变量支持** - 支持通过环境变量覆盖默认路径配置
- **路径验证** - 自动验证项目目录结构完整性
- **调试模式** - 提供路径配置调试信息输出

### 🔧 环境管理
- **Conda环境检查** - 自动检测并创建Conda虚拟环境
- **依赖管理** - 智能安装和更新Python依赖包
- **环境变量配置** - 自动设置API服务相关环境变量
- **Python版本验证** - 确保使用正确的Python版本（3.11）

### 🚀 服务模式
- **前台模式** - 开发调试使用，支持实时日志输出
- **后台模式** - 生产环境使用，支持daemon进程管理
- **多Worker支持** - 支持单worker和多worker模式
- **生产级配置** - 完整的并发连接、Keep-alive等配置

### 📊 进程管理
- **后台服务管理** - 支持启动、停止、重启后台服务
- **PID文件管理** - 自动管理进程ID文件
- **优雅关闭** - 支持TERM信号优雅停止和KILL强制终止
- **状态监控** - 实时查看服务运行状态

### 📝 日志系统
- **详细日志记录** - 启动/运行/错误日志完整记录
- **日志分类管理** - 启动日志和daemon日志分离存储
- **实时日志查看** - 支持日志实时跟踪和查看
- **自动清理** - 7天前的日志自动删除

### ⚙️ 高级配置
- **并发控制** - 可配置最大并发连接数和连接队列长度
- **性能优化** - Keep-alive超时、Worker数量等参数调优
- **环境适配** - 支持开发、测试、生产环境配置

## 🛠️ 使用方法

### 基础命令

```bash
# 显示帮助信息（查看全局路径配置）
./start_backend.sh --help

# 查看服务状态
./start_backend.sh status

# 前台启动服务（开发模式）
./start_backend.sh

# 后台启动服务（生产模式）
./start_backend.sh --daemon

# 停止后台服务
./start_backend.sh stop

# 重启后台服务
./start_backend.sh restart
```

### 高级选项

```bash
# 自定义主机和端口
./start_backend.sh --host 0.0.0.0 --port 9001 --daemon

# 指定Worker数量（生产环境推荐）
./start_backend.sh --workers 8 --daemon

# 单Worker模式（开发调试）
./start_backend.sh --workers 1 --daemon

# 强制更新依赖包
./start_backend.sh --update-deps --daemon

# 指定运行环境
./start_backend.sh --env production --daemon
```

### 全局路径配置

```bash
# 使用默认路径配置
./start_backend.sh --daemon

# 自定义项目根目录
KK_PROJECT_ROOT=/custom/path ./start_backend.sh --daemon

# 自定义后端目录
KK_BACKEND_DIR=/custom/backend ./start_backend.sh --daemon

# 启用路径调试信息
DEBUG_PATHS=true ./start_backend.sh --debug-paths --daemon
```

### 日志管理

```bash
# 查看最新启动日志（实时跟踪）
./start_backend.sh logs

# 查看最新后台运行日志（实时跟踪）
./start_backend.sh logs --daemon

# 列出所有日志文件
./start_backend.sh list-logs

# 清理7天前的日志
./start_backend.sh --clean-logs
```

### 服务管理命令

```bash
# 显式启动命令
./start_backend.sh start                    # 前台启动
./start_backend.sh start --daemon           # 后台启动
./start_backend.sh start --workers 4        # 指定worker数

# 服务状态管理
./start_backend.sh status                   # 查看状态
./start_backend.sh stop                     # 停止服务
./start_backend.sh restart                  # 重启服务
```

## 📁 项目结构

```
kk_Stock_Analysis/
├── start_backend.sh           # 后端启动脚本
├── kk_stock_backend/          # 后端项目目录
│   ├── api/                   # API接口层
│   │   ├── main.py           # API服务入口
│   │   └── routers/          # 路由模块（20+个API模块）
│   ├── analysis/             # 核心分析引擎
│   ├── backtrader_strategies/ # 量化策略框架
│   ├── qlib_quantitative/    # Qlib深度学习框架
│   ├── requirements.txt      # Python依赖
│   ├── environment.yml       # Conda环境配置
│   ├── kk_stock_backend.pid  # PID文件（运行时创建）
│   └── logs/                 # 日志目录（自动创建）
│       ├── startup_*.log     # 启动日志
│       └── daemon_*.log      # 后台运行日志
└── kk_stock_desktop/         # 前端项目目录
```

## 🔧 配置说明

### 默认配置
- **API主机**: 0.0.0.0（所有网卡）
- **API端口**: 9001
- **Worker数量**: 4（生产环境）
- **最大并发连接**: 1000
- **Keep-alive超时**: 5秒
- **连接队列长度**: 2048
- **Python版本**: 3.11
- **Conda环境名**: kk_stock

### 环境变量
脚本支持以下环境变量配置：

#### 全局路径配置
- `KK_PROJECT_ROOT` - 覆盖项目根目录路径
- `KK_BACKEND_DIR` - 覆盖后端目录路径
- `KK_FRONTEND_DIR` - 覆盖前端目录路径
- `DEBUG_PATHS=true` - 启用路径调试信息

#### 服务配置
- `API_HOST` - API服务主机地址
- `API_PORT` - API服务端口
- `ENVIRONMENT` - 运行环境（development/production）
- `UVICORN_WORKERS` - Worker进程数量
- `UVICORN_LIMIT_CONCURRENCY` - 最大并发连接数
- `UVICORN_KEEPALIVE` - Keep-alive超时时间
- `UVICORN_BACKLOG` - 连接队列长度

## 📊 服务状态说明

### 状态检查输出示例
```
[SUCCESS] 服务正在运行 (PID: 12345)
[INFO] 服务地址: http://0.0.0.0:9001
[INFO] API文档: http://0.0.0.0:9001/docs
[INFO] 日志文件: /path/to/logs/daemon_20240804.log
```

### 进程文件
- `kk_stock_backend.pid` - 后台服务进程ID文件
- 位置：`{后端目录}/kk_stock_backend.pid`

### API文档访问
- **Swagger UI**: `http://localhost:9001/docs`
- **ReDoc**: `http://localhost:9001/redoc`
- **OpenAPI规范**: `http://localhost:9001/openapi.json`

## 💡 最佳实践

### 开发环境启动
1. **首次启动**：
   ```bash
   ./start_backend.sh
   ```

2. **后台开发**（推荐用于长期开发）：
   ```bash
   ./start_backend.sh --workers 1 --daemon
   ```

3. **调试模式**：
   ```bash
   DEBUG_PATHS=true ./start_backend.sh --debug-paths
   ```

### 生产环境部署
1. **多Worker生产模式**：
   ```bash
   ./start_backend.sh --workers 8 --daemon
   ```

2. **高并发配置**：
   ```bash
   UVICORN_LIMIT_CONCURRENCY=2000 UVICORN_BACKLOG=4096 ./start_backend.sh --workers 16 --daemon
   ```

3. **自定义路径部署**：
   ```bash
   KK_PROJECT_ROOT=/opt/kk_stock ./start_backend.sh --daemon
   ```

### 日常维护
1. **检查服务状态**：
   ```bash
   ./start_backend.sh status
   ```

2. **查看实时日志**：
   ```bash
   ./start_backend.sh logs --daemon
   ```

3. **重启服务**：
   ```bash
   ./start_backend.sh restart
   ```

4. **清理日志**：
   ```bash
   ./start_backend.sh --clean-logs
   ```

## ⚠️ 注意事项

1. **端口冲突**：确保9001端口未被其他应用占用
2. **Conda环境**：需要预先安装Anaconda或Miniconda
3. **Python版本**：推荐使用Python 3.11版本
4. **依赖安装**：首次运行需要创建虚拟环境和安装依赖
5. **权限问题**：脚本需要可执行权限（`chmod +x start_backend.sh`）
6. **数据库连接**：确保MongoDB和Redis服务正常运行
7. **环境变量**：生产环境需要设置Tushare Token等API密钥

## 🐛 故障排除

### 常见问题

1. **端口被占用**：
   ```bash
   # 查找占用端口的进程
   lsof -i :9001
   # 强制结束进程
   kill -9 <PID>
   ```

2. **Conda环境问题**：
   ```bash
   # 重新创建虚拟环境
   conda env remove -n kk_stock
   conda env create -f kk_stock_backend/environment.yml
   ```

3. **依赖安装失败**：
   ```bash
   # 手动激活环境并安装依赖
   conda activate kk_stock
   pip install -r kk_stock_backend/requirements.txt --upgrade
   ```

4. **服务启动失败**：
   ```bash
   # 检查启动日志
   ./start_backend.sh logs
   # 或查看具体日志文件
   tail -f kk_stock_backend/logs/startup_*.log
   ```

5. **路径配置问题**：
   ```bash
   # 启用路径调试
   DEBUG_PATHS=true ./start_backend.sh --debug-paths --help
   ```

### 性能调优

1. **Worker数量设置**：
   - 开发环境：1个worker
   - 测试环境：2-4个worker  
   - 生产环境：CPU核心数的1-2倍

2. **内存优化**：
   ```bash
   # 监控内存使用
   ps aux | grep uvicorn
   # 适当调整worker数量
   ```

3. **并发连接调优**：
   ```bash
   # 高并发场景
   UVICORN_LIMIT_CONCURRENCY=2000 ./start_backend.sh --workers 16 --daemon
   ```

### 日志分析
所有运行日志都保存在 `kk_stock_backend/logs/` 目录下：

```bash
# 实时查看启动日志
./start_backend.sh logs

# 实时查看后台运行日志  
./start_backend.sh logs --daemon

# 查看具体日志文件
tail -f kk_stock_backend/logs/daemon_20240804.log

# 查看错误日志
grep -i error kk_stock_backend/logs/*.log
```

## 🎯 总结

`start_backend.sh` 脚本为KK股票量化分析系统后端提供了完整的服务管理解决方案。通过全局路径配置、智能环境管理和灵活的部署选项，大大简化了后端服务的开发、测试和生产部署流程。无论是单机开发还是集群部署，都能提供稳定可靠的服务管理能力。

### 🌟 核心优势
- 🌍 **全局路径配置** - 灵活适配不同部署环境
- 🔧 **智能环境管理** - 自动化Conda环境和依赖管理  
- 🚀 **生产级部署** - 支持多Worker高并发模式
- 📊 **完善监控** - 详细的日志记录和状态监控
- 🛠️ **易于维护** - 简单的命令行接口和故障排查

---

**Happy Coding! 🚀**