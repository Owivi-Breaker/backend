import crud
from modules import computed_data_app
from utils import utils, logger
import models
import schemas
import game_configs
from modules.game_app import game_eve_app

from typing import Dict, List, Sequence, Set, Tuple, Optional
import datetime
from sqlalchemy.orm import Session


class PlayerPvE(game_eve_app.Player):
    def __init__(self, db: Session, player_pve_model: models.PlayerPvE, season: int, date: str, is_first_turn: bool):
        self.player_pve_model: models.PlayerPvE = player_pve_model

        self.db = db
        self.season = season
        self.date = date
        self.player_model = crud.get_player_by_id(db=self.db, player_id=player_pve_model.player_id)
        self.computed_player = computed_data_app.ComputedPlayer(
            player_id=self.player_model.id, db=self.db,
            player_model=self.player_model, season=self.season, date=self.date)

        self.name = self.player_model.translated_name  # 解说用
        self.ori_location = self.player_pve_model.ori_location  # 原本位置，不会变
        self.real_location = self.player_pve_model.real_location  # 每个回合变化后的实时位置
        self.capa = dict()  # 球员能力字典
        self.init_capa()
        self.stamina = self.player_pve_model.final_stamina  # 初始体力，会随着比赛进行而减少
        self.init_stamina(is_first_turn)
        # self.data记录球员场上数据
        self.data = dict()
        self.init_data()

    def init_stamina(self, is_first_turn: bool):
        """
        在第一回合初始化体力
        """
        if is_first_turn:
            # 将体力值录入到临时表中
            self.player_pve_model.original_stamina = self.computed_player.get_real_stamina()
            self.player_pve_model.final_stamina = self.computed_player.get_real_stamina()
            self.stamina = self.player_pve_model.final_stamina
            self.db.commit()

    def init_data(self):
        self.data = {
            "original_stamina": self.player_pve_model.original_stamina,  # 初始体力
            "actions": self.player_pve_model.actions,
            "goals": self.player_pve_model.goals,
            "assists": self.player_pve_model.assists,
            "shots": self.player_pve_model.shots,
            "dribbles": self.player_pve_model.dribbles,
            "dribble_success": self.player_pve_model.dribble_success,
            "passes": self.player_pve_model.passes,
            "pass_success": self.player_pve_model.pass_success,
            "tackles": self.player_pve_model.tackles,
            "tackle_success": self.player_pve_model.tackle_success,
            "aerials": self.player_pve_model.aerials,
            "aerial_success": self.player_pve_model.aerial_success,
            "saves": self.player_pve_model.saves,
            "save_success": self.player_pve_model.save_success,
            'final_rating': self.player_pve_model.final_rating,  # 初始评分为6.0
            'real_rating': self.player_pve_model.real_rating  # 未取顶值的真实评分
        }

    def save_temporary_table(self):
        self.player_pve_model.actions = self.data['actions']
        self.player_pve_model.goals = self.data['goals']
        self.player_pve_model.assists = self.data['assists']
        self.player_pve_model.shots = self.data['shots']
        self.player_pve_model.dribbles = self.data['dribbles']
        self.player_pve_model.dribble_success = self.data['dribble_success']
        self.player_pve_model.passes = self.data['passes']
        self.player_pve_model.pass_success = self.data['pass_success']
        self.player_pve_model.tackles = self.data['tackles']
        self.player_pve_model.tackle_success = self.data['tackle_success']
        self.player_pve_model.aerials = self.data['aerials']
        self.player_pve_model.aerial_success = self.data['aerial_success']
        self.player_pve_model.saves = self.data['saves']
        self.player_pve_model.save_success = self.data['save_success']
        self.player_pve_model.final_rating = self.data['final_rating']
        self.player_pve_model.real_rating = self.data['real_rating']

        self.player_pve_model.real_location = self.real_location
        self.player_pve_model.final_rating = self.stamina
        # TODO 实时评分
