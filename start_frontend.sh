#!/bin/bash

# KK股票量化分析系统前端启动脚本
# 作者：自动生成
# 日期：$(date +%Y-%m-%d)
# 用途：管理Vue3+Vite+Electron前端应用的开发和构建

set -e  # 遇到错误立即退出

# =============================================================================
# 🌍 全局项目路径配置
# =============================================================================
# 支持通过环境变量覆盖默认配置，提高脚本灵活性

# 获取脚本所在目录（脚本在项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT_DIR="$SCRIPT_DIR"

# 全局路径配置（可通过环境变量KK_PROJECT_ROOT覆盖）
export KK_PROJECT_ROOT="${KK_PROJECT_ROOT:-$PROJECT_ROOT_DIR}"
export KK_BACKEND_DIR="${KK_BACKEND_DIR:-$KK_PROJECT_ROOT/kk_stock_backend}"
export KK_FRONTEND_DIR="${KK_FRONTEND_DIR:-$KK_PROJECT_ROOT/kk_stock_desktop}"

# 验证项目目录结构
if [ ! -d "$KK_FRONTEND_DIR" ]; then
    echo "❌ 错误：前端目录不存在 - $KK_FRONTEND_DIR"
    echo "💡 请设置环境变量 KK_PROJECT_ROOT 指向正确的项目根目录"
    exit 1
fi

# =============================================================================
# 📋 项目配置（基于全局路径）
# =============================================================================
PROJECT_NAME="KK股票分析系统前端"
PROJECT_DIR="$KK_FRONTEND_DIR"
MAIN_PACKAGE_FILE="package.json"
NODE_MIN_VERSION="18.0.0"
FRONTEND_DEV_PORT="5173"
BACKEND_API_URL="http://127.0.0.1:9023"

# =============================================================================
# 🎨 颜色定义
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 运行模式配置
DEFAULT_MODE="web"           # web | electron | build
DEFAULT_HOST="localhost"
DEFAULT_PORT="5173"

# 进程管理
WEB_PID_FILE="$PROJECT_DIR/web_dev.pid"
ELECTRON_PID_FILE="$PROJECT_DIR/electron_dev.pid"

# 日志配置
LOG_DIR="$PROJECT_DIR/logs"
STARTUP_LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"
WEB_LOG_FILE="$LOG_DIR/web_dev_$(date +%Y%m%d).log"
ELECTRON_LOG_FILE="$LOG_DIR/electron_dev_$(date +%Y%m%d).log"

# 全局变量
RUN_MODE="web"
RUN_IN_BACKGROUND=false
PACKAGE_MANAGER="npm"

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

log_highlight() {
    local message="[HIGHLIGHT] $1"
    echo -e "${PURPLE}$message${NC}"
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
    echo -e "${CYAN}"
    echo "============================================="
    echo "    🚀 $PROJECT_NAME 启动脚本"
    echo "    📱 Vue3 + Vite + Electron 架构"
    echo "============================================="
    echo -e "${NC}"
}

# 检查Node.js版本
check_nodejs() {
    log_info "检查Node.js环境..."
    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装或未添加到PATH环境变量中"
        log_error "请安装Node.js (>= $NODE_MIN_VERSION) 后重试"
        log_error "下载地址: https://nodejs.org/"
        exit 1
    fi
    
    local node_version=$(node --version | sed 's/v//')
    local node_major_version=$(echo "$node_version" | cut -d. -f1)
    local min_major_version=$(echo "$NODE_MIN_VERSION" | cut -d. -f1)
    
    if [ "$node_major_version" -lt "$min_major_version" ]; then
        log_error "Node.js版本过低: $node_version"
        log_error "要求版本: >= $NODE_MIN_VERSION"
        exit 1
    fi
    
    log_success "Node.js版本: v$node_version ✓"
}

