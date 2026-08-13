-- 本地开发初始化脚本
-- 用法（Windows PowerShell）：
--   mysql -u root -p < sql/init.sql

CREATE DATABASE IF NOT EXISTS tea_mall
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- pytest 专用测试库（与开发库隔离）
CREATE DATABASE IF NOT EXISTS tea_mall_test
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- 创建专用开发账号，密码需与 backend/.env 中的 DATABASE_URL 保持一致
CREATE USER IF NOT EXISTS 'tea_mall'@'localhost' IDENTIFIED BY 'tea_mall_dev';
GRANT ALL PRIVILEGES ON tea_mall.* TO 'tea_mall'@'localhost';
GRANT ALL PRIVILEGES ON tea_mall_test.* TO 'tea_mall'@'localhost';
FLUSH PRIVILEGES;
