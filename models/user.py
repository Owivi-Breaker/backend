from models.base import Base
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(1000), default=None, unique=True, index=True)
    hashed_password = Column(String(1000))
    is_active = Column(Boolean, default=True)

    saves = relationship("Save", backref="user",lazy="select")
