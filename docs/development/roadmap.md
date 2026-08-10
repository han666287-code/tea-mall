# 阶段任务表（Roadmap）

> 本文件是项目开发的唯一阶段依据：必须严格按照 Phase 顺序开发，每个 Phase 完成后等待用户确认，才允许进入下一 Phase。

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
