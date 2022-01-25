import crud
from utils import utils, logger
import models
import schemas
import game_configs
from modules.game_app import game_eve_app
from modules.game_app import game_pve_app

from typing import Dict, List, Sequence, Set, Tuple, Optional
from sqlalchemy.orm import Session
import datetime


class GamePvE(game_eve_app.GameEvE):
    def __init__(self, save_id: int, db: Session, player_tactic: str = ''):
        # 新添加的成员变量
        self.game_pve_models = crud.get_game_pve_by_save_id(db=db, save_id=save_id)
        self.new_script = ''  # 本回合的解说
        self.player_tactic = player_tactic  # 本回合玩家选择的战术名
        self.turns = self.game_pve_models.turns  # 本回合的序号
        self.is_player_turn: bool = False  # 本回合玩家是否是进攻方
        self.judge_attacker()
        # 为了使用父类的方法 成员的名字不能变
        self.db = db
        self.season = self.game_pve_models.season
        self.date = self.game_pve_models.date
        self.script = self.game_pve_models.script
        self.type = self.game_pve_models.type
        self.name = self.game_pve_models.name
        self.save_id = self.game_pve_models.save_id
        self.winner_id = 0
        # 默认lteam为玩家球队 rteam为电脑球队
        for t in self.game_pve_models.teams:
            if t.is_player:
                self.lteam = game_pve_app.TeamPvE(db=self.db, game=self, team_pve_model=t)
            else:
                self.rteam = game_pve_app.TeamPvE(db=self.db, game=self, team_pve_model=t)

    def add_script(self, text: str):
        """
        重写方法 添加解说
        :param text: 解说词
        """
        self.script += text + '\n'
        self.new_script += text + '\n'

    def judge_attacker(self):
        """
        判断本回合玩家是否为进攻方
        """
        if self.game_pve_models.cur_attacker == self.game_pve_models.player_club_id:
            self.is_player_turn = True
        else:
            self.is_player_turn = False

    def init_hold_ball_team(self) -> Tuple[game_pve_app.TeamPvE, game_pve_app.TeamPvE]:
        """
        重写方法 比赛开始时，根据临时表选择持球队伍
        :return: 持球队伍，无球队伍
        """

        if self.is_player_turn:
            return self.lteam, self.rteam
        else:
            return self.rteam, self.lteam

    def start_one_turn(self) -> bool:
        """
        开始新一回合
        :return: 比赛是否结束
        """
        if self.turns == 1:
            self.add_script('比赛开始！')
        hold_ball_team, no_ball_team = self.init_hold_ball_team()
        counter_attack_permitted = self.game_pve_models.counter_attack_permitted

        original_score = (self.lteam.score, self.rteam.score)
        if self.is_player_turn:

            if not self.player_tactic:
                # 只可能发生在跳过比赛中
                tactic_name = self.lteam.select_tactic(counter_attack_permitted)
            else:
                tactic_name = self.player_tactic
            # 玩家进攻
            if tactic_name == 'wing_cross':
                exchange_ball = hold_ball_team.wing_cross(no_ball_team)
            elif tactic_name == 'under_cutting':
                exchange_ball = hold_ball_team.under_cutting(no_ball_team)
            elif tactic_name == 'pull_back':
                exchange_ball = hold_ball_team.pull_back(no_ball_team)
            elif tactic_name == 'middle_attack':
                exchange_ball = hold_ball_team.middle_attack(no_ball_team)
            elif tactic_name == 'counter_attack' and counter_attack_permitted:
                exchange_ball = hold_ball_team.counter_attack(no_ball_team)
            else:
                logger.error('战术名称{}错误或不可用！'.format(self.player_tactic))
                exchange_ball = hold_ball_team
        else:
            # 电脑进攻
            exchange_ball = hold_ball_team.attack(no_ball_team, counter_attack_permitted)
        # 确定下一回合的场上位置
        self.lteam.shift_location()
        self.rteam.shift_location()

        # 比赛结束后的处理
        if self.game_pve_models.turns == 50:
            # TODO 加时判断
            # 记录胜者id
            if self.lteam.score > self.rteam.score:
                self.winner_id = self.lteam.club_id
            elif self.lteam.score < self.rteam.score:
                self.winner_id = self.rteam.club_id  # 常规时间胜负关系
            else:
                # 比分相同
                pass

            self.add_script('比赛结束！ {} {}:{} {}'.format(
                self.lteam.name, self.lteam.score, self.rteam.score, self.rteam.name))
            # 记录胜者队名
            if self.winner_id == self.lteam.club_id:
                winner_name = self.lteam.name
            elif self.winner_id == self.rteam.club_id:
                winner_name = self.rteam.name
            else:
                winner_name = None

            if winner_name:
                self.add_script('胜者为{}！'.format(winner_name))
            else:
                self.add_script('平局')

            self.rate()  # 球员评分
            self.save_temporary_table(exchange_ball, original_score)  # 保存到临时表
            self.save_game_data()  # 保存比赛
            self.update_players_data()  # 保存球员数据的改变
            return False
        else:
            # 记录球员实时评分
            self.rate()
            # 保存到临时表
            self.save_temporary_table(exchange_ball, original_score)
            return True

    def save_temporary_table(self, exchange_ball: bool, original_score: Tuple[int, int]):
        """
        保存临时表
        :param exchange_ball: 球权是否转换
        :param original_score: 本回合前的比分
        """
        self.game_pve_models.turns += 1
        self.game_pve_models.script = self.script
        self.game_pve_models.new_script = self.new_script
        if exchange_ball:
            self.game_pve_models.cur_attacker = self.game_pve_models.computer_club_id \
                if self.is_player_turn \
                else self.game_pve_models.player_club_id
        if exchange_ball and original_score == (self.lteam.score, self.rteam.score):
            # 若球权易位且比分未变，允许使用防守反击
            self.game_pve_models.counter_attack_permitted = True
        for t in (self.lteam, self.rteam):
            t.save_temporary_table()

        self.db.commit()
