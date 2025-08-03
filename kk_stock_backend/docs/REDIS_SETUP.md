# Redis缓存集成指南

## 概述

本项目已集成Redis缓存系统，用于提升API查询性能和减少数据库负载。Redis缓存支持多种数据类型的智能缓存策略，可显著提升系统响应速度。

## 功能特性

### 🚀 核心功能
- **智能缓存策略**: 根据数据类型自动选择合适的缓存时间
- **多层缓存架构**: 支持装饰器、中间件、手动缓存等多种方式
- **缓存预热**: 支持系统启动时预加载热点数据
- **性能监控**: 实时监控缓存命中率和性能指标
- **灵活配置**: 支持不同环境的缓存配置

### 📊 缓存策略
- **实时数据**: 1-10分钟缓存（行情、龙虎榜等）
- **日常数据**: 30分钟-4小时缓存（日线数据、搜索结果等）
- **基础数据**: 12-24小时缓存（股票信息、财务数据等）
- **静态数据**: 7天缓存（交易日历等）

## 快速部署Redis

### 🚀 推荐方式：使用项目配置的Docker部署

项目已提供完整的Redis部署配置，位于 `../redis/` 目录：

```bash
# 1. 进入redis目录
cd ../redis

# 2. 一键部署（推荐）
./deploy_redis.sh

# 或者手动部署
docker-compose -f docker-compose.redis.yml up -d
```

**包含服务：**
- Redis缓存服务器 (端口6379)
- Redis Commander管理界面 (端口8081)

**详细部署指南：**
- [快速启动指南](../redis/QUICK_START.md)
- [完整部署文档](../redis/REDIS_DEPLOYMENT_GUIDE.md)

### 传统安装方式

#### Ubuntu/Debian
```bash
# 更新包列表
sudo apt update

# 安装Redis
sudo apt install redis-server

# 启动Redis服务
sudo systemctl start redis-server

# 设置开机自启
sudo systemctl enable redis-server

# 检查服务状态
sudo systemctl status redis-server
```

#### CentOS/RHEL
```bash
# 安装EPEL仓库
sudo yum install epel-release

# 安装Redis
sudo yum install redis

# 启动Redis服务
sudo systemctl start redis

# 设置开机自启
sudo systemctl enable redis

# 检查服务状态
sudo systemctl status redis
```

#### macOS
```bash
# 使用Homebrew安装
brew install redis

# 启动Redis服务
brew services start redis

# 或者手动启动
redis-server
```

#### 手动Docker部署
```bash
# 拉取Redis镜像
docker pull redis:7.0-alpine

# 运行Redis容器
docker run -d \
  --name redis-cache \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7.0-alpine redis-server --appendonly yes

# 检查容器状态
docker ps | grep redis
```

## Redis配置

### 基础配置
编辑Redis配置文件 `/etc/redis/redis.conf`：

```conf
# 绑定地址（生产环境建议只绑定内网IP）
bind 127.0.0.1

# 端口
port 6379

# 密码（生产环境强烈建议设置）
# requirepass your_strong_password

# 最大内存限制
maxmemory 2gb

# 内存淘汰策略
maxmemory-policy allkeys-lru

# 持久化配置
save 900 1
save 300 10
save 60 10000

# AOF持久化
appendonly yes
appendfsync everysec

# 日志级别
loglevel notice
logfile /var/log/redis/redis-server.log
```

### 性能优化配置
```conf
# TCP连接配置
tcp-keepalive 300
timeout 0

# 客户端连接数限制
maxclients 10000

# 禁用危险命令（生产环境）
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG ""

# 慢查询日志
slowlog-log-slower-than 10000
slowlog-max-len 128
```

## 环境变量配置

在项目根目录创建或编辑 `.env` 文件：

```env
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 环境设置
ENVIRONMENT=development

# API配置
API_PORT=9000
API_HOST=0.0.0.0
```

## 安装Python依赖

```bash
# 进入API目录
cd api

# 安装依赖
pip install -r requirements_api.txt

# 或者单独安装Redis相关包
pip install redis>=5.0.0 hiredis>=2.2.0
```

## 启动和测试

### 1. 启动Redis服务
```bash
# 检查Redis是否运行
redis-cli ping
# 应该返回: PONG

# 查看Redis信息
redis-cli info server
```

### 2. 启动API服务
```bash
# 进入API目录
cd api

# 启动服务
python main.py
```

### 3. 测试缓存功能

访问以下端点测试缓存功能：

