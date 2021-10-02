from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from models.base import Base


# region 教练数据
class Coach(Base):
    __tablename__ = 'coach'
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey('club.id'))

    created_time = Column(DateTime)
    name = Column(String)
    translated_name = Column(String)
    nationality = Column(String)
    translated_nationality = Column(String)
    age = Column(Integer)
    birth_date = Column(String)
    values = Column(Integer)
    wages = Column(Integer)
    # 战术
    formation = Column(String) # 阵型
    wing_cross = Column(Integer)
    under_cutting = Column(Integer)
    pull_back = Column(Integer)
    middle_attack = Column(Integer)
    counter_attack = Column(Integer)



# endregion
