# Redis缓存服务快速启动指南

## 🚀 一键部署

### 方式一：自动化部署（推荐）

```bash
# 1. 进入redis目录
cd redis

# 2. 检查环境
./check_environment.sh

# 3. 一键部署
./deploy_redis.sh
```

### 方式二：手动部署

```bash
# 1. 进入redis目录
cd redis

# 2. 启动服务
docker-compose -f docker-compose.redis.yml up -d

# 3. 验证部署
docker-compose -f docker-compose.redis.yml ps
```

## 📋 部署检查清单

### 环境要求
- [x] Docker 20.10+
- [x] Docker Compose 2.0+
- [x] 2GB+ 可用内存
- [x] 10GB+ 可用磁盘空间

### 端口检查
- [x] 6379 (Redis服务)
- [x] 8081 (Redis Commander管理界面)

### 文件检查
- [x] `docker-compose.redis.yml`
- [x] `redis.conf`
- [x] `deploy_redis.sh`
- [x] `check_environment.sh`

## 🔧 服务管理

### 基本操作

```bash
# 启动服务
docker-compose -f docker-compose.redis.yml up -d

# 停止服务
docker-compose -f docker-compose.redis.yml down

# 重启服务
docker-compose -f docker-compose.redis.yml restart

# 查看状态
docker-compose -f docker-compose.redis.yml ps

# 查看日志
docker-compose -f docker-compose.redis.yml logs -f redis
```

### Redis命令行

```bash
# 进入Redis CLI
docker exec -it kk_redis_cache redis-cli

# 测试连接
docker exec kk_redis_cache redis-cli ping

# 查看信息
docker exec kk_redis_cache redis-cli INFO

# 查看内存使用
docker exec kk_redis_cache redis-cli INFO memory
```

## 🌐 访问地址

### Redis服务
- **主机**: localhost
- **端口**: 6379
- **连接**: `redis://localhost:6379`

### Redis Commander (Web管理界面)
- **URL**: http://localhost:8081
- **用户名**: admin
- **密码**: redis123

## 🧪 功能测试

### 基础连接测试

```bash
# Python测试
python3 -c "import redis; r=redis.Redis(host='localhost', port=6379); print('Redis连接:', r.ping())"

# 命令行测试
docker exec kk_redis_cache redis-cli ping
```

### 缓存功能测试

```bash
# 设置缓存
docker exec kk_redis_cache redis-cli SET test_key "Hello Redis"

# 获取缓存
docker exec kk_redis_cache redis-cli GET test_key

# 设置过期时间
docker exec kk_redis_cache redis-cli SETEX temp_key 60 "Temporary Value"

# 查看剩余时间
docker exec kk_redis_cache redis-cli TTL temp_key
```

### API缓存测试

```bash
# 运行API缓存测试脚本
cd ..
python api/test_redis_cache.py
```

## 📊 监控和维护

### 性能监控

```bash
# 实时监控命令
docker exec kk_redis_cache redis-cli MONITOR

# 查看慢查询
docker exec kk_redis_cache redis-cli SLOWLOG GET 10

# 查看客户端连接
docker exec kk_redis_cache redis-cli CLIENT LIST

# 查看键空间统计
docker exec kk_redis_cache redis-cli INFO keyspace
```

### 数据备份

```bash
# 手动备份
docker exec kk_redis_cache redis-cli BGSAVE

# 查看备份状态
docker exec kk_redis_cache redis-cli LASTSAVE

# 复制备份文件
docker cp kk_redis_cache:/data/dump.rdb ./backup_$(date +%Y%m%d_%H%M%S).rdb
```

### 内存管理

```bash
# 查看内存使用详情
docker exec kk_redis_cache redis-cli INFO memory

# 清理过期键
docker exec kk_redis_cache redis-cli EVAL "return redis.call('del', unpack(redis.call('keys', ARGV[1])))" 0 "*expired*"

# 手动垃圾回收
docker exec kk_redis_cache redis-cli DEBUG RESTART
```

## 🚨 故障排除

### 常见问题

#### 1. 连接超时
```bash
# 检查服务状态
docker-compose -f docker-compose.redis.yml ps

# 检查端口占用
netstat -tuln | grep 6379

# 查看容器日志
docker logs kk_redis_cache
```

#### 2. 内存不足
```bash
# 检查内存使用
docker exec kk_redis_cache redis-cli INFO memory

# 清理数据库
docker exec kk_redis_cache redis-cli FLUSHDB

# 调整内存限制
docker exec kk_redis_cache redis-cli CONFIG SET maxmemory 2gb
```

#### 3. 性能问题
```bash
# 查看慢查询日志
docker exec kk_redis_cache redis-cli SLOWLOG GET 10

# 检查键数量
docker exec kk_redis_cache redis-cli DBSIZE

# 分析内存使用
docker exec kk_redis_cache redis-cli --bigkeys
```

### 重置服务

```bash
# 完全重置（谨慎使用）
docker-compose -f docker-compose.redis.yml down -v
docker volume prune -f
docker-compose -f docker-compose.redis.yml up -d
```

## 🔧 高级配置

### 自定义配置

编辑 `redis.conf` 文件来自定义Redis配置：

```bash
# 编辑配置文件
vim redis.conf

# 重启服务使配置生效
docker-compose -f docker-compose.redis.yml restart redis
```

### 生产环境优化

```bash
# 设置密码保护
docker exec kk_redis_cache redis-cli CONFIG SET requirepass "your_strong_password"

# 禁用危险命令
docker exec kk_redis_cache redis-cli CONFIG SET rename-command FLUSHDB ""
docker exec kk_redis_cache redis-cli CONFIG SET rename-command FLUSHALL ""

# 调整持久化策略
docker exec kk_redis_cache redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### 集群模式（可选）

如需要高可用部署，可以配置Redis Sentinel或Cluster模式。详见官方文档。

## 📚 相关文档

- [完整部署指南](./REDIS_DEPLOYMENT_GUIDE.md)
- [API缓存配置](../api/cache_config.py)
- [缓存中间件](../api/cache_middleware.py)
- [Redis官方文档](https://redis.io/documentation)

## 🆘 获取帮助

### 查看帮助信息

```bash
# 部署脚本帮助
./deploy_redis.sh --help

# 环境检查帮助
./check_environment.sh --help
```

### 联系支持

如遇到问题，请：
1. 查看日志文件
2. 运行环境检查脚本
3. 参考故障排除章节
4. 联系技术支持

---

**快速启动完成！** 🎉

现在您可以开始使用Redis缓存服务来加速您的股票量化分析系统了。