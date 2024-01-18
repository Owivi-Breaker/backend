import random
from typing import Dict, List, Tuple

import schemas
from modules.ml_app.base_game import BaseTeam
from sqlalchemy.orm import Session
from utils import logger


class BaseGame:
    def __init__(self, db: Session, pos: str):
        self.db = db
        self.script = ""
        self.goal_record: List[schemas.GoalRecord] = []  # 进球记录
        self.turns = 0  # 比赛进行的回合数 用于记录进球回合
        self.lteam = BaseTeam(db=self.db, game=self)
        self.rteam = BaseTeam(db=self.db, game=self)
        self.pos = pos

    def start(self, capa: Dict, formation: Dict):
        self.lteam.score = 0
        self.rteam.score = 0
        self.lteam.init_players(formation)
        self.rteam.init_players(formation)
        for p in self.lteam.players:
            if p.ori_location == self.pos:
                p.capa = capa
                break
        else:
            logger.error("阵容中找不到目标位置球员！")

        # 模拟20场比赛
        for i in range(20):
            self.set_full_stamina()
            # 模拟一场比赛
            hold_ball_team, no_ball_team = self.init_hold_ball_team()
            counter_attack_permitted = False
            for _ in range(50):
                # 确定本次战术组织每个球员的场上位置
                self.lteam.shift_location()
                self.rteam.shift_location()
                original_score = (self.lteam.score, self.rteam.score)
                # 执行进攻战术
                exchange_ball = hold_ball_team.attack(no_ball_team, counter_attack_permitted)
                if exchange_ball:
                    hold_ball_team, no_ball_team = self.exchange_hold_ball_team(hold_ball_team)
                if exchange_ball and original_score == (self.lteam.score, self.rteam.score):
                    # 若球权易位且比分未变，允许使用防守反击
                    counter_attack_permitted = True
                else:
                    counter_attack_permitted = False
        # 返回队伍战术执行数据
        return self.lteam.score, self.rteam.score

    def set_full_stamina(self):
        """
        初始化所有球员的体力
        """
        for player in self.lteam.players:
            player.stamina = 100
        for player in self.rteam.players:
            player.stamina = 100

    def init_hold_ball_team(self) -> Tuple[BaseTeam, BaseTeam]:
        """
        比赛开始时，随机选择持球队伍
        :return: 持球队伍，无球队伍
        """
        hold_ball_team = random.choice([self.lteam, self.rteam])
        no_ball_team = self.lteam if hold_ball_team == self.rteam else self.rteam
        return hold_ball_team, no_ball_team

    def exchange_hold_ball_team(self, hold_ball_team: BaseTeam) -> Tuple[BaseTeam, BaseTeam]:
        """
        球权易位
        :param hold_ball_team: 原先持球的队伍实例
        :return: 持球队伍，无球队伍
        """
        hold_ball_team = self.lteam if hold_ball_team == self.rteam else self.rteam
        no_ball_team = self.lteam if hold_ball_team == self.rteam else self.rteam
        return hold_ball_team, no_ball_team
