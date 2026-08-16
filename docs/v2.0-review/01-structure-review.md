# 阶段 1 报告：完整结构 Review（只读）

> 日期：2026-08-16 ｜ 结论：整体结构合理、工程化程度高；发现 1 个 P1 数据一致性疑点、多个 P2/P3 契约与边界问题（详见 `issues.md`）。

## 1. 后端结构

分层与职责：
- `app/main.py`：应用入口，注册 6 个 router 与统一异常处理器（BusinessException/HTTPException/422/IntegrityError/500），静态挂载 `/uploads`。无自定义中间件，认证与鉴权由 `core/deps.py` 依赖承担，异常由 Handler 承担，结构合理。
- `app/core/`：`security.py`（bcrypt + JWT 签发/解析，Access Token 含 type/jti/ver/iat/exp）、`deps.py`（`get_current_user` / `get_optional_current_user` / `get_current_admin` / `get_optional_current_admin`，401/403 边界清晰）、`exceptions.py` + `exception_handlers.py`（统一 `{detail, code}` 错误体，500 不泄露内部细节）。
- `app/config.py`：pydantic-settings 读取环境变量；`JWT_SECRET` 必填、弱值拒绝启动；TTL/限流可配置。
- `app/database.py`：`pool_pre_ping`、请求级 Session、异常统一 rollback、finally close。
- `app/models/`：12 张表模型，约束完整（唯一约束、CHECK、FK 级联策略、索引）。商品→SKU→规格体系与订单快照设计合理。
- `app/repositories/`：查询封装，避免 N+1（selectinload/joinedload），`get_locked_by_ids` 用 `FOR UPDATE` 防超卖。
- `app/services/`：业务规则集中（注册唯一性、SKU 校验、库存扣减、订单状态机、缓存失效、fail-closed/fail-open 降级语义）。
- `app/schemas/`：请求/响应模型与前端类型一一对应，`extra: forbid` 防注入，密码 72 字节 UTF-8 校验。
- `alembic/`：0001-0008 迁移链完整，0006-0008 含存量数据回填，与模型定义一致。

## 2. 前端结构

- `src/api/`：6 个模块与后端 6 个 router 的方法/路径/参数对齐；`http.ts` 统一 axios 实例（token 注入、401 单飞刷新、ACCOUNT_DISABLED 强制登出、错误文案提取）。
- `src/router/index.ts`：`requiresAuth` / `requiresAdmin` 守卫完整；未登录跳登录页带 redirect。
- `src/store/`：Pinia auth（token/refreshToken/user，localStorage 持久化）与 cart。
- `src/views/`、`components/`、`layouts/`：页面与组件划分清晰，Admin 布局独立；空态/加载态/按钮 loading 覆盖良好。
- 环境变量：前端不依赖任何 `VITE_*` 变量；API 走 `/api` 相对路径（Vite 代理/nginx 反代）。
- `vite.config.ts` 代理 `localhost:8000` 仅限本地开发（既有遗留 P2，不随 Docker 发布）。

## 3. 基础设施

- `docker-compose.yml`：四服务编排正确；backend 依赖 mysql healthy、redis 仅 service_started（Redis 故障不阻塞平台）；健康检查合理；数据卷 mysql-data/redis-data/uploads 持久化。
- `backend/Dockerfile` + `docker-entrypoint.sh`：依赖层缓存、`alembic upgrade head` 有限重试（20×2s）、.dockerignore 排除 `.env`/`.venv`/`tests`/`uploads`。
- `frontend/Dockerfile` + `nginx.conf`：多阶段构建（npm ci + vue-tsc + vite build → nginx），`/api`、`/uploads` 反代，SPA history 回退，10MB 上传限制。注意：默认 npm 源为 npmmirror，README 未说明 `NPM_REGISTRY` build-arg 覆盖方式（非国内环境冷启动风险点）。
- `.env.example`（根 + backend）：变量完整、含必填/默认/示例说明；`JWT_SECRET` 无默认值。
- `.gitignore`：覆盖 `.env`、venv、node_modules、dist、日志、uploads、.idea 等。
- `database/init.sql` / `sql/init.sql`：Docker 初始化幂等，本地脚本建库建号，密码无字面量入库。
- `requirements.txt`：全部版本锁定且均被使用（含 pytest/httpx 测试依赖装入生产镜像，P3 优化点）。
- `package.json` + `package-lock.json`：依赖锁定，`npm ci` 可复现（Docker 内验证）。
- `README.md` / `docs/docker-deployment.md`：启动步骤与真实配置基本一致，命令可用（阶段 4 将逐条实测）。

## 4. 检查项结论

| 检查项 | 结论 |
| --- | --- |
| 结构合理性 | 合理；Router/Service/Repository/Model/Schema 职责清晰，前端与后端对应整齐 |
| 重复代码 | 无实质重复；`formatTime`/价格格式化在多个视图重复（小工具函数，非问题） |
| 死代码 | 无明显死代码；少量 `.gitkeep` 占位文件 |
| 硬编码配置 | 无硬编码 Secret/密码；仅 vite 代理 `localhost:8000`（开发配置，已知遗留） |
| 本机路径 | 无（源码/镜像/脚本均使用相对路径或环境变量） |
| 开发依赖泄漏 | backend 镜像含 pytest/httpx（P3）；前端多阶段构建不泄漏 node_modules |
| 未用重要依赖 | 未发现 |
| 异常处理 | 统一 `{detail, code}`；Service 层不抛 HTTPException；500 不泄露内部细节 |
| 前后端 API 一致 | 方法/路径/字段集合一致；**值类型存在 1 处不一致**（见 ISSUE-004） |
| 中间件 | 无自定义中间件、无 CORS——当前同源代理架构不需要，直连跨域调用会失败（设计说明） |

## 5. 本阶段发现的问题

详见 [issues.md](issues.md)：
- ISSUE-003（P1，待运行验证）：Admin 取消已支付订单只恢复商品级 `product.stock`，不恢复 SKU 库存、不重算汇总，与用户取消路径不一致，存在库存账实漂移。
- ISSUE-004（P2）：商品/SKU `price` 前端 TS 类型为 `number`，后端实际返回字符串（已实测 `"120.00"`）；运行无碍（代码均 Number() 转换），类型契约不准确。
- ISSUE-005（P2，待验证）：整体替换 SKU 时旧 SKU 被删除，`cart_items.sku_id` 级联删除会导致用户购物车项被静默清空，`order_items.sku_id` 置 NULL。
- ISSUE-006（P2/P3）：删除有订单/购物车引用的商品返回通用 409；`create_product` 用 `max(id)+1` 显式指定 ID（并发冲突有兜底，删除最大行后可复用 ID）。
- ISSUE-007/008/009/010（P3）：登录限流对成功登录也计数；`change_password` 先 commit 后 bump_epoch（Redis 故障弱一致）；README 未说明 npm 源覆盖；测试依赖进入生产镜像。

## 6. 未发现问题（通过项）

- JWT 校验（sub/type/jti/ver/黑名单/epoch）、RBAC 边界、用户状态联动设计完整。
- 商品/分类缓存键注册表清晰，写后失效覆盖创建/更新/删除/图片/库存变化。
- 迁移与模型一致，外键级联策略明确（skus CASCADE、order_items.sku_id SET NULL）。
- 前端守卫、401 单飞刷新、禁用账号强制登出、错误提示链路完整。
- `.dockerignore` / `.gitignore` / `.env.example` 覆盖到位。
