# Tea Mall

茶叶电商平台：Vue3 + TypeScript + FastAPI + MySQL + Redis，前后端分离、单体仓库，支持 Docker Compose 一键部署。

## 功能特性

- 用户体系：注册 / 登录（JWT + Refresh Token 轮换）、资料管理、改密全端失效、用户禁用即失效
- 商品：分类、列表/详情、关键词搜索、分类筛选、分页、商品 → SKU → 规格（独立价格/库存）、多图、上下架
- 购物车：加购累加、修改数量、删除、合计金额
- 订单：下单扣库存、模拟支付、取消恢复库存、我的订单；管理端状态流转（发货 / 完成 / 取消）
- 管理端：分类管理、商品管理（图片上传 / 上下架 / SKU 编辑）、订单管理、用户管理（状态 / 角色，RBAC）
- 工程化：`JWT_SECRET` 必填强校验、登录限流、Alembic 数据库迁移、统一错误格式 `{detail, code}`、Router/Service/Repository 分层、Redis 缓存（TTL 可配置）与故障降级（商品回退 MySQL、认证 fail-closed）、Docker Compose 四服务一键部署、316 项自动化测试

> 项目状态：V2.0 已完成开发与最终验收（V2.0 READY）。阶段验收记录见 `docs/v2.0-reports/`，最终审查报告见 `docs/v2.0-review/`。

## 开发历程（版本演进）

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
- 交付：Docker Compose 一键部署（四服务）、全新环境冷启动、316 项自动化测试

> 各阶段任务表见 [docs/development/roadmap.md](docs/development/roadmap.md)，逐阶段验收报告见 [docs/v2.0-reports/](docs/v2.0-reports/)。

## 技术栈

- 前端：Vue3 / TypeScript / Vite / Vue Router / Pinia / Axios / Element Plus
- 后端：Python / FastAPI / SQLAlchemy 2.x
- 数据库：MySQL 8.0（Docker 容器，数据持久化）
- 缓存：Redis 8（Docker 容器，商品 / 分类缓存，TTL 默认 300 秒）
- 部署：Docker / Docker Compose（nginx 托管前端并反向代理后端）

## 快速开始（Docker，推荐）

### 前置要求

- Docker Desktop（Windows / macOS）或 Docker Engine + Docker Compose v2（Linux）

### 5 步启动

```bash
# 1. 获取代码（默认拉取主干 master）
git clone https://github.com/han666287-code/tea-mall.git
cd tea-mall

# 2. 创建配置文件
cp .env.example .env        # Windows: Copy-Item .env.example .env

# 3. 生成随机 JWT_SECRET 并填入 .env（必填，缺失或弱值后端拒绝启动）
python -c "import secrets; print(secrets.token_urlsafe(48))"
# 将输出粘贴到 .env 的 JWT_SECRET= 后（步骤详见下方「安全配置（JWT Secret）」）

# 4. 一键启动（首次自动构建镜像、初始化 MySQL、执行数据库迁移）
docker compose up -d --build

# 5. 检查服务状态
docker compose ps
```

`docker compose ps` 中 backend / mysql / redis 显示 `Up (healthy)`、frontend 显示 `Up` 即表示平台就绪（frontend 未配置 healthcheck，正常只显示 `Up`）。启动过程中 backend 会等待 MySQL 就绪，短暂显示 `Up (starting)` 属正常；若 MySQL 不可用，backend 会显示 `Up (unhealthy)`（Redis 异常不影响健康判定，商品查询自动降级回退 MySQL）。

日常再次启动可省略 `--build`（`docker compose up -d`）；修改代码后使用 `docker compose up -d --build` 让新代码生效。

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
docker compose down -v       # 停止并删除数据卷（会清空数据库、Redis 数据与上传的商品图片，谨慎使用）
```

MySQL 数据、Redis 数据与上传的商品图片分别保存在命名卷（实际名为 `<project>_mysql-data`、`<project>_redis-data`、`<project>_uploads`），重建容器不丢失。

### 初始化管理员与示例数据（可选）

```bash
docker compose exec -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD='<强密码>' backend python seed.py
```

首次运行创建管理员（用户名默认 `admin`，密码至少 12 位且禁止弱密码）和示例分类、商品；重复执行幂等。重置密码：

```bash
docker compose exec -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD='<新强密码>' backend python seed.py --reset-admin-password
```

部署细节见 [docs/docker-deployment.md](docs/docker-deployment.md)。

## 安全配置（JWT Secret）【重点】

`JWT_SECRET` 是后端签发 / 校验登录令牌的签名密钥，为**必填配置**：缺失、少于 32 字节或命中已知弱值（如 `dev-only-*`、`change-me-*`）时，后端会拒绝启动。`.env.example` 只提供占位符，复制后必须替换。

1. 在终端生成一串随机字符：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
# 没有 Python 可用：openssl rand -base64 48
```

