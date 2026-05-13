# Warehouse (仓库管理系统)

本项目是一个包含前后端分离架构的仓库管理系统原型。后端基于 Python 的 FastAPI 框架开发，提供高性能的异步接口与 WebSocket 支持；前端主要基于 Vue 3 构建。

## 📁 仓库结构

- `app/`: Python 后端目录，包含 FastAPI 应用逻辑、路由、数据库配置及 CRUD 占位符。
- `vue/`: Vue 3 前端目录，包含主要的用户交互界面。
- `warehouse-app/`: React 前端目录（目前为初始化模板，供后续可能的技术栈选择参考）。
- `requirements.txt`: Python 后端依赖列表。

## 🛠️ 环境准备与安装

### 1. 后端 (FastAPI)
确保你的系统已安装 Python 3.8+。
```bash
# 进入项目根目录
cd Warehouse

# (可选) 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 下使用 venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 前端 (Vue 3)
确保你的系统已安装 Node.js (推荐 v14+)。
```bash
# 进入 Vue 前端目录
cd vue

# 安装依赖
npm install
```

## 🚀 运行指令

### 启动后端
在项目根目录下执行以下命令启动 FastAPI 服务（默认运行在 18808 端口）：
```bash
uvicorn app.main:app --reload --port 18808
```
后端启动后，可以访问 [http://127.0.0.1:18808/docs](http://127.0.0.1:18808/docs) 查看由 Swagger UI 自动生成的 API 接口文档。

### 启动前端
新开一个终端窗口，进入 `vue` 目录并启动开发服务器：
```bash
cd vue
npm run serve
```
启动成功后，根据终端提示（通常是 http://localhost:8080/ ）在浏览器中打开页面即可。

## 部署与域名

- [deploy-docker.md](docs/deploy-docker.md)
- [domain-subdomain.md](docs/domain-subdomain.md)
