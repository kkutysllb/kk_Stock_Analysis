# Redis缓存系统

本目录包含股票量化分析系统的Redis缓存服务配置和部署脚本。

## 📁 目录结构

```
redis/
├── README.md                    # 本文件 - 系统概述
├── QUICK_START.md              # 快速启动指南
├── REDIS_DEPLOYMENT_GUIDE.md   # 完整部署文档
├── TROUBLESHOOTING.md          # 故障排除指南
├── docker-compose.redis.yml    # Docker Compose配置
├── redis.conf                  # Redis服务器配置
├── deploy_redis.sh             # 自动化部署脚本（推荐）
├── deploy_redis_offline.sh     # 离线部署脚本
├── fix_network_issues.sh       # 网络问题修复脚本
└── check_environment.sh        # 环境检查脚本
```

## 🚀 快速开始

### 一键部署

```bash
# 1. 进入redis目录
cd redis

# 2. 运行部署脚本
./deploy_redis.sh
```

### 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.redis.yml ps

# 测试Redis连接
docker exec kk_redis_cache redis-cli ping
```

## 📋 文件说明

### 核心配置文件

#### `docker-compose.redis.yml`
- **用途**: Docker Compose服务编排配置
- **包含服务**:
  - `redis`: Redis缓存服务器 (端口6379)
  - `redis-commander`: Web管理界面 (端口8081)
- **特性**:
  - 数据持久化
  - 健康检查
  - 自动重启
  - 网络隔离

#### `redis.conf`
- **用途**: Redis服务器详细配置
- **主要配置**:
  - 内存管理策略
  - 持久化设置 (RDB + AOF)
  - 网络和安全配置
  - 性能优化参数

### 自动化脚本

#### `deploy_redis.sh` (推荐)
- **用途**: 智能一键部署Redis服务
- **功能**:
  - 环境检查
  - 自动网络问题修复
  - 服务部署
  - 健康验证
  - 信息展示
- **选项**:
  - `--clean`: 清理旧数据
  - `--backup`: 创建备份
  - `--test`: 运行测试

#### `deploy_redis_offline.sh`
- **用途**: 离线环境部署Redis服务
- **适用场景**:
  - 网络受限环境
  - Docker Hub无法访问
  - 镜像拉取失败
- **选项**:
  - `--simple`: 仅部署Redis服务
  - `--check-only`: 仅检查环境

#### `fix_network_issues.sh`
- **用途**: 网络问题诊断和修复
- **功能**:
  - Docker镜像源配置
  - 网络连接测试
  - 代理问题检测
  - 缓存清理
- **选项**:
  - `--clean-only`: 仅清理缓存
  - `--test-only`: 仅测试拉取
  - `--mirror-only`: 仅配置镜像源

#### `check_environment.sh`
- **用途**: 环境一致性检查
- **检查项目**:
  - 系统要求
  - Docker环境
  - 必要文件
  - 网络连接
  - 现有服务

### 文档文件

#### `README.md` (本文件)
- 系统概述和目录结构说明

#### `QUICK_START.md`
- 详细的快速启动指南
- 常用操作命令
- 故障排除指南

## 🔧 服务配置

### Redis服务
- **容器名**: `kk_redis_cache`
- **镜像**: `redis:7.0-alpine`
- **端口**: `6379`
- **数据卷**: `redis_data`
- **配置文件**: `./redis.conf`

### Redis Commander
- **容器名**: `kk_redis_commander`
- **镜像**: `rediscommander/redis-commander:latest`
- **端口**: `8081`
- **访问**: http://localhost:8081
- **认证**: admin / redis123

### 网络配置
- **网络名**: `kk_network`
- **类型**: bridge
- **子网**: `172.20.0.0/16`

## 📊 监控和管理

### Web管理界面
访问 http://localhost:8081 使用Redis Commander进行可视化管理：
- 实时监控Redis状态
- 浏览和编辑键值数据
- 执行Redis命令
- 查看内存使用情况

### 命令行管理

```bash
# 进入Redis CLI
docker exec -it kk_redis_cache redis-cli

# 查看服务信息
docker exec kk_redis_cache redis-cli INFO

# 监控实时命令
docker exec kk_redis_cache redis-cli MONITOR
```

## 🔄 与API系统集成

### 缓存配置
API系统的缓存配置位于：
- `../api/cache_config.py` - 缓存策略配置
- `../api/cache_manager.py` - 缓存管理器
- `../api/cache_middleware.py` - 缓存中间件

### 连接配置
API系统通过以下配置连接Redis：

```python
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'decode_responses': True
}
```

### 缓存策略
- **股票基本信息**: 24小时TTL
- **实时行情数据**: 1分钟TTL
- **技术分析数据**: 30分钟TTL
- **财务数据**: 12小时TTL

## 🚨 故障排除

### 快速解决方案

1. **网络问题（镜像拉取失败）**
   ```bash
   # 自动修复网络问题
   ./fix_network_issues.sh
   
   # 或使用离线部署
   ./deploy_redis_offline.sh
   ```

2. **服务无法启动**
   ```bash
   # 检查端口占用
   netstat -tuln | grep 6379
   
   # 查看容器日志
   docker logs kk_redis_cache
   
   # 重新部署
   ./deploy_redis.sh --clean
   ```

3. **连接超时**
   ```bash
   # 检查防火墙设置
   sudo ufw status
   
   # 检查Docker网络
   docker network ls
   
   # 运行环境检查
   ./check_environment.sh
   ```

### 详细故障排除

查看完整的故障排除指南：[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

### 获取帮助

```bash
# 运行环境检查
./check_environment.sh

# 网络问题修复
./fix_network_issues.sh --help

# 离线部署选项
./deploy_redis_offline.sh --help

# 查看部署脚本帮助
./deploy_redis.sh --help
```

## 📈 性能优化

### 内存优化
- 配置合适的 `maxmemory` 限制
- 使用 `allkeys-lru` 淘汰策略
- 定期清理过期键

### 持久化优化
- RDB + AOF 双重保障
- 合理设置保存频率
- 定期备份数据

### 网络优化
- 使用连接池
- 启用TCP keepalive
- 调整超时参数

## 🔒 安全配置

### 生产环境建议
1. **设置密码保护**
   ```bash
   # 在redis.conf中设置
   requirepass your_strong_password
   ```

2. **网络访问控制**
   ```bash
   # 限制绑定地址
   bind 127.0.0.1
   ```

3. **禁用危险命令**
   ```bash
   # 重命名危险命令
   rename-command FLUSHDB ""
   rename-command FLUSHALL ""
   ```

## 📚 相关文档

- [完整部署指南](./REDIS_DEPLOYMENT_GUIDE.md)
- [快速启动指南](./QUICK_START.md)
- [API缓存设计](../api/REDIS_SETUP.md)
- [Redis官方文档](https://redis.io/documentation)

## 🤝 贡献指南

如需修改Redis配置或脚本：

1. 修改相应配置文件
2. 运行环境检查脚本验证
3. 测试部署流程
4. 更新相关文档

## 📄 许可证

本项目遵循项目根目录的许可证条款。

---

**Redis缓存系统** - 为股票量化分析提供高性能缓存支持 🚀