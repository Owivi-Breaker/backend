from typing import Optional

from pydantic import BaseModel


class UserShow(BaseModel):
    email: str
    disabled: Optional[bool] = None


class UserBase(BaseModel):
    email: str
    is_active: bool

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
