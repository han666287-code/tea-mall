# TeaMall V2.0 Final Review 完整计划书

> 状态：已由用户确认执行（2026-08-16）；本文件为执行用计划书副本，阶段报告见 `docs/v2.0-review/0N-*.md`，问题跟踪见 `docs/v2.0-review/issues.md`。

## 0. 摘要

目标：以「交付给其他开发者使用」为标准，对仓库做最终审查——项目可运行、按 README 可在全新环境冷启动、尽可能发现并验证已有/潜在 Bug、配置问题、前后端兼容问题与冷启动问题，最终给出 **V2.0 READY / NOT READY** 明确结论。

范围边界：不开发新功能、不改变 V2.0 业务范围、不因 Review 做无意义重构；只修复影响稳定性、安全性、可运行性、核心功能与维护性的问题。先审查、后修改；每阶段产出报告并经用户验收后才进入下一阶段。

对应关系：提示词「一~十二」映射为：一（原则）贯穿全程；二→阶段 1；三→阶段 2；四→阶段 3；五→阶段 4；六→阶段 5；七→阶段 6；八→阶段 7；九→阶段 8；十→阶段 9；十一→阶段 10；十二→全程约束。

## 1. 对原提示词的增删改查

增：
- 新增「阶段 0 准备与基线」：复核环境、记录 pytest / `npm run build` / `docker compose ps` / `git diff --check` 基线，作为阶段 9 回归对照；落盘计划书。
- 新增「问题跟踪表」`docs/v2.0-review/issues.md`：问题统一编号（ISSUE-001 起），含发现阶段、严重度、状态、复现步骤、影响、建议修复、验证方式，贯穿全部阶段。
- 新增「敏感信息不打印」原则：`.env` 值、密码、Token、JWT_SECRET 只做存在性/长度/合规检查，不输出明文。
- 新增「前后端契约核对」专项：以 `openapi.json` 与前端 `src/api/*`、`src/types/*` 逐项比对方法、路径、字段与 Decimal 序列化。
- 新增「GitHub 发布检查」补充：除工作区外，扫描 git 历史（`git rev-list --objects --all` 等）是否曾提交敏感文件。
- 新增失败记录模板（失败步骤/错误信息/根本原因/影响范围/解决方案），用于冷启动等所有失败场景。

删（合并重复）：
- 商品/Redis/数据库在静态排查与实际运行验证里重复出现——保留「静态发现 → 运行验证」两轮，同一问题只记一次编号。
- 「修复后完整回归」与「最终报告」合并为阶段 9/10：回归证据直接写入最终报告第 15 节，不重复输出。
- 各节零散的「输出 Review 报告」统一为每阶段一份报告 + 一份最终汇总报告。

改：
- 「全新环境冷启动」在本机改为等价模拟：全新目录 + 全新 `.env` + 全新数据卷；用本地 `git clone` 当前 HEAD 模拟 GitHub 内容（GitHub 实际同步由用户决定）。
- 冷启动方式按用户选择「原样验证」：先暂停开发容器（保留数据卷）→ 原样 clone 用默认端口与容器名执行完整冷启动 → 验证后清理副本并恢复开发环境。
- 「修复」细化为：先提交完整问题清单与修复范围 → 用户确认 → 逐项修复并验证 → 展示 `git diff` 摘要（不自动 commit/push）。
- README 核对从「读一遍」改为「命令逐条实测」：README 中每条启动/初始化命令都在冷启动环境实际执行并核对输出。

查（新增专项核对）：
- README 命令与真实配置一致性（含 NPM_REGISTRY 默认 npmmirror 的可用性、端口、健康检查说明）。
- 依赖锁定：`requirements.txt` 全版本锁定；`package-lock.json` 与 `package.json` 一致（`npm ci` 可复现）。
- 镜像内容：`.dockerignore` 是否排除 `.env`、`.venv`、`node_modules` 等；COPY 范围。
- 多实例冲突：compose 固定 `container_name` 的影响（已在冷启动方案中处理并如实记录）。
- 跨环境差异：时区、Decimal/JSON 序列化、上传目录、大小写、换行符。

## 2. 阶段计划与验收门

每个阶段产出报告到 `docs/v2.0-review/`，完成后等待用户验收，验收通过才进入下一阶段。

阶段 0 · 准备与基线（只读）
- 复核环境与 git 状态；记录基线：pytest 全量（`127.0.0.1:3307/tea_mall_test` + Redis DB15）、`npm run build`、`docker compose ps`、`git diff --check`。
- 落盘：`docs/v2.0-review/00-plan.md`（本计划书）、`docs/v2.0-review/issues.md`（问题跟踪表）。
- 验收门：基线数据与用户确认的计划书。

