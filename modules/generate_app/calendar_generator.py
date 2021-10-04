import crud
import models
import schemas
from utils import Date, logger

from sqlalchemy.orm import Session
import random
from typing import List, Tuple
import json
import datetime


class CalendarGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.data = dict()

    def generate(self, save_id: int):
        """
        生成日程表
        :param save_id:
        :return: 日程表实例
        """
        self.generate_league_games(save_id)
        self.turn_dict2str()

        self.save_in_db(save_id)

    def add_dict(self, date: str, target_dict: dict):
        """
        为指定日期加上一个事项字典
        :param date: 日期
        :param target_dict: 事项字典
        :return:
        """
        if date not in self.data.keys():
            self.data[date] = dict()
        self.data[date].update(target_dict)

    def turn_dict2str(self):
        for key, value in self.data.items():
            self.data[key] = json.dumps(value)

    def generate_league_games(self, save_id: int):
        """
        生成联赛赛程
        :param save_id: 存档id
        """
        save_model = crud.get_save_by_id(db=self.db, save_id=save_id)
        year, month, day = save_model.time.split('-')
        # 记录联赛日
        for league_model in save_model.leagues:
            clubs: List[models.Club] = league_model.clubs
            clubs_a = random.sample(clubs, len(clubs) // 2)  # 随机挑一半
            clubs_b = list(set(clubs) ^ set(clubs_a))  # 剩下另一半
            schedule = []  # 比赛赛程
            for _ in range((len(clubs) - 1)):
                # 前半赛季的比赛
                schedule.append([game for game in zip(clubs_a, clubs_b)])
                clubs_a.insert(1, clubs_b.pop(0))
                clubs_b.append(clubs_a.pop(-1))
            schedule_reverse = []  # 主客场对调的后半赛季赛程
            for games in schedule:
                schedule_reverse.append([tuple(list(x)[::-1]) for x in games])
            schedule.extend(schedule_reverse)
            # 联赛从 8.14 到次年 4.30
            date = Date(int(year), 8, 14)
            for games in schedule:
                league_game = dict()
                league_game["eve"] = []
                for game in games:
                    league_game["eve"].append(','.join([str(game[0].id), str(game[1].id)]))
                self.add_dict(str(date), league_game)
                date.plus_days(7)

    def generate_cup_games(self, save_id: int):
        """
        生成杯赛赛程
        :param save_id:
        :return:
        """
        pass

    def generate_champions_League_games(self, save_id: int):
        pass

    def save_in_db(self, save_id: int):
        """
        :param save_id: 存档id
        将生成的日程表数据存至数据库
        """
        for key, value in self.data.items():
            data_schemas = schemas.CalendarCreate(created_time=datetime.datetime.now(),
                                                  date=key, event_str=value)
            calendar_model = crud.create_calendar(db=self.db, calendar=data_schemas)
            crud.update_calendar(db=self.db, calendar_id=calendar_model.id,
                                 attri={"save_id": save_id})
