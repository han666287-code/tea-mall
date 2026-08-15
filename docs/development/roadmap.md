# 阶段任务表（Roadmap）

> 本文件是项目开发的唯一阶段依据：必须严格按照 Phase 顺序开发，每个 Phase 完成后等待用户确认，才允许进入下一 Phase。
>
> 说明：下文 `Phase 0–6` 为 V1 阶段表（历史基线，V1 功能开发）；`V2.0-1 ~ V2.0-9` 为 V2.0 工程化升级阶段（见文末「V2.0 阶段表」）。两套编号相互独立，V2.0 各阶段叠加在 V1 功能之上，开发顺序仍按各自编号执行。

---

## Phase 0：项目初始化

**目标：**
把项目骨架搭起来，前后端都能启动，数据库和 Redis 连接打通，为后续阶段打好可运行的基础。

**任务：**

后端：
- git init，创建 `.gitignore`（忽略 `.env`、`node_modules`、`uploads/`、`__pycache__`、虚拟环境等）
- 创建 `requirements.txt`：fastapi、uvicorn、sqlalchemy、pymysql、bcrypt、PyJWT、redis、pydantic-settings、python-multipart、pytest、httpx
- 补全 `app/` 结构：`config.py`（读取 .env）、`database.py`（engine + SessionLocal + Base）
- 创建 `.env.example`：数据库连接、Redis 地址、JWT 密钥
- 创建 `sql/init.sql`：建库 `tea_mall` 并授权
- 创建 `docker-compose.yml`：仅 Redis 服务
- 用 SQLAlchemy `create_all` 实现启动时自动建表（先建空 Base，模型后补）
- 后端启动命令写入 README

前端：
- 用 Vite 创建 Vue3 + TypeScript 项目（`frontend/`）
- 安装依赖：vue-router、pinia、axios、element-plus、@element-plus/icons-vue
- 配置 `vite.config.ts`：`/api` 代理到 `http://localhost:8000`、别名 `@`
- 搭建 `src/` 目录：api、components、router、store、views、types
- 创建基础布局 `App.vue` 和空路由

数据库：
- 本机 MySQL 创建 `tea_mall` 库，确认后端能连上

**完成标准：**
- 后端 `uvicorn app.main:app` 启动成功，根接口可访问
- 前端 `npm run dev` 启动成功，页面可打开
- MySQL 建库成功，后端能连接且 `create_all` 能建表（空库验证）
- Redis 容器启动成功，`redis-cli ping` 返回 PONG
- README 写好启动步骤

---

## Phase 1：用户认证

**目标：**
实现注册、登录、JWT 认证，前端能保存登录状态并做路由拦截。

**任务：**

后端：
- 创建 `models/user.py`：users 表（username 唯一、password_hash、nickname、role）
- 创建 `schemas/user.py`：注册/登录/用户信息响应模型
- 创建 `core/security.py`：bcrypt 哈希校验 + JWT 签发/解析
- 创建 `core/deps.py`：`get_current_user` 依赖，未登录返回 401
- 创建 `routers/auth.py`：注册接口、登录接口、`/auth/me`
- 创建 `services/auth.py`：用户名查重、密码校验等业务逻辑
- 创建 `seed.py`：创建默认管理员 admin（密码初始化）

前端：
- 创建 `api/http.ts`：Axios 实例 + token 拦截器
- 创建 `api/auth.ts`、`store/auth.ts`（token + user，localStorage 持久化）
- 登录页、注册页、`/auth/me` 加载用户信息
- 路由守卫：未登录跳登录页

**完成标准：**
- 用户可以注册，重复用户名报错
- 用户可以登录，拿到 token
- 未带 token 访问 `/auth/me` 返回 401
- 前端登录状态刷新后不丢失
- pytest 通过：注册、重复用户名、登录成功/失败、鉴权失败

---

## Phase 2：商品与分类

**目标：**
实现分类和商品的完整浏览与管理，包括图片上传、搜索分页和 Redis 缓存。

**任务：**

