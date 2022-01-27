from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from models.base import Base


#  转会目标球员表
class Target_player(Base):
    __tablename__ = 'target_player'
    id = Column(Integer, primary_key=True, index=True)
    save_id = Column(Integer, ForeignKey('save.id'))
    buyer_id = Column(Integer, ForeignKey('club.id'))
    target_id = Column(Integer, ForeignKey('player.id'))
    season = Column(Integer)
