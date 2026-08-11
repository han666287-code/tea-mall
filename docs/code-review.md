# TeaMall 代码审查报告

> 审查对象：`master` @ `2eefacb`
> 审查日期：2026-08-11
> 审查方式：完整通读后端代码 + Docker 冷启动实测 + 接口层黑盒验证

**这份文档只指出问题、给出方向和验收方法，不包含现成的修改代码。** 每一条都请自己动手改，改完按「怎么验证」那一节自测。

---

## 0. 先说好的部分

这些是有意识设计的痕迹，不是随手写出来的，值得保持：

- **分层清晰**：`router` 只做参数校验和转发，业务逻辑在 `service`，ORM 模型和 Pydantic schema 分离。很多同级别的练习项目会把 SQL 直接写在路由函数里。
- **权限依赖统一**：`get_current_user` / `get_current_admin` / `get_optional_current_user` 三个依赖收口在 `core/deps.py`，没有在各个路由里重复写鉴权判断。
- **归属校验返回 404 而不是 403**：`cart.get_cart_item_for_user`、`order._get_order_for_user` 查不到别人的资源时统一返 404。这是对的 —— 返 403 等于告诉攻击者"这个 id 存在，只是不属于你"。
- **订单项做了价格快照**：`OrderItem` 冗余了 `product_name` / `price` / `subtotal`，商品后续改价不影响历史订单。很多人会直接关联 `product` 表，这是电商系统的经典错误。
- **缓存失效点覆盖完整**：商品增删改、下单扣库存、取消订单恢复库存都调了 `invalidate_products()`；改分类还会连带失效商品缓存（因为商品响应里带 `category_name`）。这个联动关系考虑到了，不容易。
- **缓存全链路做了异常兜底**：Redis 挂掉自动退化成直查数据库，不影响功能。
- **测试覆盖了 6 个模块**，不是只写个 `assert 1 == 1` 交差。

下面的问题不影响上面这些判断。分层做对了，剩下的都是可以补的。

---

## 1. 阻塞级：`docker compose up -d` 冷启动必失败

### 现象

在一台干净的机器上，严格按 README 执行：

```bash
git clone <repo> && cd tea-mall
cp .env.example .env
docker compose up -d
```

结果（连续两次冷启动，100% 复现）：

```
Container tea-mall-mysql Healthy
Container tea-mall-backend Started
Container tea-mall-backend Error dependency backend failed to start
dependency failed to start: container tea-mall-backend is unhealthy
```

退出码 1，**frontend 容器根本没有被创建**，浏览器打开 8080 什么都没有。

backend 日志：

```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError)
  (2003, "Can't connect to MySQL server on 'mysql' ([Errno 111] Connection refused)")
ERROR:    Application startup failed. Exiting.
```

### 根因

问题在 `docker-compose.yml` 里 mysql 的健康检查命令。

MySQL 客户端有个容易忽略的行为：**`-h localhost` 走的是 unix socket，不是 TCP**。而 `mysql:8.0` 镜像首次初始化时，entrypoint 会先启动一个「只监听 socket、不监听 TCP」的临时服务器，用来执行建库建用户和挂载的 `init.sql`。

于是时间线变成：

1. 临时服务器起来，socket 可用 → `mysqladmin ping -h localhost` 成功 → **容器被判定为 healthy（但此时 3306 端口还没开始监听）**
2. compose 看到 mysql healthy，启动 backend
3. backend 的 `lifespan` 里 `Base.metadata.create_all()` 通过 TCP 连 `mysql:3306` → Connection refused
4. uvicorn 启动失败退出 → backend 不健康 → frontend 的 `depends_on: service_healthy` 永远等不到 → compose 报错退出

`docs/docker-deployment.md` 里写的「backend 等待 mysql、redis 均 healthy 后才启动」这个承诺，实际上是不成立的 —— healthy 是假的。

### 为什么你自己测不出来

因为 backend 配了 `restart: unless-stopped`。它崩溃后会自动重启，几十秒后 MySQL 真正就绪，backend 就活了。你如果手动再敲一次 `docker compose up -d`，这次就会全绿。所以在你的机器上（数据卷已经初始化过、不再走首次初始化流程）几乎永远看不到这个问题，只有**别人第一次克隆运行**才会撞上 —— 而这正是最要命的场景。

### 你该怎么改

两个方向，建议都做：

