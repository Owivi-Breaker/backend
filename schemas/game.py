from datetime import datetime
from typing import List
from pydantic import BaseModel
from game_configs.game_config import Location


# region 比赛表
class GamePlayerData(BaseModel):
    # id: int
    # game_team_info_id: int
    player_id: int

    created_time: datetime
    name: str  # TODO 临时
    location: Location

    final_rating: float
    actions: int
    shots: int
    goals: int
    assists: int
    # 传球
    passes: int
    pass_success: int
    # 过人
    dribbles: int
    dribble_success: int
    # 抢断
    tackles: int
    tackle_success: int
    # 争顶
    aerials: int
    aerial_success: int
    # 扑救
    saves: int
    save_success: int
    # 体力
    original_stamina: int
    final_stamina: int

    class Config:
        orm_mode = True


class GameTeamData(BaseModel):
    # id: int
    # game_team_info_id: int

    created_time: datetime
    attempts: int
    # 下底传中
    wing_cross: int
    wing_cross_success: int
    # 内切
    under_cutting: int
    under_cutting_success: int
    # 倒三角
    pull_back: int
    pull_back_success: int
    # 中路渗透
    middle_attack: int
    middle_attack_success: int
    # 防反
    counter_attack: int
    counter_attack_success: int

    class Config:
        orm_mode = True


class GameTeamInfo(BaseModel):
    # id: int
    # game_id: int
    club_id: int

    created_time: datetime
    name: str  # TODO 临时
    score: int

    team_data: GameTeamData
    player_data: List[GamePlayerData]

    class Config:
        orm_mode = True


class Game(BaseModel):
    # id: int

    created_time: datetime
    date: str
    type: str
    season: str
    script: str
    mvp: int

    teams: List[GameTeamInfo]

    class Config:
        orm_mode = True
