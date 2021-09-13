from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from models.base import Base


# region 球员数据

class Player(Base):
    __tablename__ = 'player'
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey('club.id'))

    created_time = Column(DateTime)
    name = Column(String)
    translated_name = Column(String)
    nationality = Column(String)
    translated_nationality = Column(String)
    age = Column(Integer)
    height = Column(Integer)
    weight = Column(Integer)
    birth_date = Column(String)

    values = Column(Integer)
    wages = Column(Integer)
    # Location
    ST_num = Column(Integer)
    CM_num = Column(Integer)
    LW_num = Column(Integer)
    RW_num = Column(Integer)
    CB_num = Column(Integer)
    LB_num = Column(Integer)
    RB_num = Column(Integer)
    GK_num = Column(Integer)
    CAM_num = Column(Integer)
    LM_num = Column(Integer)
    RM_num = Column(Integer)
    CDM_num = Column(Integer)
    # rating
    shooting = Column(Float)
    passing = Column(Float)
    dribbling = Column(Float)
    interception = Column(Float)
    pace = Column(Float)
    strength = Column(Float)
    aggression = Column(Float)
    anticipation = Column(Float)
    free_kick = Column(Float)
    stamina = Column(Float)
    goalkeeping = Column(Float)
    # rating limit
    shooting_limit = Column(Integer)
    passing_limit = Column(Integer)
    dribbling_limit = Column(Integer)
    interception_limit = Column(Integer)
    pace_limit = Column(Integer)
    strength_limit = Column(Integer)
    aggression_limit = Column(Integer)
    anticipation_limit = Column(Integer)
    free_kick_limit = Column(Integer)
    stamina_limit = Column(Integer)
    goalkeeping_limit = Column(Integer)
    # 生涯数据
    game_data = relationship('GamePlayerData', backref='player', lazy='subquery')

# endregion