1. **让健康检查真正反映"能不能连"**。查一下 `mysqladmin` 怎么强制走 TCP 而不是 socket（提示：`--protocol` 参数），改完健康检查就不会在临时服务器阶段误报。
2. **让 backend 启动时能容忍数据库还没准备好**。在 `app/main.py` 的 `lifespan` 里给 `create_all()` 加重试 —— 连不上就 sleep 几秒重试，重试 N 次仍失败才退出。生产环境的服务都该这么写，依赖不可能保证永远先于你就绪。

顺带思考一个问题：`create_all()` 只能建表，不能改表。以后你给 `products` 加一个字段，线上已有的表是不会变的。查一下 **Alembic**，了解「数据库迁移」是怎么回事。这个不用现在做，但要知道 `create_all` 的边界在哪。

### 怎么验证

必须从**完全干净的状态**验证，否则测不出来：

```bash
docker compose down -v
docker compose up -d
echo $?
```

要求：退出码为 0，且 `docker compose ps` 能看到 **4 个**容器（含 frontend）。这个流程要能连续跑通两次。

---

## 2. 严重安全问题：任何人都能伪造管理员身份

### 现象

`.env.example` 里写着：

```
JWT_SECRET=change-me-to-a-random-string-at-least-32-bytes
```

而 README 的快速开始是 `cp .env.example .env && docker compose up -d` —— **照做的人不会去改这个值**。同时 `docker-compose.yml` 里还有一个兜底默认值 `dev-only-secret-change-in-production-0123456789`，连 `.env` 都没有时照样能启动。

这两个字符串都公开写在仓库里。任何人 clone 一下就知道你的签名密钥。

实测攻击：用仓库里的这个密钥，自己用 `hmac` + `sha256` 手工签一个 payload 为 `{"sub": "1", "exp": ...}` 的 HS256 token（不到 10 行代码，标准库就够），然后：

```
GET /api/auth/me
-> 200 {"id":1, "username":"admin", "role":"admin"}

GET /api/admin/orders
-> 200 {"total": 1, "items": [...]}   # 拿到了全站订单，含所有人的收货姓名、电话、地址
```

**完全不需要爆破 `admin123` 密码。** 而且 `seed.py` 创建的管理员通常就是 id=1，连猜都不用猜；就算不是，从 1 往上遍历几次就找到了。

### 为什么这个问题特别值得记住

你的鉴权代码本身没写错：`deps.py` 里角色是从数据库读的，不是从 token 里读的（**这一点做对了**，很多人会把 `role` 塞进 JWT payload，那样连密钥泄露都不需要就能提权）。

问题出在**配置的默认值**上。这是安全里非常典型的一类漏洞：代码逻辑无懈可击，但"默认配置是不安全的，而且默认配置正是绝大多数人实际在用的配置"。

### 你该怎么改

1. `.env.example` 里的 `JWT_SECRET` **留空**，旁边用注释说明怎么生成随机值（`python -c "import secrets; print(secrets.token_hex(32))"`）。示例文件里永远不要放一个"能用"的密钥。
2. 删掉 `docker-compose.yml` 里 `JWT_SECRET` 的 `:-默认值` 兜底。**缺配置就应该启动失败**，不该静默降级成不安全状态。
3. 在 `config.py` 里加校验：`jwt_secret` 为空、或长度过短、或等于任何一个已知占位串时，直接抛异常拒绝启动。
4. `seed.py` 的 `admin/admin123` 同理 —— 改成从环境变量读，或者首次运行时随机生成并打印出来。

### 怎么验证

- 把 `.env` 里的 `JWT_SECRET` 删掉 → `docker compose up` 应该**启动失败并报出清晰的错误信息**，而不是正常起来。
- 填一个 `change-me` 之类的占位串 → 同样应该拒绝启动。

### 顺带一提

`deps.py` 里 `user_id = int(payload.get("sub", 0))` 这一行：`sub` 如果不是数字，`int()` 会抛 `ValueError`，没有任何地方捕获，直接 500。实测确认。签名校验通过但 payload 内容不合预期，属于"token 无效"，应该返 401。**永远不要相信解析出来的数据的类型。**

---

## 3. 并发下单会超卖

### 现象

实测：建一个 `stock=1` 的商品，两个用户各加购 1 件，然后用两个线程同时下单：

