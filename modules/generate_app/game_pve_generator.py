import models
from utils import utils, logger
import game_configs
import crud
import schemas
from modules import game_app
from modules.game_app.player_selector import PlayerSelector

import random
import json
import datetime
from typing import Tuple, List, Dict
from sqlalchemy.orm import Session


class GamePvEGenerator:
    def __init__(self, db: Session, player_club_id: int, computer_club_id: int, save_model: models.Save):
        self.db = db
        self.player_club_id = player_club_id
        self.computer_club_id = computer_club_id
        self.save_model = save_model

    def create_game_pve(self, game: dict, date: str, season: int) -> models.game_pve:
        """
        生成game_pve临时表 只会在入口函数调用
        :param game: calendar中存放的pve字段内容
        :param date: 日期
        :param season: 赛季
        """
        data = dict()
        data['created_time'] = datetime.datetime.now()  # TODO created_time 字段都应由sqlalchemy自动生成
        data['name'] = game['game_name']
        data['type'] = game['game_type']
        data['date'] = date
        data['season'] = season
        data['player_club_id'] = self.player_club_id
        data['computer_club_id'] = self.computer_club_id
        game_pve: schemas.GamePvECreate = schemas.GamePvECreate(**data)
        crud.create_game_pve(db=self.db, game_pve=game_pve)

    def create_team_n_player_pve(self):
        """
        创建team_pve表和player_pve表
        """
        game_pve_models = crud.get_game_pve_by_club_id(db=self.db,
                                                       player_club_id=self.player_club_id,
                                                       computer_club_id=self.computer_club_id)
        # 创建玩家TeamPvE
        player_team_pve: schemas.TeamPvECreate = schemas.TeamPvECreate()
        player_team_pve.club_id = self.player_club_id
        player_team_pve.created_time = datetime.datetime.now()
        player_team_pve_model: models.TeamPvE = crud.create_team_pve(db=self.db, team_pve=player_team_pve)
        # 创建电脑TeamPvE
        computer_team_pve: schemas.TeamPvECreate = schemas.TeamPvECreate()
        computer_team_pve.club_id = self.computer_club_id
        computer_team_pve.created_time = datetime.datetime.now()
        computer_team_pve_model: models.TeamPvE = crud.create_team_pve(db=self.db, team_pve=computer_team_pve)

        game_pve_models.teams = [player_team_pve_model, computer_team_pve_model]
        # AI自动选人
        player_selector = PlayerSelector(club_id=self.computer_club_id, db=self.db,
                                         season=self.save_model.season, date=self.save_model.date)
        players_model, locations_list = player_selector.select_players()

        computer_player_pve_model_list: List[models.PlayerPvE] = []
        for player_model, location in zip(players_model, locations_list):
            player_pve: schemas.PlayerPvECreate = schemas.PlayerPvECreate()
            player_pve.created_time = datetime.datetime.now()
            player_pve.player_id = player_model.id
            player_pve.ori_location = location
            computer_player_pve_model_list.append(crud.create_player_pve(db=self.db, player_pve=player_pve))
        computer_team_pve_model.players = computer_player_pve_model_list
        # 读取save表中的选人结果完成玩家的选人
        player_player_pve_model_list: List[models.PlayerPvE] = []  # 好怪的名字
        lineup: Dict[int, str] = json.loads(self.save_model.lineup)
        for key, value in lineup.items():
            player_pve: schemas.PlayerPvECreate = schemas.PlayerPvECreate()
            player_pve.created_time = datetime.datetime.now()
            player_pve.player_id = key
            player_pve.ori_location = value
            player_player_pve_model_list.append(crud.create_player_pve(db=self.db, player_pve=player_pve))
        computer_team_pve_model.players = player_player_pve_model_list
        self.db.commit()
        # AI调整战术比重
        tactic_adjustor = game_app.TacticAdjustor(db=self.db,
                                                  club1_id=self.player_club_id, club2_id=self.computer_club_id,
                                                  player_club_id=self.player_club_id,
                                                  save_id=self.save_model.id,
                                                  season=self.save_model.season,
                                                  date=self.save_model.date)
        tactic_adjustor.adjust()
        self.db.commit()
