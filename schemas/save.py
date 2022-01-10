from datetime import datetime
from typing import List
from pydantic import BaseModel
import schemas


class SaveCreate(BaseModel):
    created_time: datetime = datetime.now()
    date: str = "2020-08-01"
    season: int = 1  # 赛季

    class Config:
        orm_mode = True


class Save(SaveCreate):
    id: int
    user_id: int

    calendars: List[schemas.Calendar] = []
    leagues: List[schemas.League] = []


class SaveShow(SaveCreate):
    id: int
    user_id: int
    player_club_id: int