```
created product id=11 stock=1
buyer0 create_order -> 201 202608111339463E63A2
buyer1 create_order -> 201 20260811133946405F2C
final stock = 0
RESULT: 2 of 2 orders succeeded on stock=1 -> OVERSOLD
```

**两个订单都创建成功了，一件货卖给了两个人。** 注意最终库存是 0 而不是 -1 —— 这说明两个事务各自读到 `stock=1`、各自算出 `1-1=0`、各自写回 0，后一次写覆盖了前一次。这个现象有个专门的名字：**丢失更新（lost update）**。

### 根因

`app/services/order.py` 里 `create_order` 的流程是：

1. 读出购物车 → 读出商品 → 检查 `cart_item.quantity > product.stock`
2. 构造订单
3. `product.stock -= quantity`

第 1 步和第 3 步之间没有任何并发保护。这是典型的 **read-modify-write** 竞态：先读、再算、再写，而读和写之间别人也能读。全仓库搜不到任何 `with_for_update`、行锁或版本号。

`cancel_order` 里恢复库存也是同样的模式，同样会丢失更新。

### 你该怎么改

这是**整个项目里最值得你亲手解决的技术问题**，别急着抄答案，先搞懂原理。需要理解的概念：

- 数据库的**事务隔离级别**（MySQL InnoDB 默认是 REPEATABLE READ）为什么挡不住这个问题
- **悲观锁**：`SELECT ... FOR UPDATE`，SQLAlchemy 里对应 `.with_for_update()`
- **乐观锁**：加一个 `version` 字段，更新时带上 `WHERE version = :old_version`，检查影响行数
- **原子更新**：`UPDATE products SET stock = stock - :n WHERE id = :id AND stock >= :n`，然后检查 `rowcount` 是不是 1

三种方案各有适用场景，选一种实现，并且**能说清楚你为什么选它、另外两种的代价是什么**。

另外注意顺序问题：如果一个订单里有多个商品，多个并发订单以不同顺序锁商品，会**死锁**。想想怎么避免（提示：固定一个加锁顺序）。

### 怎么验证

**必须写一个并发测试**，光看代码是看不出来的。用 `threading` 起两个线程，用 `threading.Barrier` 让它们尽量同时发出请求，断言：库存为 1 时，两个并发下单**只有一个能成功**，另一个返回 400「库存不足」，且最终库存为 0。

把这个测试加进 `tests/`，它应该在你改之前失败、改之后通过。

---

## 4. 两个会直接 500 的输入

### 现象

实测，全部返回 `500 Internal Server Error`：

| 请求 | 结果 |
| --- | --- |
| `POST /api/auth/login`，密码 100 个字符 | 500 |
| `POST /api/auth/register`，密码 30 个汉字 | 500 |

第一个是**未登录就能触发的 500**，任何人都能打。

### 根因

bcrypt 算法本身限制密码不超过 72 **字节**。而 `bcrypt` 这个库从 5.0 开始，超长时不再静默截断，而是直接抛 `ValueError`：

```
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```

两处漏掉了：

- `LoginRequest.password` **完全没有长度限制**（`RegisterRequest` 有，登录的忘了加）
- `RegisterRequest.password` 的 `max_length=72` 限制的是**字符数**，而 bcrypt 数的是**字节数**。一个汉字 UTF-8 编码占 3 字节，所以 25 个汉字就超了，但 Pydantic 觉得才 25 个字符，放行

这里有两个独立的教训，都很值钱：

1. **校验规则必须和下游的真实约束对齐**。你在 Pydantic 层限制"字符数"，但真正的约束在 bcrypt 层且单位是"字节"，中间这个换算差就是漏洞。凡是涉及长度限制，永远先问一句：**限制的是字符还是字节？**
2. **未捕获的异常 = 500 = 信息泄露 + 可用性问题**。任何用户可控的输入路径上，都不该有"能让服务端抛未处理异常"的可能。

### 为什么你自己测不出来

见下一节 —— 因为 `requirements.txt` 没锁版本。你开发时装的很可能是 bcrypt 4.x（会静默截断，不报错），别人今天 `docker build` 装到的是 5.x（抛异常）。**同一份代码，不同时间构建，行为不一样。**

### 你该怎么改

