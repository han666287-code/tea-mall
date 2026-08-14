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
    """FastAPI 依赖：每个请求使用独立的数据库会话。

    事务边界：业务代码显式 commit 提交成功；未处理异常在依赖层统一 rollback；
    无论成功失败，会话最终都会关闭，避免连接泄漏。
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