# 检测并设置包管理器
detect_package_manager() {
    log_info "检测包管理器..."
    
    if [ -f "$PROJECT_DIR/yarn.lock" ]; then
        if command -v yarn &> /dev/null; then
            PACKAGE_MANAGER="yarn"
            log_success "使用包管理器: Yarn"
        else
            log_warning "检测到yarn.lock但yarn未安装，使用npm"
            PACKAGE_MANAGER="npm"
        fi
    elif [ -f "$PROJECT_DIR/pnpm-lock.yaml" ]; then
        if command -v pnpm &> /dev/null; then
            PACKAGE_MANAGER="pnpm"
            log_success "使用包管理器: pnpm"
        else
            log_warning "检测到pnpm-lock.yaml但pnpm未安装，使用npm"
            PACKAGE_MANAGER="npm"
        fi
    else
        PACKAGE_MANAGER="npm"
        log_success "使用包管理器: npm"
    fi
}

# 检查项目文件
check_project_files() {
    log_info "检查项目文件..."
    
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    if [ ! -f "$PROJECT_DIR/$MAIN_PACKAGE_FILE" ]; then
        log_error "package.json文件不存在: $PROJECT_DIR/$MAIN_PACKAGE_FILE"
        exit 1
    fi
    
    # 检查关键配置文件
    local config_files=("vite.config.ts" "index.html" "electron/main.ts")
    for file in "${config_files[@]}"; do
        if [ ! -f "$PROJECT_DIR/$file" ]; then
            log_warning "配置文件不存在: $file"
        fi
    done
    
    log_success "项目文件检查通过"
}

# 安装依赖
install_dependencies() {
    log_info "检查并安装项目依赖..."
    
    cd "$PROJECT_DIR"
    
    # 检查node_modules是否存在
    if [ ! -d "node_modules" ]; then
        log_info "node_modules不存在，正在安装依赖..."
        $PACKAGE_MANAGER install
    else
        log_info "检查依赖是否需要更新..."
        case $PACKAGE_MANAGER in
            yarn)
                yarn check --verify-tree >/dev/null 2>&1 || {
                    log_info "依赖需要更新，正在安装..."
                    yarn install
                }
                ;;
            pnpm)
                pnpm verify >/dev/null 2>&1 || {
                    log_info "依赖需要更新，正在安装..."
                    pnpm install
                }
                ;;
            *)
                # npm的简单检查
                if [ "$PROJECT_DIR/package.json" -nt "$PROJECT_DIR/node_modules" ]; then
                    log_info "package.json已更新，正在重新安装依赖..."
                    npm install
                fi
                ;;
        esac
    fi
    
    log_success "依赖安装完成"
}

