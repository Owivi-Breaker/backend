from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Optional
import json

import game_configs
import schemas
import utils
from utils import logger, utils
import models
import crud


class ComputedCalendar:
    def __init__(self, save_id: int, db: Session, save_model: models.Save):
        self.db = db
        self.save_id = save_id
        self.save_model = save_model \
            if save_model \
            else crud.get_save_by_id(db=self.db, save_id=self.save_id)
        query_str = "models.Calendar.save_id=='{}'".format(self.save_id)
        self.calendars: List[models.Calendar] = crud.get_calendar_by_save_id(db=self.db, save_id=self.save_id)

    def translate_game_type(self, game_type: str, game_name: str) -> str:
        """
        获取完整的比赛名
        :param game_type: 比赛类型
        :param game_name: 比赛名
        """
        if game_type == "league":
            return game_name
        if game_type == "cup32to16":
            return game_name + "32进16"
        if game_type == "cup16to8":
            return game_name + "16进8"
        if game_type == "cup8to4":
            return game_name + "8进4"
        if game_type == "cup4to2":
            return game_name + "半决赛"
        if game_type == "cup2to1":
            return game_name + "决赛"
        if game_type == "champions_group":
            return game_name + "小组赛"
        if game_type == "champions16to8":
            return game_name + "16进8"
        if game_type == "champions8to4":
            return game_name + "8进4"
        if game_type == "champions4to2":
            return game_name + "半决赛"
        if game_type == "champions2to1":
            return game_name + "决赛"

    def get_all_games_info_with_user(self):
        """
        获取所有与玩家俱乐部对抗的比赛信息
        """
        games_info = []
        for calendar in self.calendars:
            event = json.loads(calendar.event_str)
            if 'pve' in event.keys() and event["pve"]:
                game_info_dict = event["pve"][0]
                game_info = {
                    "date": calendar.date,
                    "game_name": self.translate_game_type(
                        game_type=game_info_dict['game_type'],
                        game_name=game_info_dict['game_name']),
                    "club1_name": crud.get_club_by_id(self.db, game_info_dict["club_id"].split(',')[0]).name,
                    "club2_name": crud.get_club_by_id(self.db, game_info_dict["club_id"].split(',')[1]).name
                }
                games_info.append(game_info)
        return games_info

    def get_incoming_games(self, cur_date_str: str):
        """
        获取未进行的比赛
        """
        cur_date = utils.Date(cur_date_str)
        games_info = self.get_all_games_info_with_user()
        return [g for g in games_info if utils.Date(g["date"]).date > cur_date.date]
