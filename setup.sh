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
    if command -v yum &> /dev/null; then
        info "检测到 RHEL/CentOS 系统"
        install_rhel_dependencies
    elif command -v apt-get &> /dev/null; then
        info "检测到 Debian/Ubuntu 系统"
        install_debian_dependencies
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        info "检测到 macOS 系统"
        install_mac_dependencies
    else
        error "不支持的系统类型"
        exit 1
    fi
}

# 安装 RHEL/CentOS 依赖
install_rhel_dependencies() {
    info "安装 RHEL/CentOS 依赖..."
    
    # 安装 EPEL 仓库
    sudo yum install -y epel-release
    
    # 安装 Chrome 和开发工具
    sudo yum install -y chromium chromium-headless chromedriver
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y python3-devel

    info "RHEL/CentOS 依赖安装完成"
}

# 安装 Debian/Ubuntu 依赖
install_debian_dependencies() {
    info "安装 Debian/Ubuntu 依赖..."
    
    sudo apt-get update
    sudo apt-get install -y \
        python3-venv \
        chromium \
        chromium-driver

    info "Debian/Ubuntu 依赖安装完成"
}

# 安装 Mac 依赖
install_mac_dependencies() {
    info "安装 Mac 依赖..."
    
    if ! command -v brew &> /dev/null; then
        error "未检测到 Homebrew，请先安装 Homebrew"
        exit 1
    fi

    brew install python@3.9
    brew install --cask google-chrome
    brew install chromedriver

    info "Mac 依赖安装完成"
}

# 创建 Python 虚拟环境
setup_python_env() {
    info "设置 Python 环境..."
    
    # 检查 Python 版本
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    info "检测到 Python 版本: $PYTHON_VERSION"
    
    # 创建虚拟环境
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级 pip
    python3 -m pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    info "Python 环境设置完成"
}

# 创建必要的目录和文件
setup_directories() {
    info "创建必要的目录和文件..."
    
    # 创建数据目录
    mkdir -p data
    mkdir -p static
    
    # 检查环境文件
    if [ ! -f .env ]; then
        warn "未检测到 .env 文件，创建示例文件..."
        cat > .env << EOL
# Coze 账号配置
ACCOUNT_ID=your_account_here
PASSWORD=your_password_here

# 更新间隔（分钟）
UPDATE_INTERVAL=30

# Chrome 配置（可选，默认值适用于 RHEL/CentOS）
CHROME_BINARY_PATH=/usr/bin/chromium
CHROMEDRIVER_PATH=/usr/bin/chromedriver
EOL
        warn "请修改 .env 文件中的账号和密码"
    fi
}

# 设置文件权限
setup_permissions() {
    info "设置文件权限..."
    chmod +x start.sh
    chmod +x setup.sh
    chmod 600 .env
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
    
    # 设置权限
    setup_permissions
    
    info "安装完成！"
    info "请确保："
    info "1. 修改 .env 文件中的账号和密码"
    info "2. 运行 ./start.sh start 启动系统"
}

# 执行主函数
main 