from datetime import datetime
from typing import List
from pydantic import BaseModel
from schemas.game import GamePlayerData


# region 球员表
class PlayerCreate(BaseModel):
    created_time: datetime
    name: str
    translated_name: str
    nationality: str
    translated_nationality: str
    age: int = 14
    height: int
    weight: int
    birth_date: str
    wages: float = 0  # 周薪

    real_stamina: float = 100  # 实时体力
    # Location num
    ST_num: int = 0
    CM_num: int = 0
    LW_num: int = 0
    RW_num: int = 0
    CB_num: int = 0
    LB_num: int = 0
    RB_num: int = 0
    GK_num: int = 0
    CAM_num: int = 0
    LM_num: int = 0
    RM_num: int = 0
    CDM_num: int = 0
    # capability
    shooting: float  # 射门
    passing: float  # 传球
    dribbling: float  # 盘带
    interception: float  # 抢断
    pace: float  # 速度
    strength: float  # 力量
    aggression: float  # 侵略
    anticipation: float  # 预判
    free_kick: float  # 任意球/点球
    stamina: float  # 体能
    goalkeeping: float  # 守门
    # capability limit
    shooting_limit: int
    passing_limit: int
    dribbling_limit: int
    interception_limit: int
    pace_limit: int
    strength_limit: int
    aggression_limit: int
    anticipation_limit: int
    free_kick_limit: int
    stamina_limit: int
    goalkeeping_limit: int

    class Config:
        orm_mode = True


class Player(PlayerCreate):
    id: int
    club_id: int
    # 生涯数据
    game_data: List[GamePlayerData] = []


class PlayerShow(Player):
    value: int
# endregion
