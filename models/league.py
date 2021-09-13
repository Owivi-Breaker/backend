from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from models.base import Base


# region 联赛数据
class League(Base):
    __tablename__ = 'league'
    id = Column(Integer, primary_key=True, index=True)

    created_time = Column(DateTime)
    name = Column(String)

    clubs = relationship("Club", backref='league', lazy='subquery')


# endregion
