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

# 检查系统类型
check_system() {
    info "检查系统环境..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        info "检测到 macOS 系统"
        install_mac_dependencies
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        info "检测到 Linux 系统"
        install_linux_dependencies
    else
        error "不支持的系统类型: $OSTYPE"
        exit 1
    fi
}

# 安装 Mac 依赖
install_mac_dependencies() {
    info "安装 Mac 依赖..."
    
    # 检查 Homebrew
    if ! command -v brew &> /dev/null; then
        error "未检测到 Homebrew，请先安装 Homebrew"
        exit 1
    fi

    # 安装依赖
    info "安装必要的依赖..."
    brew install python@3.9
    brew install --cask google-chrome
    brew install chromedriver

    info "Mac 依赖安装完成"
}

# 安装 Linux 依赖
install_linux_dependencies() {
    info "安装 Linux 依赖..."
    
    # 更新包管理器
    sudo apt-get update

    # 安装依赖
    sudo apt-get install -y \
        python3.9 \
        python3.9-venv \
        chromium \
        chromium-driver

    info "Linux 依赖安装完成"
}

# 创建 Python 虚拟环境
setup_python_env() {
    info "设置 Python 环境..."
    
    # 创建虚拟环境
    python3.9 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    info "Python 环境设置完成"
}

# 创建必要的目录和文件
setup_directories() {
    info "创建必要的目录和文件..."
    
    # 创建数据目录
    mkdir -p data
    
    # 检查环境文件
    if [ ! -f .env ]; then
        warn "未检测到 .env 文件，创建示例文件..."
        echo "# 主账号配置" > .env
        echo "ACCOUNT1_ID=your_account1" >> .env
        echo "ACCOUNT1_PASSWORD=your_password1" >> .env
        echo "" >> .env
        echo "# 备用账号配置" >> .env
        echo "ACCOUNT2_ID=your_account2" >> .env
        echo "ACCOUNT2_PASSWORD=your_password2" >> .env
        warn "请修改 .env 文件中的账号和密码"
    fi
}

# 主函数
main() {
    info "开始安装 Coze 邀请码系统..."
    
    # 检查系统并安装依赖
    check_system
    
    # 设置 Python 环境
    setup_python_env
    
    # 创建目录和文件
    setup_directories
    
    info "安装完成！"
    info "请确保："
    info "1. 修改 .env 文件中的账号和密码"
    info "2. 运行 ./start.sh 启动系统"
}

# 执行主函数
main 