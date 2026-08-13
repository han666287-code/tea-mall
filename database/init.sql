-- TeaMall MySQL 容器初始化脚本（幂等，可重复执行）
-- 由 docker-compose 挂载到 /docker-entrypoint-initdb.d/，仅在数据卷首次创建时执行。
-- 数据库与用户由 MYSQL_DATABASE / MYSQL_USER / MYSQL_PASSWORD 环境变量创建，
-- 本脚本只负责兜底建库并统一字符集，不包含任何口令字面量。
CREATE DATABASE IF NOT EXISTS tea_mall
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- pytest 专用测试库（与开发库隔离）
CREATE DATABASE IF NOT EXISTS tea_mall_test
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON tea_mall_test.* TO 'tea_mall'@'%';
FLUSH PRIVILEGES;
