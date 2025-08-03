#!/bin/bash

# 环境一致性检查脚本
# 用于验证本地和云端环境配置一致性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查结果统计
CHECK_PASSED=0
CHECK_FAILED=0
CHECK_WARNING=0

# 记录检查结果
record_result() {
    case $1 in
        "PASS")
            ((CHECK_PASSED++))
            log_success "$2"
            ;;
        "FAIL")
            ((CHECK_FAILED++))
            log_error "$2"
            ;;
        "WARN")
            ((CHECK_WARNING++))
            log_warning "$2"
            ;;
    esac
}

# 检查系统信息
check_system_info() {
    log_info "=== 系统信息检查 ==="
    
    # 操作系统
    if command -v lsb_release &> /dev/null; then
        OS_INFO=$(lsb_release -d | cut -f2)
    elif [ -f /etc/os-release ]; then
        OS_INFO=$(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)
    else
        OS_INFO=$(uname -s)
    fi
    echo "操作系统: $OS_INFO"
    
    # 内核版本
    KERNEL_VERSION=$(uname -r)
    echo "内核版本: $KERNEL_VERSION"
    
    # 架构
    ARCH=$(uname -m)
    echo "系统架构: $ARCH"
    
    # 内存信息
    if command -v free &> /dev/null; then
        TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
        AVAIL_MEM=$(free -h | awk '/^Mem:/ {print $7}')
        echo "总内存: $TOTAL_MEM, 可用内存: $AVAIL_MEM"
    fi
    
    # 磁盘空间
    DISK_USAGE=$(df -h . | awk 'NR==2 {print $4" available of "$2}')
    echo "磁盘空间: $DISK_USAGE"
    
    echo
}

# 检查Docker环境
check_docker() {
    log_info "=== Docker环境检查 ==="
    
    # Docker版本
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        echo "Docker版本: $DOCKER_VERSION"
        
        # 检查版本要求 (>= 20.10)
        DOCKER_MAJOR=$(echo $DOCKER_VERSION | cut -d'.' -f1)
        DOCKER_MINOR=$(echo $DOCKER_VERSION | cut -d'.' -f2)
        
        if [ "$DOCKER_MAJOR" -gt 20 ] || ([ "$DOCKER_MAJOR" -eq 20 ] && [ "$DOCKER_MINOR" -ge 10 ]); then
            record_result "PASS" "Docker版本符合要求 (>= 20.10)"
        else
            record_result "FAIL" "Docker版本过低，需要 >= 20.10.0"
        fi
        
        # Docker服务状态
        if docker info &> /dev/null; then
            record_result "PASS" "Docker服务运行正常"
            
            # Docker存储驱动
            STORAGE_DRIVER=$(docker info --format '{{.Driver}}')
            echo "存储驱动: $STORAGE_DRIVER"
            
            # Docker根目录
            DOCKER_ROOT=$(docker info --format '{{.DockerRootDir}}')
            echo "Docker根目录: $DOCKER_ROOT"
        else
            record_result "FAIL" "Docker服务未运行"
        fi
    else
        record_result "FAIL" "Docker未安装"
    fi
    
    # Docker Compose版本
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        echo "Docker Compose版本: $COMPOSE_VERSION"
        
        # 检查版本要求 (>= 2.0)
        COMPOSE_MAJOR=$(echo $COMPOSE_VERSION | cut -d'.' -f1)
        
        if [ "$COMPOSE_MAJOR" -ge 2 ]; then
            record_result "PASS" "Docker Compose版本符合要求 (>= 2.0)"
        else
            record_result "WARN" "Docker Compose版本较低，建议升级到 >= 2.0"
        fi
    else
        record_result "FAIL" "Docker Compose未安装"
    fi
    
    echo
}

