from datetime import datetime
from typing import List
from pydantic import BaseModel
from schemas import Player
from schemas.coach import Coach


class ClubCreate(BaseModel):
    created_time: datetime
    name: str
    finance: float  # 单位：万
    reputation: float
    assistant: int = 0
    doctor: int = 0
    scout: int = 0
    negotiator: int = 0

    class Config:
        orm_mode = True


class Club(ClubCreate):
    id: int
    league_id: int

    coach: Coach = None
    players: List[Player] = []
