import datetime
import json
import random
from typing import Dict, List

import crud
import models
import schemas
from modules import game_app
from modules.game_app.player_selector import PlayerSelector
from sqlalchemy.orm import Session
from utils import logger


class GamePvEGenerator:
    def __init__(self, db: Session, save_model: models.Save):
        self.db = db
        self.save_model = save_model

    def create_game_pve(self, player_club_id: int, computer_club_id: int,
                        game: dict, date: str, season: int) -> models.game_pve:
        """
        生成game_pve临时表 只会在入口函数调用
        :param player_club_id: 玩家俱乐部id
        :param computer_club_id: 电脑俱乐部id
        :param game: calendar中存放的pve字段内容
        :param date: 日期
        :param season: 赛季
        """
        # 检查此存档中是否已有临时表 若有则删除之
        if crud.get_game_pve_by_save_id(db=self.db, save_id=self.save_model.id):
            logger.warning('game_pve 临时表已存在！删除之')
            crud.delete_all_game_temp_table(db=self.db, save_id=self.save_model.id)

        data = dict()
        data['created_time'] = datetime.datetime.now()  # TODO created_time 字段都应由sqlalchemy自动生成
        data['home_club_id'] = game['club_id'].split(',')[0]
        data['name'] = game['game_name']
        data['type'] = game['game_type']
        data['date'] = date
        data['season'] = season
        data['save_id'] = self.save_model.id
        data['player_club_id'] = player_club_id
        data['computer_club_id'] = computer_club_id
        data['cur_attacker'] = random.choice((player_club_id, computer_club_id))  # TODO 主场先攻
        game_pve: schemas.GamePvECreate = schemas.GamePvECreate(**data)
        crud.create_game_pve(db=self.db, game_pve=game_pve)

    def create_team_n_player_pve(self) -> int:
        """
        创建team_pve表和player_pve表
        在前端发送game_pve/start api请求后调用
        :return: cur_attacker
        """
        game_pve_models = crud.get_game_pve_by_save_id(db=self.db, save_id=self.save_model.id)
        player_club_id = game_pve_models.player_club_id
        computer_club_id = game_pve_models.computer_club_id
        if not game_pve_models:
            logger.error("找不到game_pve临时表")
            return -1
        # 创建玩家TeamPvE
        player_team_pve: schemas.TeamPvECreate = schemas.TeamPvECreate(
            **{
                "club_id": player_club_id,
                "created_time": datetime.datetime.now(),
                "is_player": True
            })
        player_team_pve_model: models.TeamPvE = crud.create_team_pve(db=self.db, team_pve=player_team_pve)
        # 创建电脑TeamPvE
        computer_team_pve: schemas.TeamPvECreate = schemas.TeamPvECreate(
            **{
                "club_id": computer_club_id,
                "created_time": datetime.datetime.now()
            })
        computer_team_pve_model: models.TeamPvE = crud.create_team_pve(db=self.db, team_pve=computer_team_pve)

        game_pve_models.teams = [player_team_pve_model, computer_team_pve_model]

        # 电脑自动选人
        player_selector = PlayerSelector(club_id=computer_club_id, db=self.db,
                                         season=self.save_model.season, date=self.save_model.date)
        players_model, locations_list = player_selector.select_players()
        # 创建电脑PlayerPvE
        computer_player_pve_model_list: List[models.PlayerPvE] = []
        for player_model, location in zip(players_model, locations_list):
            player_pve: schemas.PlayerPvECreate = schemas.PlayerPvECreate(
                **{
                    "created_time": datetime.datetime.now(),
                    "player_id": player_model.id,
                    "ori_location": location,
                    "real_location": location
                })
            computer_player_pve_model_list.append(crud.create_player_pve(db=self.db, player_pve=player_pve))
        computer_team_pve_model.players = computer_player_pve_model_list
        # 读取save表中的选人结果 创建玩家PlayerPvE
        player_player_pve_model_list: List[models.PlayerPvE] = []  # 好怪的名字
        if self.save_model.lineup:
            lineup: Dict[int, str] = json.loads(self.save_model.lineup)
        else:
            raise ValueError('lineup empty!')
        for key, value in lineup.items():
            player_pve: schemas.PlayerPvECreate = schemas.PlayerPvECreate(
                **{
                    "created_time": datetime.datetime.now(),
                    "player_id": key,
                    "ori_location": value,
                    "real_location": value
                })
            player_player_pve_model_list.append(crud.create_player_pve(db=self.db, player_pve=player_pve))
        player_team_pve_model.players = player_player_pve_model_list
        self.db.commit()
        # AI调整战术比重
        tactic_adjustor = game_app.TacticAdjustor(db=self.db,
                                                  club1_id=player_club_id, club2_id=computer_club_id,
                                                  player_club_id=player_club_id,
                                                  save_id=self.save_model.id,
                                                  season=self.save_model.season,
                                                  date=self.save_model.date)
        tactic_adjustor.adjust()
        self.db.commit()
        return game_pve_models.cur_attacker