后端：
- 创建 `models/category.py`、`models/product.py`（含 image_url、is_on_sale）
- 创建分类/商品 schemas
- 创建 `routers/categories.py`：列表（公开）、增删改（管理员）
- 创建 `routers/products.py`：列表+搜索（`category_id`、`keyword`、分页）、详情、增删改（管理员）
- 创建 `routers/uploads.py` 或并入 products：multipart 图片上传到 `backend/uploads/`，返回相对路径
- 配置 FastAPI 静态文件目录 `/uploads`
- 创建 `services/cache.py`：Redis 缓存分类列表、商品列表/详情（TTL 5 分钟）
- 管理员写操作后删除相关缓存键
- `seed.py` 补充示例茶叶分类和商品

前端：
- 首页：分类导航 + 商品卡片列表（分页）
- 商品列表页：搜索框、分类筛选
- 商品详情页
- 管理端：分类管理页、商品管理页（增删改、上传图片、上下架）

**完成标准：**
- 游客可浏览商品列表、详情、按分类和关键词搜索
- 管理员可管理分类和商品、上传图片
- 删除有商品的分类被拒绝
- 普通用户调管理接口返回 403
- 商品数据变更后 Redis 缓存失效
- pytest 通过：公开查询、搜索过滤、分页、权限、缓存失效

---

## Phase 3：购物车

**目标：**
实现登录用户的购物车增删改查，前端购物车页可修改数量并计算总价。

**任务：**

后端：
- 创建 `models/cart_item.py`：`unique(user_id, product_id)`
- 创建购物车 schemas
- 创建 `routers/cart.py`：列表、加购（同商品数量累加）、改数量、删除
- 创建 `services/cart.py`：校验商品存在与库存、归属校验
- 加购/改数量时检查商品 `is_on_sale` 和库存上限

前端：
- 创建 `store/cart.ts`、`api/cart.ts`
- 购物车页面：列表、改数量、删除、合计金额
- 商品详情页和列表页加入"加入购物车"按钮（未登录引导登录）

**完成标准：**
- 登录后可加购、改数量、删除、查看列表
- 同一商品重复加购数量累加
- 用户 A 无法修改用户 B 的购物车（越权返回 404/403）
- 商品下架或库存不足时提示
- pytest 通过：加购、累加、越权、数量边界

---

## Phase 4：订单与模拟支付

**目标：**
实现从购物车创建订单、扣库存、模拟支付、取消订单的完整订单流程。

**任务：**

后端：
- 创建 `models/order.py`、`models/order_item.py`：状态机 `pending → paid → shipped → completed`，pending 可 cancel
- 创建订单 schemas
- 创建 `routers/orders.py`：创建、我的订单列表（分页）、详情、模拟支付、取消
- 创建 `services/order.py`：事务（校验库存 → 写订单+订单项 → 扣库存 → 清购物车）
- 订单号生成规则：时间戳+随机数，唯一
- 支付接口：校验归属、状态为 pending 才能支付
- 取消接口：恢复库存、仅 pending 可取消

前端：
- 结算页：收货信息表单 + 订单确认
- 订单列表页、订单详情页
- 收银台页：点击"确认支付"调支付接口
- 创建 `api/orders.ts`（订单数据页内管理，不新增 store）

**完成标准：**
- 下单 → 支付 → 扣库存 → 清购物车完整链路可用
- 库存不足时整单失败、库存不变
- 重复支付被拒绝（已支付不能再次支付）
- 取消未支付订单恢复库存
- 只能查看/操作自己的订单
- pytest 通过：下单事务、库存不足、重复支付、取消恢复库存、越权

---

## Phase 5：管理端订单管理

**目标：**
管理员能查看全部订单并流转状态（发货、完成、取消）。

**任务：**

后端：
- 创建 `routers/admin.py`：订单列表（分页、按状态过滤）、更新订单状态
- 创建 `services/admin.py`：状态流转合法性校验
- 状态流转规则：pending → paid → shipped → completed；pending 可取消；已支付可取消；发货后不可取消
- 管理员权限校验返回 403

前端：
- 管理端订单列表页：状态筛选、订单详情查看
- 状态操作按钮（发货/完成/取消），非法操作禁用或报错

