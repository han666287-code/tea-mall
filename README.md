# Tea Mall

茶叶电商平台：Vue3 + TypeScript + FastAPI + MySQL + Redis，前后端分离、单体仓库，支持 Docker Compose 一键部署。

## 功能（v1）

- 用户注册 / 登录（JWT 认证，bcrypt 密码哈希）
- 商品分类、商品列表、商品详情、关键词搜索、分类筛选、分页
- 购物车：加购、数量累加、修改数量、删除、合计金额
- 订单：从购物车下单（扣库存、清购物车）、模拟支付、取消订单、我的订单
- 管理端：分类管理、商品管理（图片上传、上下架）、订单管理（状态流转）

## 技术栈

- 前端：Vue3 / TypeScript / Vite / Vue Router / Pinia / Axios / Element Plus
- 后端：Python / FastAPI / SQLAlchemy 2.x
- 数据库：MySQL 8.0（Docker 容器，数据持久化）
- 缓存：Redis 8（Docker 容器，缓存分类与商品，TTL 5 分钟）
- 部署：Docker / Docker Compose（nginx 托管前端并反向代理后端）

## Docker 一键部署（推荐）

只需安装 Docker Desktop，克隆仓库后即可运行完整平台（前端、后端、MySQL、Redis）。

### 前置要求

- Docker Desktop（Windows / macOS）或 Docker Engine + Docker Compose v2（Linux）

### 快速开始

```bash
git clone <your-repo-url>
cd tea-mall
cp .env.example .env        # Windows: Copy-Item .env.example .env
docker compose up -d
```

首次启动会自动构建前后端镜像、初始化 MySQL（建库建用户）、拉起 Redis，后端启动时自动创建数据表。

### 访问地址

| 服务 | 地址 |
| --- | --- |
| 前端 | http://localhost:8080 |
| 后端 API | http://localhost:8000 |
| 接口文档（Swagger） | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/api/health |

端口可通过 `.env` 中的 `FRONTEND_PORT` / `BACKEND_PORT` / `MYSQL_PORT` / `REDIS_PORT` 调整。

### 停止与清理

```bash
docker compose down          # 停止容器（保留数据）
docker compose down -v       # 停止并删除数据卷（会清空数据库与 Redis 数据，谨慎使用）
```

### 查看日志

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### 初始化种子数据（可选）

```bash
docker compose exec backend python seed.py
```

创建默认管理员 `admin / admin123` 和示例分类、商品。

### 数据持久化

MySQL 数据、Redis 数据、后端上传的商品图片分别保存在命名卷 `mysql-data`、`redis-data`、`uploads`，重建容器不丢失。

部署细节见 [docs/docker-deployment.md](docs/docker-deployment.md)。

## 目录结构

```text
tea-mall
├── frontend          # 前端（Vue3 + Vite）
│   ├── Dockerfile    # 多阶段构建：Node 构建 + nginx 运行
│   ├── nginx.conf    # SPA 托管 + /api、/uploads 反向代理
│   └── src
│       ├── api       # Axios 封装与接口
│       ├── components# 通用组件
│       ├── router    # 路由 + 登录/管理员守卫
│       ├── store     # Pinia（auth / cart）
│       ├── types     # TypeScript 类型
│       └── views     # 页面（含 admin/ 管理端）
├── backend           # 后端（FastAPI）
│   ├── Dockerfile    # Python 3.13 运行镜像
│   └── app
│       ├── core      # 密码哈希、JWT、权限依赖
│       ├── models    # ORM 模型
│       ├── schemas   # 请求/响应模型
│       ├── routers   # 路由
│       ├── services  # 业务逻辑
│       └── main.py   # 应用入口
├── database          # 容器初始化 SQL（挂载到 MySQL 首次启动）
├── sql               # 本地建库脚本
├── docs/development  # 阶段任务表与依赖关系
├── docker-compose.yml# 四服务编排（frontend/backend/mysql/redis）
├── .env.example      # 环境变量示例（复制为 .env）
├── README.md
└── AGENTS.md
```

## 本地开发

本地开发需要 Python 3.12+、Node.js 20+、本机 MySQL 8.0；Redis 用 Docker 启动。

### 1. 初始化数据库

```powershell
mysql -u root -p < sql/init.sql
```

该脚本会创建 `tea_mall` 数据库和开发账号 `tea_mall / tea_mall_dev`。

### 2. 启动 Redis

```powershell
docker compose up -d redis
```

### 3. 启动后端（8000 端口）

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # 首次运行，按需修改
uvicorn app.main:app --reload
```

接口文档：http://localhost:8000/docs

### 4. 初始化种子数据（可选）

```powershell
python seed.py
```

创建默认管理员 `admin / admin123` 和示例分类、商品。

### 5. 启动前端（5173 端口）

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173

## 默认账号

- 管理员：`admin / admin123`（本地学习用途，请勿用于生产）
- 普通用户：在注册页自行注册

## 测试

后端测试（需要 MySQL 与 Redis 已启动）：

```powershell
cd backend
pytest
```

前端类型检查与构建：

```powershell
cd frontend
npm run build
```

## 开发文档

- Docker 部署详解：[docs/docker-deployment.md](docs/docker-deployment.md)
- 阶段任务表：[docs/development/roadmap.md](docs/development/roadmap.md)
- 模块依赖关系：[docs/development/dependency-tree.md](docs/development/dependency-tree.md)
- 开发规则：[AGENTS.md](AGENTS.md)
