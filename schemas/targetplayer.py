import string
from datetime import datetime
from typing import List
from pydantic import BaseModel
import schemas


class TargetPlayerCreate(BaseModel):
    buyer_id: int
    target_id: int
    season: int
    save_id: int
    rejected_date: str = ''

    class Config:
        orm_mode = True


class TargetPlayer(TargetPlayerCreate):
    id: int
