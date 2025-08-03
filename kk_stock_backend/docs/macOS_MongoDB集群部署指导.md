# macOS环境MongoDB副本集部署指导

本指南专门针对macOS环境下MongoDB副本集的快速部署。

---

## 1. 环境准备

### 安装Docker Desktop
```bash
# 方式1：官网下载安装包
# https://www.docker.com/products/docker-desktop/

# 方式2：使用Homebrew安装
brew install --cask docker
```

### 验证Docker安装
```bash
docker --version
docker-compose --version
```

---

## 2. 项目准备

```bash
# 克隆项目到本地
cd ~/Projects  # 或你习惯的项目目录
git clone [项目地址]
cd kk_StockQuant_Analysis
```

---

## 3. macOS数据目录配置

### 创建数据存储目录
```bash
# 在用户目录下创建MongoDB数据目录
mkdir -p ~/mongodb_data/{mongo1_data,mongo2_data,mongo3_data}

# 验证目录创建
ls -la ~/mongodb_data/
```

### 生成副本集keyFile
```bash
# 生成keyFile（macOS版本）
openssl rand -base64 756 > ~/mongodb_data/mongo-keyfile
chmod 400 ~/mongodb_data/mongo-keyfile

# 验证keyFile
ls -la ~/mongodb_data/mongo-keyfile
```

---

## 4. 修改docker-compose配置

创建macOS专用的docker-compose配置：

```bash
cd database
cp docker-compose.yml docker-compose.macos.yml
```

修改`docker-compose.macos.yml`中的路径：

```yaml
version: '3.8'
services:
  mongo1:
    image: mongo:5.0
    container_name: mongo1
    ports:
      - 27017:27017
    environment:
      - MONGO_INITDB_ROOT_USERNAME=root
      - MONGO_INITDB_ROOT_PASSWORD=example
    command: ["mongod", "--replSet", "rs0", "--keyFile", "/data/keyfile"]
    volumes:
      - ~/mongodb_data/mongo1_data:/data/db
      - ~/mongodb_data/mongo-keyfile:/data/keyfile
      - ./init_replica.js:/database/init_replica.js:ro

  mongo2:
    image: mongo:5.0
    container_name: mongo2
    ports:
      - 27018:27017
    environment:
      - MONGO_INITDB_ROOT_USERNAME=root
      - MONGO_INITDB_ROOT_PASSWORD=example
    command: ["mongod", "--replSet", "rs0", "--keyFile", "/data/keyfile"]
    volumes:
      - ~/mongodb_data/mongo2_data:/data/db
      - ~/mongodb_data/mongo-keyfile:/data/keyfile
      - ./init_replica.js:/database/init_replica.js:ro

  mongo3:
    image: mongo:5.0
    container_name: mongo3
    ports:
      - 27019:27017
    environment:
      - MONGO_INITDB_ROOT_USERNAME=root
      - MONGO_INITDB_ROOT_PASSWORD=example
    command: ["mongod", "--replSet", "rs0", "--keyFile", "/data/keyfile"]
    volumes:
      - ~/mongodb_data/mongo3_data:/data/db
      - ~/mongodb_data/mongo-keyfile:/data/keyfile
      - ./init_replica.js:/database/init_replica.js:ro
```

---

## 5. 启动MongoDB集群

```bash
cd database

# 清理可能存在的容器
docker-compose -f docker-compose.macos.yml down -v

# 启动MongoDB副本集
docker-compose -f docker-compose.macos.yml up -d

# 查看容器状态
docker-compose -f docker-compose.macos.yml ps
```

---

## 6. 初始化副本集

```bash
# 等待容器完全启动（约30秒）
sleep 30

# 初始化副本集
docker exec -it mongo1 mongo --eval "load('/database/init_replica.js')"

# 验证副本集状态
docker exec -it mongo1 mongo --eval "rs.status()"
```

---

## 7. 初始化数据库

```bash
# 回到项目根目录
cd ..

# 安装Python依赖
pip3 install -r requirements.txt

# 初始化数据库集合
python3 database/init_db.py
```

---

## 8. 启动API服务

```bash
cd api
pip3 install uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 验证API服务。

---

## 9. macOS常见问题

### Docker Desktop内存设置
- 打开Docker Desktop > Preferences > Resources
- 建议分配至少4GB内存给Docker

### 端口冲突
```bash
# 检查端口占用
lsof -i :27017
lsof -i :27018  
lsof -i :27019

# 杀死占用进程
sudo kill -9 [PID]
```

### 权限问题
```bash
# 如果遇到keyFile权限问题
chmod 400 ~/mongodb_data/mongo-keyfile
```

### 查看日志
```bash
# 查看容器日志
docker logs mongo1
docker logs mongo2  
docker logs mongo3
```

---

## 10. 快速操作命令

```bash
# 一键启动
cd database && docker-compose -f docker-compose.macos.yml up -d

# 一键停止
cd database && docker-compose -f docker-compose.macos.yml down

# 完全清理重建
cd database && docker-compose -f docker-compose.macos.yml down -v
rm -rf ~/mongodb_data && mkdir -p ~/mongodb_data/{mongo1_data,mongo2_data,mongo3_data}
openssl rand -base64 756 > ~/mongodb_data/mongo-keyfile && chmod 400 ~/mongodb_data/mongo-keyfile
docker-compose -f docker-compose.macos.yml up -d
```

---

## 11. 性能优化建议

- 将数据目录放在SSD上以提升性能
- 如果有外置SSD，可以修改路径：`/Volumes/[SSD名称]/mongodb_data/`
- 调整Docker Desktop的CPU和内存分配

---

**部署完成！** 现在你的macOS环境已经运行了MongoDB副本集集群。 