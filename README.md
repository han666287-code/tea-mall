# Tea Mall

茶叶电商平台：Vue3 + TypeScript + FastAPI + MySQL + Redis，前后端分离、单体仓库，支持 Docker Compose 一键部署。

## 功能

### V1.0（Phase 0-6 历史基线）

- 用户注册 / 登录（JWT 认证，bcrypt 密码哈希）
- 商品分类、商品列表、商品详情、关键词搜索、分类筛选、分页
- 购物车：加购、数量累加、修改数量、删除、合计金额
- 订单：从购物车下单（扣库存、清购物车）、模拟支付、取消订单、我的订单
- 管理端：分类管理、商品管理（图片上传、上下架）、订单管理（状态流转）

### V2.0 工程化升级（V2.0-1 ~ V2.0-9）

- 安全：`JWT_SECRET` 必填且弱值拒绝启动、管理员强密码校验、登录限流
- 身份与权限：Access + Refresh Token（轮换、登出撤销、改密全部失效）、用户状态管理（禁用即失效）、RBAC 管理端用户管理
- 商品：商品 → SKU → 规格体系（独立价格/库存）、商品多图
- 工程化：Alembic 数据库迁移、统一错误格式 `{detail, code}`、Router/Service/Repository 分层
- 缓存：Redis 商品/分类缓存（TTL 可配置）、故障降级（商品回退 MySQL、认证 fail-closed）
- 交付：Docker Compose 一键部署（四服务）、全新环境冷启动、312 项自动化测试

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
docker compose up -d --build
```

首次启动会自动构建前后端镜像（`--build` 强制使用当前代码重新构建）、初始化 MySQL（建库建用户）、拉起 Redis；后端容器启动前会自动执行数据库迁移（`alembic upgrade head`）建立全部数据表。

检查服务状态：

```bash
docker compose ps
```

`docker compose ps` 中 backend / mysql / redis 显示 `Up (healthy)`、frontend 显示 `Up` 即表示平台就绪（frontend 未配置 healthcheck，正常只显示 `Up`），此时可访问前端页面；启动过程中 backend 会等待 MySQL 就绪，短暂显示 `Up (starting)` 属正常。

日常再次启动可省略 `--build`（`docker compose up -d`，复用已有镜像）；修改代码后重新构建并让新代码生效，使用 `docker compose up -d --build`。

## 安全配置（JWT Secret）

`JWT_SECRET` 是必填配置，不再提供任何默认值：缺失、少于 32 字节或命中已知弱值（如 `dev-only-*`、`change-me-*`）时，后端会拒绝启动。`.env.example` 只提供占位符，复制后必须替换。

生成命令：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

将输出粘贴到 `.env` 的 `JWT_SECRET=` 后即可。

## 环境变量说明

完整变量清单见根目录 `.env.example`（Docker 部署）与 `backend/.env.example`（本地开发）。Docker 部署使用根目录 `.env`，由 `docker-compose.yml` 注入后端；本地开发时后端读取 `backend/.env`。连接串 host 的差异：Docker 内使用 compose 服务名 `mysql` / `redis`，本地开发使用 `localhost` / `127.0.0.1`。

| 变量 | 作用 | 必填 | 默认值 / 示例值 |
| --- | --- | --- | --- |
| `MYSQL_ROOT_PASSWORD` | MySQL root 口令（仅首次初始化建库时生效） | Docker 部署必填 | 示例 `CHANGE_ME_ROOT_PASSWORD`，复制后替换 |
| `MYSQL_PASSWORD` | MySQL 应用账号 `tea_mall` 口令，必须与 `DATABASE_URL` 内密码一致 | Docker 部署必填 | 示例 `CHANGE_ME_DB_PASSWORD`，复制后替换 |
| `MYSQL_PORT` | MySQL 宿主机映射端口 | 否 | `3307`（避免与本机 3306 冲突） |
| `REDIS_PORT` | Redis 宿主机映射端口 | 否 | `6379` |
| `PRODUCT_CACHE_TTL_SECONDS` | 商品/分类缓存有效期（秒） | 否 | `300`（缺失或 <=0 回退默认） |
| `FRONTEND_PORT` / `BACKEND_PORT` | 前端 / 后端宿主机映射端口 | 否 | `8080` / `8000` |
| `DATABASE_URL` | 后端 SQLAlchemy 连接串（Docker 内 host 为 `mysql`，本地为 `localhost`/`127.0.0.1`） | 是 | 示例见 `.env.example` |
| `REDIS_URL` | Redis 连接串（Docker 内 host 为 `redis`，本地为 `localhost`；可携带密码，仅允许来自环境变量） | 是 | `redis://redis:6379/0` |
| `JWT_SECRET` | JWT 签名密钥；缺失、少于 32 字节或命中弱值时后端拒绝启动 | 是 | 无默认值，复制后生成随机串填入 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期（分钟） | 否 | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效期（天） | 否 | `7` |
| `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | 登录限流统计窗口（秒） | 否 | `300` |
| `LOGIN_RATE_LIMIT_MAX_PER_IP` | 单 IP 登录失败上限（0/负数关闭） | 否 | `30` |
| `LOGIN_RATE_LIMIT_MAX_PER_USER` | 单用户名登录失败上限（0/负数关闭） | 否 | `10` |
| `ADMIN_USERNAME` | `seed.py` 初始化管理员用户名（运行 seed 时使用） | 否 | `admin` |
| `ADMIN_PASSWORD` | `seed.py` 创建/重置管理员密码（至少 12 位，禁止弱密码） | 运行 seed 时必填 | 无默认值 |

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
│       ├── api         # Axios 封装与接口
│       ├── components  # 通用组件
│       ├── layouts     # 页面布局（含 Admin 管理端布局）
│       ├── router      # 路由 + 登录/管理员守卫
│       ├── store       # Pinia（auth / cart）
│       ├── styles      # 全局样式
│       ├── types       # TypeScript 类型
│       └── views       # 页面（含 admin/ 管理端）
├── backend           # 后端（FastAPI）
│   ├── Dockerfile    # Python 3.13 运行镜像
│   └── app
│       ├── core          # 密码哈希、JWT、权限依赖
│       ├── database      # 数据库连接与会话
│       ├── models        # ORM 模型
│       ├── repositories  # 数据访问层（商品/订单/SKU）
│       ├── schemas       # 请求/响应模型
│       ├── routers       # 路由
│       ├── services      # 业务逻辑
│       └── main.py       # 应用入口
├── database          # 容器初始化 SQL（挂载到 MySQL 首次启动）
├── sql               # 本地建库脚本
├── docs/development  # 阶段任务表与依赖关系
├── docs/v2.0-reports # V2.0 升级阶段验收报告（phase1-8 + final）
├── docs/v2.0-review  # V2.0 Final Review 审查过程报告与最终报告
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

该脚本会创建 `tea_mall` 与 `tea_mall_test` 数据库，以及本地开发账号 `tea_mall`（默认密码 `tea_mall_dev`，与 `backend/.env.example` 中 `DATABASE_URL` 一致；如需改密码，需同步修改 `sql/init.sql` 与 `backend/.env`）。

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

# 使用 Docker 容器 MySQL / Redis 时（<MYSQL_PASSWORD> 替换为根目录 .env 中 MYSQL_PASSWORD 的值）
$env:DATABASE_URL='mysql+pymysql://tea_mall:<MYSQL_PASSWORD>@127.0.0.1:3307/tea_mall_test?charset=utf8mb4'
$env:REDIS_URL='redis://127.0.0.1:6379/15'
pytest
```