# 检查后端API连接
check_backend_connection() {
    log_info "检查后端API连接..."
    
    if command -v curl &> /dev/null; then
        if curl --output /dev/null --silent --head --fail "$BACKEND_API_URL/health" 2>/dev/null; then
            log_success "后端API连接正常: $BACKEND_API_URL"
        else
            log_warning "无法连接到后端API: $BACKEND_API_URL"
            log_warning "请确保后端服务正在运行"
        fi
    else
        log_info "curl未安装，跳过后端连接检查"
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 停止进程
stop_process() {
    local pid_file=$1
    local process_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_info "正在停止$process_name进程 (PID: $pid)..."
            
            # 发送TERM信号
            kill -TERM "$pid" 2>/dev/null || true
            
            # 等待进程结束
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 15 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # 如果进程仍在运行，强制杀死
            if ps -p "$pid" > /dev/null 2>&1; then
                log_warning "进程未响应TERM信号，强制终止..."
                kill -KILL "$pid" 2>/dev/null || true
                sleep 1
            fi
            
            log_success "$process_name 进程已停止"
        fi
        
        # 清理PID文件
        rm -f "$pid_file"
    fi
}

# 停止所有开发服务
stop_all_services() {
    log_info "正在停止所有前端开发服务..."
    stop_process "$WEB_PID_FILE" "Web开发服务器"
    stop_process "$ELECTRON_PID_FILE" "Electron应用"
}

# 检查服务状态
check_service_status() {
    local has_running_service=false
    
    echo ""
    log_highlight "📊 前端服务状态检查"
    
    # 检查Web开发服务器
    if [ -f "$WEB_PID_FILE" ]; then
        local web_pid=$(cat "$WEB_PID_FILE")
        if ps -p "$web_pid" > /dev/null 2>&1; then
            log_success "🌐 Web开发服务器正在运行 (PID: $web_pid)"
            log_info "   访问地址: http://$DEFAULT_HOST:$DEFAULT_PORT"
            has_running_service=true
        fi
    fi
    
    # 检查Electron应用
    if [ -f "$ELECTRON_PID_FILE" ]; then
        local electron_pid=$(cat "$ELECTRON_PID_FILE")
        if ps -p "$electron_pid" > /dev/null 2>&1; then
            log_success "⚡ Electron应用正在运行 (PID: $electron_pid)"
            has_running_service=true
        fi
    fi
    
    if [ "$has_running_service" = false ]; then
        log_warning "❌ 没有正在运行的前端服务"
    fi
    
    # 检查端口占用
    if check_port $DEFAULT_PORT; then
        local port_pid=$(lsof -ti:$DEFAULT_PORT 2>/dev/null | head -1)
        log_info "🔌 端口 $DEFAULT_PORT 被占用 (PID: $port_pid)"
    else
        log_info "🔌 端口 $DEFAULT_PORT 空闲"
    fi
}

# 启动Web开发服务器
start_web_dev() {
    log_info "🌐 启动Web开发服务器..."
    
    cd "$PROJECT_DIR"
    
    # 检查端口是否被占用
    if check_port $DEFAULT_PORT; then
        log_error "端口 $DEFAULT_PORT 已被占用"
        log_error "请停止占用该端口的进程或使用其他端口"
        exit 1
    fi
    
    # 设置环境变量
    export VITE_API_BASE_URL="$BACKEND_API_URL"
    export VITE_APP_VERSION=$(node -p "require('./package.json').version")
    
    if [ "$RUN_IN_BACKGROUND" = true ]; then
        # 后台启动
        log_info "以后台模式启动Web开发服务器..."
        
        case $PACKAGE_MANAGER in
            yarn)
                nohup yarn dev > "$WEB_LOG_FILE" 2>&1 &
                ;;
            pnpm)
                nohup pnpm dev > "$WEB_LOG_FILE" 2>&1 &
                ;;
            *)
                nohup npm run dev > "$WEB_LOG_FILE" 2>&1 &
                ;;
        esac
        
        local web_pid=$!
        echo "$web_pid" > "$WEB_PID_FILE"
        
        # 等待服务启动
        log_info "等待Web服务器启动..."
        sleep 5
        
        if ps -p "$web_pid" > /dev/null 2>&1; then
            log_success "Web开发服务器启动成功 (PID: $web_pid)"
            log_info "访问地址: http://$DEFAULT_HOST:$DEFAULT_PORT"
            log_info "日志文件: $WEB_LOG_FILE"
        else
            log_error "Web开发服务器启动失败"
            rm -f "$WEB_PID_FILE"
            exit 1
        fi
    else
        # 前台启动
        log_info "启动Web开发服务器 (前台模式)..."
        log_info "访问地址: http://$DEFAULT_HOST:$DEFAULT_PORT"
        log_info "按 Ctrl+C 停止服务"
        echo ""
        
        case $PACKAGE_MANAGER in
            yarn)
                yarn dev 2>&1 | tee -a "$WEB_LOG_FILE"
                ;;
            pnpm)
                pnpm dev 2>&1 | tee -a "$WEB_LOG_FILE"
                ;;
            *)
                npm run dev 2>&1 | tee -a "$WEB_LOG_FILE"
                ;;
        esac
    fi
}

