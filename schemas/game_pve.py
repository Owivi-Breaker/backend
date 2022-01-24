from datetime import datetime
from typing import List
from pydantic import BaseModel

import game_configs


class PlayerPvECreate(BaseModel):
    created_time: datetime
    player_id: int
    ori_location: game_configs.Location
    real_location: game_configs.Location = None

    real_rating: float = 6.0
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
    # 体力
    original_stamina: int = 0  # 初始体力值 在第一回合被初始化 之后不会改变
    final_stamina: int = 0  # 场上的真实体力值 一直会改变

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

    save_id: int
    player_club_id: int  # 玩家俱乐部id外键
    computer_club_id: int  # 电脑俱乐部id外键

    name: str
    type: str
    date: str
    season: int

    cur_attacker: int  # 进攻方club_id
    turns: int = 0  # 进行的回合数
    script: str = ""  # 解说

    counter_attack_permitted: bool = False  # 下一回合是否允许打防反

    class Config:
        orm_mode = True


class GamePvE(GamePvECreate):
    id: int
    player_team: TeamPvE
    computer_team: TeamPvE
