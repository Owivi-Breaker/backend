from models.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String


# region 教练数据
class Coach(Base):
    __tablename__ = "coach"
    id = Column(Integer, primary_key=True, index=True)

    created_time = Column(DateTime)
    name = Column(String(1000))
    translated_name = Column(String(1000))
    nationality = Column(String(1000))
    translated_nationality = Column(String(1000))
    age = Column(Integer)
    birth_date = Column(String(1000))
    values = Column(Integer)
    wages = Column(Integer)
    # 战术
    formation = Column(String(1000))  # 阵型
    wing_cross = Column(Integer)
    under_cutting = Column(Integer)
    pull_back = Column(Integer)
    middle_attack = Column(Integer)
    counter_attack = Column(Integer)

    club_id = Column(Integer, ForeignKey("club.id"))


# endregion
