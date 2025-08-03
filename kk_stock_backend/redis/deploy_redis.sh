#!/bin/bash

# Redis自动化部署脚本
# 适用于本地开发和云端生产环境
# 确保配置一致性

set -e  # 遇到错误立即退出

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

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查Docker服务状态
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 检查必要文件
check_files() {
    log_info "检查必要文件..."
    
    if [ ! -f "docker-compose.redis.yml" ]; then
        log_error "docker-compose.redis.yml文件不存在"
        exit 1
    fi
    
    if [ ! -f "redis.conf" ]; then
        log_error "redis.conf文件不存在"
        exit 1
    fi
    
    log_success "必要文件检查通过"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    # 创建Redis数据目录（根据docker-compose.yml中的卷配置）
    mkdir -p data/redis
    
    # 创建备份和日志目录
    mkdir -p backups
    mkdir -p logs
    
    log_success "目录创建完成"
}

# 停止现有服务
stop_existing_services() {
    log_info "停止现有Redis服务..."
    
    if docker-compose -f docker-compose.redis.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.redis.yml down
        log_success "现有服务已停止"
    else
        log_info "没有运行中的Redis服务"
    fi
}

# 清理旧数据（可选）
clean_old_data() {
    if [ "$1" = "--clean" ]; then
        log_warning "清理旧数据..."
        read -p "确定要清理所有Redis数据吗？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker volume rm redis_redis_data 2>/dev/null || true
            log_success "旧数据已清理"
        else
            log_info "跳过数据清理"
        fi
    fi
}

# 检查本地镜像是否存在
check_local_images() {
    local redis_image="redis:7.0-alpine"
    local commander_image="rediscommander/redis-commander:latest"
    
    log_info "检查本地镜像..."
    
    # 检查Redis镜像
    if docker image inspect "$redis_image" >/dev/null 2>&1; then
        log_info "发现本地Redis镜像: $redis_image"
        local redis_exists=true
    elif docker image inspect "redis:7-alpine" >/dev/null 2>&1; then
        log_info "发现本地Redis镜像: redis:7-alpine，创建标签..."
        docker tag redis:7-alpine "$redis_image"
        log_success "镜像标签创建完成: $redis_image"
        local redis_exists=true
    else
        log_warning "未找到Redis镜像"
        local redis_exists=false
    fi
    
    # 检查Redis Commander镜像
    if docker image inspect "$commander_image" >/dev/null 2>&1; then
        log_info "发现本地Redis Commander镜像: $commander_image"
        local commander_exists=true
    else
        log_warning "未找到Redis Commander镜像"
        local commander_exists=false
    fi
    
    # 如果Redis镜像存在，就可以继续部署（Redis Commander是可选的）
    if [ "$redis_exists" = true ]; then
        if [ "$commander_exists" = true ]; then
            log_success "所有必需镜像已存在，跳过拉取步骤"
        else
            log_info "Redis镜像已存在，Redis Commander将在拉取时获取"
        fi
        return 0
    fi
    
    return 1
}

# 拉取最新镜像
pull_images() {
    # 先检查本地镜像
    if check_local_images; then
        return 0
    fi
    
    log_info "拉取缺失的Docker镜像..."
    
    # 首次尝试拉取
    if docker-compose -f docker-compose.redis.yml pull; then
        log_success "镜像拉取完成"
        return 0
    fi
    
    log_warning "镜像拉取失败，尝试网络问题修复..."
    
    # 检查网络修复脚本是否存在
    if [ -f "./fix_network_issues.sh" ]; then
        log_info "运行网络修复脚本..."
        if ./fix_network_issues.sh --mirror-only; then
            log_info "网络配置已更新，重新尝试拉取镜像..."
            if docker-compose -f docker-compose.redis.yml pull; then
                log_success "镜像拉取完成"
                return 0
            fi
        fi
    fi
    
    # 如果仍然失败，检查是否有部分可用镜像
    log_warning "镜像拉取失败，检查现有镜像..."
    if check_local_images; then
        log_info "发现可用的本地镜像，继续部署..."
        return 0
    fi
    
    # 如果仍然失败，提供解决方案
    log_error "镜像拉取失败，可能的解决方案:"
    echo "1. 检查网络连接和代理设置"
    echo "2. 运行网络修复脚本: ./fix_network_issues.sh"
    echo "3. 使用离线部署脚本: ./deploy_redis_offline.sh"
    echo "4. 手动拉取镜像:"
    echo "   docker pull redis:7.0-alpine"
    echo "   docker pull rediscommander/redis-commander:latest"
    
    return 1
}