# 启动Electron开发模式
start_electron_dev() {
    log_info "⚡ 启动Electron开发模式..."
    
    cd "$PROJECT_DIR"
    
    # 设置环境变量
    export VITE_API_BASE_URL="$BACKEND_API_URL"
    export ELECTRON_RENDERER_URL="http://localhost:$DEFAULT_PORT"
    
    if [ "$RUN_IN_BACKGROUND" = true ]; then
        # 后台启动
        log_info "以后台模式启动Electron应用..."
        
        case $PACKAGE_MANAGER in
            yarn)
                nohup yarn electron:dev > "$ELECTRON_LOG_FILE" 2>&1 &
                ;;
            pnpm)
                nohup pnpm electron:dev > "$ELECTRON_LOG_FILE" 2>&1 &
                ;;
            *)
                nohup npm run electron:dev > "$ELECTRON_LOG_FILE" 2>&1 &
                ;;
        esac
        
        local electron_pid=$!
        echo "$electron_pid" > "$ELECTRON_PID_FILE"
        
        # 等待应用启动
        log_info "等待Electron应用启动..."
        sleep 8
        
        if ps -p "$electron_pid" > /dev/null 2>&1; then
            log_success "Electron应用启动成功 (PID: $electron_pid)"
            log_info "日志文件: $ELECTRON_LOG_FILE"
        else
            log_error "Electron应用启动失败"
            rm -f "$ELECTRON_PID_FILE"
            exit 1
        fi
    else
        # 前台启动
        log_info "启动Electron应用 (前台模式)..."
        log_info "按 Ctrl+C 停止应用"
        echo ""
        
        case $PACKAGE_MANAGER in
            yarn)
                yarn electron:dev 2>&1 | tee -a "$ELECTRON_LOG_FILE"
                ;;
            pnpm)
                pnpm electron:dev 2>&1 | tee -a "$ELECTRON_LOG_FILE"
                ;;
            *)
                npm run electron:dev 2>&1 | tee -a "$ELECTRON_LOG_FILE"
                ;;
        esac
    fi
}

# 构建生产版本
build_production() {
    log_info "🔨 构建生产版本..."
    
    cd "$PROJECT_DIR"
    
    # 清理之前的构建
    log_info "清理之前的构建文件..."
    rm -rf dist dist-electron release
    
    # 构建Web版本
    log_info "构建Web版本..."
    case $PACKAGE_MANAGER in
        yarn)
            yarn build
            ;;
        pnpm)
            pnpm build
            ;;
        *)
            npm run build
            ;;
    esac
    
    log_success "生产版本构建完成"
    log_info "Web版本目录: $PROJECT_DIR/dist"
    log_info "Electron版本目录: $PROJECT_DIR/dist-electron"
}

# 构建Electron应用
build_electron() {
    local platform="$1"
    
    log_info "📦 构建Electron应用..."
    
    cd "$PROJECT_DIR"
    
    case $platform in
        mac|darwin)
            log_info "构建macOS版本..."
            case $PACKAGE_MANAGER in
                yarn)
                    yarn electron:build:mac
                    ;;
                pnpm)
                    pnpm electron:build:mac
                    ;;
                *)
                    npm run electron:build:mac
                    ;;
            esac
            ;;
        win|windows)
            log_info "构建Windows版本..."
            case $PACKAGE_MANAGER in
                yarn)
                    yarn electron:build:win
                    ;;
                pnpm)
                    pnpm electron:build:win
                    ;;
                *)
                    npm run electron:build:win
                    ;;
            esac
            ;;
        linux)
            log_info "构建Linux版本..."
            case $PACKAGE_MANAGER in
                yarn)
                    yarn electron:build:linux
                    ;;
                pnpm)
                    pnpm electron:build:linux
                    ;;
                *)
                    npm run electron:build:linux
                    ;;
            esac
            ;;
        *)
            log_info "构建所有平台版本..."
            case $PACKAGE_MANAGER in
                yarn)
                    yarn electron:build
                    ;;
                pnpm)
                    pnpm electron:build
                    ;;
                *)
                    npm run electron:build
                    ;;
            esac
            ;;
    esac
    
    log_success "Electron应用构建完成"
    log_info "构建产物目录: $PROJECT_DIR/release"
}

# 显示项目信息
show_project_info() {
    cd "$PROJECT_DIR"
    
    local version=$(node -p "require('./package.json').version" 2>/dev/null || echo "unknown")
    local description=$(node -p "require('./package.json').description" 2>/dev/null || echo "")
    
    echo ""
    log_highlight "📋 项目信息"
    echo "  📦 项目名称: $PROJECT_NAME"
    echo "  📊 版本: v$version"
    echo "  📝 描述: $description"
    echo "  📁 项目目录: $PROJECT_DIR"
    echo "  🔧 包管理器: $PACKAGE_MANAGER"
    echo "  🌐 开发端口: $DEFAULT_PORT"
    echo "  🔗 后端API: $BACKEND_API_URL"
    echo ""
}