**完成标准：**
- 管理员可查看全部订单并按状态筛选
- 状态流转符合规则，非法流转（如未支付直接发货）被拒绝
- 普通用户访问管理接口返回 403
- pytest 通过：状态机校验、权限校验

---

## Phase 6：联调打磨

**目标：**
全流程走查，统一错误提示，补全种子数据和文档，让项目可作为学习样例完整交付。

**任务：**

后端：
- 统一错误格式与状态码检查
- 完善 `seed.py`：管理员、分类、若干茶叶商品（含图片占位）
- 确认上传目录与静态文件在路径下可用

前端：
- 统一页面错误提示（Element Plus message）
- 空状态、加载状态、按钮 loading 补齐
- 补齐未登录跳转、管理员入口等细节

文档：
- README 补全：环境要求、启动步骤、测试命令、默认管理员账号、目录说明
- 核对 AGENTS.md 与实际开发流程一致

**完成标准：**
- 完整链路走通：注册 → 登录 → 浏览 → 搜索 → 加购 → 下单 → 支付 → 后台发货 → 完成
- 后端 pytest 全部通过
- 按 README 从零启动项目不超过 5 步
- 交付一份可复现的学习项目说明

## V2.0 阶段表（V2.0-1 ~ V2.0-9）

> V2.0 各阶段叠加在 V1 功能（Phase 0–6）之上，编号与 V1 阶段表相互独立；每个 V2.0 阶段的验收报告见 `docs/v2.0-phaseN-report.md`。

### V2.0-1 安全与启动基础（完成）

**目标：** 将 V1 项目升级为安全、稳定、可重复启动、测试隔离的 V2.0 基础状态。

**任务：**
- `JWT_SECRET` 必填且无默认值：缺失、<32 字节、命中已知弱值时拒绝启动
- Docker 冷启动成功、健康检查准确、MySQL 未就绪不随机失败、正常错误不产生 500
- pytest 使用独立测试库与 Redis，破坏性操作有环境保护；敏感配置不进 Git

**完成标准：** 冷启动/健康检查/安全配置回归通过；`docs/v2.0-phase1-report.md` 结论 PASS

### V2.0-2 数据库工程化（完成）

**目标：** 数据库与后端工程化：版本管理、事务/Session、异常处理、API 规范、分层与查询质量。

**任务：**
- Alembic 迁移体系（空库可完整建表），移除启动 `create_all`，Docker 入口先 `alembic upgrade head` 再启动
- Session/Transaction 管理、统一异常处理与 API Response 规范、Request/Response Schema
- Router/Service/Repository 分层、数据库约束与索引、N+1/查询质量/分页

**完成标准：** 迁移可重复执行、回归测试通过；`docs/v2.0-phase2-report.md` 结论 PASS

### V2.0-3 用户身份与权限体系（完成）

**目标：** 从"能注册登录"升级为企业级用户身份与权限体系。

**任务：**
- 注册唯一性与邮箱规范（`USERNAME_TAKEN` / `EMAIL_TAKEN`）
- Access + Refresh Token 生命周期：Redis 存 SHA-256 指纹、轮换即删、登出撤销、epoch 失效
- 账户安全（改密使全部旧 Token 失效）、RBAC、用户状态生命周期与认证强制、前后端联调

**完成标准：** Token 生命周期/RBAC/账户安全回归通过；`docs/v2.0-phase3-report.md` 结论 PASS

### V2.0-4 商品/SKU 体系（完成）

**目标：** 商品升级为「商品 → SKU → 规格/规格值」结构，SKU 独立价格与库存。

**任务：**
- SKU/规格表与规格组合唯一约束，存量数据自动回填默认 SKU
- 库存与上下架校验链、订单按 SKU 快照与取消恢复；购物车按 SKU
- 商品多图；前端规格选择器与管理端 SKU 编辑器

**完成标准：** SKU 校验/库存/订单快照/多图测试通过；`docs/v2.0-phase4-report.md` 结论 PASS

### V2.0-5 认证整合与 RBAC（完成）

**目标：** 收敛认证面，统一权限控制。

