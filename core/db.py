from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import scoped_session

from core.config import settings
from models.base import Base

engine = create_engine(
    settings.DB_URL["sqlite"], connect_args={"check_same_thread": False}
)

# engine = create_engine(settings.DB_URL["MySQLLocal"], encoding="utf-8")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionLocal)  # 使用安全的线程

Base.metadata.create_all(bind=engine)


def drop_all():
    """
    清空数据库中的所有内容
    """
    Base.metadata.drop_all(bind=engine)


def get_db():
    db = ScopedSession()
    try:
        yield db
    finally:
        db.close()


# def get_db():
#     db = SessionFactory()
#     try:
#         yield db
#     finally:
#         db.close()


def get_session():
    return Session()
