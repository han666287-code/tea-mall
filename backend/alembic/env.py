"""Alembic 迁移环境：从应用配置读取数据库 URL，绑定全部 ORM 模型元数据。"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# 确保 backend 目录在 sys.path 中（无论从哪个目录调用 alembic）
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 从 backend/.env 加载配置（不覆盖调用方已显式设置的环境变量），
# 保证 alembic 从任意目录执行时 app.config 都能读到 JWT_SECRET / DATABASE_URL
_ENV_FILE = BACKEND_DIR / ".env"
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _key, _, _value = _line.partition("=")
        _key = _key.strip()
        _value = _value.strip().strip('"').strip("'")
        if _key:
            os.environ.setdefault(_key, _value)

from app import models  # noqa: F401  注册全部模型到 Base.metadata
from app.config import settings
from app.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 数据库连接统一由应用配置（环境变量 / backend/.env）提供，不在 alembic.ini 写死
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：不连接数据库，仅生成 SQL。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：使用应用配置的引擎执行迁移。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
