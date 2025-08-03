#!/bin/bash

# Redis离线部署脚本
# 适用于网络受限或无法访问Docker Hub的环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "======================================"
echo "    Redis离线部署脚本"
echo "    适用于网络受限环境"
echo "======================================"
echo

# 检查Docker服务
check_docker() {
    log_info "检查Docker服务..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker服务未运行或权限不足"
        echo "请尝试:"
        echo "  sudo systemctl start docker"
        echo "  sudo usermod -aG docker $USER"
        exit 1
    fi
    
    log_success "Docker服务正常"
}

# 检查Docker Compose
check_docker_compose() {
    log_info "检查Docker Compose..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装"
        echo "请安装Docker Compose:"
        echo "  sudo apt install docker-compose-plugin"
        exit 1
    fi
    
    log_success "Docker Compose可用"
}

# 检查必要文件
check_files() {
    log_info "检查必要文件..."
    
    local missing_files=()
    
    if [ ! -f "docker-compose.redis.yml" ]; then
        missing_files+=("docker-compose.redis.yml")
    fi
    
    if [ ! -f "redis.conf" ]; then
        missing_files+=("redis.conf")
    fi
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log_error "缺少必要文件: ${missing_files[*]}"
        exit 1
    fi
    
    log_success "必要文件检查通过"
}

