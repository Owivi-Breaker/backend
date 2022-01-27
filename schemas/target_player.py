import string
from datetime import datetime
from typing import List
from pydantic import BaseModel
import schemas


class Target_PlayerCreate(BaseModel):
    buyer_id: int
    target_id: int
    season: int
    save_id: int

    class Config:
        orm_mode = True


class Target_Player(Target_PlayerCreate):
    id: int

