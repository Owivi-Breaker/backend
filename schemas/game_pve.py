from datetime import datetime
from typing import List
from pydantic import BaseModel

import game_configs


class PlayerPvECreate(BaseModel):
    created_time: datetime
    player_id: int
    ori_location: game_configs.Location
    real_location: game_configs.Location

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
    final_stamina: int  # 场上的真实体力值

    class Config:
        orm_mode = True


class PlayerPvE(PlayerPvECreate):
    id: int
    team_pve_id: int


class TeamPvECreate(BaseModel):
    created_time: datetime
    club_id: int  # 俱乐部id外键
    score: int = 0  # 比分

    # 球队比赛数据
    attempts: int = 0
    # 下底传中
    wing_cross: int = 0
    wing_cross_success: int = 0
    # 内切
    under_cutting: int = 0
    under_cutting_success: int = 0
    # 倒三角
    pull_back: int = 0
    pull_back_success: int = 0
    # 中路渗透
    middle_attack: int = 0
    middle_attack_success: int = 0
    # 防反
    counter_attack: int = 0
    counter_attack_success: int = 0

    class Config:
        orm_mode = True


class TeamPvE(TeamPvECreate):
    id: int
    players: List[PlayerPvE]
    game_pve_id: int


class GamePvECreate(BaseModel):
    created_time: datetime
    player_club_id: int  # 玩家俱乐部id外键
    computer_club_id: int  # 电脑俱乐部id外键

    name: str
    type: str
    date: str
    season: int

    turns: int = 0  # 进行的回合数
    script: str = ""  # 解说

    class Config:
        orm_mode = True


class GamePvE(GamePvECreate):
    id: int
    teams: List[TeamPvE]
