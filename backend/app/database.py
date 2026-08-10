"""数据库连接：SQLAlchemy engine / SessionLocal / Base。"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# pool_pre_ping：每次取连接前先探测，避免连接被 MySQL 静默断开
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类（模型从 Phase 1 开始添加）。"""


def get_db():
    """FastAPI 依赖：每个请求使用独立的数据库会话，请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
