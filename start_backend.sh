#!/bin/bash

# 量化股票分析后端服务启动脚本
# 作者：自动生成
# 日期：$(date +%Y-%m-%d)
# 用途：激活conda虚拟环境并启动FastAPI后端服务

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="kk_stock量化分析后端"
CONDA_ENV_NAME="kk_stock"
PYTHON_VERSION="3.11"
PROJECT_DIR="/Users/libing/kk_Projects/kk_Stock/kk_Stock_Analysis/kk_stock_backend"
MAIN_FILE="api/main.py"
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="9001"

# 生产环境配置
DEFAULT_WORKERS="4"                    # 默认worker数量
DEFAULT_LIMIT_CONCURRENCY="1000"       # 最大并发连接数
DEFAULT_KEEPALIVE="5"                  # Keep-alive超时
DEFAULT_BACKLOG="2048"                 # 连接队列长度

# 日志配置
LOG_DIR="$PROJECT_DIR/logs"
STARTUP_LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"

# 日志函数（同时输出到终端和文件）
log_info() {
    local message="[INFO] $1"
    echo -e "${BLUE}$message${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') $message" >> "$STARTUP_LOG_FILE"
}

log_success() {
    local message="[SUCCESS] $1"
    echo -e "${GREEN}$message${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') $message" >> "$STARTUP_LOG_FILE"
}

log_warning() {
    local message="[WARNING] $1"
    echo -e "${YELLOW}$message${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') $message" >> "$STARTUP_LOG_FILE"
}

log_error() {
    local message="[ERROR] $1"
    echo -e "${RED}$message${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') $message" >> "$STARTUP_LOG_FILE"
}

# 初始化日志目录和文件
init_logging() {
    # 创建日志目录
    mkdir -p "$LOG_DIR"
    
    # 创建启动日志文件
    touch "$STARTUP_LOG_FILE"
    
    # 记录启动开始
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SYSTEM] ========== $PROJECT_NAME 启动日志 ==========" >> "$STARTUP_LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SYSTEM] 启动时间: $(date)" >> "$STARTUP_LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SYSTEM] 日志文件: $STARTUP_LOG_FILE" >> "$STARTUP_LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SYSTEM] ================================================" >> "$STARTUP_LOG_FILE"
}

# 显示启动横幅
show_banner() {
    echo -e "${GREEN}"
    echo "============================================="
    echo "      $PROJECT_NAME 启动脚本"
    echo "============================================="
    echo -e "${NC}"
}

# 检查conda是否安装
check_conda() {
    log_info "检查conda是否已安装..."
    if ! command -v conda &> /dev/null; then
        log_error "conda未安装或未添加到PATH环境变量中"
        log_error "请安装Anaconda或Miniconda后重试"
        exit 1
    fi
    log_success "conda已安装"
}

# 检查虚拟环境是否存在
check_conda_env() {
    log_info "检查conda虚拟环境 '$CONDA_ENV_NAME' 是否存在..."
    if ! conda env list | grep -q "^$CONDA_ENV_NAME "; then
        log_warning "虚拟环境 '$CONDA_ENV_NAME' 不存在"
        log_info "正在创建虚拟环境..."
        
        if [ -f "$PROJECT_DIR/environment.yml" ]; then
            log_info "使用environment.yml创建虚拟环境..."
            conda env create -f "$PROJECT_DIR/environment.yml"
        else
            log_info "创建Python $PYTHON_VERSION虚拟环境并安装依赖..."
            conda create -n "$CONDA_ENV_NAME" python="$PYTHON_VERSION" -y
            conda activate "$CONDA_ENV_NAME"
            if [ -f "$PROJECT_DIR/requirements.txt" ]; then
                pip install -r "$PROJECT_DIR/requirements.txt"
            fi
        fi
        log_success "虚拟环境创建完成"
    else
        log_success "虚拟环境 '$CONDA_ENV_NAME' 已存在"
    fi
}

