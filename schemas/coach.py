from datetime import datetime

from pydantic import BaseModel


class CoachCreate(BaseModel):
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
    formation: str  # 阵型
    wing_cross: int
    under_cutting: int
    pull_back: int
    middle_attack: int
    counter_attack: int

    class Config:
        orm_mode = True


class Coach(CoachCreate):
    id: int
    club_id: int


class CoachShow(BaseModel):
    id: int
    club_id: int
    name: str
    translated_name: str
    translated_nationality: str
    age: int = 20
    birth_date: str
    values: int = 0
    wages: int = 0
    # 战术
    formation: str  # 阵型
    wing_cross: int
    under_cutting: int
    pull_back: int
    middle_attack: int
    counter_attack: int
