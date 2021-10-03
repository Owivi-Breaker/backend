from datetime import datetime
from typing import List
from pydantic import BaseModel
from schemas.club import Club


class LeagueCreate(BaseModel):
    created_time: datetime = datetime.now()

    name: str
    points: float

    class Config:
        orm_mode = True


class League(LeagueCreate):
    id: int
    upper_league: int = None
    lower_league: int = None

    clubs: List[Club] = []
