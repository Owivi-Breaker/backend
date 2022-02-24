from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TEXT
from models.base import Base


class Calendar(Base):
    __tablename__ = 'calendar'
    id = Column(Integer, primary_key=True, index=True)
    created_time = Column(DateTime)

    date = Column(String(50))
    event_str = Column(TEXT)

    save_id = Column(Integer, ForeignKey('save.id'))
