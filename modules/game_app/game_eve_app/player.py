import datetime
from typing import Optional

import game_configs
import models
import schemas
from modules import computed_data_app
from sqlalchemy.orm import Session
from utils import utils


class Player:
    # 比赛球员类
    def __init__(self, db: Session, player_model: models.Player, location: str, season: int, date: str):
        self.db = db
        self.season = season
        self.date = date
        self.player_model = player_model
        self.computed_player = computed_data_app.ComputedPlayer(
            player_id=self.player_model.id, db=self.db,
            player_model=self.player_model, season=self.season, date=self.date)
        self.name = player_model.translated_name  # 解说用
        self.ori_location = location  # 原本位置，不会变
        self.real_location = location  # 每个回合变化后的实时位置
        self.capa = dict()  # 球员能力字典
        self.init_capa()
        self.stamina = self.computed_player.get_real_stamina()  # 初始体力，会随着比赛进行而减少
        # self.data记录球员场上数据
        self.data = dict()
        self.init_data()

    def reset(self):
        self.init_capa()
        self.stamina = self.player_model.real_stamina
        self.init_data()

    def init_data(self):
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
        self.capa = self.computed_player.get_all_capa()

    def export_game_player_data_schemas(self, created_time=datetime.datetime.now()) -> schemas.GamePlayerDataCreate:
        """
        导出数据至GamePlayerData
        :param created_time: 创建时间
        :return: schemas.GamePlayerDataCreate
        """
        data = {
            'created_time': created_time,
            'player_id': self.player_model.id,
            'location': self.ori_location,
            **self.data,
            'final_stamina': self.stamina
        }
        game_player_data = schemas.GamePlayerDataCreate(**data)
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

    def plus_data(self, data_name: str, average_stamina: Optional[float] = 0):
        """
        根据指定动作，更新场上数据，并消耗体力
        :param data_name: 动作名
        :param average_stamina: 对方球队的平均体力能力
        """
        stamina_diff = 0  # 需要扣除的体力值
        if data_name == 'shots' or data_name == 'dribbles' \
                or data_name == 'tackles' \
                or data_name == 'saves' or data_name == 'aerials':
            stamina_diff = 2.5
        elif data_name == 'passes':
            stamina_diff = 1

        self.data['actions'] += 1
        if average_stamina and utils.select_by_pro(
                {False: self.get_capa('stamina'), True: average_stamina}):
            # 若capa stamina判定结果是False，则扣除体力
            self.stamina -= stamina_diff

        if self.stamina < 0:
            self.stamina = 0
        self.data[data_name] += 1

    def shift_location(self):
        """
        确定每次战术的场上位置
        TODO 将概率值抽离出来作为可更改的全局变量
        """
        location = game_configs.Location

        if self.ori_location == game_configs.Location.CM:
            # 中场有概率前压或后撤
            self.real_location = utils.select_by_pro(
                {location.ST: 10, location.CB: 10, location.CM: 80}
            )
        elif self.ori_location == location.LB:
            self.real_location = utils.select_by_pro(
                {location.LW: 20, location.LB: 80}
            )
        elif self.ori_location == location.RB:
            self.real_location = utils.select_by_pro(
                {location.RW: 20, location.RB: 80}
            )
        elif self.ori_location == location.CAM:
            self.real_location = utils.select_by_pro(
                {location.ST: 40, location.CM: 60}
            )
        elif self.ori_location == location.LM:
            self.real_location = utils.select_by_pro(
                {location.LW: 25, location.CM: 60, location.LB: 15}
            )
        elif self.ori_location == location.RM:
            self.real_location = utils.select_by_pro(
                {location.RW: 40, location.CM: 60, location.RB: 15}
            )
        elif self.ori_location == location.CDM:
            self.real_location = utils.select_by_pro(
                {location.CB: 40, location.CM: 60}
            )
        else:
            self.real_location = self.ori_location

    def get_location(self):
        """
        获取球员的实时位置
        :return: 球员的实时位置
        """
        return self.real_location