# 清理日志文件
clean_old_logs() {
    if [ -d "$LOG_DIR" ]; then
        # 删除7天前的日志
        find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
        log_info "已清理7天前的日志文件"
    fi
}

# 查看最新日志
show_latest_log() {
    local log_type="$1"
    
    if [ -d "$LOG_DIR" ]; then
        local latest_log
        case $log_type in
            web)
                latest_log=$(ls -t "$LOG_DIR"/web_dev_*.log 2>/dev/null | head -1)
                ;;
            electron)
                latest_log=$(ls -t "$LOG_DIR"/electron_dev_*.log 2>/dev/null | head -1)
                ;;
            *)
                latest_log=$(ls -t "$LOG_DIR"/startup_*.log 2>/dev/null | head -1)
                ;;
        esac
        
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

# 主执行流程
main() {
    # 初始化基本配置
    init_basic_config
    # 初始化日志系统
    init_logging
    
    # 参数处理
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode|-m)
                RUN_MODE="$2"
                shift 2
                ;;
            --host)
                DEFAULT_HOST="$2"
                shift 2
                ;;
            --port|-p)
                DEFAULT_PORT="$2"
                FRONTEND_DEV_PORT="$2"
                shift 2
                ;;
            --backend-url)
                BACKEND_API_URL="$2"
                shift 2
                ;;
            --daemon|-d)
                RUN_IN_BACKGROUND=true
                shift
                ;;
            --manager)
                PACKAGE_MANAGER="$2"
                shift 2
                ;;
            --clean-logs)
                clean_old_logs
                exit 0
                ;;
            --debug-paths)
                export DEBUG_PATHS=true
                shift
                ;;
            --help|-h)
                echo "🚀 $PROJECT_NAME 启动脚本"
                echo ""
                echo "用法: $0 [选项|命令]"
                echo ""
                echo "🌍 全局路径配置:"
                echo "  项目根目录: $KK_PROJECT_ROOT"
                echo "  前端目录: $KK_FRONTEND_DIR"
                echo "  后端目录: $KK_BACKEND_DIR"
                echo "  工作目录: $PROJECT_DIR"
                echo ""
                echo "📋 启动选项:"
                echo "  --mode, -m MODE     设置运行模式 (web|electron|build) (默认: web)"
                echo "  --host HOST         设置开发服务器主机 (默认: localhost)"
                echo "  --port, -p PORT     设置开发服务器端口 (默认: 5173)"
                echo "  --backend-url URL   设置后端API地址 (默认: http://localhost:9001)"
                echo "  --daemon, -d        后台运行模式"
                echo "  --manager PKG       指定包管理器 (npm|yarn|pnpm)"
                echo "  --clean-logs        清理7天前的日志文件"
                echo "  --debug-paths       显示路径配置调试信息"
                echo "  --help, -h          显示此帮助信息"
                echo ""
                echo "🔧 服务管理命令:"
                echo "  dev                 启动Web开发服务器"
                echo "  electron            启动Electron开发模式"
                echo "  build [platform]    构建生产版本 (mac|win|linux|all)"
                echo "  stop                停止所有开发服务"
                echo "  status              查看服务状态"
                echo "  restart             重启所有服务"
                echo ""
                echo "📝 日志命令:"
                echo "  logs [type]         查看日志 (web|electron|startup)"
                echo ""
                echo "📁 当前路径配置:"
                init_basic_config > /dev/null 2>&1
                echo "  日志目录: $LOG_DIR/"
                echo "  Web PID文件: $WEB_PID_FILE"
                echo "  Electron PID文件: $ELECTRON_PID_FILE"
                echo ""
                echo "🔧 环境变量配置:"
                echo "  KK_PROJECT_ROOT     覆盖项目根目录路径"
                echo "  KK_FRONTEND_DIR     覆盖前端目录路径"
                echo "  KK_BACKEND_DIR      覆盖后端目录路径"
                echo "  DEBUG_PATHS=true    启用路径调试信息"
                echo ""
                echo "💡 使用示例:"
                echo "  $0 dev                      # 启动Web开发服务器"
                echo "  $0 electron                 # 启动Electron开发模式"
                echo "  $0 dev --daemon             # 后台启动Web服务器"
                echo "  $0 build mac                # 构建macOS版本"
                echo "  $0 --port 3000 dev         # 使用3000端口启动"
                echo "  $0 status                   # 查看服务状态"
                echo ""
                echo "  # 自定义项目路径:"
                echo "  KK_PROJECT_ROOT=/custom/path $0 dev"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                log_info "使用 --help 查看可用选项"
                exit 1
                ;;
        esac
    done
    
    # 显示横幅和项目信息
    if [ "$RUN_IN_BACKGROUND" != true ]; then
        show_banner
        show_project_info
    fi
    
    # 清理旧日志
    clean_old_logs
    
    # 执行基础检查
    check_nodejs
    detect_package_manager
    check_project_files
    check_backend_connection
    
    # 安装依赖
    install_dependencies
    
    # 根据模式启动相应服务
    case $RUN_MODE in
        web)
            start_web_dev
            ;;
        electron)
            start_electron_dev
            ;;
        build)
            build_production
            ;;
        *)
            log_error "未知运行模式: $RUN_MODE"
            log_info "支持的模式: web, electron, build"
            exit 1
            ;;
    esac
}

