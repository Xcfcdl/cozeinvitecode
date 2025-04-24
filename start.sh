#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境
check_environment() {
    info "检查环境配置..."
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        error "未检测到虚拟环境，请先运行 ./setup.sh"
        exit 1
    fi
    
    # 检查环境文件
    if [ ! -f ".env" ]; then
        error "未检测到 .env 文件，请先运行 ./setup.sh"
        exit 1
    fi
    
    # 检查账号配置
    if grep -q "your_account1\|your_password1\|your_account2\|your_password2" .env; then
        error "请先在 .env 文件中配置您的账号和密码"
        exit 1
    fi
    
    # 检查至少配置了一个账号
    source .env
    if [ -z "$ACCOUNT1_ID" ] && [ -z "$ACCOUNT2_ID" ]; then
        error "至少需要配置一个账号"
        exit 1
    fi
}

# 启动服务
start_service() {
    info "启动 Coze 邀请码系统..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 检查端口占用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        error "端口 8000 已被占用，请先关闭占用的进程"
        exit 1
    fi
    
    # 启动服务
    info "正在启动服务..."
    if [ "$1" == "--dev" ]; then
        info "以开发模式启动..."
        uvicorn app:app --reload --host 0.0.0.0 --port 8000
    else
        info "以生产模式启动..."
        nohup uvicorn app:app --host 0.0.0.0 --port 8000 > ./data/app.log 2>&1 &
        echo $! > ./data/app.pid
        info "服务已在后台启动，PID: $(cat ./data/app.pid)"
        info "日志文件: ./data/app.log"
    fi
}

# 停止服务
stop_service() {
    if [ -f "./data/app.pid" ]; then
        PID=$(cat ./data/app.pid)
        if ps -p $PID > /dev/null; then
            kill $PID
            rm ./data/app.pid
            info "服务已停止"
        else
            warn "服务未运行"
            rm ./data/app.pid
        fi
    else
        warn "未找到 PID 文件，服务可能未运行"
    fi
}

# 主函数
main() {
    case "$1" in
        "start")
            check_environment
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            stop_service
            sleep 2
            check_environment
            start_service
            ;;
        "dev")
            check_environment
            start_service --dev
            ;;
        *)
            echo "用法: $0 {start|stop|restart|dev}"
            echo "  start   - 在后台启动服务"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            echo "  dev     - 以开发模式启动（实时重载）"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 