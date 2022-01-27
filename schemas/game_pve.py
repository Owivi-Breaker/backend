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
    is_player: bool = False  # 是否是玩家球队

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
    home_club_id: int  # 主场俱乐部id

    name: str
    type: str
    date: str
    season: int

    cur_attacker: int  # 进攻方club_id
    turns: int = 1  # 进行的回合数
    script: str = ""  # 解说
    new_script: str = ""  # 最近一回合的解说

    counter_attack_permitted: bool = False  # 下一回合是否允许打防反

    class Config:
        orm_mode = True


class GamePvE(GamePvECreate):
    id: int
    teams: List[TeamPvE]


class GamePvEShow(BaseModel):
    player_club_id: int  # 玩家俱乐部id外键
    computer_club_id: int  # 电脑俱乐部id外键

    home_club_id: int  # 主场俱乐部id
    name: str
    type: str
    date: str
    season: int

    cur_attacker: int
    turns: int
    script: str
    new_script: str
    is_extra_time: bool = False

    counter_attack_permitted: bool = False  # 下一回合是否允许打防反


class TeamPvEShow(BaseModel):
    club_id: int  # 俱乐部id外键
    score: int  # 比分
    is_player: bool

    # 球队比赛数据
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


class PlayerPvEShow(BaseModel):
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


class GamePvEInfo(BaseModel):
    """
    发送给前端的整合数据
    """
    game_info: GamePvEShow
    player_team_info: TeamPvEShow
    computer_team_info: TeamPvEShow
    player_players_info: List[PlayerPvEShow]
    computer_players_info: List[PlayerPvEShow]