# 激活虚拟环境
activate_conda_env() {
    log_info "激活conda虚拟环境 '$CONDA_ENV_NAME'..."
    
    # 初始化conda（必需步骤）
    eval "$(conda shell.bash hook)"
    
    # 激活环境
    conda activate "$CONDA_ENV_NAME"
    
    if [ "$CONDA_DEFAULT_ENV" = "$CONDA_ENV_NAME" ]; then
        log_success "虚拟环境激活成功"
        log_info "当前Python版本: $(python --version)"
        log_info "当前环境: $CONDA_DEFAULT_ENV"
    else
        log_error "虚拟环境激活失败"
        exit 1
    fi
}

# 检查项目目录和主文件
check_project_files() {
    log_info "检查项目文件..."
    
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    if [ ! -f "$PROJECT_DIR/$MAIN_FILE" ]; then
        log_error "主程序文件不存在: $PROJECT_DIR/$MAIN_FILE"
        exit 1
    fi
    
    log_success "项目文件检查通过"
}

# 检查环境变量和配置
check_env_config() {
    log_info "检查环境配置..."
    
    # 切换到项目目录
    cd "$PROJECT_DIR"
    
    # 检查.env文件
    if [ -f ".env" ]; then
        log_success "发现.env配置文件"
    else
        log_warning ".env文件不存在，将使用默认配置"
    fi
    
    # 设置默认环境变量（如果未设置）
    export API_HOST="${API_HOST:-$DEFAULT_HOST}"
    export API_PORT="${API_PORT:-$DEFAULT_PORT}"
    export ENVIRONMENT="${ENVIRONMENT:-production}"
    export UVICORN_WORKERS="${UVICORN_WORKERS:-$DEFAULT_WORKERS}"
    export UVICORN_LIMIT_CONCURRENCY="${UVICORN_LIMIT_CONCURRENCY:-$DEFAULT_LIMIT_CONCURRENCY}"
    export UVICORN_KEEPALIVE="${UVICORN_KEEPALIVE:-$DEFAULT_KEEPALIVE}"
    export UVICORN_BACKLOG="${UVICORN_BACKLOG:-$DEFAULT_BACKLOG}"
    
    log_info "服务配置:"
    log_info "  - 主机地址: $API_HOST"
    log_info "  - 端口: $API_PORT"
    log_info "  - 环境: $ENVIRONMENT"
    log_info "  - Worker数量: $UVICORN_WORKERS"
    log_info "  - 最大并发连接: $UVICORN_LIMIT_CONCURRENCY"
    log_info "  - Keep-alive超时: ${UVICORN_KEEPALIVE}s"
    log_info "  - 连接队列长度: $UVICORN_BACKLOG"
}

# 安装/更新依赖
update_dependencies() {
    log_info "检查并更新Python依赖包..."
    
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        log_info "安装requirements.txt中的依赖..."
        pip install -r "$PROJECT_DIR/requirements.txt" --upgrade
        log_success "依赖包更新完成"
    else
        log_warning "requirements.txt文件不存在，跳过依赖安装"
    fi
}

# 后台运行配置
PID_FILE="$PROJECT_DIR/kk_stock_backend.pid"
DAEMON_LOG_FILE="$LOG_DIR/daemon_$(date +%Y%m%d).log"
RUN_IN_BACKGROUND=false

# 检查服务是否正在运行
check_service_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # 服务正在运行
        else
            # PID文件存在但进程不存在，清理PID文件
            rm -f "$PID_FILE"
            return 1  # 服务未运行
        fi
    else
        return 1  # 服务未运行
    fi
}

# 显示服务状态
show_service_status() {
    if check_service_status; then
        local pid=$(cat "$PID_FILE")
        log_success "服务正在运行 (PID: $pid)"
        log_info "服务地址: http://$API_HOST:$API_PORT"
        log_info "API文档: http://$API_HOST:$API_PORT/docs"
        log_info "日志文件: $DAEMON_LOG_FILE"
    else
        log_warning "服务未运行"
    fi
}