# 检查镜像是否存在
check_images() {
    log_info "检查Docker镜像..."
    
    local redis_image="redis:7.0-alpine"
    local commander_image="rediscommander/redis-commander:latest"
    
    local missing_images=()
    
    if ! docker image inspect "$redis_image" >/dev/null 2>&1; then
        missing_images+=("$redis_image")
    fi
    
    if ! docker image inspect "$commander_image" >/dev/null 2>&1; then
        missing_images+=("$commander_image")
    fi
    
    if [ ${#missing_images[@]} -gt 0 ]; then
        log_warning "缺少镜像: ${missing_images[*]}"
        return 1
    else
        log_success "所需镜像已存在"
        return 0
    fi
}

# 尝试从国内镜像源拉取
pull_from_mirrors() {
    log_info "尝试从国内镜像源拉取镜像..."
    
    # 配置临时镜像源
    local mirrors=(
        "docker.mirrors.ustc.edu.cn"
        "hub-mirror.c.163.com"
        "mirror.baidubce.com"
    )
    
    for mirror in "${mirrors[@]}"; do
        log_info "尝试镜像源: $mirror"
        
        # 临时修改Docker配置
        if configure_mirror "$mirror"; then
            if attempt_pull; then
                log_success "镜像拉取成功"
                return 0
            fi
        fi
    done
    
    log_error "所有镜像源都无法访问"
    return 1
}

# 配置镜像源
configure_mirror() {
    local mirror="$1"
    
    # 创建临时配置
    local temp_config="/tmp/docker-daemon-temp.json"
    cat > "$temp_config" << EOF
{
  "registry-mirrors": ["https://$mirror"],
  "insecure-registries": []
}
EOF
    
    # 备份原配置
    if [ -f "/etc/docker/daemon.json" ]; then
        sudo cp "/etc/docker/daemon.json" "/etc/docker/daemon.json.backup"
    fi
    
    # 应用新配置
    sudo cp "$temp_config" "/etc/docker/daemon.json"
    sudo systemctl reload docker 2>/dev/null || sudo systemctl restart docker
    sleep 3
    
    return 0
}

# 尝试拉取镜像
attempt_pull() {
    local timeout=30
    
    # 设置超时
    if timeout $timeout docker pull redis:7.0-alpine >/dev/null 2>&1; then
        if timeout $timeout docker pull rediscommander/redis-commander:latest >/dev/null 2>&1; then
            return 0
        fi
    fi
    
    return 1
}

# 提供离线镜像下载链接
provide_offline_solutions() {
    echo
    log_info "离线部署解决方案:"
    echo
    echo "1. 从其他有网络的机器下载镜像:"
    echo "   docker pull redis:7.0-alpine"
    echo "   docker pull rediscommander/redis-commander:latest"
    echo "   docker save redis:7.0-alpine > redis-7-alpine.tar"
    echo "   docker save rediscommander/redis-commander:latest > redis-commander.tar"
    echo
    echo "2. 将镜像文件传输到当前机器，然后加载:"
    echo "   docker load < redis-7-alpine.tar"
    echo "   docker load < redis-commander.tar"
    echo
    echo "3. 使用轻量级Redis镜像（如果可用）:"
    echo "   docker pull alpine:latest"
    echo "   # 然后手动安装Redis"
    echo
    echo "4. 使用本地Redis安装:"
    echo "   sudo apt install redis-server"
    echo "   sudo systemctl start redis-server"
    echo
}

# 创建简化的Docker Compose配置（仅Redis）
create_simple_compose() {
    log_info "创建简化配置（仅Redis服务）..."
    
    cat > "docker-compose.redis-simple.yml" << 'EOF'
services:
  redis:
    image: redis:7.0-alpine
    container_name: kk_redis_cache
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - kk_network

volumes:
  redis_data:
    driver: local

networks:
  kk_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF
    
    log_success "简化配置已创建: docker-compose.redis-simple.yml"
}

# 部署Redis服务
deploy_redis() {
    local compose_file="$1"
    
    log_info "停止现有服务..."
    docker-compose -f "$compose_file" down 2>/dev/null || true
    
    log_info "启动Redis服务..."
    if docker-compose -f "$compose_file" up -d; then
        log_success "Redis服务启动成功"
        
        # 等待服务就绪
        log_info "等待服务就绪..."
        sleep 10
        
        # 验证服务
        if docker exec kk_redis_cache redis-cli ping >/dev/null 2>&1; then
            log_success "Redis服务验证通过"
            return 0
        else
            log_error "Redis服务验证失败"
            return 1
        fi
    else
        log_error "Redis服务启动失败"
        return 1
    fi
}

# 显示服务信息
show_service_info() {
    echo
    log_success "Redis服务部署完成！"
    echo
    echo "服务信息:"
    echo "  - Redis服务: localhost:6379"
    echo "  - 容器名称: kk_redis_cache"
    echo
    echo "常用命令:"
    echo "  - 连接Redis: docker exec -it kk_redis_cache redis-cli"
    echo "  - 查看日志: docker logs kk_redis_cache"
    echo "  - 停止服务: docker-compose -f docker-compose.redis-simple.yml down"
    echo
    echo "测试连接:"
    echo "  docker exec kk_redis_cache redis-cli ping"
    echo
}

# 主函数
main() {
    check_docker
    check_docker_compose
    check_files
    
    # 检查镜像是否存在
    if check_images; then
        # 镜像已存在，直接部署
        log_info "使用现有镜像部署..."
        if deploy_redis "docker-compose.redis.yml"; then
            show_service_info
            exit 0
        fi
    fi
    
    # 尝试拉取镜像
    log_info "尝试拉取Docker镜像..."
    if pull_from_mirrors; then
        if deploy_redis "docker-compose.redis.yml"; then
            show_service_info
            exit 0
        fi
    fi
    
    # 如果拉取失败，创建简化配置
    log_warning "无法拉取完整镜像，尝试简化部署..."
    
    # 检查是否至少有Redis镜像
    if docker image inspect "redis:7.0-alpine" >/dev/null 2>&1; then
        create_simple_compose
        if deploy_redis "docker-compose.redis-simple.yml"; then
            log_warning "仅部署了Redis服务（无Web管理界面）"
            show_service_info
            exit 0
        fi
    fi
    
    # 所有方法都失败
    log_error "部署失败，请尝试离线解决方案"
    provide_offline_solutions
    exit 1
}

# 脚本帮助信息
show_help() {
    echo "Redis离线部署脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help      显示帮助信息"
    echo "  --simple        仅部署Redis服务（无Web界面）"
    echo "  --check-only    仅检查环境和镜像"
    echo
    echo "示例:"
    echo "  $0              # 完整部署（自动降级）"
    echo "  $0 --simple     # 仅部署Redis服务"
    echo "  $0 --check-only # 检查环境状态"
    echo
}

# 处理命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --simple)
        check_docker
        check_docker_compose
        check_files
        create_simple_compose
        deploy_redis "docker-compose.redis-simple.yml"
        show_service_info
        ;;
    --check-only)
        check_docker
        check_docker_compose
        check_files
        check_images
        ;;
    "")
        main
        ;;
    *)
        log_error "未知选项: $1"
        show_help
        exit 1
        ;;
esac