import json
from typing import List
from sqlalchemy.orm import Session

import crud
import models
from utils import Date
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
        query_str = "and_(models.Calendar.save_id=='{}', models.Calendar.date=='{}')".format(
            self.save_model.id, str(self.date))
        calendars: List[models.Calendar] = crud.get_calendars_by_attri(db=self.db, query_str=query_str)
        for calendar in calendars:
            event = json.loads(calendar.event_str)
            if 'eve' in event.keys():
                self.eve_starter()
            if 'pve' in event.keys():
                self.pve_starter()
            if 'transfer' in event.keys():
                self.transfer_starter()

    def eve_starter(self):
        pass

    def pve_starter(self):
        pass

    def transfer_starter(self):
        pass
