# Tea Mall

茶叶电商平台学习项目：Vue3 + TypeScript + FastAPI + MySQL + Redis，前后端分离。

## 技术栈

- 前端：Vue3 / TypeScript / Vite / Vue Router / Pinia / Axios / Element Plus
- 后端：Python / FastAPI / SQLAlchemy
- 数据库：MySQL 8.0（本机）
- 缓存：Redis（Docker）

## 目录结构

```text
tea-mall
├── frontend          # 前端（Vue3 + Vite）
├── backend           # 后端（FastAPI）
├── sql               # SQL 初始化脚本
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

## 启动步骤

### 1. 初始化数据库

在 PowerShell 中执行（按提示输入 MySQL root 密码）：

```powershell
mysql -u root -p < sql/init.sql
```

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

可选：创建默认管理员账号（首次执行）

```powershell
python seed.py
```

默认管理员：`admin / admin123`（本地学习用途，请勿用于生产）

### 4. 启动前端（5173 端口）

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173

## 测试

后端测试：

```powershell
cd backend
pytest
```

## 开发文档

- 阶段任务表：[docs/development/roadmap.md](docs/development/roadmap.md)
- 模块依赖关系：[docs/development/dependency-tree.md](docs/development/dependency-tree.md)