阶段 1 · 完整结构 Review（只读，不修改）
- 按清单逐项检查后端（FastAPI/Router/Service/Repository/Model/Schema/Config/Auth/RBAC/Redis/Exception/Middleware/Database）、前端（Router/API Client/页面/Components/Store/环境变量/API 调用）、基础设施（Dockerfile/compose/.env.example/.gitignore/初始化脚本/requirements/package.json/README/tests/docs）。
- 核对项：结构合理性、重复/死代码、硬编码配置、本机路径、开发依赖泄漏、未用重要依赖、异常处理缺陷、前后端 API 不一致。
- 产出：`docs/v2.0-review/01-structure-review.md`，问题入 `issues.md`。
- 验收门：完整 Review 报告。

阶段 2 · Bug 与潜在 Bug 排查（只读，不修改）
- 按六大域排查：认证、权限、商品、Redis、数据库、前端；横切关注：并发、边界条件、空数据、重复请求、数据一致性、潜在安全漏洞。
- 产出：`docs/v2.0-review/02-bug-hunting.md`，输出完整 P0/P1/P2/P3 问题清单。
- 验收门：完整问题清单（此时不修改任何代码）。

阶段 3 · 实际运行验证（当前环境）
- 验证后端启动、前端启动、MySQL/Redis 连通、`/api/health`、`openapi.json`、前后端通信。
- 执行 pytest 全量与 `npm run build`，记录所有错误与警告。
- 产出：`docs/v2.0-review/03-runtime-verification.md`，新发现问题入 `issues.md`。
- 验收门：运行验证报告与错误清单。

阶段 4 · 冷启动验证（重点）
- 前置确认：进入本阶段前先征得用户同意暂停开发容器（数据卷保留，测后恢复）。
- 步骤：全新目录 `git clone` 当前仓库 → 按 README `Copy-Item .env.example .env` → 生成随机 JWT_SECRET 与随机 MySQL 密码并同步 `DATABASE_URL` → `docker compose up -d --build` → `docker compose ps` → 四服务就绪、前端可访问、后端健康检查、`seed.py` 初始化 → 服务间通信验证。
- 逐项确认不依赖：本机文件/个人路径/未提交 `.env`/既有数据/本机 Python 与 Node 环境。
- 失败必须记录：失败步骤、错误信息、根本原因、影响范围、解决方案（修复在阶段 8，修复后重跑本阶段）。
- 结束后：清理冷启动副本（`docker compose down -v`），恢复开发环境（`docker compose up -d`，卷保留）。
- 产出：`docs/v2.0-review/04-coldstart.md`。
- 验收门：冷启动报告（通过或含失败清单）。

阶段 5 · 核心业务流程验收
- 普通用户 8 步：注册 → 登录 → 获取用户信息 → 浏览商品 → 搜索 → 分类筛选 → 商品详情 → Logout。
- Admin 6 项：Admin 登录 → 管理页面 → 商品管理 → SKU → 库存 → 上下架 → 分类管理。
- 权限：普通用户直调 Admin API 必须 403；异常场景：错误密码、重复注册、无效 Token、过期 Token、Logout 后 Token、禁用用户、非法请求参数。
- 产出：`docs/v2.0-review/05-core-flows.md`（请求/响应摘要，不含敏感数据）。
- 验收门：业务流程验收报告。

阶段 6 · Docker 更新验证
- 代码修改（优先使用阶段 8 的真实修复；若阶段 8 前执行，则用临时 `/api/health` 版本字段模拟）→ `docker compose up -d --build` → 确认新镜像 ID 变化、容器使用新镜像、新代码生效、MySQL 数据不丢（表计数与 Alembic 版本）、Redis 正常、前后端通信正常 → 恢复临时修改并重建回归。
- 产出：`docs/v2.0-review/06-docker-update.md`。
- 验收门：镜像更新验证报告。

阶段 7 · 安全与配置最终检查
- 检查 git 追踪内容与历史：不得包含 `.env`、真实密码、Redis 密码、JWT Secret、Admin 密码、Token、本地数据库文件、node_modules、虚拟环境、日志、本机配置。
- 核对 `.gitignore` 与 `.env.example` 可复制即用；复核 JWT/Refresh Token/RBAC/Admin/用户状态/登录限流；扫描认证绕过、权限绕过、敏感信息泄露、硬编码 Secret。
- 产出：`docs/v2.0-review/07-security.md`。
- 验收门：安全检查报告。

阶段 8 · 问题修复（先确认后修改）
- 汇总 `issues.md`：P0/P1 全部列为必修，P2 给出影响分析与建议（默认只修低成本高收益项，逐项由用户确认），P3 记录不修。
- 先展示完整修复清单与变更摘要，经用户确认后逐项修复。
- 修复纪律：不做无关重构、不新增功能；后端 API/Response/Schema 变化必须同步前端并跑契约测试；每项修复后运行相关测试；修复完展示 `git diff` 摘要（不自动 commit/push）。
- 产出：`docs/v2.0-review/08-fixes.md`，更新 `issues.md` 状态。
- 验收门：修复清单确认与修复完成。

