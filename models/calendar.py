from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from models.base import Base


class Calendar(Base):
    __tablename__ = 'calendar'
    id = Column(Integer, primary_key=True, index=True)
    created_time = Column(DateTime)

    date = Column(String(50))
    event_str = Column(String(1000))

    save_id = Column(Integer, ForeignKey('save.id'))
