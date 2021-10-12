from utils import Date, utils, logger
import game_configs
import crud
import models
import schemas
from modules.game_app import game_eve_app

import random
from typing import Dict, List, Sequence, Set, Tuple, Optional
import datetime
from sqlalchemy.orm import Session
import time


class GameEvE:
    def __init__(self, db: Session, club1_id: int, club2_id: int,
                 date: Date, game_type: str, game_name: str, season: int, save_id: int):
        self.db = db
        self.lteam = game_eve_app.Team(self, club1_id)
        self.rteam = game_eve_app.Team(self, club2_id)
        self.date = str(date)
        self.script = ''
        self.type = game_type
        self.name = game_name
        self.season = season
        self.save_id = save_id

    def start(self) -> Tuple:
        """
        开始比赛
        :return: 比分元组
        """
        # 战术调整
        # self.adjust_tactic(*self.tactical_start(num=10))
        # # 重置队伍、球员信息
        # self.lteam.reset()
        # self.rteam.reset()

        self.add_script('比赛开始！')
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
        self.add_script('比赛结束！ {} {}:{} {}'.format(
            self.lteam.name, self.lteam.score, self.rteam.score, self.rteam.name))

        self.rate()  # 球员评分
        self.save_in_db()  # 保存比赛
        self.update_players_data()  # 保存球员数据的改变

        return self.lteam.score, self.rteam.score

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

    def adjust_tactic(self, lteam_data, rteam_data, player_club_id: int = 0):
        """
        调整两队的战术比重
        """
        tactic_pro1 = dict()
        tactic_pro1['wing_cross'] = int((lteam_data['wing_cross_success'] / lteam_data['wing_cross']) * 1000) + 5
        tactic_pro1['under_cutting'] = int(
            (lteam_data['under_cutting_success'] / lteam_data['under_cutting']) * 1000) + 5
        tactic_pro1['pull_back'] = int((lteam_data['pull_back_success'] / lteam_data['pull_back']) * 1000) + 5
        tactic_pro1['middle_attack'] = int(
            (lteam_data['middle_attack_success'] / lteam_data['middle_attack']) * 1000) + 5
        tactic_pro1['counter_attack'] = int(
            (lteam_data['counter_attack_success'] / lteam_data['counter_attack']) * 1000) + 5

        tactic_pro2 = dict()
        tactic_pro2['wing_cross'] = int((rteam_data['wing_cross_success'] / rteam_data['wing_cross']) * 1000) + 5
        tactic_pro2['under_cutting'] = int(
            (rteam_data['under_cutting_success'] / rteam_data['under_cutting']) * 1000) + 5
        tactic_pro2['pull_back'] = int((rteam_data['pull_back_success'] / rteam_data['pull_back']) * 1000) + 5
        tactic_pro2['middle_attack'] = int(
            (rteam_data['middle_attack_success'] / rteam_data['middle_attack']) * 1000) + 5
        tactic_pro2['counter_attack'] = int(
            (rteam_data['counter_attack_success'] / rteam_data['counter_attack']) * 1000) + 5

        if self.lteam.club_id != player_club_id:
            coach_id = crud.get_club_by_id(db=self.db, club_id=self.lteam.club_id).coach.id
            crud.update_coach(db=self.db, coach_id=coach_id, attri=tactic_pro1)
        if self.rteam.club_id != player_club_id:
            coach_id = crud.get_club_by_id(db=self.db, club_id=self.rteam.club_id).coach.id
            crud.update_coach(db=self.db, coach_id=coach_id, attri=tactic_pro2)

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
        for player in self.rteam.players:
            self.update_player_data(player)
        self.db.commit()

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

        # region TODO 剩余体力保存
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
            'season': self.season,
            'script': self.script,
            'mvp': self.get_highest_rating_player().player_model.id,
            'save_id': self.save_id
        }
        game_data = schemas.GameCreate(**data)
        return game_data

    def save_in_db(self):
        """
        将比赛数据写入数据库
        """
        created_time = datetime.datetime.now()
        # 保存Game
        game_data = self.export_game_schemas(created_time)
        game_model = crud.create_game(db=self.db, game=game_data)
        # 保存GameTeamInfo
        for team in [self.lteam, self.rteam]:
            game_team_info_schemas = team.export_game_team_info_schemas(created_time)
            game_team_info_model = crud.create_game_team_info(db=self.db, game_team_info=game_team_info_schemas)
            crud.update_game_team_info(db=self.db, game_team_info_id=game_team_info_model.id,
                                       attri={"game_id": game_model.id})
            # 保存GameTeamData
            game_team_data_schemas = team.export_game_team_data_schemas(created_time)
            game_team_data_model = crud.create_game_team_data(db=self.db, game_team_data=game_team_data_schemas)
            crud.update_game_team_data(db=self.db, game_team_data_id=game_team_data_model.id,
                                       attri={"game_team_info_id": game_team_info_model.id})
            # 保存GamePlayerData
            game_player_data_model_list: List[models.GamePlayerData] = []
            for player in team.players:
                game_player_data_schemas = player.export_game_player_data_schemas(created_time)
                game_player_data_model = crud.create_game_player_data(db=self.db,
                                                                      game_player_data=game_player_data_schemas)

                # 将game_player_data_model放在一个列表里，统一commit
                attri = {"game_team_info_id": game_team_info_model.id}
                for key, value in attri.items():
                    setattr(game_player_data_model, key, value)
                game_player_data_model_list.append(game_player_data_model)

                # crud.update_game_player_data(db=self.db, game_player_data_id=game_player_data_model.id,
                #                              attri={"game_team_info_id": game_team_info_model.id})
            self.db.commit()

    def add_script(self, text: str):
        """
        添加解说
        :param text: 解说词
        """
        self.script += text + '\n'

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
            player.data['real_rating'] += goals * 1.5 + assists * 1.1 + saves * 0.4
        for player in self.rteam.players:
            goals = player.data['goals']
            assists = player.data['assists']
            saves = player.data['save_success']
            player.data['real_rating'] += goals * 1.5 + assists * 1.1 + saves * 0.4
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
        return _sum / 11

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
        获取a比b高或低的比例
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
            player.data['real_rating'] += 0.7
        if 0.4 <= offset < 0.6:
            player.data['real_rating'] += 1.0
        if 0.6 <= offset < 0.8:
            player.data['real_rating'] += 1.5
        if 0.8 <= offset:
            player.data['real_rating'] += 2
        if -0.2 < offset <= -0.1:
            player.data['real_rating'] -= 0.3
        if -0.4 < offset <= -0.2:
            player.data['real_rating'] -= 0.7
        if -0.6 < offset <= -0.4:
            player.data['real_rating'] -= 1.0
        if -0.8 < offset <= -0.6:
            player.data['real_rating'] -= 1.5
        if offset <= -0.8:
            player.data['real_rating'] -= 2

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
