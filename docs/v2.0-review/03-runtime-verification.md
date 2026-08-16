# 阶段 3 报告：实际运行验证（当前环境 + 隔离验证环境）

> 日期：2026-08-16 ｜ 结论：当前环境前后端/DB/Redis 连通正常；隔离环境完成问题复现验证：ISSUE-003/004/005/006/011 均获运行证据；认证主链路与权限边界符合设计。

## 1. 当前开发环境连通性（运行中容器）

| 检查项 | 结果 |
| --- | --- |
| `GET /api/health`（backend:8000 直连） | 200，status=ok database=true redis=true |
| `GET /api/health`（nginx:8080 反代） | 200，前后端通信正常 |
| `GET /`（frontend:8080） | 200，index.html 正常（含 #app 挂载点） |
| `GET /`（backend root） | 200，`Tea Mall API` |
| `GET /openapi.json` | 25 个路径，6 个 router + root/health 齐全 |
| `docker compose ps` / `config` | 四服务 healthy / 配置合法 |

## 2. 测试与构建

- pytest 全量：**312 passed, 1 warning**（128s；警告为 Starlette TestClient httpx 弃用，ISSUE-001）。
- `npm run build`：通过（8.7s；chunk 体积与动态/静态导入警告，ISSUE-002）。

## 3. 隔离验证环境与问题复现

为不污染开发库，使用独立实例：uvicorn :8001 + `tea_mall_test` + Redis DB15 + 专用测试管理员；验证结束后已停止实例、`FLUSHDB` 清空测试 Redis。验证数据使用 `testvr*` 前缀（pytest conftest 会清理 `test%` 行）。

| 验证项 | 结果 | 证据 |
| --- | --- | --- |
| ISSUE-003 Admin 取消订单库存恢复 | **复现（P1 确认）** | 商品库存 10，下单 2 件后 product.stock=8；admin 取消后 product.stock=10 但 **sku.stock=8**（SKU 未恢复） |
| ISSUE-004 price 序列化类型 | **确认（P2）** | 新建商品 price=88.5 → 响应 `"88.50"`（str）；product.price 与 sku.price 均为字符串 |
| ISSUE-005 替换 SKU 清空购物车 | **复现（P2 确认）** | 加购 1 件后 `PUT /products/{id}/skus` 替换 SKU → 购物车变为 0 项（`cart_items.sku_id` CASCADE 级联删除） |
| ISSUE-006 商品删除行为 | **复现并细化（P2）** | 有购物车引用：DELETE → 204（经 `skus→cart_items.sku_id` CASCADE 静默清空购物车）；有订单引用：DELETE → 409（`order_items.product_id` NO ACTION）；`information_schema` 确认外键规则 |
| ISSUE-011 登录限流 IP 伪造绕过 | **复现（P2 确认）** | 12 个不同用户名+不同伪造 `X-Forwarded-For` → 0×429；同用户名+同 IP 12 次失败 → 2×429（用户名维度仍生效） |

## 4. 认证主链路与权限抽查（隔离环境）

| 场景 | 结果 |
| --- | --- |
| 注册 / 登录 / /auth/me | 201 / 200 / 200，符合预期 |
| Refresh 轮换 + 旧 refresh 复用 | 200 + 401 REFRESH_TOKEN_INVALID，符合预期 |
| Logout 后 Access Token | 401 TOKEN_INVALID（黑名单生效），符合预期 |
| 禁用用户已登录会话 | 401（epoch 失效先触发 TOKEN_INVALID；登录路径 403 ACCOUNT_DISABLED；测试已锁定该设计） |
| 普通用户调 Admin API | 403，符合预期 |
| 普通用户访问他人订单 | 404 ORDER_NOT_FOUND，符合预期 |

## 5. 本阶段结论

- 无新增 P0/P1 运行期故障；ISSUE-003 确认为真实数据一致性 Bug（P1）。
- ISSUE-006 行为细化：商品删除会经 SKU 级联静默清空购物车（与 ISSUE-005 同根），有订单时返回通用 409。
- 新增 ISSUE-016（P3）：已登录用户被禁用后前端提示为「登录已过期」而非「账号已被禁用」（TOKEN_INVALID 优先于 ACCOUNT_DISABLED，前端 ACCOUNT_DISABLED 分支实际难以触发）。
- 开发环境未被修改：全部验证数据位于测试库，测试 Redis 已清空。
