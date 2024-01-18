import json

from utils import utils, logger
import game_configs
import crud
import models
import schemas
from modules.game_app import game_eve_app

import random
from typing import Dict, List, Tuple
import datetime
from sqlalchemy.orm import Session


class GameEvE:
    def __init__(self, db: Session, club1_id: int, club2_id: int,
                 date: str, game_type: str, game_name: str, season: int, save_id: int,
                 club1_model: models.Club = None, club2_model: models.Club = None):
        self.db = db
        self.season = season
        self.date = date
        self.script = ''
        self.type = game_type
        self.name = game_name
        self.save_id = save_id
        self.winner_id = 0
        self.goal_record: List[schemas.GoalRecord] = []  # 进球记录
        self.turns = 0  # 比赛进行的回合数 用于记录进球回合
        self.lteam = game_eve_app.Team(db=self.db, game=self, club_id=club1_id, club_model=club1_model,
                                       season=self.season, date=self.date)
        self.rteam = game_eve_app.Team(db=self.db, game=self, club_id=club2_id, club_model=club2_model,
                                       season=self.season, date=self.date)
        self.ingame_time = 0

    def start(self) -> Tuple:
        """
        开始比赛
        :return: 比分元组
        """
        self.add_script('比赛开始！', 's')
        hold_ball_team, no_ball_team = self.init_hold_ball_team()
        counter_attack_permitted = False

        for turns in range(50):
            self.turns = turns
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
        # 记录胜者id
        if self.lteam.score > self.rteam.score:
            self.winner_id = self.lteam.club_id
        elif self.lteam.score < self.rteam.score:
            self.winner_id = self.rteam.club_id  # 常规时间胜负关系
        else:
            # 比分相同
            pass

        judge = self.judge_extra_time()  # 加时判断与点球判断 最后修改self.winner_id
        if judge == 1:
            self.add_script('比赛结束！ {} {}:{} {}'.format(
                self.lteam.name, self.lteam.score, self.rteam.score, self.rteam.name), 'ae')
        else:
            self.add_script('比赛结束！ {} {}:{} {}'.format(
                self.lteam.name, self.lteam.score, self.rteam.score, self.rteam.name), 'e')

        if self.winner_id == self.lteam.club_id:
            winner_name = self.lteam.name
        elif self.winner_id == self.rteam.club_id:
            winner_name = self.rteam.name
        else:
            winner_name = None

        if winner_name:
            self.add_script('胜者为{}！'.format(winner_name), 'e')
        else:
            self.add_script('平局', 'e')
        year, month, day = self.date.split('-')
        date = datetime.datetime(int(year), int(month), int(day))
        save = crud.get_save_by_id(db=self.db, save_id=self.save_id)
        user_club_id = save.player_club_id
        #  杯赛奖金
        if self.type == 'champions2to1':
            if self.lteam.club_id == self.winner_id:
                self.lteam.team_model.finance += 4000
                self.rteam.team_model.finance += 2500
                if self.lteam.club_id == user_club_id:
                    user_finance = schemas.UserFinanceCreate(save_id=self.save_id, amount=4000,
                                                             event="欧冠冠军奖金",
                                                             date=date)
                    crud.add_user_finance(db=self.db, user_finance=user_finance)
                elif self.rteam.club_id == user_club_id:
                    user_finance = schemas.UserFinanceCreate(save_id=self.save_id, amount=2500,
                                                             event="欧冠亚军奖金",
                                                             date=date)
                    crud.add_user_finance(db=self.db, user_finance=user_finance)
            else:
                self.rteam.team_model.finance += 4000
                self.lteam.team_model.finance += 2500
                if self.rteam.club_id == user_club_id:
                    user_finance = schemas.UserFinanceCreate(save_id=self.save_id, amount=4000,
                                                             event="欧冠冠军奖金",
                                                             date=date)
                    crud.add_user_finance(db=self.db, user_finance=user_finance)
                elif self.lteam.club_id == user_club_id:
                    user_finance = schemas.UserFinanceCreate(save_id=self.save_id, amount=2500,
                                                             event="欧冠亚军奖金",
                                                             date=date)
                    crud.add_user_finance(db=self.db, user_finance=user_finance)
            logger.info("欧冠冠军奖金")

        if self.type == 'cup2to1':
            if self.lteam.club_id == self.winner_id:
                self.lteam.team_model.finance += 1500
                if self.lteam.club_id == user_club_id:
                    user_finance = schemas.UserFinanceCreate(save_id=self.save_id, amount=1500,
                                                             event="杯赛冠军奖金",
                                                             date=date)
                    crud.add_user_finance(db=self.db, user_finance=user_finance)
            else:
                self.rteam.team_model.finance += 1500
                if self.rteam.club_id == user_club_id:
                    user_finance = schemas.UserFinanceCreate(save_id=self.save_id, amount=1500,
                                                             event="杯赛冠军奖金",
                                                             date=date)
                    crud.add_user_finance(db=self.db, user_finance=user_finance)
            logger.info("杯赛冠军奖金")
        if self.lteam.team_model.reputation > self.rteam.team_model.reputation:
            seat_rate = self.lteam.team_model.reputation / 100
        else:
            seat_rate = self.rteam.team_model.reputation / 100
        viewer = seat_rate * 8
        if self.type == 'league':
            self.lteam.team_model.finance += viewer * 100
        elif self.name == 'champions_league':
            self.lteam.team_model.finance += viewer * 150
        else:
            self.lteam.team_model.finance += viewer * 50
            if self.lteam.club_id == user_club_id:
                user_finance = schemas.UserFinanceCreate(save_id=self.save_id, amount=viewer * 50,
                                                         event="门票收益",
                                                         date=date)
                crud.add_user_finance(db=self.db, user_finance=user_finance)

        self.rate()  # 球员评分
        self.save_game_data()  # 保存比赛
        self.update_players_data()  # 保存球员数据的改变
        return self.lteam.team_model.name, self.rteam.team_model.name, self.lteam.score, self.rteam.score

    def judge_extra_time(self):
        """
        type:比赛类型
        l_score,r_score:两队的比分
        判断比赛类型及结果，决定是否要进行加时赛
        """
        if 'cup' in self.type and self.rteam.score == self.lteam.score:
            self.extra_time()
            return 1
        if 'champion' in self.type and 'group' not in self.type:
            if self.type == 'champions2to1' and self.rteam.score == self.lteam.score:
                self.extra_time()
                return 1
            else:
                query_str = "and_(models.Game.save_id=='{}', models.Game.season=='{}', models.Game.type=='{}')".format(
                    self.save_id, int(self.season), self.type)
                games = crud.get_games_by_attri(db=self.db, query_str=query_str)  # 查找同阶段的其他比赛
                for game in games:
                    team1 = game.teams[0]
                    team2 = game.teams[1]
                    if self.lteam.club_id == team2.club_id or self.lteam.club_id == team1.club_id:  # 查找这两队上一次比赛
                        if team1.score == team2.score:  # 上一轮打平，这一轮加时
                            self.extra_time()
                            return 1

    def extra_time(self):
        """
        进行加时比赛
        """
        print('加时')
        self.add_script('\n开始加时比赛！', 'as')
        hold_ball_team, no_ball_team = self.init_hold_ball_team()
        counter_attack_permitted = False
        for _ in range(20):  # 加时赛20个回合
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

        if self.lteam.score > self.rteam.score:
            self.winner_id = self.lteam.club_id
        elif self.lteam.score < self.rteam.score:
            self.winner_id = self.rteam.club_id  # 加时时间胜负关系
        else:
            self.penalty()

    def penalty(self):
        """
        进行点球
        """
        print('点球')
        lteam_p = 0  # 点球进球数
        rteam_p = 0

        turn = 0
        win_club_id = 0  # 胜者
        while win_club_id == 0:
            self.add_script('\n第{}轮点球！'.format(turn + 1), 'n')
            l_out = self.lteam.making_final_penalty(self.rteam, turn)  # 点球结果
            if l_out:
                self.add_script('稳稳将球罚进！', 'n')
                lteam_p += 1
            elif not l_out:
                self.add_script('被门将拒之门外！', 'n')

            r_out = self.rteam.making_final_penalty(self.lteam, turn)

            if r_out:
                self.add_script('稳稳将球罚进！', 'n')
                rteam_p += 1
            elif not r_out:
                self.add_script('被门将拒之门外！', 'n')
            self.add_script('{} : {}'.format(lteam_p, rteam_p), 'n')
            if turn < 3 and lteam_p - rteam_p > 2:  # 前三轮，2：0还能继续
                win_club_id = self.lteam.club_id

            if turn < 3 and rteam_p - lteam_p > 2:  # 前三轮，2：0还能继续
                win_club_id = self.rteam.club_id

            # turn=3,第四轮
            if turn == 3 and lteam_p - rteam_p >= 2:
                win_club_id = self.lteam.club_id

            if turn == 3 and rteam_p - lteam_p >= 2:
                win_club_id = self.rteam.club_id

            if turn > 3 and lteam_p - rteam_p >= 1:  # 第五轮及以后，1：0就结束
                win_club_id = self.lteam.club_id

            if turn > 3 and rteam_p - lteam_p >= 1:  # 第五轮及以后，1：0就结束
                win_club_id = self.rteam.club_id

            turn += 1

        self.winner_id = win_club_id
        self.add_script('点球结束！ {} {}:{} {}'.format(
            self.lteam.name, lteam_p, rteam_p, self.rteam.name), 'n')

    def tactical_start(self, num: int = 20):
        """
        用于战术调整的模拟比赛
        :return: 两队的战术数据
        """
        tactic = dict()
        tactic['wing_cross'] = 50
        tactic['under_cutting'] = 50
        tactic['pull_back'] = 50
        tactic['middle_attack'] = 50
        tactic['counter_attack'] = 50
        self.lteam.tactic = tactic
        self.rteam.tactic = tactic

        for i in range(num):
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
        # logger.info("{}场模拟比赛耗时{}秒".format(num, str(e - s)))
        # 返回队伍战术执行数据
        return self.lteam.data, self.rteam.data

    def set_full_stamina(self):
        """
        初始化所有球员的体力
        """
        for player in self.lteam.players:
            player.stamina = player.data['original_stamina']
        for player in self.rteam.players:
            player.stamina = player.data['original_stamina']

    def update_players_data(self):
        """
        保存球员数据的改变
        """
        for player in self.lteam.players:
            self.update_player_data(player)
        self.db.commit()
        for player in self.rteam.players:
            self.update_player_data(player)
        # self.db.commit() # 感觉不用加

    def update_player_data(self, player: game_eve_app.Player):
        """
        保存球员数据的改变
        :param player: 球员实例
        """
        lo = player.ori_location
        # region 记录场上位置数
        if lo == 'ST':
            self.update_player(player.player_model,
                               attri={'ST_num': player.player_model.ST_num + 1})
        elif lo == 'CM':
            self.update_player(player.player_model,
                               attri={'CM_num': player.player_model.CM_num + 1})
        elif lo == 'LW':
            self.update_player(player.player_model,
                               attri={'LW_num': player.player_model.LW_num + 1})
        elif lo == 'RW':
            self.update_player(player.player_model,
                               attri={'RW_num': player.player_model.RW_num + 1})
        elif lo == 'CB':
            self.update_player(player.player_model,
                               attri={'CB_num': player.player_model.CB_num + 1})
        elif lo == 'LB':
            self.update_player(player.player_model,
                               attri={'LB_num': player.player_model.LB_num + 1})
        elif lo == 'RB':
            self.update_player(player.player_model,
                               attri={'RB_num': player.player_model.RB_num + 1})
        elif lo == 'GK':
            self.update_player(player.player_model,
                               attri={'GK_num': player.player_model.GK_num + 1})
        elif lo == 'CAM':
            self.update_player(player.player_model,
                               attri={'CAM_num': player.player_model.CAM_num + 1})
        elif lo == 'LM':
            self.update_player(player.player_model,
                               attri={'LM_num': player.player_model.LM_num + 1})
        elif lo == 'RM':
            self.update_player(player.player_model,
                               attri={'RM_num': player.player_model.RM_num + 1})
        elif lo == 'CDM':
            self.update_player(player.player_model,
                               attri={'CDM_num': player.player_model.CDM_num + 1})
        else:
            logger.warning('没有球员对应的位置！')
        # endregion
        # region 能力成长
        if player.data['real_rating'] < 4:
            self.update_player(player.player_model, self.get_cap_improvement(player, 0.025))
        elif 4 <= player.data['real_rating'] < 5:
            self.update_player(player.player_model, self.get_cap_improvement(player, 0.05))
        elif 5 <= player.data['real_rating'] < 6:
            self.update_player(player.player_model, self.get_cap_improvement(player, 0.075))
        elif 6 <= player.data['real_rating'] < 7:
            self.update_player(player.player_model, self.get_cap_improvement(player, 0.1))
        elif 7 <= player.data['real_rating'] < 8:
            self.update_player(player.player_model, self.get_cap_improvement(player, 0.125))
        elif 8 <= player.data['real_rating'] < 9:
            self.update_player(player.player_model, self.get_cap_improvement(player, 0.15))
        elif player.data['real_rating'] >= 9:
            self.update_player(player.player_model, self.get_cap_improvement(player, 0.175))
        else:
            logger.error('没有球员相对应的评分！')
        # endregion

        # region  剩余体力保存
        self.update_player(player.player_model,
                           attri={'real_stamina': player.stamina, 'last_game_date': self.date})
        # endregion
        # region 比赛结束计算身价
        self.update_player(player.player_model,
                           attri={'values': player.computed_player.get_values()})
        # self.db.commit()
        # endregion

    @staticmethod
    def update_player(player_model: models.Player, attri: dict):
        """
        为了统一commit所设置的中间函数
        :param player_model:
        :param attri:
        :return:
        """
        for key, value in attri.items():
            setattr(player_model, key, value)

    @staticmethod
    def get_cap_improvement(player: game_eve_app.Player, value: float) -> Dict[str, float]:
        """
        根据评分，获取能力的提升值
        :param player: 球员实例
        :param value: 外部函数传入的提升值
        :return: 记录能力提升的字典
        """
        original_location = dict()  # 对应位置的能力比重字典
        for x in game_configs.location_capability:
            if x['name'] == player.ori_location:
                original_location = x
                break
        count = 0
        circulation = 0  # 记录循环次数，防止当所有能力都满值时无法跳出循环
        result = dict()
        while True:
            capa_name = utils.select_by_pro(original_location['weight'])
            limit = eval('player.player_model.{}_limit'.format(capa_name))
            real_capa = eval('player.player_model.{}'.format(capa_name))
            if real_capa + value <= limit:
                result[capa_name] = float(utils.retain_decimal(real_capa + value))
                count += 1
            circulation += 1
            if count == 2 or circulation > 20:
                # 若加满两项能力或循环超过20次，退出
                break
        return result

    def export_game_schemas(self, created_time=datetime.datetime.now()) -> schemas.GameCreate:
        """
        导出game_schemas
        :param created_time: 生成时间
        :return: schemas.GameCreate
        """
        data = {
            'name': self.name,
            'type': self.type,
            'created_time': created_time,
            'date': self.date,
            'season': str(self.season),
            'script': self.script,
            'mvp': self.get_highest_rating_player().player_model.id,
            'save_id': self.save_id,
            'winner_id': self.winner_id,
            'goal_record': self.goal_record2str()
        }
        game_data = schemas.GameCreate(**data)
        return game_data

    def save_game_data(self):
        """
        将比赛数据写入数据库
        """
        created_time = datetime.datetime.now()
        # 保存Game
        game_data = self.export_game_schemas(created_time)
        game_model = crud.create_game(db=self.db, game=game_data)
        game_team_info_model_list = []
        # 保存GameTeamInfo
        for team in [self.lteam, self.rteam]:
            game_team_info_schemas = team.export_game_team_info_schemas(created_time)
            game_team_info_model = crud.create_game_team_info(db=self.db, game_team_info=game_team_info_schemas)
            game_team_info_model.season = game_model.season  # 添加赛季
            game_team_info_model_list.append(game_team_info_model)
            # 保存GameTeamData
            game_team_data_schemas = team.export_game_team_data_schemas(created_time)
            game_team_data_model = crud.create_game_team_data(db=self.db, game_team_data=game_team_data_schemas)
            game_team_data_model.season = game_model.season  # 添加赛季
            game_team_info_model.team_data = game_team_data_model

            # 保存GamePlayerData
            game_player_data_model_list: List[models.GamePlayerData] = []
            for player in team.players:
                game_player_data_schemas = player.export_game_player_data_schemas(created_time)
                game_player_data_model = crud.create_game_player_data(db=self.db,
                                                                      game_player_data=game_player_data_schemas)
                game_player_data_model.season = game_model.season  # 添加赛季
                game_player_data_model_list.append(game_player_data_model)
            game_team_info_model.player_data = game_player_data_model_list
        game_model.teams = game_team_info_model_list
        self.db.commit()
        self.db.refresh(game_model)
        return game_model.id
        # 更迅速地保存GamePlayerData
        # game_player_data_schemas_list: List[schemas.GamePlayerData] = list(
        #     map(lambda p: p.export_game_player_data_schemas(created_time), team.players))
        # crud.create_game_player_data_bulk(game_player_data=game_player_data_schemas_list,
        #                                   game_team_info_id=game_team_info_model.id)

    def add_script(self, text: str, status: str):
        """
        添加解说
        :param text: 解说词
        :param status:状态参数
        """
        grade = '@' + str(random.randint(1, 5))
        if status == 's':  # 开始
            str_time = '@00:00'
            self.ingame_time = 0
            self.script += text + str_time + grade + '\n'
        elif status == 'as':  # 加时开始
            str_time = '@090:00'
            self.ingame_time = 9000
            self.script += text + str_time + grade + '\n'
        elif status == 'e':  # 结束
            str_time = '@90:00'
            self.script += text + str_time + grade + '\n'
        elif status == 'ae':
            str_time = '@120:00'  # 加时结束
            self.script += text + str_time + grade + '\n'
        elif status == 'd':  # 两段动作
            happening_time = random.randint(self.ingame_time + 25, self.ingame_time + 100)
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
            self.ingame_time = happening_time
            if len(str_time) < 5:  # 100分钟以内
                str_sec = cstr_time[-2:]
                str_min = cstr_time[:2]
                str_time = str_min + ":" + str_sec
            else:
                str_sec = cstr_time[-2:]
                str_min = cstr_time[:3]
                str_time = str_min + ":" + str_sec
            self.script += text + '@' + str_time + grade + '\n'
        elif status == 'c':  # 连续动作,时间间隔短
            happening_time = random.randint(self.ingame_time + 1, self.ingame_time + 4)
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
            self.ingame_time = happening_time
            if len(str_time) < 5:  # 100分钟以内
                str_sec = cstr_time[-2:]
                str_min = cstr_time[:2]
                str_time = str_min + ":" + str_sec
            else:
                str_sec = cstr_time[-2:]
                str_min = cstr_time[:3]
                str_time = str_min + ":" + str_sec
            self.script += text + '@' + str_time + grade + '\n'
        elif status == 'n':  # 纯解说
            self.script += text + grade + '\n'

    def init_hold_ball_team(self) -> Tuple[game_eve_app.Team, game_eve_app.Team]:
        """
        比赛开始时，随机选择持球队伍
        :return: 持球队伍，无球队伍
        """
        hold_ball_team = random.choice([self.lteam, self.rteam])
        no_ball_team = self.lteam if hold_ball_team == self.rteam else self.rteam
        return hold_ball_team, no_ball_team

    def exchange_hold_ball_team(self, hold_ball_team: game_eve_app.Team) -> Tuple[game_eve_app.Team, game_eve_app.Team]:
        """
        球权易位
        :param hold_ball_team: 原先持球的队伍实例
        :return: 持球队伍，无球队伍
        """
        hold_ball_team = self.lteam if hold_ball_team == self.rteam else self.rteam
        no_ball_team = self.lteam if hold_ball_team == self.rteam else self.rteam
        return hold_ball_team, no_ball_team

    def rate(self):
        """
        球员评分，写入到每一个球员实例的.data['real_rating']中
        """
        # 动作次数评分
        average_actions = self.get_average_actions()
        # 按动作数偏移值评分
        if average_actions > 7:
            # 总动作书超过7次 才开始为动作数评分 以免造成比赛初期评分波动较大的情况出现
            for player in self.lteam.players:
                if player.ori_location != game_configs.Location.GK:
                    offset = self.get_offset_per(player.data['actions'], average_actions)
                    self.rate_by_actions(player, offset)
            for player in self.rteam.players:
                if player.ori_location != game_configs.Location.GK:
                    offset = self.get_offset_per(player.data['actions'], average_actions)
                    self.rate_by_actions(player, offset)
        # 各项动作准确率评分
        average_pass_success = \
            self.get_average_capa('pass_success', action_name='passes') / \
            self.get_average_capa('passes', is_action=True)
        average_dribble_success = \
            self.get_average_capa('dribble_success', action_name='dribbles') / \
            self.get_average_capa('dribbles', is_action=True)
        average_tackle_success = \
            self.get_average_capa('tackle_success', action_name='tackles') / \
            self.get_average_capa('tackles', is_action=True)
        average_aerial_success = \
            self.get_average_capa('aerial_success', action_name='aerials') / \
            self.get_average_capa('aerials', is_action=True)

        for player in self.lteam.players:
            if player.ori_location != game_configs.Location.GK:
                if player.data['passes'] >= 5:
                    # 动作次数不小于5次，才将其计入评分
                    offset = self.get_offset_per(player.data['pass_success'] / player.data['passes'],
                                                 average_pass_success)
                    self.rate_by_capa(player, offset)
                if player.data['dribbles'] >= 5:
                    offset = self.get_offset_per(player.data['dribble_success'] / player.data['dribbles'],
                                                 average_dribble_success)
                    self.rate_by_capa(player, offset)
                if player.data['tackles'] >= 5:
                    offset = self.get_offset_per(player.data['tackle_success'] / player.data['tackles'],
                                                 average_tackle_success)
                    self.rate_by_capa(player, offset)
                if player.data['aerials'] >= 5:
                    offset = self.get_offset_per(player.data['aerial_success'] / player.data['aerials'],
                                                 average_aerial_success)
                    self.rate_by_capa(player, offset)
        for player in self.rteam.players:
            if player.ori_location != game_configs.Location.GK:
                # 动作次数不小于5次才计入评分
                if player.data['passes'] >= 5:
                    offset = self.get_offset_per(player.data['pass_success'] / player.data['passes'],
                                                 average_pass_success)
                    self.rate_by_capa(player, offset)
                if player.data['dribbles'] >= 5:
                    offset = self.get_offset_per(player.data['dribble_success'] / player.data['dribbles'],
                                                 average_dribble_success)
                    self.rate_by_capa(player, offset)
                if player.data['tackles'] >= 5:
                    offset = self.get_offset_per(player.data['tackle_success'] / player.data['tackles'],
                                                 average_tackle_success)
                    self.rate_by_capa(player, offset)
                if player.data['aerials'] >= 5:
                    offset = self.get_offset_per(player.data['aerial_success'] / player.data['aerials'],
                                                 average_aerial_success)
                    self.rate_by_capa(player, offset)
        # 其他加成
        for player in self.lteam.players:
            goals = player.data['goals']
            assists = player.data['assists']
            saves = player.data['save_success']
            player.data['real_rating'] += goals * 1.3 + assists * 0.8 + saves * 0.4
        for player in self.rteam.players:
            goals = player.data['goals']
            assists = player.data['assists']
            saves = player.data['save_success']
            player.data['real_rating'] += goals * 1.3 + assists * 0.8 + saves * 0.4
        for player in self.lteam.players:
            self.perf_rating(player.data['real_rating'], player)
        for player in self.rteam.players:
            self.perf_rating(player.data['real_rating'], player)

    def get_average_actions(self) -> float:
        """
        获取动作数量的均值
        :return: 均值
        """
        _sum = 0
        for player in self.lteam.players:
            _sum += player.data['actions']
        for player in self.rteam.players:
            _sum += player.data['actions']
        return _sum / 22

    def get_average_capa(self, capa_name: str, is_action=False, action_name: str = None) -> float:
        """
        获取指定数据的平均值
        :param capa_name: 数据名
        :param is_action: 是否是动作
        :param action_name: 如果不是动作，则其相应的动作名
        :return: 均值
        """
        _sum = 0
        count = 0
        for player in self.lteam.players:
            if is_action:
                if player.data[capa_name] < 5:
                    continue
            else:
                if player.data[action_name] < 5:
                    continue
            _sum += player.data[capa_name]
            count += 1  # 说明有一个球员被选中参与评分
        for player in self.rteam.players:
            if is_action:
                if player.data[capa_name] < 5:
                    continue
            else:
                if player.data[action_name] < 5:
                    continue
            _sum += player.data[capa_name]
            count += 1
        if is_action and _sum == 0:
            # 防止分母为零
            _sum = 1
        if count == 0:
            return 1
        else:
            return _sum / count

    @staticmethod
    def get_offset_per(a, b) -> float:
        """
        获取a比b高或低的比例 可能为负
        """
        if b == 0:
            return 0
        else:
            return (a - b) / b

    @staticmethod
    def rate_by_actions(player, offset):
        """
        动作数量的评分办法
        :param player: 球员实例
        :param offset: 与均值的偏移百分比
        """
        if 0.1 <= offset < 0.2:
            player.data['real_rating'] += 0.3
        if 0.2 <= offset < 0.4:
            player.data['real_rating'] += 0.5
        if 0.4 <= offset < 0.6:
            player.data['real_rating'] += 0.8
        if 0.6 <= offset < 0.8:
            player.data['real_rating'] += 1.2
        if 0.8 <= offset:
            player.data['real_rating'] += 1.6
        if -0.2 < offset <= -0.1:
            player.data['real_rating'] -= 0.3
        if -0.4 < offset <= -0.2:
            player.data['real_rating'] -= 0.5
        if -0.6 < offset <= -0.4:
            player.data['real_rating'] -= 0.8
        if -0.8 < offset <= -0.6:
            player.data['real_rating'] -= 1.2
        if offset <= -0.8:
            player.data['real_rating'] -= 1.6

    @staticmethod
    def rate_by_capa(player, offset):
        """
        TODO 这种参数统统分离到game_configs里去
        各项能力数值的评分办法
        :param player: 球员实例
        :param offset: 与均值的偏移值
        """
        if 0.1 <= offset < 0.2:
            player.data['real_rating'] += 0.3
        if 0.2 <= offset < 0.4:
            player.data['real_rating'] += 0.6
        if 0.4 <= offset < 0.6:
            player.data['real_rating'] += 0.9
        if 0.6 <= offset < 0.8:
            player.data['real_rating'] += 1.2
        if 0.8 <= offset:
            player.data['real_rating'] += 1.5
        if -0.2 < offset <= -0.1:
            player.data['real_rating'] -= 0.3
        if -0.4 < offset <= -0.2:
            player.data['real_rating'] -= 0.6
        if -0.6 < offset <= -0.4:
            player.data['real_rating'] -= 1.0
        if -0.8 < offset <= -0.6:
            player.data['real_rating'] -= 1.3
        if -1 < offset <= -0.8:
            player.data['real_rating'] -= 1.6

    @staticmethod
    def perf_rating(rating, player):
        """
        调整评分在正常范围内
        :param rating: 评分
        :param player: 球员实例
        """
        rating = player.data['real_rating']
        if rating < 0:
            rating = 0
        if rating > 10:
            rating = 10
        player.data['final_rating'] = float(utils.retain_decimal(rating))

    def get_highest_rating_player(self) -> game_eve_app.Player:
        """
        获取全场mvp
        :return: mvp球员实例
        """
        player_list = [p for p in self.lteam.players]
        player_list.extend([p for p in self.rteam.players])
        player_list = [(p, p.data['real_rating']) for p in player_list]
        highest_rating_player = max(player_list, key=lambda x: x[1])[0]
        return highest_rating_player

    def goal_record2str(self) -> str:
        """
        将goal_record中的数据转换为字符串
        """
        if not self.goal_record:
            return '[]'
        return json.dumps([g.dict() for g in self.goal_record], ensure_ascii=False)