**任务：**
- JWT 编解码与认证依赖单点化（`core/security.py`、`core/deps.py`）
- 集中式可选管理员依赖 `get_optional_current_admin`，公开读/管理写权限边界清晰
- 用户状态联动（禁用即失效）、管理端用户管理（状态/角色）、权限矩阵测试

**完成标准：** 权限矩阵回归通过；`docs/v2.0-phase5-report.md` 结论 PASS

### V2.0-6 Redis 缓存与降级（完成）

**目标：** 缓存工程化与故障降级。

**任务：**
- 统一 Redis 客户端（短超时快速失败）；`PRODUCT_CACHE_TTL_SECONDS` 可配置 TTL
- 商品/分类缓存命中/过期重建/写后失效；故障降级：商品 fail-open 回退 MySQL、认证 fail-closed 503、限流 fail-open

**完成标准：** 缓存命中/失效/降级测试通过；`docs/v2.0-phase6-report.md` 结论 PASS

### V2.0-7 测试与核心业务验证（完成）

**目标：** 对前六阶段功能做系统性测试与核心业务验证，补齐认证安全与商品 Redis 缓存/降级测试缺口，形成可重复的回归基线。

**任务：**
- 审计既有测试体系（pytest + Alembic 迁移建表 + 测试库/测试 Redis 隔离 + 破坏性操作环境保护）
- 认证与权限：401/403/`ACCOUNT_DISABLED`/Refresh 轮换/Logout 撤销/提权防护
- 商品与 Redis：缓存命中/失效/降级语义锁定；基础并发；前后端真实 HTTP 联调与 `npm run build`

**完成标准：** pytest 全量 312 passed、`npm run build` 通过、生产代码零修改；`docs/v2.0-phase7-report.md` 结论 PASS

### V2.0-8 冷启动与 Docker 环境标准化（完成）

**目标：** 解决全新协作者 Clone 后无法启动、环境不一致、Redis/MySQL 启动顺序等问题；一个没有本项目开发环境的人仅凭 README 与 `.env.example` 即可完成 Clone → 配置 → 启动依赖 → 启动前后端 → 访问商城并做基础功能验证。不开发新的业务功能。

**任务：**

冷启动分析（8.1）：
- 只读检查 README、`.env`/`.env.example`、`.gitignore`、compose、Dockerfile、前后端启动方式、数据库初始化与 Redis/MySQL 配置
- 输出失败点分类：阻塞启动 / 影响功能 / 文档不完整，并给出修改文件清单

环境变量与配置标准化（8.2）：
- `.env.example` 完整且可复制即用（JWT_SECRET 必填由开发者生成）；新增 ADMIN_* 说明；逐项注明作用/必填/默认/示例
- `.gitignore` 复核；敏感信息不入 Git；不硬编码数据库/Redis/JWT 秘密；不新增无必要的拆分变量
- README 增加环境变量总表（Docker 用服务名 `mysql`/`redis`，本地用 `localhost`）

Docker Compose 环境标准化（8.3）：
- 四服务（frontend/backend/mysql/redis）由 Compose 编排，MySQL 持久化 + 初始化 + healthcheck；backend 等待 MySQL healthy，Redis 仅等待启动不阻塞后端
- Redis 故障时商品查询回退 MySQL、认证 fail-closed；保留 redis healthcheck 供观察
- 同步更新 `docs/docker-deployment.md` 启动顺序说明

全新环境冷启动验证（8.4）：
- 全新目录 git clone → 按 README 创建 `.env` → `docker compose up -d --build` → 全部服务健康
- 基础功能：前端打开、健康检查、注册/登录/Refresh、商品列表/详情/搜索、Admin 登录与商品管理、普通用户越权 403
- Redis 停止/恢复降级回归；完成后清理冷启动环境，开发环境不受影响

最终验收（8.5）：
- 环境/服务/冷启动/前后端/文档验收；pytest 全量、`npm run build`、README 十项核对
- 更新本文件与 `docs/development/dependency-tree.md`；创建 `docs/v2.0-phase8-report.md`

