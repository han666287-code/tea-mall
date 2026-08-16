# 阶段 9 报告：修复后完整回归

> 日期：2026-08-16 ｜ 结论：**回归通过，无新增问题**。修复未破坏任何既有功能；基线对照见阶段 3（pytest 312 → 316，新增 4 个修复相关用例）。

## 1. 回归结果对照

| 回归项 | 基线（阶段 0/3） | 修复后（阶段 8/9） | 结果 |
| --- | --- | --- | --- |
| pytest 全量 | 312 passed | **316 passed, 1 warning**（同一既有 Starlette 告警） | 通过 |
| `npm run build` | 通过 | 通过（同一既有 chunk/导入告警） | 通过 |
| `git diff --check` | 通过 | 通过（exit 0，仅 LF/CRLF 提示） | 通过 |
| `docker compose ps` | 四服务 healthy | dev 栈四服务 healthy（容器名 tea-mall-*-1） | 通过 |
| 冷启动重跑 | 一次通过（隔离卷） | **一次通过**：coldstart2 全新 clone + .env + `-p coldstart2` + 端口覆盖（8081/8001/3308/6380），与 dev 栈**并行运行**均 healthy；seed 后 10 商品/5 分类/Admin 可登录；验证后已清理 | 通过 |
| 核心流程与权限（阶段 5 全量） | 41/41 | **41/41**（普通用户 8 步、Admin 6 项、403×6、异常场景、订单链路、缓存行为） | 通过 |
| Redis 缓存/降级 | pytest 覆盖 | pytest 全量含 test_cache_consistency / test_cache_degradation / test_redis_isolation / test_product_cache 全部通过；运行期 TTL=300、写后失效通过 | 通过 |
| Docker 镜像重建 | 阶段 6 PASS | 阶段 8 重建生效；**dev 容器活体验证**：同 X-Real-IP 31 次登录触发 429（限流修复已入镜像） | 通过 |

## 2. 多实例并行验证（ISSUE-017 修复确认）

- dev 栈（默认端口 8080/8000/3307/6379）与 coldstart2（偏移端口 8081/8001/3308/6380）**同时运行**，容器名与端口均无冲突，数据互不影响（dev products=13 / coldstart2 空库）。
- 移除固定 `container_name` 后，同主机多实例能力验证通过；端口覆盖走 README 文档化路径。

## 3. 修复针对性回归（阶段 8 运行期复核，9/9）

Admin 取消订单 sku.stock=10 同步恢复；SKU 替换遇购物车引用 400 且购物车保留；删除有引用商品 400；XFF 末值/IP 限流伪造不再绕过；X-Real-IP 优先。

## 4. 结论

- 6 项修复（ISSUE-003/004/005/006/011/017）全部通过回归，未破坏前后端正常运行与既有功能。
- 工作区变更范围：10 个文件 +165/-30（3 后端服务、1 前端类型、compose、5 测试文件）+ `docs/v2.0-review/` 审查产物；未自动 commit/push。
- 阶段 9 完成后进入阶段 10（最终报告），无需再修问题。
