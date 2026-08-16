# 阶段 5 报告：核心业务流程验收

> 日期：2026-08-16 ｜ 结论：**41/41 全部通过**，未发现新问题。验证环境为隔离实例（uvicorn :8001 + tea_mall_test + Redis DB15），开发环境与开发库未受影响；测试 Redis 已清空。

## A. 普通用户流程（8 步）

| 步骤 | 结果 |
| --- | --- |
| 注册 | 201，通过 |
| 登录 | 200，返回 access + refresh，通过 |
| 获取用户信息（/auth/me） | 200，通过 |
| 浏览商品列表 | 200，通过 |
| 关键词搜索 | 200，通过 |
| 分类筛选 | 200，通过 |
| 商品详情 | 200，通过 |
| Logout | 200；随后使用原 token → 401 TOKEN_INVALID，通过 |

## B. Admin 流程（6 项）

| 项 | 结果 |
| --- | --- |
| Admin 登录 | 200（role=admin），通过 |
| 商品管理（创建商品） | 201，通过 |
| SKU 管理（替换 SKU：规格/价格/库存） | 200，通过 |
| 库存（SKU 级更新并同步商品汇总） | sku.stock=15、product.stock=15，通过 |
| 上下架 | 下架后公开详情 404；重新上架后恢复，通过 |
| 分类管理（创建/修改/含下架商品列表） | 通过 |

## C. 权限（普通用户直调 Admin API）

6 项全部 403：`GET /admin/orders`、`GET /admin/users`、`POST /categories`、`POST /products`、`PATCH /admin/orders/{id}/status`、`PATCH /admin/users/{id}/status`。

## D. 异常场景

| 场景 | 结果 |
| --- | --- |
| 错误密码 | 400 INVALID_CREDENTIALS |
| 重复注册 | 400 USERNAME_TAKEN |
| 无效 Token | 401 TOKEN_INVALID |
| 过期 Token（构造过期 JWT） | 401 |
| 禁用用户已登录会话 | 401 TOKEN_INVALID |
| 禁用用户重新登录 | 403 ACCOUNT_DISABLED |
| 非法参数（page_size>50） | 422 |
| 非法参数（quantity=0） | 422 |

## E. 购物车 → 订单 → 支付 → 发货 → 完成（核心链路）

加购（201）→ 下单（201，total=176.00）→ 支付（paid）→ Admin 发货（shipped）→ Admin 完成（completed）→ 商品库存 15→13，全部通过。

## F. Redis 缓存行为

- 商品详情缓存写入：通过（cache:product:* 命中 1 个键）。
- 列表缓存 TTL：ttl=300s，通过。
- 商品更新后缓存失效：cache:products:* / cache:product:* 归零，通过。

## 结论

- 核心业务全流程（普通用户/Admin/权限/异常/订单链路/缓存）验收通过。
- 未发现新的 P0-P3 问题；阶段 5 不涉及代码修改。
- 前端页面加载与 nginx 反代已在阶段 3/4 验证（本阶段为 API 级真实 HTTP 流程验收）。