# 停止后台服务
stop_daemon_service() {
    if check_service_status; then
        local pid=$(cat "$PID_FILE")
        log_info "正在停止后台服务 (PID: $pid)..."
        
        # 发送TERM信号
        kill -TERM "$pid" 2>/dev/null || true
        
        # 等待进程结束
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # 如果进程仍在运行，强制杀死
        if ps -p "$pid" > /dev/null 2>&1; then
            log_warning "进程未响应TERM信号，强制终止..."
            kill -KILL "$pid" 2>/dev/null || true
            sleep 2
        fi
        
        # 清理PID文件
        rm -f "$PID_FILE"
        log_success "服务已停止"
    else
        log_warning "服务未运行，无需停止"
    fi
}

# 重启服务
restart_service() {
    log_info "重启服务..."
    stop_daemon_service
    sleep 2
    RUN_IN_BACKGROUND=true
    main "--daemon"
}

# 后台启动服务
start_daemon_service() {
    # 检查服务是否已在运行
    if check_service_status; then
        local pid=$(cat "$PID_FILE")
        log_warning "服务已在运行 (PID: $pid)"
        show_service_status
        return 0
    fi
    
    log_info "以后台模式启动服务..."
    
    # 切换到项目目录并设置Python路径
    cd "$PROJECT_DIR"
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    
    # 初始化conda环境
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    
    # 创建生产环境后台启动命令
    local start_cmd
    if [ "$UVICORN_WORKERS" -gt 1 ]; then
        log_info "使用多worker模式启动服务 (Workers: $UVICORN_WORKERS)"
        start_cmd="uvicorn api.main:app --host $API_HOST --port $API_PORT --workers $UVICORN_WORKERS --limit-concurrency $UVICORN_LIMIT_CONCURRENCY --timeout-keep-alive $UVICORN_KEEPALIVE --backlog $UVICORN_BACKLOG --log-level info"
    else
        log_info "使用单worker模式启动服务"
        start_cmd="python -m api.main"
    fi
    
    # 记录启动信息
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] ========== 生产环境后台服务启动 ==========" >> "$DAEMON_LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] 启动命令: $start_cmd" >> "$DAEMON_LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] 工作目录: $(pwd)" >> "$DAEMON_LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] PYTHONPATH: $PYTHONPATH" >> "$DAEMON_LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] Worker数量: $UVICORN_WORKERS" >> "$DAEMON_LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DAEMON] 环境变量: ENVIRONMENT=$ENVIRONMENT" >> "$DAEMON_LOG_FILE"
    
    # 后台启动服务并记录PID
    nohup $start_cmd >> "$DAEMON_LOG_FILE" 2>&1 &
    local service_pid=$!
    
    # 保存PID到文件
    echo "$service_pid" > "$PID_FILE"
    
    # 等待一下确保服务启动
    sleep 3
    
    # 验证服务是否成功启动
    if check_service_status; then
        log_success "后台服务启动成功 (PID: $service_pid)"
        log_info "服务地址: http://$API_HOST:$API_PORT"
        log_info "API文档: http://$API_HOST:$API_PORT/docs"
        log_info "日志文件: $DAEMON_LOG_FILE"
        log_info "PID文件: $PID_FILE"
        echo ""
        log_info "使用以下命令管理服务:"
        log_info "  查看状态: $0 status"
        log_info "  停止服务: $0 stop"
        log_info "  重启服务: $0 restart"
        log_info "  查看日志: $0 logs --daemon"
    else
        log_error "后台服务启动失败"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# 启动后端服务（修改版本，支持后台模式）
