#!/bin/bash

# Redis部署网络问题修复脚本
# 解决Docker镜像拉取失败和代理连接问题

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
echo "    Redis网络问题修复脚本"
echo "    解决Docker镜像拉取失败"
echo "======================================"
echo

# 检查Docker状态
check_docker() {
    log_info "检查Docker服务状态..."
    if ! systemctl is-active --quiet docker; then
        log_warning "Docker服务未运行，尝试启动..."
        sudo systemctl start docker
        sleep 3
    fi
    
    if docker info >/dev/null 2>&1; then
        log_success "Docker服务正常运行"
    else
        log_error "Docker服务异常，请检查Docker安装"
        exit 1
    fi
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    
    # 检查基本网络连接
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_success "基本网络连接正常"
    else
        log_error "网络连接异常，请检查网络设置"
        return 1
    fi
    
    # 检查Docker Hub连接
    if curl -s --connect-timeout 5 https://registry-1.docker.io >/dev/null; then
        log_success "Docker Hub连接正常"
    else
        log_warning "Docker Hub连接异常，可能需要配置镜像源"
        return 1
    fi
}

# 配置Docker镜像源
configure_docker_mirror() {
    log_info "配置Docker镜像源..."
    
    # 创建Docker配置目录
    sudo mkdir -p /etc/docker
    
    # 备份原配置
    if [ -f /etc/docker/daemon.json ]; then
        sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup.$(date +%Y%m%d_%H%M%S)
        log_info "已备份原Docker配置"
    fi
    
    # 创建新的daemon.json配置
    cat << EOF | sudo tee /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
  ],
  "insecure-registries": [],
  "debug": false,
  "experimental": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    
    log_success "Docker镜像源配置完成"
}

# 重启Docker服务
restart_docker() {
    log_info "重启Docker服务以应用新配置..."
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    sleep 5
    
    if systemctl is-active --quiet docker; then
        log_success "Docker服务重启成功"
    else
        log_error "Docker服务重启失败"
        exit 1
    fi
}

# 清理Docker缓存
clean_docker_cache() {
    log_info "清理Docker缓存..."
    
    # 清理未使用的镜像
    docker image prune -f >/dev/null 2>&1 || true
    
    # 清理未使用的容器
    docker container prune -f >/dev/null 2>&1 || true
    
    # 清理未使用的网络
    docker network prune -f >/dev/null 2>&1 || true
    
    # 清理未使用的卷
    docker volume prune -f >/dev/null 2>&1 || true
    
    log_success "Docker缓存清理完成"
}

# 测试镜像拉取
test_image_pull() {
    log_info "测试Redis镜像拉取..."
    
    # 尝试拉取Redis镜像
    if docker pull redis:7.0-alpine; then
        log_success "Redis镜像拉取成功"
        return 0
    else
        log_error "Redis镜像拉取失败"
        return 1
    fi
}

# 检查代理设置
check_proxy() {
    log_info "检查代理设置..."
    
    if [ -n "$http_proxy" ] || [ -n "$https_proxy" ] || [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ]; then
        log_warning "检测到代理设置:"
        [ -n "$http_proxy" ] && echo "  http_proxy: $http_proxy"
        [ -n "$https_proxy" ] && echo "  https_proxy: $https_proxy"
        [ -n "$HTTP_PROXY" ] && echo "  HTTP_PROXY: $HTTP_PROXY"
        [ -n "$HTTPS_PROXY" ] && echo "  HTTPS_PROXY: $HTTPS_PROXY"
        
        echo
        log_warning "如果代理不可用，请临时禁用代理:"
        echo "  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY"
        echo
    else
        log_success "未检测到代理设置"
    fi
}

# 提供解决方案
provide_solutions() {
    echo
    log_info "网络问题解决方案:"
    echo
    echo "1. 临时禁用代理（如果代理不可用）:"
    echo "   unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY"
    echo
    echo "2. 使用国内镜像源（已自动配置）:"
    echo "   - 中科大镜像源"
    echo "   - 网易镜像源"
    echo "   - 百度镜像源"
    echo "   - 腾讯云镜像源"
    echo
    echo "3. 手动拉取镜像:"
    echo "   docker pull redis:7.0-alpine"
    echo "   docker pull rediscommander/redis-commander:latest"
    echo
    echo "4. 使用本地镜像文件（如果有）:"
    echo "   docker load -i redis-7-alpine.tar"
    echo
    echo "5. 检查防火墙设置:"
    echo "   sudo ufw status"
    echo "   sudo iptables -L"
    echo
}

# 主函数
main() {
    # 检查是否以root权限运行某些操作
    if [ "$EUID" -eq 0 ]; then
        log_warning "检测到root权限，将跳过sudo命令"
    fi
    
    # 执行检查和修复步骤
    check_docker
    check_proxy
    
    if ! check_network; then
        log_warning "网络连接异常，配置镜像源..."
        configure_docker_mirror
        restart_docker
        clean_docker_cache
    fi
    
    # 测试镜像拉取
    if test_image_pull; then
        echo
        log_success "网络问题已解决，可以继续部署Redis"
        echo
        echo "现在可以运行部署脚本:"
        echo "  ./deploy_redis.sh"
        echo
    else
        echo
        log_error "镜像拉取仍然失败，请尝试以下解决方案:"
        provide_solutions
    fi
}

# 脚本帮助信息
show_help() {
    echo "Redis网络问题修复脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  --clean-only   仅清理Docker缓存"
    echo "  --test-only    仅测试镜像拉取"
    echo "  --mirror-only  仅配置镜像源"
    echo
    echo "示例:"
    echo "  $0              # 完整的网络问题检查和修复"
    echo "  $0 --clean-only # 仅清理Docker缓存"
    echo "  $0 --test-only  # 仅测试镜像拉取"
    echo
}

# 处理命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --clean-only)
        check_docker
        clean_docker_cache
        exit 0
        ;;
    --test-only)
        check_docker
        test_image_pull
        exit 0
        ;;
    --mirror-only)
        configure_docker_mirror
        restart_docker
        exit 0
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