前端类型检查与构建：

```powershell
cd frontend
npm run build
```

## 常见启动问题

1. **JWT_SECRET 缺失或为弱值，后端反复重启**：`JWT_SECRET` 是必填配置，缺失、少于 32 字节或命中弱值（`dev-only-*`、`change-me-*`）时后端拒绝启动并在日志中报错。用 `python -c "import secrets; print(secrets.token_urlsafe(48))"` 生成后填入 `.env`。
2. **数据库连接失败**：多为密码不一致——`.env` 中 `DATABASE_URL` 内的密码必须与 `MYSQL_PASSWORD` 相同；修改密码后需重建数据卷（`docker compose down -v && docker compose up -d`，会清空数据，谨慎使用）才生效。
3. **端口冲突（本机已有 MySQL 3306 等）**：MySQL 默认映射宿主 3307；仍冲突时修改 `.env` 中的 `MYSQL_PORT` / `REDIS_PORT` / `FRONTEND_PORT` / `BACKEND_PORT` 后重新 `docker compose up -d`。
4. **容器反复 restarting**：`docker compose logs <service>` 查看具体报错；常见原因：环境变量缺失、端口占用、MySQL 初始化失败、镜像构建/拉取失败。
5. **前端页面打开但接口 502**：backend 尚未就绪或已退出，先 `docker compose ps` 查看状态，再 `docker compose logs -f backend` 查看错误。
6. **镜像拉取或构建失败（网络原因）**：在 Docker Desktop → Settings → Docker Engine 配置 `registry-mirrors` 镜像加速，或配置代理后重试。

## 开发文档

- Docker 部署详解：[docs/docker-deployment.md](docs/docker-deployment.md)
- 阶段任务表：[docs/development/roadmap.md](docs/development/roadmap.md)
- 模块依赖关系：[docs/development/dependency-tree.md](docs/development/dependency-tree.md)
- 开发规则：[AGENTS.md](AGENTS.md)
