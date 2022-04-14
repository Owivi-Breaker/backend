from sqlalchemy import create_engine, Index, table
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.exc import OperationalError
from sqlalchemy_utils import database_exists, create_database
from core.config import settings
from models.base import Base
import models
from utils import logger
from core import dburl

engine = create_engine(settings.DB_URL[dburl.mysql_db_url], encoding='utf-8')
# 建数据库
if not database_exists(engine.url):
    create_database(engine.url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
ScopedSession = scoped_session(SessionLocal)  # 使用安全的线程
Base.metadata.create_all(bind=engine)
# 构建索引 老存档只需运行一次即可
try:
    player_id_index = Index('player_id_idx', models.GamePlayerData.player_id)
    player_id_index.create(bind=engine)
except OperationalError:
    logger.warning("player_id_idx already exists")
# try:
#     values = Column('values', Float)
#     models.Player.__table__.append_column(values)
# except OperationalError:
#     logger.warning("add column failed")


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


def get_session():
    db = ScopedSession()
    return db
