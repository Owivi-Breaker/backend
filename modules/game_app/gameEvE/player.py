from utils import utils, logger
import models
import schemas
import game_configs

from typing import Dict, List, Sequence, Set, Tuple, Optional
import datetime


class Player:
    # 比赛球员类
    def __init__(self, player_model: models.Player, location: str):
        self.player_model = player_model
        self.name = player_model.translated_name  # 解说用
        self.ori_location = location  # 原本位置
        self.real_location = location  # 每个回合变化后的实时位置
        self.capa = dict()  # 球员能力字典
        self.init_capa()
        self.stamina = player_model.real_stamina  # 初始体力，会随着比赛进行而减少
        # self.data记录球员场上数据
        self.data = {
            "original_stamina": self.stamina,  # 初始体力
            "actions": 0,
            "goals": 0,
            "assists": 0,
            "shots": 0,
            "dribbles": 0,
            "dribble_success": 0,
            "passes": 0,
            "pass_success": 0,
            "tackles": 0,
            "tackle_success": 0,
            "aerials": 0,
            "aerial_success": 0,
            "saves": 0,
            "save_success": 0,
            'final_rating': 6.0,  # 初始评分为6.0
            'real_rating': 6.0  # 未取顶值的真实评分
        }

    def init_capa(self):
        """
        将球员的各项能力值读入self.rating中
        """
        self.capa['shooting'] = self.player_model.shooting
        self.capa['passing'] = self.player_model.passing
        self.capa['dribbling'] = self.player_model.dribbling
        self.capa['interception'] = self.player_model.interception
        self.capa['pace'] = self.player_model.pace
        self.capa['strength'] = self.player_model.strength
        self.capa['aggression'] = self.player_model.aggression
        self.capa['anticipation'] = self.player_model.anticipation
        self.capa['free_kick'] = self.player_model.free_kick
        self.capa['stamina'] = self.player_model.stamina  # 注意，这个是体力“能力”，不是真正的体力！
        self.capa['goalkeeping'] = self.player_model.goalkeeping

    def export_game_player_data_schemas(self, created_time=datetime.datetime.now()) -> schemas.GamePlayerDataCreate:
        """
        导出数据至GamePlayerData
        :param created_time: 创建时间
        :return: schemas.GamePlayerData
        """
        data = {
            'created_time': created_time,
            'player_id': self.player_model.id,
            'location': self.ori_location,
            **self.data,
            'final_stamina': self.stamina
        }
        game_player_data = schemas.GamePlayerData(**data)
        return game_player_data

    def get_capa(self, capa_name: str) -> float:
        """
        获取指定能力属性
        :param capa_name: 能力名称
        :return: 扣除体力debuff后的数据
        """
        if capa_name == 'stamina':
            return self.capa['stamina']
        return self.capa[capa_name] * (self.stamina / 100)

    def get_data(self, data_name: str) -> str:
        """
        获取指定场上数据
        :param data_name: 数据名
        :return: 指定场上数据
        """
        return self.data[data_name]

    def plus_data(self, data_name: str, average_stamina: Optional[float] = None):
        """
        根据指定动作，更新场上数据，并消耗体力
        :param data_name: 动作名
        :param average_stamina: 对方球队的平均体力能力
        """
        if data_name == 'shots' or data_name == 'dribbles' \
                or data_name == 'tackles' \
                or data_name == 'saves' or data_name == 'aerials':
            self.data['actions'] += 1
            if utils.select_by_pro(
                    {False: self.get_capa('stamina'), True: average_stamina}
            ) and average_stamina:
                # 若capa stamina判定结果是False，则扣除体力
                self.stamina -= 2.5
        elif data_name == 'passes':
            self.data['actions'] += 1
            if utils.select_by_pro(
                    {False: self.get_capa('stamina'), True: average_stamina}
            ) and average_stamina:
                self.stamina -= 1

        if self.stamina < 0:
            self.stamina = 0
        self.data[data_name] += 1

    def shift_location(self):
        """
        确定每次战术的场上位置
        TODO 将概率值抽离出来作为可更改的全局变量
        """
        if self.ori_location == game_configs.Location.CAM:
            self.real_location = utils.select_by_pro(
                {game_configs.Location.ST: 40, game_configs.Location.CM: 60}
            )
        elif self.ori_location == game_configs.Location.LM:
            self.real_location = utils.select_by_pro(
                {game_configs.Location.LW: 25, game_configs.Location.CM: 60, game_configs.Location.LB: 15}
            )
        elif self.ori_location == game_configs.Location.RM:
            self.real_location = utils.select_by_pro(
                {game_configs.Location.RW: 40, game_configs.Location.CM: 60, game_configs.Location.RB: 15}
            )
        elif self.ori_location == game_configs.Location.CDM:
            self.real_location = utils.select_by_pro(
                {game_configs.Location.CB: 40, game_configs.Location.CM: 60}
            )
        elif self.ori_location == game_configs.Location.CM:
            # 中场有概率前压或后撤
            self.real_location = utils.select_by_pro(
                {game_configs.Location.ST: 10, game_configs.Location.CB: 10, game_configs.Location.CM: 80}
            )
        elif self.ori_location == game_configs.Location.LB:
            self.real_location = utils.select_by_pro(
                {game_configs.Location.LW: 20, game_configs.Location.LB: 80}
            )
        elif self.ori_location == game_configs.Location.RB:
            self.real_location = utils.select_by_pro(
                {game_configs.Location.RW: 20, game_configs.Location.RB: 80}
            )
        else:
            self.real_location = self.ori_location

    def get_location(self):
        """
        获取球员的实时位置
        :return: 球员的实时位置
        """
        return self.real_location
