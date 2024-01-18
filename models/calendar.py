from models.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import TEXT


class Calendar(Base):
    __tablename__ = "calendar"
    id = Column(Integer, primary_key=True, index=True)
    created_time = Column(DateTime)

    date = Column(String(50))
    event_str = Column(TEXT)

    save_id = Column(Integer, ForeignKey("save.id"))