# 初始化基本配置函数
init_basic_config() {
    # 使用全局项目路径配置
    WEB_PID_FILE="$PROJECT_DIR/web_dev.pid"
    ELECTRON_PID_FILE="$PROJECT_DIR/electron_dev.pid"
    LOG_DIR="$PROJECT_DIR/logs"
    STARTUP_LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"
    WEB_LOG_FILE="$LOG_DIR/web_dev_$(date +%Y%m%d).log"
    ELECTRON_LOG_FILE="$LOG_DIR/electron_dev_$(date +%Y%m%d).log"
    
    # 确保日志目录存在
    mkdir -p "$LOG_DIR"
    
    # 显示当前使用的路径配置（调试信息）
    if [ "${DEBUG_PATHS:-false}" = "true" ]; then
        echo "🔍 路径配置调试信息:"
        echo "  项目根目录: $KK_PROJECT_ROOT"
        echo "  前端目录: $KK_FRONTEND_DIR"
        echo "  当前工作目录: $PROJECT_DIR"
        echo "  Web PID文件: $WEB_PID_FILE"
        echo "  Electron PID文件: $ELECTRON_PID_FILE"
        echo "  日志目录: $LOG_DIR"
    fi
}

# 信号处理（优雅关闭）
trap 'log_info "正在关闭前端服务..."; stop_all_services; echo "$(date "+%Y-%m-%d %H:%M:%S") [SYSTEM] 前端服务已停止" >> "$STARTUP_LOG_FILE" 2>/dev/null; exit 0' INT TERM

# 检查特殊命令参数
if [ "$1" = "dev" ]; then
    shift
    RUN_MODE="web"
    main "$@"
    exit 0
elif [ "$1" = "electron" ]; then
    shift
    RUN_MODE="electron"
    main "$@"
    exit 0
elif [ "$1" = "build" ]; then
    shift
    if [ -n "$1" ]; then
        build_electron "$1"
    else
        build_production
    fi
    exit 0
elif [ "$1" = "stop" ]; then
    # 初始化基本配置
    init_basic_config
    init_logging
    stop_all_services
    exit 0
elif [ "$1" = "status" ]; then
    # 初始化基本配置
    init_basic_config
    init_logging
    check_service_status
    exit 0
elif [ "$1" = "restart" ]; then
    # 初始化基本配置
    init_basic_config
    init_logging
    log_info "重启所有前端服务..."
    stop_all_services
    sleep 2
    RUN_IN_BACKGROUND=true
    RUN_MODE="electron"
    main "--daemon"
    exit 0
elif [ "$1" = "logs" ]; then
    # 初始化日志配置
    init_basic_config
    show_latest_log "$2"
    exit 0
fi

# 执行主函数
main "$@"