start_backend_service() {
    if [ "$RUN_IN_BACKGROUND" = true ]; then
        start_daemon_service
    else
        # 根据worker数量选择启动方式
        if [ "$UVICORN_WORKERS" -gt 1 ]; then
            log_info "启动FastAPI后端服务 (多Worker模式: $UVICORN_WORKERS个worker)..."
            local start_cmd="uvicorn api.main:app --host $API_HOST --port $API_PORT --workers $UVICORN_WORKERS --limit-concurrency $UVICORN_LIMIT_CONCURRENCY --timeout-keep-alive $UVICORN_KEEPALIVE --backlog $UVICORN_BACKLOG --log-level info"
        else
            log_info "启动FastAPI后端服务 (单Worker模式)..."
            local start_cmd="python -m api.main"
        fi
        
        log_info "服务地址: http://$API_HOST:$API_PORT"
        log_info "API文档地址: http://$API_HOST:$API_PORT/docs"
        log_info "启动日志: $STARTUP_LOG_FILE"
        log_info "Worker数量: $UVICORN_WORKERS"
        log_info "按 Ctrl+C 停止服务"
        echo ""
        
        # 切换到项目目录并设置Python路径
        cd "$PROJECT_DIR"
        
        # 设置PYTHONPATH环境变量，确保可以正确导入模块
        export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
        
        # 记录启动命令
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SYSTEM] 执行启动命令: $start_cmd" >> "$STARTUP_LOG_FILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SYSTEM] PYTHONPATH: $PYTHONPATH" >> "$STARTUP_LOG_FILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SYSTEM] 工作目录: $(pwd)" >> "$STARTUP_LOG_FILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S') [SYSTEM] Worker数量: $UVICORN_WORKERS" >> "$STARTUP_LOG_FILE"
        
        # 使用选定的启动命令
        # 使用tee命令同时输出到终端和日志文件
        $start_cmd 2>&1 | tee -a "$STARTUP_LOG_FILE"
    fi
}

# 日志清理功能
clean_old_logs() {
    if [ -d "$LOG_DIR" ]; then
        # 删除7天前的启动日志
        find "$LOG_DIR" -name "startup_*.log" -type f -mtime +7 -delete 2>/dev/null || true
        log_info "已清理7天前的启动日志"
    fi
}

# 主执行流程（修改版本）
main() {
    # 初始化日志系统
    init_logging
    
    # 参数处理
    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                API_HOST="$2"
                shift 2
                ;;
            --port)
                API_PORT="$2"
                shift 2
                ;;
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --workers)
                UVICORN_WORKERS="$2"
                shift 2
                ;;
            --daemon|-d)
                RUN_IN_BACKGROUND=true
                shift
                ;;
            --update-deps)
                UPDATE_DEPS=true
                shift
                ;;
            --clean-logs)
                clean_old_logs
                exit 0
                ;;
            --help|-h)
                echo "🚀 $PROJECT_NAME 启动脚本"
                echo ""
                echo "用法: $0 [选项|命令]"
                echo ""
                echo "📋 启动选项:"
                echo "  --host HOST        设置服务主机地址 (默认: $DEFAULT_HOST)"
                echo "  --port PORT        设置服务端口 (默认: $DEFAULT_PORT)"
                echo "  --env ENV          设置运行环境 (默认: production)"
                echo "  --workers NUM      设置worker进程数量 (默认: $DEFAULT_WORKERS)"
                echo "  --daemon, -d       后台运行模式"
                echo "  --update-deps      强制更新依赖包"
                echo "  --clean-logs       清理7天前的启动日志"
                echo "  --help, -h         显示此帮助信息"
                echo ""
                echo "🔧 服务管理命令:"
                echo "  start              启动服务（前台模式）"
                echo "  start --daemon     启动服务（后台模式）"
                echo "  stop               停止后台服务"
                echo "  restart            重启后台服务"
                echo "  status             查看服务状态"
                echo ""
                echo "📝 日志命令:"
                echo "  logs               查看最新启动日志（实时跟踪）"
                echo "  logs --daemon      查看最新后台日志（实时跟踪）"
                echo "  list-logs          列出所有启动日志文件"
                echo ""
                echo "📁 日志文件位置: $LOG_DIR/"
                echo "📁 PID文件位置: $PID_FILE"
                echo ""
                echo "💡 使用示例:"
                echo "  $0                         # 前台启动服务(4个worker)"
                echo "  $0 --daemon                # 后台启动服务(4个worker)"
                echo "  $0 --workers 8 --daemon    # 后台启动服务(8个worker)"
                echo "  $0 --workers 1 --daemon    # 后台启动服务(单worker)"
                echo "  $0 stop                    # 停止后台服务"
                echo "  $0 status                  # 查看服务状态"
                echo "  $0 logs --daemon           # 查看后台日志"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                log_info "使用 --help 查看可用选项"
                exit 1
                ;;
        esac
    done
    
    # 如果是后台模式，不显示横幅
    if [ "$RUN_IN_BACKGROUND" != true ]; then
        show_banner
    fi
    
    # 清理旧日志
    clean_old_logs
    
    # 执行启动流程
    check_conda
    check_conda_env
    activate_conda_env
    check_project_files
    check_env_config
    
    if [ "$UPDATE_DEPS" = true ]; then
        update_dependencies
    fi
    
    start_backend_service
}

