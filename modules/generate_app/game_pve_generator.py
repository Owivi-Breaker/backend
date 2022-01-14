import models
from utils import utils, logger
import game_configs
import crud
import schemas

import random
import json
import datetime
from typing import Tuple
from sqlalchemy.orm import Session


class GamePvEGenerator:
    def __init__(self, db: Session, player_club_id: int, computer_club_id: int):
        self.db = db
        self.player_club_id = player_club_id
        self.computer_club_id = computer_club_id

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
        for club_id in [self.player_club_id, self.computer_club_id]:
            team_pve: schemas.TeamPvECreate = schemas.TeamPvECreate()
            team_pve.club_id = club_id
            team_pve.created_time = datetime.datetime.now()
