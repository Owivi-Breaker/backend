from datetime import datetime
from typing import List
from pydantic import BaseModel
from game_configs.game_config import Location


class GamePlayerDataCreate(BaseModel):
    player_id: int

    created_time: datetime
    location: Location

    real_rating: float
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


class GamePlayerData(GamePlayerDataCreate):
    id: int
    game_team_info_id: int


class GameTeamDataCreate(BaseModel):
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


class GameTeamData(GameTeamDataCreate):
    id: int
    game_team_info_id: int


class GameTeamInfoCreate(BaseModel):
    club_id: int

    created_time: datetime
    score: int

    class Config:
        orm_mode = True


class GameTeamInfo(GameTeamInfoCreate):
    id: int
    game_id: int
    team_data: GameTeamData
    player_data: List[GamePlayerData]


class GameCreate(BaseModel):
    created_time: datetime
    date: str

    name: str
    type: str
    season: str
    script: str
    mvp: int
    save_id: int
    winner_id: int = 0

    class Config:
        orm_mode = True


class Game(BaseModel):
    id: int
    teams: List[GameTeamInfo]
