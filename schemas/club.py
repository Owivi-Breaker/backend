from datetime import datetime
from typing import List
from pydantic import BaseModel
from schemas import Player
from schemas.coach import Coach


# region 俱乐部表

class Club(BaseModel):
    # id: int
    # league_id: int
    created_time: datetime
    name: str
    finance: float  # 单位：万

    coach: Coach = None
    players: List[Player] = []

    class Config:
        orm_mode = True
# endregion
