import json
from typing import List
from sqlalchemy.orm import Session

import crud
import models
from utils import Date, utils, logger
from modules import game_app


class NextTurner:
    def __init__(self, db: Session, save_id: int):
        self.db = db
        self.save_id = save_id
        self.save_model = crud.get_save_by_id(db=self.db, save_id=self.save_id)
        self.date = None

    def plus_days(self):
        date = Date(self.save_model.time)
        date.plus_days(1)
        self.save_model.time = str(date)
        self.db.commit()
        self.date = date

    def check(self):
        self.plus_days()
        logger.info(str(self.date))
        query_str = "and_(models.Calendar.save_id=='{}', models.Calendar.date=='{}')".format(
            self.save_model.id, str(self.date))
        calendars: List[models.Calendar] = crud.get_calendars_by_attri(db=self.db, query_str=query_str)
        total_events = dict()
        for calendar in calendars:
            event = json.loads(calendar.event_str)
            total_events = utils.merge_dict_with_list_items(total_events, event)
        if 'pve' in total_events.keys():
            self.pve_starter(total_events['pve'])
        if 'eve' in total_events.keys():
            self.eve_starter(total_events['eve'])
        if 'transfer' in total_events.keys():
            self.transfer_starter(total_events['transfer'])

    def eve_starter(self, eve: list):
        for game in eve:
            clubs_id = game['club_id'].split(',')
            tactic_adjustor = game_app.TacticAdjustor(db=self.db,
                                                      club1_id=clubs_id[0], club2_id=clubs_id[1],
                                                      player_club_id=self.save_model.player_club_id,
                                                      save_id=self.save_model.id)
            tactic_adjustor.adjust()
            # 开始模拟比赛
            game_eve = game_app.GameEvE(db=self.db,
                                        club1_id=clubs_id[0], club2_id=clubs_id[1],
                                        date=self.date,
                                        game_name=game['game_name'],
                                        game_type=game['game_type'],
                                        season=self.save_model.season,
                                        save_id=self.save_model.id)
            name1, name2, score1, score2 = game_eve.start()
            logger.info("{}: {} {}:{} {}".format(game['game_name'], name1, score1, score2, name2))

    def pve_starter(self, pve: list):
        # 暂时跟eve作相同处理
        self.eve_starter(pve)

    def transfer_starter(self, transfer: list):
        pass