# 启动Redis服务
start_services() {
    log_info "启动Redis服务..."
    
    docker-compose -f docker-compose.redis.yml up -d
    
    log_success "Redis服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec kk_redis_cache redis-cli ping &> /dev/null; then
            log_success "Redis服务就绪"
            return 0
        fi
        
        log_info "等待Redis服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_error "Redis服务启动超时"
    return 1
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."
    
    # 检查容器状态
    if ! docker-compose -f docker-compose.redis.yml ps | grep -q "Up"; then
        log_error "Redis容器未正常运行"
        return 1
    fi
    
    # 检查Redis连接
    if ! docker exec kk_redis_cache redis-cli ping &> /dev/null; then
        log_error "Redis连接失败"
        return 1
    fi
    
    # 检查Redis Commander
    if ! curl -s http://localhost:8081 &> /dev/null; then
        log_warning "Redis Commander可能未就绪，请稍后访问 http://localhost:8081"
    else
        log_success "Redis Commander可访问: http://localhost:8081"
    fi
    
    log_success "部署验证通过"
}

# 显示服务信息
show_service_info() {
    log_info "服务信息:"
    echo
    echo "Redis服务:"
    echo "  - 主机: localhost"
    echo "  - 端口: 6379"
    echo "  - 状态: $(docker exec kk_redis_cache redis-cli ping 2>/dev/null || echo 'DISCONNECTED')"
    echo
    echo "Redis Commander:"
    echo "  - URL: http://localhost:8081"
    echo "  - 用户名: admin"
    echo "  - 密码: redis123"
    echo
    echo "数据卷:"
    echo "  - redis_data: $(docker volume inspect redis_redis_data --format '{{.Mountpoint}}' 2>/dev/null || echo '未创建')"
    echo
    echo "管理命令:"
    echo "  - 查看日志: docker-compose -f docker-compose.redis.yml logs -f"
    echo "  - 停止服务: docker-compose -f docker-compose.redis.yml down"
    echo "  - 重启服务: docker-compose -f docker-compose.redis.yml restart"
    echo "  - Redis CLI: docker exec -it kk_redis_cache redis-cli"
    echo
}

# 创建备份
create_backup() {
    if [ "$1" = "--backup" ]; then
        log_info "创建数据备份..."
        
        local backup_file="backups/redis_backup_$(date +%Y%m%d_%H%M%S).rdb"
        
        # 触发Redis保存
        docker exec kk_redis_cache redis-cli BGSAVE
        
        # 等待保存完成
        sleep 5
        
        # 复制备份文件
        docker cp kk_redis_cache:/data/dump.rdb "$backup_file"
        
        log_success "备份已保存到: $backup_file"
    fi
}

# 运行测试
run_tests() {
    if [ "$1" = "--test" ]; then
        log_info "运行Redis缓存测试..."
        
        if [ -f "test_redis_cache.py" ]; then
            python test_redis_cache.py
        else
            log_warning "test_redis_cache.py文件不存在，跳过测试"
        fi
    fi
}

# 显示帮助信息
show_help() {
    echo "Redis自动化部署脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  --clean     清理旧数据后重新部署"
    echo "  --backup    部署前创建数据备份"
    echo "  --test      部署后运行测试"
    echo "  --help      显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0                    # 标准部署"
    echo "  $0 --clean           # 清理旧数据后部署"
    echo "  $0 --backup --test   # 备份数据并在部署后测试"
    echo
}

# 主函数
main() {
    echo "======================================"
    echo "    Redis自动化部署脚本"
    echo "    本地与云端统一配置"
    echo "======================================"
    echo
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean)
                CLEAN_DATA=true
                shift
                ;;
            --backup)
                CREATE_BACKUP=true
                shift
                ;;
            --test)
                RUN_TESTS=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行部署步骤
    check_requirements
    check_files
    create_directories
    
    if [ "$CREATE_BACKUP" = true ]; then
        create_backup --backup
    fi
    
    stop_existing_services
    
    if [ "$CLEAN_DATA" = true ]; then
        clean_old_data --clean
    fi
    
    if ! pull_images; then
        log_error "无法获取必需的Docker镜像，部署失败"
        echo "建议运行: ./deploy_redis_offline.sh"
        exit 1
    fi
    
    start_services
    
    if wait_for_services; then
        verify_deployment
        show_service_info
        
        if [ "$RUN_TESTS" = true ]; then
            run_tests --test
        fi
        
        echo
        log_success "Redis部署完成！"
        echo
    else
        log_error "Redis部署失败！"
        echo
        log_info "查看日志: docker-compose -f docker-compose.redis.yml logs"
        exit 1
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi