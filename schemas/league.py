from datetime import datetime
from typing import List
from pydantic import BaseModel
from schemas.club import Club


# region 联赛表

class League(BaseModel):
    # id: int

    created_time: datetime
    name: str

    clubs: List[Club] = []

    class Config:
        orm_mode = True
# endregion
