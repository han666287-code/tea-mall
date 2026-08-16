# TeaMall V2.0 Final Review — 问题跟踪表

> 编号规则：ISSUE-001 起；严重度 P0/P1/P2/P3；状态：open / fixing / fixed / wontfix / 待验证。
> 原则：同一问题只记一次编号；敏感信息（.env 值、密码、Token、JWT_SECRET）不落盘。

| 编号 | 严重度 | 发现阶段 | 状态 | 标题 | 描述/复现 | 影响 | 建议修复 | 验证方式 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ISSUE-001 | P3 | 阶段 0 基线 | open | Starlette TestClient 弃用警告 | 导入 `fastapi.testclient` 触发 `StarletteDeprecationWarning`（提示安装 httpx2） | 无功能影响，仅告警噪音 | 后续随 httpx2/TestClient 升级处理 | pytest 无该告警 |
| ISSUE-002 | P3 | 阶段 0 基线 | open | 前端主 chunk 超 500 kB | `npm run build` 主 chunk 1107.64 kB（gzip 368.44 kB）；`src/store/auth.ts` 动态+静态混合导入；@vueuse PURE 注释告警 | 首屏体积偏大 | 路由级代码分割 / manualChunks（后续优化） | `npm run build` 无 chunk 告警 |
| ISSUE-007 | P3 | 阶段 1 结构审查 | open | 登录限流对成功登录也计数 | `check_login_rate_limit` 在认证前对所有登录请求计数（含成功），与「登录失败上限」表述有偏差；refresh/改密等敏感操作未限流 | 极端情况下正常用户频繁登录可能被限流；安全面略窄 | 按失败次数计数；敏感操作补限流（后续优化） | 静态 + 限流测试 |
| ISSUE-008 | P3 | 阶段 1 结构审查 | open | change_password 提交与 Token 失效非原子 | 先 `db.commit()` 再 `bump_epoch()`；Redis 故障时客户端收到 503 但密码已修改，旧 Token 仍有效到过期 | 弱一致，非安全漏洞 | 调整顺序或记录待失效任务（后续优化） | 静态审查 |
| ISSUE-009 | P3 | 阶段 1 结构审查 | open | README 未说明 npm 源覆盖 | `frontend/Dockerfile` 默认 `registry.npmmirror.com`，README 常见问题仅提 Docker registry-mirrors，未提 `NPM_REGISTRY` build-arg | 非国内/受限网络环境下前端镜像构建可能失败 | README/部署文档补充 `--build-arg NPM_REGISTRY=...` 说明 | 阶段 4 冷启动 |
| ISSUE-010 | P3 | 阶段 1 结构审查 | open | 测试依赖进入生产镜像 | `requirements.txt` 含 pytest/httpx，`backend/Dockerfile` 全量安装 | 镜像体积增大 | 拆分 requirements-dev.txt（后续优化） | 镜像构建观察 |
| ISSUE-003 | P1 | 阶段 1 结构审查 | fixed（阶段 8）| Admin 取消订单库存恢复不一致 | `services/admin.py update_order_status` 取消 paid 订单时仅 `product.stock += quantity`，不恢复 SKU 库存、不调用 `refresh_product_summaries`；用户取消路径（`services/order.py cancel_order`）则恢复 `sku.stock` 并重算汇总 | 商品汇总库存与 SKU 实际库存漂移，库存展示虚高、账实不一致 | 统一走「恢复 sku.stock + refresh_product_summaries」路径（与用户取消一致） | 阶段 3 已复现：admin 取消后 product.stock=10、sku.stock=8 |
| ISSUE-004 | P2 | 阶段 1 结构审查 | fixed（阶段 8）| 商品/SKU price 类型契约不一致 | 后端 Decimal 序列化为字符串（实测 `"88.50"`），前端 `types/product.ts` 声明 `price: number`；契约测试只锁字段集合不锁值类型 | 类型声明不准确（运行无碍，代码均 Number() 转换） | 前端类型改为 `string`，或补充契约测试锁定值类型 | 阶段 3 已确认：product/sku price 均为字符串 |
| ISSUE-005 | P2 | 阶段 1 结构审查 | fixed（阶段 8）| 整体替换 SKU 会静默清空购物车 | `_sync_skus` 先删除旧 SKU；`cart_items.sku_id` 外键 ondelete=CASCADE → 引用旧 SKU 的购物车项被级联删除；`order_items.sku_id` 置 NULL | 用户购物车数据丢失；历史订单失去 SKU 关联 | 替换 SKU 前提示影响，或仅当规格定义变化时才重建 SKU | 阶段 3 已复现：替换 SKU 后购物车 0 项 |
| ISSUE-006 | P2 | 阶段 1 结构审查 | fixed（阶段 8）| 商品删除行为与 ID 复用 | 删除有购物车引用的商品返回 204 并经 `skus→cart_items.sku_id` CASCADE 静默清空购物车；删除有订单引用的商品返回通用 409（`order_items.product_id` NO ACTION）；`create_product` 用 `max(id)+1` 显式指定 ID | 用户购物车被静默清空；管理端删除提示不明确 | 删除前检查引用并返回明确业务码/二次确认；去掉显式 ID 分配 | 阶段 3 已复现：购物车引用删除 204、订单引用删除 409 |
| ISSUE-011 | P2 | 阶段 2 Bug 排查 | fixed（阶段 8）| 登录限流 IP 维度可被 X-Forwarded-For 伪造绕过 | `services/rate_limit.py _client_ip` 取 `X-Forwarded-For` 首值；nginx 场景首值由客户端可控（nginx 用 `$proxy_add_x_forwarded_for` 追加而非覆盖） | 攻击者可伪造 IP 绕过 IP 维度限流（用户名维度仍生效）；后端 8000 端口直接暴露加剧该风险 | 优先信任 nginx 设置的 `X-Real-IP`，或取 X-Forwarded-For 末值；或仅容器内网暴露 backend | 阶段 3 已复现：12 次伪造 IP 0×429；同用户名 2×429 |
| ISSUE-016 | P3 | 阶段 3 运行验证 | open | 禁用账号前端提示不一致 | 禁用用户已登录会话触发 TOKEN_INVALID（epoch 失效优先），前端 401 拦截器走「登录已过期」而非「账号已被禁用」；ACCOUNT_DISABLED 仅在登录/刷新路径出现 | 提示文案与用户预期不符（安全行为正确） | 前端对 TOKEN_INVALID + 用户已禁用场景补充提示（后续优化） | 阶段 3 已复现：禁用后 /me 返回 TOKEN_INVALID |
| ISSUE-012 | P3 | 阶段 2 Bug 排查 | open | 并发加购同 SKU 可能返回通用 409 | `add_to_cart` 先查后写，并发下唯一约束 `uq_cart_user_sku` 冲突未捕获，落入全局 IntegrityError 409 | 极端并发下加购偶发失败而非数量累加 | 捕获 IntegrityError 后重查重试累加（后续优化） | 并发加购测试 |
| ISSUE-013 | P3 | 阶段 2 Bug 排查 | open | 图片上传未校验文件魔数 | 仅校验 content-type 前缀与扩展名白名单，不校验文件头 | 可上传伪装为图片的恶意文件（扩展名/类型白名单已大幅降低风险，纵深防御缺口） | 校验常见图片格式文件头（后续优化） | 上传伪造文件测试 |
| ISSUE-014 | P3 | 阶段 2 Bug 排查 | open | 前后端邮箱校验规则不一致 | 前端正则 `^[^\s@]+@[^\s@]+\.[^\s@]+$` 宽松于后端 EmailStr | 前端通过、后端 422 的边界输入体验不一致 | 前端与后端规则对齐（后续优化） | 边界邮箱输入测试 |
| ISSUE-015 | P3 | 阶段 2 Bug 排查 | open | Redis 数据丢失后会话失效回退 | `auth:epoch` 存 Redis；Redis 清空/卷丢失后 `get_epoch` 回退 0，改密/禁用产生的 epoch 失效丢失，历史 ver=0 的 Access Token 可能重新有效（Access TTL 15 分钟，窗口有限） | 极端场景下已撤销的短时 Token 复活 | epoch 落库或接受该权衡（后续优化） | 静态 + 恢复演练 |
| ISSUE-017 | P2 | 阶段 4 冷启动 | fixed（阶段 8）| compose 固定容器名与命名卷阻碍多实例/存在数据卷复用风险 | `docker-compose.yml` 固定 `container_name: tea-mall-*` 与命名卷 `mysql-data/redis-data/uploads`（无项目名隔离）；本机保留开发数据卷时，默认 `docker compose up` 的冷启动实例直接挂载旧卷（实测 Access denied） | 同主机无法并行运行两套环境；默认命令在本机会复用旧数据（对全新机器无影响） | 移除固定 container_name 并让卷名带项目前缀，或文档明确「单实例部署、多环境需改卷名」 | 阶段 4 已实测：默认命令失败，`-p` 隔离卷后通过 |
| ISSUE-018 | P3 | 阶段 7 安全检查 | open（观察项） | 本地开发默认口令内置于代码/脚本 | `config.py` 默认 `DATABASE_URL` 含 `tea_mall_dev`，与 `backend/.env.example`、`sql/init.sql` 一致（仅本地开发；Docker 由 .env 覆盖） | 非真实暴露；本地库口令可预测，若开发者照抄默认值且暴露本机 MySQL 3306 有风险 | 文档标注「仅本地开发，生产必改」或移除默认值（后续优化） | 静态确认 |

（后续阶段发现的问题持续追加。）
