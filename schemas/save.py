from datetime import datetime
from typing import List
from pydantic import BaseModel
import schemas


class SaveCreate(BaseModel):
    created_time: datetime = datetime.now()

    time: str

    class Config:
        orm_mode = True


class Save(SaveCreate):
    id: int
    calendars: List[schemas.Calendar] = []
    leagues: List[schemas.League] = []