- 给 `LoginRequest.password` 补长度限制
- 在 `core/security.py` 里按**字节**处理：要么明确拒绝超长（返 400 而不是 500），要么显式截断到 72 字节。选哪个都行，但要在注释里写清楚为什么
- 想一想：还有没有别的地方，Pydantic 的 `max_length` 和数据库列宽（比如 `String(50)`）单位不一致？中文昵称存进 `VARCHAR(50)` 会怎样？（这个 MySQL 层面是按字符算的，但值得你自己去确认一遍，别猜）

### 怎么验证

补两个测试用例：100 字节 ASCII 密码登录、30 个汉字密码注册，断言返回 **400 而不是 500**。

---

## 5. 依赖没锁版本

`backend/requirements.txt` 里 11 个依赖，**一个版本号都没有**：

```
fastapi
uvicorn[standard]
sqlalchemy
...
```

有意思的是，前端做对了：`package-lock.json` 提交进了仓库，Dockerfile 里用的是 `npm ci`（严格按 lock 文件装）。**前后端标准不一致。**

后果是真实的，不是理论问题 —— 上一节那两个 500 就是它造成的。今天构建的镜像和你三个月前构建的不是同一个东西，出了问题你甚至无法复现。

改：至少 `pip freeze > requirements.txt` 锁一份，更好的做法是了解一下 `pip-tools`（`requirements.in` 写直接依赖 → 编译出带完整版本的 `requirements.txt`）或者 `uv`。

顺带：`Dockerfile` 用的是 `python:3.13-slim`，`README` 里说本地开发用 Python 3.12+。**构建环境和开发环境的大版本不一致**，也是同类问题。

---

## 6. 测试会清空真实数据库

`tests/conftest.py` 的 teardown：

```python
db.execute(delete(OrderItem))
db.execute(delete(Order))
db.execute(delete(CartItem))
db.execute(delete(Product).where(Product.name.like("test%")))
db.execute(delete(Category).where(Category.name.like("test%")))
db.execute(delete(User).where(User.username.like("test%")))
```

商品、分类、用户都带了 `LIKE 'test%'` 过滤，**唯独订单和购物车这三行是全表删除**。

而 conftest 直接 `from app.database import engine` —— 它连的就是 `.env` 里 `DATABASE_URL` 指向的那个库，没有任何隔离。README 里还写着「后端测试需要 MySQL 与 Redis 已启动」。

也就是说：**在一个跑着的环境里执行一次 `pytest`，所有真实订单数据全部消失。** `clear_cache` fixture 里的 `cache.clear_all()` 同理，打的是真 Redis。

这个问题现在看起来无所谓（反正是练习项目，数据本来就是假的），但它是一个必须现在就改掉的**习惯问题**。工作中这种代码会造成真事故。

改的方向：

- 测试必须用**独立的数据库**。查一下 FastAPI 的 `app.dependency_overrides`，把 `get_db` 覆盖成指向测试库的 session
- 最省事的做法是测试用 SQLite in-memory，但注意：SQLite 和 MySQL 行为有差异（比如上面第 3 节的行锁，SQLite 测不出来），要清楚你放弃了什么
- 保底也要加一道保险：`prepare_database` 里断言 `settings.database_url` 里含 `test` 字样，否则直接报错拒绝运行

---

## 7. 部署环境下图片上传超过 1MB 必失败

实测，同一个 2MB 的图片：

| 路径 | 结果 |
| --- | --- |
| 经 nginx（`http://localhost:8080/api/...`） | **413 Request Entity Too Large** |
| 直连后端（`http://localhost:8000/api/...`） | 200 成功 |

原因：`frontend/nginx.conf` 没有设置 `client_max_body_size`，nginx 默认上限是 1MB。

注意这个 bug 的特点：**本地开发时测不出来**。因为 `npm run dev` 走的是 Vite 的代理，没有这个限制。只有 Docker 部署后才会出现。手机随手拍一张照片就有好几 MB，也就是说别人第一次上传商品图基本必踩。

而且前端的错误提示会很难懂 —— 413 是 nginx 直接返的，body 是 nginx 的 HTML 错误页，不是你的 `{"detail": "..."}` 格式，`http.ts` 的响应拦截器取不到 `detail`，只会弹一句 `Request failed with status code 413`。

改的方向：

