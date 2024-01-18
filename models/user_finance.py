from models.base import Base
from sqlalchemy import Column, Date, ForeignKey, Integer, String


#  玩家收支情况记录表
class UserFinance(Base):
    __tablename__ = 'user_finance'
    id = Column(Integer, primary_key=True, index=True)
    save_id = Column(Integer, ForeignKey('save.id'))
    amount = Column(Integer)
    event = Column(String(100))
    date = Column(Date)

