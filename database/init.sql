-- TeaMall MySQL 容器初始化脚本（幂等，可重复执行）
-- 由 docker-compose 挂载到 /docker-entrypoint-initdb.d/，仅在数据卷首次创建时执行。
-- 数据库与用户通常已由 MYSQL_DATABASE / MYSQL_USER / MYSQL_PASSWORD 环境变量创建，
-- 本脚本作为双保险并统一字符集；若用户已存在则保留环境变量设置的密码。

CREATE DATABASE IF NOT EXISTS tea_mall
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'tea_mall'@'%' IDENTIFIED BY 'tea_mall_dev';
GRANT ALL PRIVILEGES ON tea_mall.* TO 'tea_mall'@'%';
FLUSH PRIVILEGES;
