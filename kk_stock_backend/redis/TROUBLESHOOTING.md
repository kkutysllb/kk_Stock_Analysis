# Redis部署故障排除指南

本文档提供Redis缓存系统部署过程中常见问题的解决方案。

## 🚨 常见问题分类

### 1. 网络连接问题

#### 问题症状
- Docker镜像拉取失败
- 连接超时错误
- 代理连接被拒绝

#### 解决方案

**方案一：使用网络修复脚本**
```bash
# 自动检测和修复网络问题
./fix_network_issues.sh

# 仅配置镜像源
./fix_network_issues.sh --mirror-only

# 仅测试镜像拉取
./fix_network_issues.sh --test-only
```

**方案二：手动配置镜像源**
```bash
# 编辑Docker配置
sudo nano /etc/docker/daemon.json

# 添加以下内容
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}

# 重启Docker服务
sudo systemctl restart docker
```

**方案三：临时禁用代理**
```bash
# 如果代理不可用，临时禁用
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 然后重新运行部署脚本
./deploy_redis.sh
```

**方案四：离线部署**
```bash
# 使用离线部署脚本
./deploy_redis_offline.sh

# 或仅部署Redis服务（无Web界面）
./deploy_redis_offline.sh --simple
```

### 2. Docker相关问题

#### 问题症状
- Docker服务未运行
- 权限被拒绝
- Docker Compose版本警告

#### 解决方案

**Docker服务问题**
```bash
# 检查Docker状态
sudo systemctl status docker

# 启动Docker服务
sudo systemctl start docker

# 设置开机自启
sudo systemctl enable docker
```

**权限问题**
```bash
# 将用户添加到docker组
sudo usermod -aG docker $USER

# 重新登录或刷新组权限
newgrp docker

# 测试权限
docker ps
```

**Docker Compose版本警告**
```bash
# 版本警告不影响功能，可以忽略
# 或者更新到最新版本
sudo apt update
sudo apt install docker-compose-plugin
```

### 3. 端口占用问题

#### 问题症状
- 端口6379或8081被占用
- 服务启动失败

#### 解决方案

**检查端口占用**
```bash
# 检查Redis端口
netstat -tuln | grep 6379
lsof -i :6379

# 检查Redis Commander端口
netstat -tuln | grep 8081
lsof -i :8081
```

**停止占用端口的服务**
```bash
# 停止Redis服务
sudo systemctl stop redis-server

# 或杀死占用进程
sudo kill -9 $(lsof -t -i:6379)
sudo kill -9 $(lsof -t -i:8081)
```

**修改端口配置**
```bash
# 编辑docker-compose.redis.yml
nano docker-compose.redis.yml

# 修改端口映射
ports:
  - "6380:6379"  # 使用6380端口
  - "8082:8081"  # 使用8082端口
```

### 4. 文件权限问题

#### 问题症状
- 配置文件无法读取
- 数据卷挂载失败
- 脚本无执行权限

#### 解决方案

**修复文件权限**
```bash
# 修复脚本执行权限
chmod +x *.sh

# 修复配置文件权限
chmod 644 redis.conf docker-compose.redis.yml

# 修复目录权限
chmod 755 .
```

**检查文件所有者**
```bash
# 查看文件所有者
ls -la

# 修改文件所有者（如果需要）
sudo chown $USER:$USER *
```

### 5. 内存和磁盘空间问题

#### 问题症状
- 容器启动失败
- 内存不足警告
- 磁盘空间不足

#### 解决方案

**检查系统资源**
```bash
# 检查内存使用
free -h

# 检查磁盘空间
df -h

# 检查Docker空间使用
docker system df
```

**清理Docker资源**
```bash
# 清理未使用的镜像
docker image prune -f

# 清理未使用的容器
docker container prune -f

# 清理未使用的卷
docker volume prune -f

# 清理所有未使用资源
docker system prune -a -f
```

**调整Redis内存配置**
```bash
# 编辑redis.conf
nano redis.conf

# 设置最大内存（例如1GB）
maxmemory 1gb
maxmemory-policy allkeys-lru
```

### 6. 服务健康检查失败

#### 问题症状
- 容器状态显示unhealthy
- 健康检查超时
- 服务无法正常响应

#### 解决方案

**检查服务状态**
```bash
# 查看容器状态
docker-compose -f docker-compose.redis.yml ps

# 查看容器日志
docker logs kk_redis_cache

# 手动测试Redis连接
docker exec kk_redis_cache redis-cli ping
```

**调整健康检查配置**
```bash
# 编辑docker-compose.redis.yml
nano docker-compose.redis.yml

# 调整健康检查参数
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 60s      # 增加检查间隔
  timeout: 30s       # 增加超时时间
  retries: 5         # 增加重试次数
  start_period: 60s  # 增加启动等待时间
```

## 🔧 诊断工具和命令

### 环境检查
```bash
# 运行环境检查脚本
./check_environment.sh

# 检查Docker环境
docker info
docker version

# 检查网络连接
ping 8.8.8.8
curl -I https://registry-1.docker.io
```

### 服务诊断
```bash
# 查看所有容器
docker ps -a

# 查看服务日志
docker-compose -f docker-compose.redis.yml logs

# 实时查看日志
docker-compose -f docker-compose.redis.yml logs -f

# 进入容器调试
docker exec -it kk_redis_cache sh
```

### 网络诊断
```bash
# 检查Docker网络
docker network ls
docker network inspect kk_network

# 测试容器间连接
docker exec kk_redis_cache ping kk_redis_commander

# 检查端口监听
docker exec kk_redis_cache netstat -tuln
```

## 📋 部署检查清单

### 部署前检查
- [ ] Docker服务正常运行
- [ ] Docker Compose已安装
- [ ] 端口6379和8081未被占用
- [ ] 有足够的磁盘空间（至少10GB）
- [ ] 有足够的内存（至少2GB）
- [ ] 网络连接正常

### 部署后验证
- [ ] 容器状态为healthy
- [ ] Redis服务响应ping命令
- [ ] Redis Commander可以访问
- [ ] 数据持久化正常工作
- [ ] 日志无错误信息

## 🆘 获取帮助

### 收集诊断信息
```bash
# 生成诊断报告
./check_environment.sh > diagnosis_report.txt
docker-compose -f docker-compose.redis.yml logs >> diagnosis_report.txt
docker system info >> diagnosis_report.txt
```

### 常用调试命令
```bash
# 重启所有服务
docker-compose -f docker-compose.redis.yml restart

# 完全重新部署
docker-compose -f docker-compose.redis.yml down -v
./deploy_redis.sh

# 查看详细错误信息
docker-compose -f docker-compose.redis.yml up --no-daemon
```

### 联系支持
如果以上解决方案都无法解决问题，请：

1. 运行诊断脚本收集信息
2. 查看详细的错误日志
3. 记录具体的错误信息和操作步骤
4. 提供系统环境信息（操作系统、Docker版本等）

## 📚 相关文档

- [快速启动指南](./QUICK_START.md)
- [完整部署指南](./REDIS_DEPLOYMENT_GUIDE.md)
- [网络修复脚本](./fix_network_issues.sh)
- [离线部署脚本](./deploy_redis_offline.sh)
- [环境检查脚本](./check_environment.sh)

---

**记住**：大多数问题都可以通过重新运行部署脚本或使用离线部署方案来解决。如果遇到持续问题，请不要犹豫寻求帮助！