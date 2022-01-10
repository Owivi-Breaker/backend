from datetime import datetime
from typing import List
from pydantic import BaseModel
from game_configs.game_config import Location


class GamePlayerDataCreate(BaseModel):
    player_id: int

    created_time: datetime
    season: int = -1
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


class GamePlayerDataShow(BaseModel):
    location: Location = 'ST'

    final_rating: float = 6.0
    actions: int = 0
    shots: int = 0
    goals: int = 0
    assists: int = 0
    # 传球
    passes: int = 0
    pass_success: int = 0
    # 过人
    dribbles: int = 0
    dribble_success: int = 0
    # 抢断
    tackles: int = 0
    tackle_success: int = 0
    # 争顶
    aerials: int = 0
    aerial_success: int = 0
    # 扑救
    saves: int = 0
    save_success: int = 0

    class Config:
        orm_mode = True


class GameTeamDataCreate(BaseModel):
    created_time: datetime
    attempts: int
    season: int = -1
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

    season: int = -1
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
