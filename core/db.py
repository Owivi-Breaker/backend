from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import scoped_session

from core.config import settings
from models.base import Base

# engine = create_engine(
#     settings.DB_URL["sqlite"], connect_args={"check_same_thread": False}
# )

engine = create_engine(settings.DB_URL["sqlite"], encoding="utf-8")

Session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def drop_all():
    """
    清空数据库中的所有内容
    """
    Base.metadata.drop_all(bind=engine)


def get_db():
    db = Session_factory()
    try:
        yield db
    finally:
        db.close()


def get_session():
    return Session()
