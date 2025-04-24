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

### 使用 Docker（推荐）

1. 克隆仓库：

   ```bash
   git clone https://github.com/yourusername/cozeinvitecode.git
   cd cozeinvitecode
   ```
2. 创建环境变量文件：

   ```bash
   /Users/Zhuanz/development/Projects/cozeinvitecode/.envcp .env.example .env
   ```

   编辑 `.env` 文件，填入你的账号信息。
3. 启动服务：

   ```bash
   docker-compose up -d
   ```

### 手动安装

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```
2. 安装 Chrome 和 ChromeDriver：

   - macOS: `brew install --cask google-chrome chromedriver`
   - Linux: `apt install google-chrome-stable chromium-chromedriver`
   - Windows: 下载并安装 Chrome 和对应版本的 ChromeDriver
3. 配置环境变量：

   ```bash
   cp .env.example .env
   ```

   编辑 `.env` 文件，填入你的账号信息。
4. 运行服务：

   ```bash
   ./start.sh
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

- 请确保 Chrome 和 ChromeDriver 版本匹配
- 建议使用 Docker 部署以避免环境问题
- 首次运行可能需要等待一段时间完成初始化

## 许可证

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。