2. 打开项目根目录的 `.env` 文件，找到这一行：

```
JWT_SECRET=
```

3. 把生成的随机串粘贴到 `=` 后面并保存，例如：

```
JWT_SECRET=8jFk2mQx...（一大串随机字符）
```

注意：`.env` 已被 `.gitignore` 排除，不会提交到 GitHub；更换密钥后所有已登录用户需重新登录。

## 环境变量

- 必填：`MYSQL_ROOT_PASSWORD`、`MYSQL_PASSWORD`（须与 `DATABASE_URL` 内密码一致）、`DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`
- 可选：`MYSQL_PORT` / `REDIS_PORT` / `FRONTEND_PORT` / `BACKEND_PORT`（宿主机端口）、`PRODUCT_CACHE_TTL_SECONDS`（缓存 TTL）、`ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS`（Token 有效期）、`LOGIN_RATE_LIMIT_*`（登录限流）、`ADMIN_USERNAME` / `ADMIN_PASSWORD`（seed 使用）

完整变量清单、默认值与说明见根目录 `.env.example`（Docker 部署）与 `backend/.env.example`（本地开发）。

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

```powershell
# 1. 初始化数据库（创建 tea_mall 与 tea_mall_test 及本地账号 tea_mall）
mysql -u root -p < sql/init.sql

# 2. 启动 Redis
docker compose up -d redis

# 3. 启动后端（8000 端口）
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # 生成并填写随机 JWT_SECRET（方法见「安全配置」章节），按需修改数据库连接
alembic upgrade head          # 按 Alembic 迁移建立/更新数据表
uvicorn app.main:app --reload

# 4. 初始化种子数据（可选；重置密码加 --reset-admin-password）
$env:ADMIN_PASSWORD = '<强密码>'
python seed.py

# 5. 启动前端（5173 端口）
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173（前端 dev server 已将 `/api` 与 `/uploads` 代理到后端 8000 端口）。

## 测试

后端测试使用独立的测试数据库 `tea_mall_test` 与独立的测试 Redis（DB 15），与开发数据完全隔离；测试库由 `sql/init.sql` 或 Docker 的 `database/init.sql` 创建。破坏性清理在非测试环境下会被拒绝执行。

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

1. **后端反复重启 / JWT_SECRET 缺失或为弱值**：按「安全配置（JWT Secret）」生成随机值填入 `.env` 后重新 `docker compose up -d`。
2. **数据库连接失败**：多为密码不一致——`.env` 中 `DATABASE_URL` 内的密码必须与 `MYSQL_PASSWORD` 相同；修改密码后需 `docker compose down -v && docker compose up -d` 重建数据卷（会清空数据，谨慎使用）。
3. **端口冲突**：MySQL 默认映射宿主 3307；仍冲突时修改 `.env` 中的 `MYSQL_PORT` / `REDIS_PORT` / `FRONTEND_PORT` / `BACKEND_PORT` 后重新 `docker compose up -d`。
4. **前端 502 / 容器 restarting / 镜像构建失败**：先 `docker compose ps` 查看状态，再用 `docker compose logs -f <service>` 查看报错；网络原因可在 Docker Desktop → Settings → Docker Engine 配置 `registry-mirrors` 加速或配置代理；前端镜像默认使用国内 npm 源（npmmirror），非国内 / 受限网络可指定官方源重建：`docker compose build --build-arg NPM_REGISTRY=https://registry.npmjs.org frontend && docker compose up -d`。

## 文档入口

- Docker 部署详解：[docs/docker-deployment.md](docs/docker-deployment.md)
- 阶段任务表：[docs/development/roadmap.md](docs/development/roadmap.md)
- 模块依赖关系：[docs/development/dependency-tree.md](docs/development/dependency-tree.md)
- V2.0 阶段验收报告：[docs/v2.0-reports/](docs/v2.0-reports/)
- V2.0 最终审查报告：[docs/v2.0-review/](docs/v2.0-review/)
- 开发规则：[AGENTS.md](AGENTS.md)
