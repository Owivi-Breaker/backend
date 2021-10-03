from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from models.base import Base


class Save(Base):
    __tablename__ = 'save'
    id = Column(Integer, primary_key=True, index=True)
    # user_id = Column(Integer, ForeignKey('user.id'))

    created_time = Column(DateTime)
    time = Column(String)

    leagues = relationship("League", backref="save", lazy='subquery')
    calendar = relationship("Calendar", backref="save", uselist=False, lazy='subquery')