# 检查Python环境
check_python() {
    log_info "=== Python环境检查 ==="
    
    # Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        echo "Python版本: $PYTHON_VERSION"
        
        # 检查版本要求 (>= 3.8)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            record_result "PASS" "Python版本符合要求 (>= 3.8)"
        else
            record_result "FAIL" "Python版本过低，需要 >= 3.8"
        fi
        
        # pip版本
        if command -v pip3 &> /dev/null; then
            PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
            echo "pip版本: $PIP_VERSION"
            record_result "PASS" "pip可用"
        else
            record_result "WARN" "pip未安装或不可用"
        fi
    else
        record_result "FAIL" "Python3未安装"
    fi
    
    echo
}

# 检查必要文件
check_required_files() {
    log_info "=== 必要文件检查 ==="
    
    local required_files=(
        "docker-compose.redis.yml"
        "redis.conf"
        "deploy_redis.sh"
        "api/cache_manager.py"
        "api/cache_config.py"
        "api/cache_middleware.py"
        "api/requirements_api.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            record_result "PASS" "文件存在: $file"
        else
            record_result "FAIL" "文件缺失: $file"
        fi
    done
    
    echo
}

# 检查配置文件内容
check_config_files() {
    log_info "=== 配置文件检查 ==="
    
    # 检查Redis配置
    if [ -f "redis.conf" ]; then
        # 检查关键配置项
        if grep -q "^port 6379" redis.conf; then
            record_result "PASS" "Redis端口配置正确"
        else
            record_result "WARN" "Redis端口配置可能不正确"
        fi
        
        if grep -q "^save" redis.conf; then
            record_result "PASS" "Redis持久化配置存在"
        else
            record_result "WARN" "Redis持久化配置缺失"
        fi
        
        if grep -q "^maxmemory" redis.conf; then
            record_result "PASS" "Redis内存限制配置存在"
        else
            record_result "WARN" "Redis内存限制配置缺失"
        fi
    fi
    
    # 检查Docker Compose配置
    if [ -f "docker-compose.redis.yml" ]; then
        if grep -q "redis:7.0-alpine" docker-compose.redis.yml; then
            record_result "PASS" "Redis镜像版本配置正确"
        else
            record_result "WARN" "Redis镜像版本可能不正确"
        fi
        
        if grep -q "6379:6379" docker-compose.redis.yml; then
            record_result "PASS" "Redis端口映射配置正确"
        else
            record_result "FAIL" "Redis端口映射配置错误"
        fi
    fi
    
    echo
}

# 检查网络连接
check_network() {
    log_info "=== 网络连接检查 ==="
    
    # 检查Docker Hub连接
    if curl -s --connect-timeout 10 https://hub.docker.com &> /dev/null; then
        record_result "PASS" "Docker Hub连接正常"
    else
        record_result "WARN" "Docker Hub连接失败，可能影响镜像拉取"
    fi
    
    # 检查本地端口占用
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":6379 "; then
            record_result "WARN" "端口6379已被占用"
        else
            record_result "PASS" "端口6379可用"
        fi
        
        if netstat -tuln | grep -q ":8081 "; then
            record_result "WARN" "端口8081已被占用"
        else
            record_result "PASS" "端口8081可用"
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":6379 "; then
            record_result "WARN" "端口6379已被占用"
        else
            record_result "PASS" "端口6379可用"
        fi
        
        if ss -tuln | grep -q ":8081 "; then
            record_result "WARN" "端口8081已被占用"
        else
            record_result "PASS" "端口8081可用"
        fi
    fi
    
    echo
}

# 检查Python依赖
check_python_dependencies() {
    log_info "=== Python依赖检查 ==="
    
    if [ -f "api/requirements_api.txt" ]; then
        local redis_deps=("redis" "redis-py-cluster")
        
        for dep in "${redis_deps[@]}"; do
            if grep -q "^$dep" api/requirements_api.txt; then
                record_result "PASS" "依赖项存在: $dep"
            else
                record_result "WARN" "依赖项缺失: $dep"
            fi
        done
        
        # 检查是否已安装
        if command -v python3 &> /dev/null; then
            if python3 -c "import redis" &> /dev/null; then
                record_result "PASS" "Redis Python客户端已安装"
            else
                record_result "WARN" "Redis Python客户端未安装"
            fi
        fi
    else
        record_result "FAIL" "requirements_api.txt文件不存在"
    fi
    
    echo
}

# 检查现有Redis服务
check_existing_redis() {
    log_info "=== 现有Redis服务检查 ==="
    
    # 检查Docker容器
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "kk_redis_cache"; then
        record_result "PASS" "Redis容器正在运行"
        
        # 检查Redis连接
        if docker exec kk_redis_cache redis-cli ping &> /dev/null; then
            record_result "PASS" "Redis服务响应正常"
            
            # 获取Redis信息
            REDIS_VERSION=$(docker exec kk_redis_cache redis-cli INFO server | grep redis_version | cut -d: -f2 | tr -d '\r')
            echo "Redis版本: $REDIS_VERSION"
            
            REDIS_MEMORY=$(docker exec kk_redis_cache redis-cli INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
            echo "Redis内存使用: $REDIS_MEMORY"
            
            REDIS_CLIENTS=$(docker exec kk_redis_cache redis-cli INFO clients | grep connected_clients | cut -d: -f2 | tr -d '\r')
            echo "Redis连接数: $REDIS_CLIENTS"
        else
            record_result "FAIL" "Redis服务无响应"
        fi
    else
        record_result "WARN" "Redis容器未运行"
    fi
    
    # 检查Redis Commander
    if curl -s http://localhost:8081 &> /dev/null; then
        record_result "PASS" "Redis Commander可访问"
    else
        record_result "WARN" "Redis Commander不可访问"
    fi
    
    echo
}

# 生成环境报告
generate_report() {
    log_info "=== 环境检查报告 ==="
    
    echo "检查时间: $(date)"
    echo "检查主机: $(hostname)"
    echo
    echo "检查结果统计:"
    echo "  ✅ 通过: $CHECK_PASSED"
    echo "  ⚠️  警告: $CHECK_WARNING"
    echo "  ❌ 失败: $CHECK_FAILED"
    echo
    
    if [ $CHECK_FAILED -eq 0 ]; then
        if [ $CHECK_WARNING -eq 0 ]; then
            log_success "环境检查完全通过，可以部署Redis服务"
            echo "建议执行: ./deploy_redis.sh"
        else
            log_warning "环境检查基本通过，但有警告项需要注意"
            echo "可以执行: ./deploy_redis.sh"
        fi
    else
        log_error "环境检查失败，请解决上述问题后重新检查"
        echo "修复问题后重新执行: ./check_environment.sh"
    fi
    
    echo
}

# 保存报告到文件
save_report() {
    local report_file="environment_check_$(date +%Y%m%d_%H%M%S).log"
    
    {
        echo "环境一致性检查报告"
        echo "==================="
        echo "检查时间: $(date)"
        echo "检查主机: $(hostname)"
        echo "操作系统: $OS_INFO"
        echo "内核版本: $KERNEL_VERSION"
        echo "系统架构: $ARCH"
        echo
        echo "检查结果统计:"
        echo "  通过: $CHECK_PASSED"
        echo "  警告: $CHECK_WARNING"
        echo "  失败: $CHECK_FAILED"
        echo
    } > "$report_file"
    
    log_info "详细报告已保存到: $report_file"
}

# 显示帮助信息
show_help() {
    echo "环境一致性检查脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  --save-report   保存检查报告到文件"
    echo "  --help          显示此帮助信息"
    echo
    echo "此脚本检查以下项目:"
    echo "  - 系统信息和资源"
    echo "  - Docker环境"
    echo "  - Python环境"
    echo "  - 必要文件"
    echo "  - 配置文件"
    echo "  - 网络连接"
    echo "  - Python依赖"
    echo "  - 现有Redis服务"
    echo
}

# 主函数
main() {
    echo "======================================"
    echo "    环境一致性检查脚本"
    echo "    本地与云端环境验证"
    echo "======================================"
    echo
    
    local save_report=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --save-report)
                save_report=true
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
    
    # 执行检查
    check_system_info
    check_docker
    check_python
    check_required_files
    check_config_files
    check_network
    check_python_dependencies
    check_existing_redis
    
    # 生成报告
    generate_report
    
    if [ "$save_report" = true ]; then
        save_report
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi