from datetime import datetime
from typing import List
from pydantic import BaseModel
import schemas


class ClubCreate(BaseModel):
    created_time: datetime
    name: str
    finance: float  # 单位：万
    reputation: float
    assistant: int = 0  # 助理教练
    doctor: int = 0  # 队医
    scout: int = 0  # 球探
    negotiator: int = 0  # 谈判专家

    class Config:
        orm_mode = True


class Club(ClubCreate):
    id: int
    league_id: int

    coach: schemas.Coach = None
    players: List[schemas.Player] = []


class ClubShow(BaseModel):
    id: int
    league_id: int

    finance: float  # 单位：万
    reputation: float
    assistant: int = 0  # 助理教练
    doctor: int = 0  # 队医
    scout: int = 0  # 球探
    negotiator: int = 0  # 谈判专家

    formation: str
    wing_cross: int
    under_cutting: int
    pull_back: int
    middle_attack: int
    counter_attack: int
