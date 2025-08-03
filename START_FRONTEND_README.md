# 🚀 KK股票分析系统前端启动脚本使用指南

## 📋 概述

`start_frontend.sh` 是一个功能强大的前端项目管理脚本，专为 **KK股票量化分析系统前端** 设计。该脚本基于 `Vue3 + Vite + Electron` 架构，提供完整的开发、构建和部署解决方案。

## ✨ 主要功能

### 🔧 环境管理
- **Node.js 版本检查** - 自动检测并验证 Node.js 环境（≥18.0.0）
- **包管理器智能检测** - 自动识别 npm/yarn/pnpm
- **依赖自动安装** - 智能检查和安装项目依赖
- **后端连接检查** - 验证后端API服务可用性

### 🚀 开发模式
- **Web开发服务器** - 支持前台/后台模式启动
- **Electron开发模式** - 桌面应用开发环境
- **热重载支持** - 代码修改实时预览
- **端口冲突检测** - 自动检查端口占用情况

### 📦 构建功能
- **生产版本构建** - Web + Electron 完整构建
- **多平台支持** - macOS/Windows/Linux 交叉编译
- **构建产物管理** - 自动清理和组织构建文件

### 📊 进程管理
- **后台服务管理** - 支持后台运行和进程监控
- **服务状态检查** - 实时查看运行状态
- **优雅停止** - 安全关闭所有服务进程
- **一键重启** - 快速重启开发环境

### 📝 日志系统
- **详细日志记录** - 启动/运行/错误日志完整记录
- **日志分类管理** - Web/Electron/Startup 日志分离
- **实时日志查看** - 支持日志实时跟踪
- **自动清理** - 7天前的日志自动删除

## 🛠️ 使用方法

### 基础命令

```bash
# 显示帮助信息
./start_frontend.sh --help

# 查看服务状态
./start_frontend.sh status

# 启动Web开发服务器（默认模式）
./start_frontend.sh dev

# 启动Electron开发模式
./start_frontend.sh electron

# 停止所有服务
./start_frontend.sh stop

# 重启所有服务
./start_frontend.sh restart
```

### 高级选项

```bash
# 自定义端口启动
./start_frontend.sh --port 3000 dev

# 后台运行模式
./start_frontend.sh dev --daemon

# 指定包管理器
./start_frontend.sh --manager yarn dev

# 自定义后端API地址
./start_frontend.sh --backend-url http://192.168.1.100:9001 dev
```

### 构建命令

```bash
# 构建Web生产版本
./start_frontend.sh build

# 构建macOS版本
./start_frontend.sh build mac

# 构建Windows版本
./start_frontend.sh build win

# 构建Linux版本
./start_frontend.sh build linux

# 构建所有平台版本
./start_frontend.sh build all
```

### 日志管理

```bash
# 查看最新启动日志
./start_frontend.sh logs

# 查看Web开发服务器日志
./start_frontend.sh logs web

# 查看Electron应用日志
./start_frontend.sh logs electron

# 清理7天前的日志
./start_frontend.sh --clean-logs
```

## 📁 项目结构

```
kk_Stock_Analysis/
├── start_frontend.sh          # 前端启动脚本
├── kk_stock_desktop/          # 前端项目目录
│   ├── src/                   # 源代码
│   ├── electron/              # Electron主进程代码
│   ├── package.json           # 项目配置
│   ├── vite.config.ts         # Vite配置
│   └── logs/                  # 日志目录（自动创建）
│       ├── startup_*.log      # 启动日志
│       ├── web_dev_*.log      # Web开发日志
│       └── electron_dev_*.log # Electron开发日志
└── kk_stock_backend/          # 后端项目目录
```

## 🔧 配置说明

### 默认配置
- **开发端口**: 5173
- **主机地址**: localhost
- **后端API**: http://localhost:9001
- **Node.js要求**: ≥18.0.0
- **日志保留**: 7天

### 环境变量
脚本会自动设置以下环境变量：
- `VITE_API_BASE_URL` - 后端API基础地址
- `VITE_APP_VERSION` - 应用版本号
- `ELECTRON_RENDERER_URL` - Electron渲染进程URL

## 📊 服务状态说明

### 状态检查输出示例
```
📊 前端服务状态检查
🌐 Web开发服务器正在运行 (PID: 12345)
   访问地址: http://localhost:5173
⚡ Electron应用正在运行 (PID: 12346)
🔌 端口 5173 被占用 (PID: 12345)
```

### 进程文件
- `web_dev.pid` - Web开发服务器进程ID
- `electron_dev.pid` - Electron应用进程ID

## 💡 最佳实践

### 开发环境启动
1. **首次启动**：
   ```bash
   ./start_frontend.sh dev
   ```

2. **桌面应用开发**：
   ```bash
   ./start_frontend.sh electron
   ```

3. **后台开发**（推荐用于长期开发）：
   ```bash
   ./start_frontend.sh dev --daemon
   ```

### 生产环境部署
1. **构建生产版本**：
   ```bash
   ./start_frontend.sh build
   ```

2. **构建桌面应用**：
   ```bash
   ./start_frontend.sh build mac  # macOS版本
   ```

### 日常维护
1. **检查服务状态**：
   ```bash
   ./start_frontend.sh status
   ```

2. **清理日志**：
   ```bash
   ./start_frontend.sh --clean-logs
   ```

3. **重启服务**：
   ```bash
   ./start_frontend.sh restart
   ```

## ⚠️ 注意事项

1. **端口冲突**：确保5173端口未被其他应用占用
2. **Node.js版本**：推荐使用 Node.js 18+ 版本
3. **网络连接**：确保后端服务(9001端口)可正常访问
4. **权限问题**：脚本需要可执行权限 (`chmod +x start_frontend.sh`)
5. **依赖安装**：首次运行可能需要较长时间安装依赖

## 🐛 故障排除

### 常见问题

1. **端口被占用**：
   ```bash
   # 查找占用端口的进程
   lsof -i :5173
   # 强制结束进程
   kill -9 <PID>
   ```

2. **依赖安装失败**：
   ```bash
   # 清理node_modules重新安装
   cd kk_stock_desktop
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Electron启动失败**：
   ```bash
   # 检查Electron是否正确安装
   cd kk_stock_desktop
   npm list electron
   ```

### 日志查看
所有运行日志都保存在 `kk_stock_desktop/logs/` 目录下，可以通过以下方式查看：

```bash
# 实时查看启动日志
./start_frontend.sh logs

# 查看具体日志文件
tail -f kk_stock_desktop/logs/web_dev_20250804.log
```

## 🎯 总结

`start_frontend.sh` 脚本为KK股票分析系统前端提供了完整的开发、构建和部署解决方案。通过简单的命令就能管理整个前端开发生命周期，大大提高了开发效率和项目管理的便利性。

---

**Happy Coding! 🚀**