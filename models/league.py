from models.base import Base
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


# region 联赛数据
class League(Base):
    __tablename__ = "league"
    id = Column(Integer, primary_key=True, index=True)

    created_time = Column(DateTime)
    name = Column(String(1000))
    points = Column(Float)

    cup = Column(String(1000))
    upper_league = Column(Integer)
    lower_league = Column(Integer)

    save_id = Column(Integer, ForeignKey("save.id"))
    clubs = relationship("Club", backref="league", lazy="select")


# endregion
