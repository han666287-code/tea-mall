# 阶段 6 报告：Docker 更新验证

> 日期：2026-08-16 ｜ 结论：**PASS**。代码修改 → `docker compose up -d --build` → 新镜像生效 → 数据不丢 → 恢复后回归无残留。

## 1. 基线

| 项 | 更新前 |
| --- | --- |
| backend 镜像 | `tea-mall-backend:latest` = `f691c68708b6` |
| frontend 镜像 | `tea-mall-frontend:latest` = `8316018fe4f4` |
| 开发数据 | products=13 |

## 2. 模拟代码更新（临时修改）

在 `backend/app/main.py` 的 `/api/health` 响应中临时增加 `"version": "docker-update-test"` 字段（仅验证用，不改业务逻辑）。

## 3. 重建与验证

| 验证项 | 结果 |
| --- | --- |
| `docker compose up -d --build` | 成功；backend 镜像重建，容器 Recreate |
| 新镜像 ID | backend `f691c68708b6 → 40d47e164485`，容器使用新镜像 |
| 新代码生效 | `/api/health` 返回 `version=docker-update-test`（8000 直连 + 8080 nginx 反代均可见） |
| MySQL 数据不丢 | products=13（与基线一致） |
| Redis | health redis=true，正常 |
| 前后端通信 | nginx 反代 health 正常、前端 index 正常 |

## 4. 恢复与回归

| 验证项 | 结果 |
| --- | --- |
| 恢复临时修改 | 移除 version 字段，重新 `docker compose up -d --build` 成功 |
| health 还原 | 不再包含 version 字段，status=ok db/redis=true |
| git 残留 | `git diff --stat` 为空，仅 untracked `docs/v2.0-review/`（审查产物）；`git diff --check` 通过 |
| 数据 | products=13，四服务 healthy |

## 5. 结论

- 代码修改 → 重建镜像 → 新容器使用新镜像 → 新代码生效链路完整可用。
- MySQL 数据卷在容器重建后数据不丢；Redis 正常；前后端通信正常。
- 临时修改已完全恢复，无业务代码残留；开发环境回到基线。
