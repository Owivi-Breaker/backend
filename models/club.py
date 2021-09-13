from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from models.base import Base


# region 俱乐部数据
class Club(Base):
    __tablename__ = 'club'
    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey('league.id'))

    created_time = Column(DateTime)
    name = Column(String)
    finance = Column(Float)

    coach = relationship("Coach", uselist=False, backref="club", lazy='subquery')
    players = relationship("Player", backref="club", lazy='subquery')


# endregion
