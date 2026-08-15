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
- 缓存：Redis 8（Docker 容器，缓存分类与商品，TTL 默认 300 秒，可通过 `PRODUCT_CACHE_TTL_SECONDS` 调整；Redis 故障时商品查询自动回退 MySQL）
- 部署：Docker / Docker Compose（nginx 托管前端并反向代理后端）

## Docker 一键部署（推荐）

只需安装 Docker Desktop，克隆仓库后即可运行完整平台（前端、后端、MySQL、Redis）。
后端启动时会先等待 MySQL 就绪（有限重试，最多约 40 秒），MySQL 尚未完成初始化不会随机失败；配置错误会在日志中明确报出。Redis 不是后端启动的硬依赖：应用启动、数据库迁移均不依赖 Redis 可用，Redis 故障时商品查询自动回退 MySQL（详见「缓存配置与降级」）。

### 前置要求

- Docker Desktop（Windows / macOS）或 Docker Engine + Docker Compose v2（Linux）

### 快速开始

```bash
git clone <your-repo-url>
cd tea-mall
cp .env.example .env        # Windows: Copy-Item .env.example .env
# 生成随机 JWT_SECRET 并填入 .env（必填，缺失或弱值后端拒绝启动）
python -c "import secrets; print(secrets.token_urlsafe(48))"
docker compose up -d
```

首次启动会自动构建前后端镜像、初始化 MySQL（建库建用户）、拉起 Redis；后端容器启动前会自动执行数据库迁移（`alembic upgrade head`）建立全部数据表。

## 安全配置（JWT Secret）

`JWT_SECRET` 是必填配置，不再提供任何默认值：缺失、少于 32 字节或命中已知弱值（如 `dev-only-*`、`change-me-*`）时，后端会拒绝启动。`.env.example` 只提供占位符，复制后必须替换。

生成命令：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

将输出粘贴到 `.env` 的 `JWT_SECRET=` 后即可。

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
# 设置管理员初始密码（至少 12 位，禁止 admin123 等弱密码）
docker compose exec -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD='<强密码>' backend python seed.py
```

首次运行创建管理员（用户名默认 `admin`，可用 `ADMIN_USERNAME` 覆盖）和示例分类、商品；重复执行幂等，不会重复创建，密码不会打印。

重置已存在管理员的密码：

```bash
docker compose exec -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD='<新强密码>' backend python seed.py --reset-admin-password
```

### 数据持久化

MySQL 数据、Redis 数据、后端上传的商品图片分别保存在命名卷 `mysql-data`、`redis-data`、`uploads`，重建容器不丢失。

部署细节见 [docs/docker-deployment.md](docs/docker-deployment.md)。

## 缓存配置与降级

- `PRODUCT_CACHE_TTL_SECONDS`：商品/分类缓存有效期（秒），默认 `300`，缺失或 <=0 时回退默认值。已在 `backend/.env.example`、根目录 `.env.example` 与 `docker-compose.yml` 中同步。
- `REDIS_URL`：Redis 连接串（本地开发默认 `redis://localhost:6379/0`）。连接串可携带密码（如 `redis://:password@host:6379/0`），密码只允许来自环境变量，禁止写入代码。
- 降级行为：Redis 不可用时，商品列表/详情/分类查询自动回退 MySQL，接口正常返回；认证链路（登录、Refresh Token、登出）保持 fail-closed（503），不会因为商品缓存降级逻辑放行失效 Token。
- 冷启动：全新环境下即使 Redis 未启动，后端也能正常启动（`alembic upgrade head` 建表、uvicorn 启动、商品 API 均可用），`/api/health` 中 `redis` 字段会如实反映 Redis 状态。

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

该脚本会创建 `tea_mall` 数据库和本地开发账号（用户名与密码需与 `backend/.env` 中 `DATABASE_URL` 保持一致）。

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
Copy-Item .env.example .env   # 首次运行：生成并填写随机 JWT_SECRET（方法见「安全配置」章节），按需修改数据库连接
alembic upgrade head          # 按 Alembic 迁移建立/更新数据表
uvicorn app.main:app --reload
```

接口文档：http://localhost:8000/docs

说明：Redis 不需要先于后端启动；未启动 Redis 时后端仍可启动并正常提供商品查询（自动回退 MySQL），Redis 就绪后缓存自动生效。

### 4. 初始化种子数据（可选）

```powershell
$env:ADMIN_PASSWORD = '<强密码>'   # 可选：$env:ADMIN_USERNAME = 'admin'
python seed.py
```

首次运行创建管理员（默认用户名 `admin`）和示例分类、商品；重复执行幂等。

重置已存在管理员的密码：

```powershell
$env:ADMIN_PASSWORD = '<新强密码>'
python seed.py --reset-admin-password
```

### 5. 启动前端（5173 端口）

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173

## 默认账号

- 管理员：首次初始化时通过 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 环境变量创建（默认用户名 `admin`；密码至少 12 位，禁止弱密码）
- 普通用户：在注册页自行注册

## 测试

后端测试使用独立的测试数据库 `tea_mall_test` 和独立的测试 Redis（DB 15），与开发数据完全隔离；破坏性清理在非测试环境下会被拒绝执行。

初始化测试库（首次，任选其一）：

```powershell
# 本地 MySQL：sql/init.sql 会同时创建 tea_mall 与 tea_mall_test
mysql -u root -p < sql/init.sql
```

```bash
# Docker 容器 MySQL：全新数据卷由 database/init.sql 自动创建 tea_mall_test；
# 已初始化的旧卷需手动执行一次授权：
docker compose exec mysql mysql -uroot -p'<MYSQL_ROOT_PASSWORD>' -e "CREATE DATABASE IF NOT EXISTS tea_mall_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON tea_mall_test.* TO 'tea_mall'@'%'; FLUSH PRIVILEGES;"
```

运行测试（默认连接本机 `localhost:3306` 的 `tea_mall_test`；使用 Docker 容器时用环境变量覆盖）：

```powershell
cd backend
pytest

# 使用 Docker 容器 MySQL / Redis 时
$env:DATABASE_URL='mysql+pymysql://tea_mall:tea_mall_dev@127.0.0.1:3307/tea_mall_test?charset=utf8mb4'
$env:REDIS_URL='redis://127.0.0.1:6379/15'
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
