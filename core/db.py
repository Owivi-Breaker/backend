from sqlalchemy import create_engine, Index
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import scoped_session
from sqlalchemy.exc import OperationalError

from core.config import settings
from models.base import Base
import models
from utils import logger

engine = create_engine(
    settings.DB_URL["sqlite"], connect_args={"check_same_thread": False}
)

# engine = create_engine(settings.DB_URL["MySQLLocal"], encoding="utf-8")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
ScopedSession = scoped_session(SessionLocal)  # 使用安全的线程

Base.metadata.create_all(bind=engine)

# 构建索引 老存档只需运行一次即可
try:
    player_id_index = Index('player_id_idx', models.GamePlayerData.player_id)
    player_id_index.create(bind=engine)
except OperationalError:
    logger.warning("player_id_idx already exists")


def drop_all():
    """
    清空数据库中的所有内容
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


# def get_db():
#     db = SessionFactory()
#     try:
#         yield db
#     finally:
#         db.close()


def get_session():
    db = ScopedSession()
    return db
