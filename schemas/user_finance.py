import string
from datetime import datetime
from typing import List
from pydantic import BaseModel
import schemas


class UserFinanceCreate(BaseModel):
    save_id: int
    amount: int
    event: str
    date: datetime

    class Config:
        orm_mode = True


class UserFinance(UserFinanceCreate):
    id: int
