from datetime import datetime
from typing import List
from pydantic import BaseModel
import schemas


class SaveCreate(BaseModel):
    created_time: datetime = datetime.now()

    time: str = "2020-08-01"
    player_club_id: int = 0  # TODO 暂时设一个默认值
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
