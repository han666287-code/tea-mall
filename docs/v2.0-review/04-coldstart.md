# 阶段 4 报告：冷启动验证

> 日期：2026-08-16 ｜ 结论：**冷启动通过**（隔离数据卷模拟干净环境）。首次默认命令在保留开发数据卷的本机暴露「固定命名卷复用」风险（失败 #1，已定位并记录）；按干净环境等价方式重新验证全部通过。开发环境已恢复基线（products=13）。

## 1. 执行过程（按 README 逐条实测）

| 步骤 | 命令/操作 | 结果 |
| --- | --- | --- |
| 1. Clone | `git clone <repo>` 到全新目录（仓库外） | 183 个文件，HEAD `3cb1aed`，工作区干净 |
| 2. 创建 .env | `Copy-Item .env.example .env` + 生成随机 JWT_SECRET(64) / MySQL 密码(32)，同步 DATABASE_URL | 完成；无 CHANGE_ME 残留（仅注释示例）；`.env` 被 gitignore 排除 |
| 3. 启动 Docker | `docker compose up -d --build` | 镜像构建成功（缓存层），四服务依次就绪 |
| 4. 初始化 MySQL | 首次启动由 MYSQL_* + `database/init.sql` 完成；backend 自动 `alembic upgrade head` | 迁移版本 **0008**，11 张业务表建齐 |
| 5. 启动 Redis | compose 编排 | healthy |
| 6. 启动 Backend | docker-entrypoint.sh（迁移→uvicorn） | healthy |
| 7. 启动 Frontend | nginx 托管 | Up |

## 2. 服务与连通性验证

| 检查项 | 结果 |
| --- | --- |
| `docker compose ps` | backend/mysql/redis `Up (healthy)`，frontend `Up` |
| `GET /api/health`（8000 直连） | status=ok database=true redis=true |
| `GET /api/health`（8080 nginx 反代） | 正常，前后端通信 OK |
| `GET /`（8080） | index.html 正常 |
| `GET /docs`（8000） | 200 |
| 启动时数据 | products=0 / categories=0（空库，无既有数据依赖） |
| `seed.py` | admin + 5 分类 + 10 商品；Admin 登录成功（role=admin, is_root=true） |
| Alembic | 0008；users=1, categories=5, products=10, skus=10 |
| 本地路径依赖 | 跟踪文件扫描无本机路径（唯一命中为 500 错误测试的断言字符串） |
| 本机 Python/Node | 未使用（镜像内 npm ci / pip install / 构建） |

## 3. 失败记录（模板）

### 失败 #1：默认项目名冷启动挂载开发环境数据卷

- 失败步骤：Clone → .env → `docker compose up -d --build`（默认项目名 `tea-mall`）。
- 错误信息：backend 日志 `Access denied for user 'tea_mall'@'172.19.0.4' (using password: YES)`，迁移重试后失败；MySQL 容器内用自身 `MYSQL_PASSWORD` 登录同样被拒。
- 根本原因：compose 使用**固定命名卷**（`tea-mall_mysql-data` 等，无项目名隔离）；本机开发环境已占用同名卷（42 小时旧数据，密码与随机新密码不一致）。冷启动容器复用了开发数据卷，相当于「依赖了之前创建的数据」，与干净环境不等价。
- 影响范围：本机执行默认命令时会复用旧数据卷；对全新机器无此问题。属于「同主机多实例/数据卷复用」工程风险（ISSUE-017）。
- 解决方案：① 保持开发数据卷不动（用户已确认保留），用 `-p coldstart1` 隔离全新数据卷（compose 文件、容器名、端口、.env 均不变）重新验证 → 一次通过；② 交付层面建议移除固定 `container_name`/卷名或文档注明单实例限制（ISSUE-017，P2）。

### 验证时序备注（非产品缺陷）

在 seed 之前访问商品/分类接口会把「空列表」写入 Redis 缓存（TTL 300s），seed 写库后 5 分钟内 API 仍返回空缓存。README 的标准流程（启动 → seed → 使用）不会触发；清空缓存后数据正常返回（10/5）。已作为缓存行为记录，不列入问题。

## 4. 结论

- 干净环境等价冷启动：**一次通过**（隔离卷后）。四服务健康、空库建表、seed 初始化、前后端通信、Admin 登录全部正常。
- 不依赖本机文件/个人路径/未提交 .env/既有数据/本机 Python 与 Node 环境：全部满足。
- 新增 ISSUE-017（P2）：compose 固定容器名与命名卷阻碍同主机多实例，且默认命令在本机存在数据卷复用风险。
- 冷启动副本已清理（容器 + 本次新建卷 + 目录），开发环境已恢复：四服务 healthy，products=13（与阶段 3 基线一致）。
