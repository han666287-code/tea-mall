# Tea Mall

茶叶电商平台学习项目：Vue3 + TypeScript + FastAPI + MySQL + Redis，前后端分离、单体仓库。

## 功能（v1）

- 用户注册 / 登录（JWT 认证，bcrypt 密码哈希）
- 商品分类、商品列表、商品详情、关键词搜索、分类筛选、分页
- 购物车：加购、数量累加、修改数量、删除、合计金额
- 订单：从购物车下单（扣库存、清购物车）、模拟支付、取消订单、我的订单
- 管理端：分类管理、商品管理（图片上传、上下架）、订单管理（状态流转）

## 技术栈

- 前端：Vue3 / TypeScript / Vite / Vue Router / Pinia / Axios / Element Plus
- 后端：Python / FastAPI / SQLAlchemy 2.x
- 数据库：MySQL 8.0（本机）
- 缓存：Redis（Docker，缓存分类与商品，TTL 5 分钟）

## 目录结构

```text
tea-mall
├── frontend          # 前端（Vue3 + Vite）
│   └── src
│       ├── api       # Axios 封装与接口
│       ├── components# 通用组件
│       ├── router    # 路由 + 登录/管理员守卫
│       ├── store     # Pinia（auth / cart）
│       ├── types     # TypeScript 类型
│       └── views     # 页面（含 admin/ 管理端）
├── backend           # 后端（FastAPI）
│   └── app
│       ├── core      # 密码哈希、JWT、权限依赖
│       ├── models    # ORM 模型
│       ├── schemas   # 请求/响应模型
│       ├── routers   # 路由
│       ├── services  # 业务逻辑
│       └── main.py   # 应用入口
├── sql               # 建库脚本
├── docs/development  # 阶段任务表与依赖关系
├── docker-compose.yml
├── README.md
└── AGENTS.md
```

## 环境要求

- Python 3.12+
- Node.js 20+
- MySQL 8.0（本机安装并已启动）
- Docker（用于运行 Redis）

## 启动步骤（从零到可访问）

### 1. 初始化数据库

```powershell
mysql -u root -p < sql/init.sql
```

该脚本会创建 `tea_mall` 数据库和开发账号 `tea_mall / tea_mall_dev`。

### 2. 启动 Redis

```powershell
docker compose up -d
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

创建默认管理员 `admin / admin123` 和 5 个分类、10 个示例茶叶商品。

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

- 阶段任务表：[docs/development/roadmap.md](docs/development/roadmap.md)
- 模块依赖关系：[docs/development/dependency-tree.md](docs/development/dependency-tree.md)
- 开发规则：[AGENTS.md](AGENTS.md)
