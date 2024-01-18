from datetime import datetime
from typing import List

from game_configs.game_config import Location
from pydantic import BaseModel


# region 比赛表
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
    id: int
    location: Location = "ST"

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


class TotalGamePlayerDataShow(BaseModel):
    id: int = -1
    appearance: int = 0

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
    save_id: int

    name: str  # 比赛名
    type: str  # 比赛类型
    season: str
    script: str  # 解说
    mvp: int  # mvp球员id

    winner_id: int = 0  # 胜利球队id 平局为0
    goal_record: str = ""  # 进球纪录

    class Config:
        orm_mode = True


class Game(BaseModel):
    id: int
    teams: List[GameTeamInfo]


# endregion


# region 比赛中出现的数据结构
class GoalRecord(BaseModel):
    player_id: int
    player_name: str
    turns: int
    club_id: int
    club_name: str


# endregion


# region 比赛展示
class GamePlayerShow(BaseModel):
    player_id: int
    player_name: str

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


class GameTeamShow(BaseModel):
    club_id: int
    club_name: str
    score: int
    players_info: List[GamePlayerShow]

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


class GameShow(BaseModel):
    id: int
    season: int
    name: str
    type: str
    date: str
    script: str
    mvp: int
    winner_id: int
    goal_record: List[GoalRecord]

    teams_info: List[GameTeamShow]


# endregion