# 查看最新日志（增强版本）
show_latest_log() {
    local log_type="startup"
    if [ "$1" = "--daemon" ]; then
        log_type="daemon"
    fi
    
    if [ -d "$LOG_DIR" ]; then
        local latest_log
        if [ "$log_type" = "daemon" ]; then
            latest_log=$(ls -t "$LOG_DIR"/daemon_*.log 2>/dev/null | head -1)
        else
            latest_log=$(ls -t "$LOG_DIR"/startup_*.log 2>/dev/null | head -1)
        fi
        
        if [ -n "$latest_log" ]; then
            echo "📋 最新${log_type}日志: $latest_log"
            echo "----------------------------------------"
            tail -f "$latest_log"
        else
            echo "❌ 没有找到${log_type}日志文件"
        fi
    else
        echo "❌ 日志目录不存在: $LOG_DIR"
    fi
}

# 列出所有日志文件
list_logs() {
    if [ -d "$LOG_DIR" ]; then
        echo "📋 启动日志文件列表:"
        ls -la "$LOG_DIR"/startup_*.log 2>/dev/null || echo "没有找到启动日志文件"
    else
        echo "❌ 日志目录不存在: $LOG_DIR"
    fi
}

# 信号处理（优雅关闭）
trap 'log_info "正在关闭服务..."; echo "$(date "+%Y-%m-%d %H:%M:%S") [SYSTEM] 服务已停止" >> "$STARTUP_LOG_FILE" 2>/dev/null; exit 0' INT TERM

# 检查特殊命令参数（增强版本）
if [ "$1" = "logs" ]; then
    # 初始化日志配置（但不创建新日志文件）
    LOG_DIR="$PROJECT_DIR/logs"
    show_latest_log "$2"
    exit 0
elif [ "$1" = "list-logs" ]; then
    LOG_DIR="$PROJECT_DIR/logs"
    list_logs
    exit 0
elif [ "$1" = "status" ]; then
    # 初始化基本配置
    PROJECT_DIR="/home/libing/kk_Projects/kk_stock/kk_stock_backend"
    PID_FILE="$PROJECT_DIR/kk_stock_backend.pid"
    API_HOST="${API_HOST:-$DEFAULT_HOST}"
    API_PORT="${API_PORT:-$DEFAULT_PORT}"
    LOG_DIR="$PROJECT_DIR/logs"
    DAEMON_LOG_FILE="$LOG_DIR/daemon_$(date +%Y%m%d).log"
    show_service_status
    exit 0
elif [ "$1" = "stop" ]; then
    # 初始化基本配置
    PROJECT_DIR="/home/libing/kk_Projects/kk_stock/kk_stock_backend"
    PID_FILE="$PROJECT_DIR/kk_stock_backend.pid"
    LOG_DIR="$PROJECT_DIR/logs"
    STARTUP_LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"
    init_logging
    stop_daemon_service
    exit 0
elif [ "$1" = "restart" ]; then
    # 初始化基本配置
    PROJECT_DIR="/home/libing/kk_Projects/kk_stock/kk_stock_backend"
    PID_FILE="$PROJECT_DIR/kk_stock_backend.pid"
    LOG_DIR="$PROJECT_DIR/logs"
    STARTUP_LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"
    API_HOST="${API_HOST:-$DEFAULT_HOST}"
    API_PORT="${API_PORT:-$DEFAULT_PORT}"
    DAEMON_LOG_FILE="$LOG_DIR/daemon_$(date +%Y%m%d).log"
    init_logging
    restart_service
    exit 0
elif [ "$1" = "start" ]; then
    # 移除start参数，传递其他参数给main函数
    shift
    main "$@"
    exit 0
fi

# 执行主函数
main "$@"