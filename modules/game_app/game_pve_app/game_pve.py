import json
import random
from typing import List, Tuple

import crud
import game_configs
import schemas
from modules.game_app import game_eve_app, game_pve_app
from sqlalchemy.orm import Session
from utils import logger


class GamePvE(game_eve_app.GameEvE):
    def __init__(self, save_id: int, db: Session, player_tactic: str = ""):
        # 新添加的成员变量
        self.game_pve_models = crud.get_game_pve_by_save_id(db=db, save_id=save_id)
        self.is_extra_time = self.game_pve_models.is_extra_time
        self.new_script = ""  # 本回合的解说
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
        self.goal_record: List[schemas.GoalRecord] = self.str2goal_record(self.game_pve_models.goal_record)  # 进球记录
        logger.info(self.goal_record)
        self.winner_id = 0

        self.total_turns = 50 if not self.is_extra_time else 70  # 总比赛回合数
        # 默认lteam为玩家球队 rteam为电脑球队
        for t in self.game_pve_models.teams:
            if t.is_player:
                self.lteam = game_pve_app.TeamPvE(db=self.db, game=self, team_pve_model=t)
            else:
                self.rteam = game_pve_app.TeamPvE(db=self.db, game=self, team_pve_model=t)

    def add_script(self, text: str, status: str) -> None:
        """
        重写方法 添加解说
        :param text: 解说词
        :param status: 解说状态
        """
        self.new_script += text + "@" + status + "\n"

    def judge_attacker(self):
        """
        判断本回合玩家是否为进攻方
        """
        if self.game_pve_models.cur_attacker == self.game_pve_models.player_club_id:
            self.is_player_turn = True
        else:
            self.is_player_turn = False

    @staticmethod
    def str2goal_record(text: str) -> List[schemas.GoalRecord]:
        """
        将 goal_record 字符串转换为 schemas.GoalRecord 形式
        """
        if not text:
            return []
        goal_record_dict = json.loads(text)

        if not goal_record_dict:
            return []
        return [schemas.GoalRecord(**x) for x in goal_record_dict]

    def init_hold_ball_team(self) -> Tuple[game_pve_app.TeamPvE, game_pve_app.TeamPvE]:
        """
        重写方法 比赛开始时，根据临时表选择持球队伍
        :return: 持球队伍，无球队伍
        """

        if self.is_player_turn:
            return self.lteam, self.rteam
        else:
            return self.rteam, self.lteam

    def deal_new_script(self) -> None:
        """
        处理新解说
        """
        print(self.new_script)
        turns: int = self.game_pve_models.turns - 1
        ingame_time = turns * 108 // 60 * 100 + turns * 108 % 60
        temp = self.new_script.split("\n")
        for i in range(len(temp)):
            if temp[i] == "":
                continue
            text, status = tuple(temp[i].split("@"))
            grade = "@" + str(random.randint(1, 5))
            if status == "s":  # 开始
                str_time = "@00:00"
                ingame_time = 0
                temp[i] = text + str_time + grade + "\n"
            elif status == "as":  # 加时开始
                str_time = "@090:00"
                ingame_time = 9000
                temp[i] = text + str_time + grade + "\n"
            elif status == "e":  # 结束
                str_time = "@90:00"
                temp[i] = text + str_time + grade + "\n"
            elif status == "ae":
                str_time = "@120:00"  # 加时结束
                temp[i] = text + str_time + grade + "\n"
            elif status == "d" or status == "c":
                if status == "d":
                    happening_time = random.randint(ingame_time + 30, ingame_time + 90)
                else:
                    happening_time = random.randint(ingame_time + 1, ingame_time + 4)
                str_time = str(happening_time)
                if int(str_time[-2:]) > 60:  # 60进制
                    happening_time += 40
                str_time = str(happening_time)
                cstr_time = str_time
                if len(str_time) == 1:
                    cstr_time = "000" + str_time
                if len(str_time) == 2:
                    cstr_time = "00" + str_time
                if len(str_time) == 3:
                    cstr_time = "0" + str_time
                ingame_time = happening_time
                if len(str_time) < 5:  # 100分钟以内
                    str_sec = cstr_time[-2:]
                    str_min = cstr_time[:2]
                    str_time = str_min + ":" + str_sec
                else:
                    str_sec = cstr_time[-2:]
                    str_min = cstr_time[:3]
                    str_time = str_min + ":" + str_sec
                temp[i] = text + "@" + str_time + grade + "\n"
            elif status == "n":  # 纯解说
                temp[i] = text + grade + "\n"
        self.new_script = "".join(temp)
        self.script += self.new_script + "\n"

    def start_one_turn(self) -> Tuple[bool, int]:
        """
        开始新一回合
        :return: 比赛是否结束; game id 若无则为0
        """
        if self.turns == 1:
            self.add_script("比赛开始！", "s")
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
            if tactic_name == "wing_cross":
                if hold_ball_team.get_location_players(
                    (game_configs.Location.LW, game_configs.Location.LB)
                ) or hold_ball_team.get_location_players((game_configs.Location.RW, game_configs.Location.RB)):
                    exchange_ball = hold_ball_team.wing_cross(no_ball_team)
                else:
                    return True, 0
            elif tactic_name == "under_cutting":
                if hold_ball_team.get_location_players((game_configs.Location.LW, game_configs.Location.RW)):
                    exchange_ball = hold_ball_team.under_cutting(no_ball_team)
                else:
                    return True, 0
            elif tactic_name == "pull_back":
                if hold_ball_team.get_location_players((game_configs.Location.LW, game_configs.Location.RW)):
                    exchange_ball = hold_ball_team.pull_back(no_ball_team)
                else:
                    return True, 0
            elif tactic_name == "middle_attack":
                if hold_ball_team.get_location_players((game_configs.Location.CM,)):
                    exchange_ball = hold_ball_team.middle_attack(no_ball_team)
                else:
                    return True, 0
            elif tactic_name == "counter_attack" and counter_attack_permitted:
                if hold_ball_team.get_location_players((game_configs.Location.GK, game_configs.Location.CB)):
                    exchange_ball = hold_ball_team.counter_attack(no_ball_team)
                else:
                    return True, 0
            else:
                logger.error("战术名称{}错误或不可用！".format(self.player_tactic))
                exchange_ball = hold_ball_team
        else:
            # 电脑进攻
            exchange_ball = hold_ball_team.attack(no_ball_team, counter_attack_permitted)
        # 确定下一回合的场上位置
        self.lteam.shift_location()
        self.rteam.shift_location()

        # 比赛结束后的处理
        if self.game_pve_models.turns == self.total_turns:
            if self.is_need_extra_time():
                if self.is_extra_time:
                    # 此时加时赛结束 两队仍然平分 需要进入点球阶段
                    self.add_script("\n开始点球！", "ae")
                    self.penalty()
                    game_id = self.end_game(exchange_ball, original_score)
                    return False, game_id
                else:
                    # 常规比赛时间结束 需要进入加时阶段
                    self.is_extra_time = True
                    self.add_script("\n开始加时比赛！", "as")
            else:
                # 结束比赛
                game_id = self.end_game(exchange_ball, original_score)
                return False, game_id

        # 记录球员实时评分
        self.rate()
        # 保存到临时表
        self.deal_new_script()
        self.save_temporary_table(exchange_ball, original_score)
        return True, 0

    def end_game(self, exchange_ball: bool, original_score: Tuple[int, int]) -> int:
        """
        比赛结束后的处理
        :return: game id
        """
        # 记录胜者id
        if self.lteam.score > self.rteam.score:
            self.winner_id = self.lteam.club_id
        elif self.lteam.score < self.rteam.score:
            self.winner_id = self.rteam.club_id  # 常规时间胜负关系

        self.add_script(
            "比赛结束！ {} {}:{} {}".format(self.lteam.name, self.lteam.score, self.rteam.score, self.rteam.name), "n"
        )
        # 记录胜者队名
        if self.winner_id == self.lteam.club_id:
            winner_name = self.lteam.name
        elif self.winner_id == self.rteam.club_id:
            winner_name = self.rteam.name
        else:
            winner_name = None

        if winner_name:
            self.add_script("胜者为{}！".format(winner_name), "n")
        else:
            self.add_script("平局", "n")

        self.rate()  # 球员评分
        self.deal_new_script()
        self.save_temporary_table(exchange_ball, original_score)  # 保存到临时表
        game_id = self.save_game_data()  # 保存比赛
        self.update_players_data()  # 保存球员数据的改变
        return game_id

    def is_need_extra_time(self) -> bool:
        """
        判断是否需要进行加时比赛
        """
        if self.rteam.score == self.lteam.score:
            if "cup" in self.type:
                return True
            if "champion" in self.type and "group" not in self.type:
                if self.type == "champions2to1":
                    return True
                else:
                    query_str = (
                        "and_(models.Game.save_id=='{}', models.Game.season=='{}', models.Game.type=='{}')".format(
                            self.save_id, int(self.season), self.type
                        )
                    )
                    games = crud.get_games_by_attri(db=self.db, query_str=query_str)  # 查找同阶段的其他比赛
                    for game in games:
                        team1 = game.teams[0]
                        team2 = game.teams[1]
                        if self.lteam.club_id == team2.club_id or self.lteam.club_id == team1.club_id:  # 查找这两队上一次比赛
                            # 上一轮打平，这一轮加时
                            return True
        return False

    def save_temporary_table(self, exchange_ball: bool, original_score: Tuple[int, int]):
        """
        保存临时表
        :param exchange_ball: 球权是否转换
        :param original_score: 本回合前的比分
        """
        self.game_pve_models.turns += 1
        self.game_pve_models.script = self.script
        self.game_pve_models.new_script = self.new_script
        self.game_pve_models.is_extra_time = self.is_extra_time
        self.game_pve_models.goal_record = self.goal_record2str()
        if exchange_ball:
            self.game_pve_models.cur_attacker = (
                self.game_pve_models.computer_club_id if self.is_player_turn else self.game_pve_models.player_club_id
            )
        if exchange_ball and original_score == (self.lteam.score, self.rteam.score):
            # 若球权易位且比分未变，允许使用防守反击
            self.game_pve_models.counter_attack_permitted = True
        for t in (self.lteam, self.rteam):
            t.save_temporary_table()

        self.db.commit()
