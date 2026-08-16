# 阶段 7 报告：安全与配置最终检查

> 日期：2026-08-16 ｜ 结论：**通过**。未发现敏感信息入库（含 git 历史）、未发现认证/权限绕过、无硬编码真实 Secret；新增 1 条 P3 观察（本地开发默认口令，ISSUE-018）。

## 1. Git 仓库与历史检查

| 检查项 | 结果 |
| --- | --- |
| 追踪文件 | 183 个，全部为源码/迁移/测试/文档/部署配置；无 `.env`、node_modules、虚拟环境、日志、数据库文件、本机配置 |
| 历史敏感路径 | `git log --all --name-only` 与 `git rev-list --objects --all` 均无 `.env`/node_modules/venv/日志/密钥文件提交记录 |
| 历史内容扫描 | `git log --all -p` 无私钥/AWS/ghp 等 Token 模式 |
| 忽略规则 | `.env`、backend/.env、backend/uploads/、frontend/node_modules/、frontend/dist/、backend/.venv/、.pytest_cache/ 全部命中 `.gitignore` |
| 镜像内容 | backend/frontend 镜像内无任何 `.env*` 文件 |
| 开发 .env | 未跟踪；JWT_SECRET 长度 64（≥32），仅做长度检查不输出明文 |

## 2. 敏感模式扫描（源码 + 配置文件）

- 私钥头、AWS/ghp/sk-/AIza Token 模式：**零命中**（工作区与历史）。
- 口令/Secret 字面量：仅 `.env.example` 注释中的 `ADMIN_PASSWORD='<强密码>'` 占位示例（无实际值）。
- 配置默认值：`config.py` 默认 `DATABASE_URL` 内嵌本地开发口令 `tea_mall_dev`（与 `backend/.env.example`、`sql/init.sql` 一致，仅本地开发；Docker 环境必须由 `.env` 覆盖）→ 记录 ISSUE-018（P3）。

## 3. .env.example 可复制即用

- 根 `.env.example`：15 个变量齐全（MySQL/Redis/端口/TTL/DATABASE_URL/REDIS_URL/JWT/Token 有效期/限流/ADMIN 注释说明），`JWT_SECRET=` 为空占位，无真实 Secret。
- `backend/.env.example`：本地开发所需变量齐全（DATABASE_URL/REDIS_URL/TTL/JWT/Token 有效期/限流），`JWT_SECRET=` 为空占位。
- 冷启动实测：`Copy-Item .env.example .env` + 随机 JWT_SECRET/密码 后一次启动成功（阶段 4）。

## 4. 认证/权限复核（静态 + 阶段 3/5 运行证据）

| 项 | 结果 |
| --- | --- |
| JWT | 签发/解析严格校验（type/jti/ver/sub/exp），黑名单 + epoch 双失效，阶段 3 实测过期/伪造/登出后均 401 |
| Refresh Token | 轮换即删、旧 token 复用 401，阶段 3/5 实测 |
| RBAC / Admin | 路由鉴权静态扫描：所有写操作均挂 `get_current_user` 或 `get_current_admin`，无绕过路径；普通用户直调 Admin API 6 项全部 403（阶段 5 实测） |
| 用户状态 | 禁用即失效（会话 401 / 登录 403 ACCOUNT_DISABLED），root 保护、禁止操作自己，通过 |
| 登录限流 | 用户名维度生效（阶段 3 实测）；IP 维度存在 X-Forwarded-For 伪造风险（ISSUE-011，P2） |
| 认证绕过/权限绕过 | 未发现 |

## 5. 结论

- Git 仓库（含历史）不含敏感信息；`.gitignore`/`.env.example` 覆盖完整、可复制即用。
- 认证、Refresh、RBAC、Admin、用户状态、限流设计正确且经运行验证；无认证/权限绕过、无敏感信息泄露、无硬编码真实 Secret。
- 新增 ISSUE-018（P3，观察项）：本地开发默认口令 `tea_mall_dev` 内置于 `config.py` 默认值与 `sql/init.sql`，建议文档标注或移除默认值。
