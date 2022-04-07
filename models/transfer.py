from sqlalchemy import Column, ForeignKey, Integer, String, Date
from models.base import Base


#  转会目标球员表
class TargetPlayer(Base):
    __tablename__ = 'target_player'
    id = Column(Integer, primary_key=True, index=True)
    save_id = Column(Integer, ForeignKey('save.id'))
    buyer_id = Column(Integer, ForeignKey('club.id'))
    target_id = Column(Integer, ForeignKey('player.id'))
    rejected_date = Column(String(1000))
    season = Column(Integer)


#  转会目标球员表
class Offer(Base):
    __tablename__ = 'offer'
    id = Column(Integer, primary_key=True, index=True)
    save_id = Column(Integer, ForeignKey('save.id'))
    buyer_id = Column(Integer, ForeignKey('club.id'))
    target_id = Column(Integer, ForeignKey('player.id'))
    target_club_id = Column(Integer, ForeignKey('club.id'))
    offer_price = Column(Integer)
    season = Column(Integer)
    status = Column(String(2))
    date = Column(Date)
