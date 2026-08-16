# 阶段 2 报告：Bug 与潜在 Bug 排查（只读）

> 日期：2026-08-16 ｜ 结论：未发现 P0；P1×1（库存一致性，ISSUE-003）；P2×4（契约/数据一致性/限流绕过，ISSUE-004/005/006/011）；P3 若干。完整清单见 `issues.md`，本阶段不修改代码。

## 1. 认证域

| 场景 | 结论 |
| --- | --- |
| 注册 | 用户名/邮箱唯一性、邮箱规范化、密码 72 字节校验、重复注册 400 业务码，通过 |
| 登录 | 失败统一 400（不泄露用户是否存在）；禁用账号 403 ACCOUNT_DISABLED，通过 |
| Access Token | type/jti/ver/sub/exp 严格校验，黑名单校验，通过 |
| Refresh Token | 轮换即删、epoch 校验、TTL 管理，通过；并发双刷新时一方失败（客户端单飞缓解） |
| Logout | 黑名单 Access + 删除 Refresh；依赖有效 Access（既有设计契约） |
| 用户禁用 | DB status 即时生效 + epoch 失效，通过 |
| 密码错误 | 统一文案，通过 |
| 登录限流 | **IP 维度可被 X-Forwarded-For 伪造绕过**（见 ISSUE-011）；用户名维度限流仍生效 |

## 2. 权限域

- 普通用户/Admin 边界清晰：`get_current_admin` 基于 DB role，管理接口全部走该依赖；`include_off_sale`/下架详情对普通用户返回 403/404；直调 API 无绕过路径，通过。
- 用户状态联动、root 账号保护、禁止操作自己，前后端双重限制，通过。
- 管理端可互相禁用/降权其他管理员（非 root）——功能上允许，非缺陷。

## 3. 商品域

- 列表/详情/搜索/分类筛选/分页：公开只读上架商品，搜索 LIKE 含通配符语义（`%`/`_` 会被当通配符，属可接受行为）。
- SKU：规格名一致性、组合唯一、库存/价格非负、上下架与 SKU 启用校验，通过。
- **整体替换 SKU 会静默清空购物车**（ISSUE-005，`cart_items.sku_id` 级联删除）。
- **商品删除在有引用时返回通用 409**、`create_product` 显式 `max(id)+1`（ISSUE-006）。
- 商品级 price/stock 直改仅限单 SKU，多 SKU 强制走 SKU 管理，通过。
- 图片上传：content-type + 扩展名白名单 + 10MB 限制 + 超限清理半成品，通过；未校验文件魔数（ISSUE-013，纵深防御 P3）。

## 4. Redis 域

- Cache Hit/Miss/TTL/写后失效：键名注册表清晰，商品/分类写操作后按前缀失效，通过。
- 故障降级：商品 fail-open 回退 MySQL、认证 fail-closed 503、限流 fail-open，测试已锁定，通过。
- 恢复：Redis 重启后缓存自动重建；`auth:epoch` 丢失时回退 0（见 ISSUE-015，P3）。
- 数据一致性：缓存仅加速读、MySQL 为权威，TTL 300s 内库存展示可能滞后（设计接受）。

## 5. 数据库域

- 初始化：Docker `database/init.sql` 幂等 + Alembic 0001-0008，空库可完整建表；本地 `sql/init.sql` 建库建号，通过。
- 表结构/约束：唯一约束（用户名/邮箱/分类名/规格组合/SKU 编码）、CHECK 非负、FK 级联策略明确，通过。
- NULL/默认值：email 可空唯一（MySQL 多 NULL 不冲突）、server_default 完整，通过。
- 数据类型：Numeric(10,2)、order_no 长度充足，通过。
- 连接失败：`pool_pre_ping`、启动迁移有限重试后明确失败，通过。

## 6. 前端域

- 页面加载/API 请求/错误处理：axios 统一拦截、单飞刷新、ACCOUNT_DISABLED 强制登出、错误文案提取，通过。
- 401/403：刷新重放仅非认证 URL；403 统一提示，通过。
- 页面权限：路由守卫 `requiresAuth/requiresAdmin` + 后端 401/403 双保险，通过。
- Admin 页面：自身操作/root 保护 UI 与后端一致，通过。
- 环境变量：前端零 `VITE_*` 依赖，API 走相对路径，通过。
- 类型契约：`price` 声明 number、实为 string（ISSUE-004）；注册邮箱前端正则比后端宽松（ISSUE-014，P3）。

## 7. 横切关注

- 并发：下单 `FOR UPDATE` 防超卖，通过；并发加购同 SKU 有唯一约束竞态（ISSUE-012，P3）；`create_product` 并发 ID 冲突有 409 兜底（ISSUE-006 子项）。
- 边界/空数据：分页上限 50、空态覆盖、库存 0/下架/规格选择边界处理完整。
- 重复请求：刷新单飞、提交/支付按钮 loading 防重，通过。
- 数据一致性：**Admin 取消订单库存恢复不一致**（ISSUE-003，P1）；改密提交与 Token 失效非原子（ISSUE-008，P3）。
- 安全：无调试代码、无本机路径、无硬编码 Secret；限流 IP 可伪造（ISSUE-011，P2）；Token 存 localStorage（既有 P2 遗留）；上传未验魔数（ISSUE-013）。

## 8. 静态扫描

- TODO/FIXME/debugger/console.log：无残留（命中仅为 seed.py 正常 CLI 输出与文档示例）。
- 本机路径硬编码（`C:\Users`、`D:\zzh`、`/Users/`、`/home/`）：源码零命中。
- 未使用重要依赖：无；测试依赖进入生产镜像（ISSUE-010，P3）。

## 9. 问题清单（完整）

| 严重度 | 问题 |
| --- | --- |
| P0 | 无 |
| P1 | ISSUE-003：Admin 取消订单只恢复商品级库存，SKU 库存不恢复（账实漂移） |
| P2 | ISSUE-004：price 类型契约不一致；ISSUE-005：替换 SKU 清空购物车；ISSUE-006：删除有引用商品返回通用 409 / 显式 ID 分配；ISSUE-011：X-Forwarded-For 伪造绕过 IP 限流 |
| P3 | ISSUE-001/002（既有告警）、007（限流计数与覆盖面）、008（改密非原子）、009（npm 源说明）、010（测试依赖进镜像）、012（并发加购 409）、013（上传魔数校验）、014（邮箱校验不一致）、015（Redis 丢失后 epoch 回退） |