阶段 9 · 修复后完整回归
- 对照阶段 3 基线逐项重跑：pytest 全量、`npm run build`、`docker compose ps`、冷启动（重跑阶段 4）、核心流程与权限（阶段 5）、Redis 缓存/降级、Docker 镜像重建（阶段 6）、`git diff --check`。
- 确认修复未破坏其他功能。
- 产出：`docs/v2.0-review/09-regression.md`。
- 验收门：回归报告。

阶段 10 · 最终报告
- 按用户指定 17 章节生成 `docs/v2.0-review/v2.0-final-review-report.md`，给出 **V2.0 READY** 或 **V2.0 NOT READY**；NOT READY 必须列出阻塞原因。
- 更新 `issues.md` 未修复问题清单；提交/推送由用户决定（红线，不自动执行）。
- 最终验收：报告确认。

## 3. 测试与验收场景

- 基线回归：pytest 全量（目标 ≥312 passed，记录警告）、`npm run build`（vue-tsc + vite）、`git diff --check`、`docker compose config`。
- 冷启动：全新目录 clone → 生成 `.env` → `docker compose up -d --build` → `docker compose ps` 四服务健康 → 前端 8080、后端 `/api/health`、`/docs`、`seed.py` → 服务间通信。
- 业务流：普通用户 8 步、Admin 6 项、越权直调 API 403、异常场景全清单（见阶段 5）。
- 安全：JWT/Refresh 轮换与撤销/RBAC/用户禁用即失效/登录限流；敏感信息扫描（工作区 + git 历史）；认证绕过与权限绕过验证。
- Redis：Cache Hit/Miss/TTL/写后失效、Redis 停止时商品查询回退 MySQL（fail-open）、认证链路 fail-closed 503、Redis 恢复后缓存重建。
- Docker 更新：镜像重建后新代码生效、MySQL 数据与 Alembic 版本不丢、Redis 正常、前后端通信正常、恢复后无残留差异。
- 回归：修复后重跑上述全部场景，逐项对照阶段 3 基线结论。

## 4. 问题分级与修复策略

- P0：必须立即修复（项目无法启动、核心业务不可用、严重安全漏洞、严重数据错误）。
- P1：必须修复（重要业务流程异常、前后端严重不一致、Docker 冷启动失败、数据库初始化问题、Redis 关键功能异常）。
- P2：根据实际影响修复，逐项经用户确认，默认只修低成本高收益项。
- P3：记录为后续优化，不扩大 V2.0 范围。
- 禁止为修 P2/P3 做大型重构；禁止自动开发 V3.0；禁止自动 push、删除 git 历史、危险 git 操作。

## 5. 假设与默认决策

- 用户已确认：冷启动采用「原样验证」（阶段 4 暂停开发容器、保留数据卷、测后恢复）；计划书与阶段报告落盘 `docs/v2.0-review/`，最终报告写入 `docs/v2.0-review/v2.0-final-review-report.md`。
- 冷启动以本地 clone 当前 HEAD（`develop@3cb1aed`，工作区干净）模拟 GitHub 内容；`origin/develop` 落后 4 个提交，GitHub 同步由用户决定。
- pytest 使用 Docker MySQL `127.0.0.1:3307/tea_mall_test` + Redis DB15（按 README 覆盖环境变量），不触碰开发库数据。
- 本计划不改变任何公共 API/类型定义；若修复必须修改后端接口或字段，将同步更新前端 `src/api/*` 与 `src/types/*`，并跑契约与前后端联调测试。
- 阶段报告与最终报告仅记录事实与证据，不编造未经确认的数据；敏感信息全程不打印明文。

## 附：阶段 0 基线记录（2026-08-16）

| 项目 | 结果 | 备注 |
| --- | --- | --- |
| git 状态 | 干净 | `develop@3cb1aed`，领先 `origin/develop` 4 个提交 |
| `git diff --check` | 通过 | 无空白错误 |
| `docker compose config --quiet` | 通过 | 配置合法 |
| `docker compose ps` | 4 服务就绪 | frontend Up / backend Up (healthy) / mysql Up (healthy) / redis Up (healthy) |
| pytest 全量 | **312 passed, 1 warning** | 128 秒；警告：Starlette TestClient httpx 弃用（httpx2） |
| `npm run build` | 通过 | 8.7 秒；警告：主 chunk 1107.64 kB、auth.ts 动态+静态导入、@vueuse PURE 注释 |

环境备注：本机沙箱内 Docker CLI 与 npm 构建需权限提升（目录访问限制），属执行环境约束，非仓库问题。
