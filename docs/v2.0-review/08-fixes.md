# 阶段 8 报告：问题修复

> 日期：2026-08-16 ｜ 结论：**修复完成**。P1×1 + P2×5 全部实施并验证：pytest **316 passed**（新增 4 用例）、`npm run build` 通过、运行期复核 9/9 通过、镜像已重建生效、开发栈四服务 healthy（products=13）。

## 1. 修复清单与实施

| 编号 | 级别 | 修复内容 | 涉及文件 |
| --- | --- | --- | --- |
| ISSUE-003 | P1 | Admin 取消订单恢复 SKU 库存并重算商品汇总（与用户取消路径一致） | `backend/app/services/admin.py` |
| ISSUE-004 | P2 | 前端 `Product.price` / `Sku.price` 类型改为 `string`（与后端 Decimal 序列化一致） | `frontend/src/types/product.ts` |
| ISSUE-005 | P2 | 整体替换 SKU 前检查购物车引用，存在则 400 `SKU_IN_USE_IN_CART`，不再静默清空购物车 | `backend/app/services/product.py` |
| ISSUE-006 | P2 | 商品删除前检查购物车/订单引用，返回 400 `PRODUCT_IN_USE`；去掉显式 `max(id)+1`，改自增 | `backend/app/services/product.py` |
| ISSUE-011 | P2 | 客户端 IP 解析：优先 `X-Real-IP` → `X-Forwarded-For` 末值 → 直连地址，杜绝伪造首值绕过 | `backend/app/services/rate_limit.py` |
| ISSUE-017 | P2 | 移除 compose 4 处固定 `container_name`，支持同主机多环境并行 | `docker-compose.yml` |

## 2. 测试增强（不改变业务范围）

- `test_admin_orders`：Admin 取消后断言 SKU 级库存同步恢复。
- `test_products`：ID 自增行为（替换原 max+1 断言）；删除有购物车/订单引用商品返回 400。
- `test_skus`：购物车引用存在时替换 SKU 返回 400。
- `test_rate_limit`：XFF 取末值、X-Real-IP 优先。
- `test_schema_contract`：price 值类型断言（str）。

## 3. 验证结果

| 项 | 结果 |
| --- | --- |
| 针对性 pytest（10 个文件） | 99 passed |
| 全量 pytest | **316 passed, 1 warning**（既有 Starlette 弃用告警） |
| `npm run build` | 通过（仅既有 chunk/导入告警） |
| 运行期复核（隔离实例 8001 + tea_mall_test） | 9/9：Admin 取消 sku.stock=10；SKU 替换 400 且购物车保留；删除引用 400；同末值 IP 31 次触发 429；X-Real-IP 优先触发 429 |
| 镜像更新 | backend/frontend 镜像重建，容器 tea-mall-*-1 全部 healthy |
| 开发栈回归 | health ok、products=13、nginx 反代与前端正常 |
| compose 变更 | 容器名改为项目前缀（tea-mall-backend-1 等），四服务正常；`docker compose config` 合法 |

## 4. 未修改项

ISSUE-001/002/007/008/009/010/012/013/014/015/016/018（P3/观察项）按计划记录不修。

## 5. 结论

- 6 项修复全部完成并验证，未改变前后端正常运行；`git diff` 摘要已展示。
- 修复未自动 commit/push（按红线要求，由用户决定）。