```bash
# 缓存统计
curl http://localhost:9000/cache/cache-stats

# 缓存演示
curl "http://localhost:9000/cache/cached-stock-list?market=主板&limit=10"

# 手动缓存演示
curl "http://localhost:9000/cache/manual-cache-demo?symbol=000001.SZ"

# 性能测试
curl "http://localhost:9000/cache/performance-test?iterations=20&use_cache=true"

# 缓存预热
curl "http://localhost:9000/cache/cache-warmup?data_type=stock_basic&limit=100"

# 系统指标（包含缓存状态）
curl http://localhost:9000/metrics
```

## 缓存使用方式

### 1. 装饰器方式（推荐）
```python
from cache_middleware import cache_endpoint

@router.get("/stocks")
@cache_endpoint(data_type='stock_list', ttl=1800)
async def get_stocks():
    # 自动缓存30分钟
    return await query_stocks()
```

### 2. 手动缓存
```python
from cache_manager import get_cache_manager

async def get_stock_detail(symbol: str):
    cache_manager = get_cache_manager()
    cache_key = f"stock:detail:{symbol}"
    
    # 尝试从缓存获取
    cached_data = await cache_manager.async_get(cache_key)
    if cached_data:
        return cached_data
    
    # 查询数据库
    data = await query_database(symbol)
    
    # 存储到缓存
    await cache_manager.async_set(cache_key, data, 3600)
    return data
```

### 3. 中间件自动缓存
中间件会自动缓存GET请求的响应，无需修改现有代码。

## 监控和维护

### 缓存监控
```bash
# 查看缓存统计
curl http://localhost:9000/cache/cache-stats

# 查看系统指标
curl http://localhost:9000/metrics

# Redis命令行监控
redis-cli monitor

# 查看内存使用
redis-cli info memory

# 查看慢查询
redis-cli slowlog get 10
```

### 缓存清理
```bash
# 清理特定模式的缓存
curl -X DELETE "http://localhost:9000/cache/clear?pattern=stock"

# 清理所有API缓存
curl -X DELETE http://localhost:9000/cache/clear

# Redis命令行清理
redis-cli FLUSHDB  # 清理当前数据库
redis-cli FLUSHALL # 清理所有数据库（谨慎使用）
```

## 生产环境部署

### 安全配置
1. **设置密码**：在redis.conf中设置requirepass
2. **绑定内网IP**：避免暴露到公网
3. **禁用危险命令**：重命名或禁用FLUSHDB等命令
4. **防火墙配置**：只允许应用服务器访问Redis端口

### 高可用配置
1. **主从复制**：配置Redis主从架构
2. **哨兵模式**：实现自动故障转移
3. **集群模式**：支持数据分片和高并发

### 监控告警
1. **内存使用率**：监控Redis内存使用情况
2. **连接数**：监控客户端连接数
3. **命中率**：监控缓存命中率
4. **慢查询**：监控慢查询日志

## 故障排除

### 常见问题

1. **连接失败**
   ```bash
   # 检查Redis服务状态
   sudo systemctl status redis
   
   # 检查端口是否监听
   netstat -tlnp | grep 6379
   
   # 测试连接
   redis-cli ping
   ```

2. **内存不足**
   ```bash
   # 查看内存使用
   redis-cli info memory
   
   # 清理过期键
   redis-cli --scan --pattern "*" | xargs redis-cli del
   
   # 调整maxmemory配置
   redis-cli config set maxmemory 4gb
   ```

3. **性能问题**
   ```bash
   # 查看慢查询
   redis-cli slowlog get 10
   
   # 监控命令执行
   redis-cli monitor
   
   # 检查持久化配置
   redis-cli config get save
   ```

### 日志分析
```bash
# 查看Redis日志
tail -f /var/log/redis/redis-server.log

# 查看API日志中的缓存相关信息
grep -i "cache\|redis" /path/to/api.log
```

## 性能优化建议

1. **合理设置TTL**：根据数据更新频率设置合适的过期时间
2. **使用连接池**：避免频繁创建和销毁连接
3. **批量操作**：使用pipeline进行批量读写
4. **内存优化**：选择合适的数据结构和编码方式
5. **监控调优**：根据监控数据调整配置参数

## 扩展功能

- **分布式锁**：实现分布式环境下的并发控制
- **消息队列**：使用Redis实现简单的消息队列
- **会话存储**：将用户会话存储在Redis中
- **限流控制**：实现API访问频率限制

---

通过以上配置，您的API系统将获得显著的性能提升。如有问题，请查看日志或联系技术支持。