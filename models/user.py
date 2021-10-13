from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Float, Boolean
from sqlalchemy.orm import relationship
from models.base import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(1000), default=None, unique=True, index=True)
    hashed_password = Column(String(1000))
    is_active = Column(Boolean, default=True)

    saves = relationship("Save", backref="user",lazy="select")