1. nginx 加上 `client_max_body_size`，值和你允许的图片大小对齐
2. **后端也要加大小限制**。现在 `upload_product_image` 是无脑 `copyfileobj` 到磁盘，没有任何上限 —— 别人可以直接把你的硬盘写满。虽然是管理员接口风险较低，但「不信任任何输入的大小」是基本功
3. 前端在选择文件时就先检查大小，给出明确提示，别等到请求发出去才失败

顺带记住这个教训：**开发环境和生产环境之间的每一个差异，都是一个潜在的 bug 藏身处。** 你的 dev 走 Vite 代理、prod 走 nginx，这两者的行为差异就是这个 bug 的温床。

---

## 8. 给别人跑起来还缺的东西

这一节是把上面的问题从"新人视角"重新组织一遍。目标是：**一个完全不了解这个项目的人，克隆下来能不能顺利跑起来。**

必须补的：

1. **第 1 节的健康检查问题** —— README 的第一条命令现在是错的
2. **`seed.py` 从「可选」提升为必做步骤**。不 seed 的话：没有任何分类和商品（首页是空的）、没有 admin 账号（管理端完全进不去）。新人会以为项目坏了。README 和 `docs/docker-deployment.md` 里现在都写的是"可选"
3. **第 7 节的上传限制** —— 别人上传的第一张商品图就会失败

应该补的：

4. **两份 `init.sql` 没解释区别**：`sql/init.sql` 建的是 `'tea_mall'@'localhost'`，`database/init.sql` 建的是 `'tea_mall'@'%'`，一个给本机开发一个给容器。两份 `.env.example` 也一样（根目录 host 是 `mysql`，`backend/` 下 host 是 `localhost`）。新人极容易复制错那一份，然后卡在连不上数据库。各加一句说明
5. **`docs/docker-deployment.md` 的常见问题写得不错**，但缺了实际最容易撞上的两条（冷启动 backend 不健康、上传 413）。等你修完，把「怎么排查」的过程也补进去
6. **没有 LICENSE**。公开仓库不放许可证，严格来讲别人不能合法使用你的代码。选一个（MIT 最省事）
7. **没有 CI**。加一个 GitHub Actions，每次 push 跑 `docker compose build` + `npm run build` + `pytest`。这样"README 里的命令跑不通"这类问题会被自动挡住，不用等别人来告诉你。这也是简历上能写的一条

---

## 9. 优先级建议

如果时间有限，按这个顺序：

| 顺序 | 事项 | 理由 |
| --- | --- | --- |
| 1 | 第 2 节 JWT 密钥 | 仓库已公开，任何人都能拿管理员权限 |
| 2 | 第 1 节 冷启动 | README 第一条命令就跑不通，别人根本进不了门 |
| 3 | 第 6 节 测试污染真库 | 现在无所谓，但这个习惯在工作中会出事故 |
| 4 | 第 3 节 超卖 | 技术含量最高，最值得慢慢做 |
| 5 | 第 4、5、7 节 | 都是小改动 |
| 6 | 第 8 节 文档和 CI | 收尾 |

---

## 10. 最后

前面列了不少问题，但别误解 —— 这些**不是"你写得差"的证据，恰恰是这个项目已经跑到足够远、能撞上真实工程问题的证据**。一个只有 CRUD 的玩具项目，是不会有超卖、不会有冷启动竞态、不会有 nginx 和 dev server 行为差异这些问题的。

另外注意一个规律：本文里最严重的几个问题（冷启动失败、bcrypt 500、上传 413、超卖），**你在自己机器上正常开发时全都碰不到**。它们分别只在「首次初始化」「特定依赖版本」「Docker 部署」「并发请求」这些条件下才暴露。这就是为什么工程里需要 CI、需要锁版本、需要在干净环境验证、需要写并发测试 —— **不是流程官僚，是因为人肉自测的覆盖面天然有巨大盲区。**

改完之后，这些经历都是面试时的好素材。比起罗列"我用了 Vue3 + FastAPI + Redis"，下面这种讲法有说服力得多：

> 我发现自己的下单接口在并发下会超卖 —— 两个用户同时买最后一件，两单都成功了。根因是先查库存再扣减的 read-modify-write 竞态。我用 xxx 方案修复，并写了一个用 Barrier 同步两个线程的并发测试来证明修复有效。

这句话里有：**你自己发现的问题 + 你能说清的根因 + 你做的技术选型 + 你用来证明的手段**。四样都有，才是完整的工程能力。

改的过程中有想不明白的地方，随时来问。
