# Coze 邀请码管理系统

这是一个用于自动化管理和获取 Coze 邀请码的系统。该系统可以自动登录 Coze 平台，获取邀请码信息，并提供 API 接口进行查询。

## 功能特性

- 🔄 自动化登录 Coze 平台
- 📊 自动获取并更新邀请码状态
- 🌐 RESTful API 接口支持
- 📱 响应式 Web 界面
- 🔒 支持多账号管理
- 🕒 定时自动更新
- 🐳 Docker 支持

## 技术栈

- Backend: FastAPI
- Frontend: HTML/CSS/JavaScript
- 自动化: Selenium
- 容器化: Docker
- 数据存储: JSON

## 安装说明

### RHEL/CentOS Linux 安装步骤

1. 安装系统依赖：
   ```bash
   # 安装 EPEL 仓库
   sudo yum install -y epel-release

   # 安装 Chrome
   sudo yum install -y chromium chromium-headless chromedriver

   # 安装 Python 开发工具
   sudo yum groupinstall -y "Development Tools"
   sudo yum install -y python3-devel
   ```

2. 创建并激活 Python 虚拟环境：
   ```bash
   # 创建虚拟环境
   python3 -m venv venv

   # 激活虚拟环境
   source venv/bin/activate
   ```

3. 安装 Python 依赖：
   ```bash
   # 更新 pip
   pip install --upgrade pip

   # 安装项目依赖
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   ```bash
   cp .env.example .env
   ```
   编辑 `.env` 文件，填入以下信息：
   ```
   ACCOUNT_ID=你的Coze账号
   PASSWORD=你的账号密码
   UPDATE_INTERVAL=30  # 更新间隔（分钟）
   ```

5. 运行服务：
   ```bash
   ./start.sh
   ```

### 使用 Docker（推荐）

1. 安装 Docker 和 Docker Compose：
   ```bash
   # 安装 Docker
   sudo yum install -y docker

   # 启动 Docker 服务
   sudo systemctl start docker
   sudo systemctl enable docker

   # 安装 Docker Compose
   sudo yum install -y docker-compose
   ```

2. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/cozeinvitecode.git
   cd cozeinvitecode
   ```

3. 创建环境变量文件：
   ```bash
   cp .env.example .env
   ```
   编辑 `.env` 文件，填入你的账号信息。

4. 启动服务：
   ```bash
   docker-compose up -d
   ```

## 使用方法

1. 访问 Web 界面：
   ```
   http://localhost:8000
   ```

2. API 接口：
   - 获取所有邀请码：
     ```
     GET /api/codes
     ```
   - 获取最新邀请码状态：
     ```
     GET /api/invite_codes
     ```

## 配置说明

在 `.env` 文件中配置以下参数：
- `ACCOUNT_ID`: Coze 账号
- `PASSWORD`: 账号密码
- `UPDATE_INTERVAL`: 更新间隔（分钟）

## 注意事项

- 确保系统防火墙允许访问 8000 端口：
  ```bash
  sudo firewall-cmd --permanent --add-port=8000/tcp
  sudo firewall-cmd --reload
  ```
- 如果使用 SELinux，可能需要适当配置安全策略
- 首次运行可能需要等待一段时间完成初始化

## 常见问题解决

1. 如果遇到权限问题：
   ```bash
   # 确保当前用户有权限访问相关目录
   sudo chown -R $USER:$USER .
   ```

2. 如果遇到 ChromeDriver 问题：
   ```bash
   # 检查 ChromeDriver 是否正确安装
   chromedriver --version
   
   # 如果版本不匹配，可以尝试更新
   sudo yum update chromium chromedriver
   ```

3. 如果遇到 Python 相关错误：
   - 确保虚拟环境已正确激活
   - 使用 `python3 -m pip install --upgrade pip` 更新 pip

## 许可证

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。
