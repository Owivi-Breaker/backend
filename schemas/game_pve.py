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
    final_stamina: int

    class Config:
        orm_mode = True


class PlayerPvE(PlayerPvECreate):
    id: int
    team_pve_id: int


class TeamPvECreate(BaseModel):
    created_time: datetime
    team_id: int
    score: int

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


class TeamPvE(TeamPvECreate):
    id: int
    players: List[PlayerPvE]
    game_pve_id: int


class GamePvECreate(BaseModel):
    created_time: datetime
    player_club_id: int
    computer_club_id: int

    turns: int
    script: str = ""

    class Config:
        orm_mode = True


class GamePvE(GamePvECreate):
    id: int
    teams: List[TeamPvE]
