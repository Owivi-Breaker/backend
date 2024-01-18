from models.base import Base
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class Club(Base):
    __tablename__ = 'club'
    id = Column(Integer, primary_key=True, index=True)

    created_time = Column(DateTime)
    name = Column(String(1000))

    finance = Column(Float)
    reputation = Column(Float)

    assistant = Column(Integer)
    doctor = Column(Integer)
    scout = Column(Integer)
    negotiator = Column(Integer)

    league_id = Column(Integer, ForeignKey('league.id'))
    coach = relationship("Coach", uselist=False, backref="club")
    players = relationship("Player", backref="club", lazy='select')
    game_team_info = relationship("GameTeamInfo", backref="club")

