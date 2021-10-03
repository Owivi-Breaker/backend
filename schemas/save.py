from datetime import datetime
from typing import List
from pydantic import BaseModel
from schemas.league import League


class SaveCreate(BaseModel):
    created_time: datetime = datetime.now()

    time: str

    class Config:
        orm_mode = True


class Save(SaveCreate):
    id: int

    leagues: List[League] = []