**完成标准：**
- 冷启动全流程一次通过，12 项基础功能 + 降级验证通过
- 四服务 healthy；Alembic 迁移 0001–0008 全部应用；MySQL/Redis 容器内连通正常
- pytest 全量通过、`npm run build` 通过
- README 覆盖：项目介绍、环境要求、环境变量、本地启动、Docker 启动、数据库初始化、管理员账号、前后端访问地址、常见启动问题
- 无业务逻辑改动、无硬编码 Secret、无本机路径、无调试代码
- 输出 `docs/v2.0-phase8-report.md`，结论 PASS；完成后停止，不自动进入下一阶段

### V2.0-9 最终工程化与交付验收（完成）

**目标：** 对 V2.0 前八个阶段进行最终检查和收尾，确保项目达到：代码可维护、配置完整、GitHub 仓库规范、Docker 可正常运行、可冷启动、代码更新后可重新构建镜像、前后端正常联调、核心业务正常运行。不新增大型业务功能，只修复最终验收发现的必要问题。

**任务：**

整体最终检查（9.1）：
- 八维度只读检查（后端/前端/MySQL/Redis/Docker/测试/配置/文档）：明显 Bug、调试代码、硬编码配置、本机路径、前后端 API 不一致、异常处理缺失、未使用的重要依赖、前八阶段遗留问题
- 按 P0/P1/P2 分类：P0 必须修复，影响启动/安全/核心功能的 P1 一并修复，其余记录为遗留；不进行无意义大规模重构
- 运行 pytest、`npm run build`、`git diff --check`

安全与配置最终检查（9.2）：
- `.env`/`.env.example`/`.gitignore` 检查；敏感信息不入库；`.env.example` 可复制即用且变量说明完整
- 数据库/Redis/缓存 TTL/JWT/前端 API 地址无个人电脑硬编码
- 认证与权限抽查：Access/Refresh/Logout/用户状态/RBAC/Admin 权限无越权
- 运行 pytest、`git diff --check`

GitHub 仓库工程化整理（9.3）：
- 检查 `.gitignore`/README/`.env.example`/docs/Dockerfile/compose/数据库初始化/测试目录，确认不提交 `.env`、密码、Secret、node_modules、虚拟环境、缓存、构建产物、本地数据库、日志、本机配置
- `git status`/`git diff --stat`/`git diff --check` + 敏感信息扫描；不自动 push

README 与部署文档完善（9.4）：
- README 覆盖 13 项：项目介绍、技术栈、目录结构、环境要求、环境变量说明、本地开发启动、Docker 启动（含 `docker compose up -d --build` 与 `docker compose ps` 状态检查）、数据库初始化、Redis 使用说明、前后端访问地址、测试方法、常见启动问题
- 命令与项目实际配置一致，禁止编写不存在的功能

Docker 镜像更新与重新部署验证（9.5）：
- 基线 → 模拟代码更新（健康检查版本字段）→ `docker compose up -d --build` 重建 → 验证新镜像生效、MySQL 数据不丢、Redis 正常、前后端通信正常 → 恢复并回归

全链路最终验收（9.6）：
- 全新环境冷启动（本地 clone 模拟 GitHub）、普通用户流程、Admin 流程、权限验证（直调 API 403）、Redis 缓存/降级验收
- pytest、`npm run build`、`docker compose ps`、`git diff --check`；最终检查无敏感信息/本机路径/调试代码/无关文件

最终交付报告（9.7）：
- 创建 `docs/v2.0-final-report.md`（20 章节，明确区分 V1.0 与 V2.0 流程编号）
- 更新本文件与 `docs/development/dependency-tree.md`（新增 V2.0-9）

**完成标准：**
- 9.1-9.7 依次验收通过：pytest 312 passed、前端构建通过、四服务 healthy、冷启动一次成功、镜像重建链路 PASS、全链路功能与权限验收通过、GitHub 仓库检查通过
- 最终报告结论为 V2.0 COMPLETE；遗留问题（P2）明确列出
- 提交方案先展示摘要与 commit message，经用户确认后提交；不自动 push；完成后停止，不进入 V3.0
