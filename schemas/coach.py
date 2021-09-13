from datetime import datetime
from typing import List
from pydantic import BaseModel


# region 教练表
class Coach(BaseModel):
    # id: int
    # club_id: int
    # 基本信息
    created_time: datetime
    name: str
    translated_name: str
    nationality: str
    translated_nationality: str
    age: int = 20
    birth_date: str
    values: int = 0
    wages: int = 0
    # 战术
    tactic: str
    wing_cross: int
    under_cutting: int
    pull_back: int
    middle_attack: int
    counter_attack: int

    class Config:
        orm_mode = True
# endregion
