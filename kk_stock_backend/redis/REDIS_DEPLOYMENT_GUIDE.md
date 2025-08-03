# Redis部署指南 - 本地与云端统一配置

## 概述

本指南提供了在本地开发环境和云端生产环境中统一部署Redis的完整方案，确保配置一致性和环境统一性。

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少2GB可用内存
- 至少10GB可用磁盘空间

## 部署架构

### 服务组件
1. **Redis服务器** - 主要缓存服务
2. **Redis Commander** - Web管理界面
3. **数据持久化** - RDB + AOF双重保障
4. **健康检查** - 自动故障检测

## 快速部署

### 1. 启动Redis服务

```bash
# 进入redis目录
cd redis

# 启动Redis服务
docker-compose -f docker-compose.redis.yml up -d
```

### 2. 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.redis.yml ps

# 检查Redis连接
docker exec -it kk_redis_cache redis-cli ping
```

### 3. 访问管理界面

- **Redis Commander**: http://localhost:8081
- **用户名**: admin
- **密码**: redis123

## 配置说明

### Redis配置文件 (redis.conf)

```bash
# 查看当前配置
cat redis.conf
```

**关键配置项**:
- **端口**: 6379 (标准Redis端口)
- **持久化**: RDB + AOF双重保障
- **内存策略**: allkeys-lru (LRU淘汰策略)
- **最大内存**: 1GB (可根据需要调整)
- **安全**: 密码保护 + 网络隔离

### Docker Compose配置

```yaml
# docker-compose.redis.yml 主要配置
services:
  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./redis.conf:/usr/local/etc/redis/redis.conf
      - redis_data:/data
    command: redis-server /usr/local/etc/redis/redis.conf
```

## 环境配置

### 本地开发环境

```bash
# 1. 克隆项目
git clone <项目地址>
cd kk_StockQuant_Analysis

# 2. 进入redis目录并启动服务
cd redis
./deploy_redis.sh

# 3. 验证连接
python -c "import redis; r=redis.Redis(host='localhost', port=6379); print(r.ping())"
```

### 云端生产环境

```bash
# 1. 服务器准备
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker

# 2. 部署Redis
git clone <项目地址>
cd kk_StockQuant_Analysis/redis
./deploy_redis.sh

# 3. 配置防火墙 (如需要)
sudo ufw allow 6379/tcp
sudo ufw allow 8081/tcp
```

## 数据持久化

### 备份策略

```bash
# 手动备份
docker exec stockquant_redis redis-cli BGSAVE

# 查看备份文件
docker exec stockquant_redis ls -la /data/
```

### 恢复数据

```bash
# 停止服务
docker-compose -f docker-compose.redis.yml down

# 恢复备份文件到数据卷
docker run --rm -v redis_data:/data -v $(pwd):/backup alpine cp /backup/dump.rdb /data/

# 重启服务
docker-compose -f docker-compose.redis.yml up -d
```

## 性能监控

### 基础监控命令

```bash
# 连接信息
docker exec stockquant_redis redis-cli INFO clients

# 内存使用
docker exec stockquant_redis redis-cli INFO memory

# 性能统计
docker exec stockquant_redis redis-cli INFO stats

# 慢查询日志
docker exec stockquant_redis redis-cli SLOWLOG GET 10
```

### 性能调优

```bash
# 查看当前配置
docker exec stockquant_redis redis-cli CONFIG GET "*"

# 动态调整最大内存
docker exec stockquant_redis redis-cli CONFIG SET maxmemory 2gb

# 调整淘汰策略
docker exec stockquant_redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 安全配置

### 网络安全

```bash
# 仅允许本地连接 (生产环境推荐)
# 在redis.conf中设置:
# bind 127.0.0.1

# 设置密码保护
# requirepass your_strong_password
```

### 访问控制

```bash
# 创建用户 (Redis 6.0+)
docker exec stockquant_redis redis-cli ACL SETUSER api_user on >api_password ~cached:* +@read +@write

# 查看用户列表
docker exec stockquant_redis redis-cli ACL LIST
```

## 故障排除

### 常见问题

1. **连接超时**
```bash
# 检查服务状态
docker-compose -f docker-compose.redis.yml ps

# 查看日志
docker-compose -f docker-compose.redis.yml logs redis
```

2. **内存不足**
```bash
# 检查内存使用
docker exec stockquant_redis redis-cli INFO memory

# 清理过期键
docker exec stockquant_redis redis-cli FLUSHDB
```

3. **性能问题**
```bash
# 查看慢查询
docker exec stockquant_redis redis-cli SLOWLOG GET 10

# 监控实时命令
docker exec stockquant_redis redis-cli MONITOR
```

### 日志分析

```bash
# 实时查看日志
docker-compose -f docker-compose.redis.yml logs -f redis

# 查看错误日志
docker-compose -f docker-compose.redis.yml logs redis | grep ERROR
```

## 维护操作

### 定期维护

```bash
# 每日备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d)
docker exec stockquant_redis redis-cli BGSAVE
docker cp stockquant_redis:/data/dump.rdb ./backups/redis_backup_$DATE.rdb
```

### 版本升级

```bash
# 1. 备份数据
docker exec stockquant_redis redis-cli BGSAVE

# 2. 停止服务
docker-compose -f docker-compose.redis.yml down

# 3. 更新镜像
docker-compose -f docker-compose.redis.yml pull

# 4. 重启服务
docker-compose -f docker-compose.redis.yml up -d
```

## API集成验证

### 测试缓存功能

```bash
# 运行缓存测试
python test_redis_cache.py

# 检查缓存统计
curl http://localhost:8000/cache/stats

# 清理测试缓存
curl -X POST http://localhost:8000/cache/clear
```

### 性能基准测试

```bash
# Redis基准测试
docker exec stockquant_redis redis-benchmark -h localhost -p 6379 -n 10000 -c 50

# API缓存性能测试
python test_redis_cache.py --benchmark
```

## 生产环境建议

### 硬件配置
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: SSD 20GB以上
- **网络**: 1Gbps以上

### 监控告警
- 内存使用率 > 80%
- 连接数 > 1000
- 慢查询 > 100ms
- 服务不可用

### 高可用配置
```bash
# Redis Sentinel (可选)
# 适用于关键生产环境
# 详见官方文档配置主从复制
```

## 总结

通过本指南，您可以在本地和云端环境中部署完全一致的Redis缓存服务，确保:

✅ **配置统一**: 相同的Redis配置文件  
✅ **环境一致**: 相同的Docker镜像和版本  
✅ **数据安全**: RDB + AOF双重持久化  
✅ **监控完善**: 健康检查和性能监控  
✅ **易于维护**: 标准化的部署和维护流程  

如有问题，请参考故障排除章节或联系技术支持。