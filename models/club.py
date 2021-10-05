from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from models.base import Base


class Club(Base):
    __tablename__ = 'club'
    id = Column(Integer, primary_key=True, index=True)

    created_time = Column(DateTime)
    name = Column(String)

    finance = Column(Float)
    reputation = Column(Float)

    assistant = Column(Integer)
    doctor = Column(Integer)
    scout = Column(Integer)
    negotiator = Column(Integer)

    league_id = Column(Integer, ForeignKey('league.id'))
    coach = relationship("Coach", uselist=False, backref="club", lazy='select')
    players = relationship("Player", backref="club", lazy='select')
