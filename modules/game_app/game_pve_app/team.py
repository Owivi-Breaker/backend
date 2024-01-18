from typing import List

import crud
import models
from modules.game_app import game_eve_app, game_pve_app
from sqlalchemy.orm import Session


class TeamPvE(game_eve_app.Team):
    def __init__(self, db: Session, game: "game_pve_app.GamePvE", team_pve_model: models.TeamPvE):
        # 为了使用父类的方法 成员的名字不能变
        self.team_pve_model: models.TeamPvE = team_pve_model

        self.db = db
        self.game = game
        self.season = game.season
        self.date = game.date
        self.club_id = team_pve_model.club_id
        self.team_model = crud.get_club_by_id(db=self.db, club_id=self.team_pve_model.club_id)
        self.name = self.team_model.name  # 解说用
        self.tactic = dict()  # 战术比重字典
        self.init_tactic()

        self.players: List[game_pve_app.PlayerPvE] = [
            game_pve_app.PlayerPvE(
                db=self.db,
                player_pve_model=player_pve_model,
                season=self.season,
                date=self.date,
                is_first_turn=True if self.game.turns == 1 else False,
            )
            for player_pve_model in self.team_pve_model.players
        ]
        self.score: int = self.team_pve_model.score  # 本方比分

        # self.data记录俱乐部场上数据
        self.data = dict()
        self.init_data()

    def init_data(self):
        """
        获取临时表中的球队统计数据
        """
        self.data = {
            "attempts": self.team_pve_model.attempts,
            "wing_cross": self.team_pve_model.wing_cross,
            "wing_cross_success": self.team_pve_model.wing_cross_success,
            "under_cutting": self.team_pve_model.under_cutting,
            "under_cutting_success": self.team_pve_model.under_cutting_success,
            "pull_back": self.team_pve_model.pull_back,
            "pull_back_success": self.team_pve_model.pull_back_success,
            "middle_attack": self.team_pve_model.middle_attack,
            "middle_attack_success": self.team_pve_model.middle_attack_success,
            "counter_attack": self.team_pve_model.counter_attack,
            "counter_attack_success": self.team_pve_model.counter_attack_success,
        }

    def save_temporary_table(self):
        """
        保存临时表
        """
        self.team_pve_model.attempts = self.data["attempts"]
        self.team_pve_model.wing_cross = self.data["wing_cross"]
        self.team_pve_model.wing_cross_success = self.data["wing_cross_success"]
        self.team_pve_model.under_cutting = self.data["under_cutting"]
        self.team_pve_model.under_cutting_success = self.data["under_cutting_success"]
        self.team_pve_model.pull_back = self.data["pull_back"]
        self.team_pve_model.pull_back_success = self.data["pull_back_success"]
        self.team_pve_model.middle_attack = self.data["middle_attack"]
        self.team_pve_model.middle_attack_success = self.data["middle_attack_success"]
        self.team_pve_model.counter_attack = self.data["counter_attack"]
        self.team_pve_model.counter_attack_success = self.data["counter_attack_success"]
        self.team_pve_model.score = self.score
        for p in self.players:
            p.save_temporary_table()
