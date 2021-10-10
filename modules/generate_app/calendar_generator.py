import crud
import models
import schemas
from utils import Date, logger, utils

from sqlalchemy.orm import Session
import random
from typing import List, Tuple
import json
import datetime


class CalendarGenerator:
    # 日程事项生成器
    def __init__(self, db: Session, save_id: int):
        self.db = db
        self.data = dict()
        self.save_id = save_id
        self.save_model = crud.get_save_by_id(db=self.db, save_id=self.save_id)

    def generate(self):
        """
        在赛季开始时，生成日程表
        :return: 日程表实例
        """
        self.generate_league_games()
        self.generate_cup_games(game_type="cup32to16")
        self.generate_transfer_days()
        self.turn_dict2str()

        self.save_in_db()
        self.data = dict()  # 清空数据

    def add_dict(self, date: str, target_dict: dict):
        """
        为指定日期加上一个事项字典
        :param date: 日期
        :param target_dict: 事项字典
        :return:
        """
        if date not in self.data.keys():
            self.data[date] = dict()
        for key, value in target_dict.items():
            if key in self.data[date]:
                if isinstance(value, list):
                    self.data[date][key].extend(value)
                else:
                    self.data[date][key] = value
            else:
                self.data[date][key] = value

    def turn_dict2str(self):
        for key, value in self.data.items():
            self.data[key] = json.dumps(value)

    def generate_league_games(self):
        """
        生成联赛赛程
        """
        year, month, day = self.save_model.time.split('-')
        # 记录联赛日
        for league_model in self.save_model.leagues:
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
                league_game["pve"] = []
                for game in games:
                    one_game_dict = dict()
                    one_game_dict["game_type"] = league_model.name
                    one_game_dict["club_id"] = ",".join([str(game[0].id), str(game[1].id)])
                    if game[0].id == self.save_model.player_club_id or \
                            game[1].id == self.save_model.player_club_id:
                        league_game["pve"].append(one_game_dict)
                    else:
                        league_game["eve"].append(one_game_dict)
                self.add_dict(str(date), league_game)
                date.plus_days(7)

    def generate_cup_games(self, game_type: str):
        """
        :param game_type: 比赛类型
        生成杯赛赛程
        适用于两级联赛的杯赛
        """
        year, month, day = self.save_model.time.split('-')
        if game_type == "cup32to16":
            # 一般是在赛季开始初始化日程表时，生成32进16的赛事
            for league_model in self.save_model.leagues:
                if not league_model.upper_league:
                    # 生成一个联赛的杯赛赛事
                    lower_league = crud.get_league_by_id(db=self.db, league_id=league_model.lower_league)

                    clubs: List[models.Club] = league_model.clubs.copy()  # 参赛俱乐部
                    for club in lower_league.clubs:
                        # TODO 按排名选择二级联赛的队伍
                        # 把参赛俱乐部数量填充到32支：所有一级联赛俱乐部+部分二级联赛俱乐部
                        clubs.append(club)
                        if len(clubs) == 32:
                            break
                    clubs_a = random.sample(clubs, 16)  # 随机挑一半
                    clubs_b = list(set(clubs) ^ set(clubs_a))  # 剩下另一半
                    two_days_schedule = [game for game in zip(clubs_a, clubs_b)]
                    one_day_schedule = [two_days_schedule[:8], two_days_schedule[8:]]
                    date = Date(int(year), 8, 24)
                    for games in one_day_schedule:
                        league_game = dict()
                        league_game["eve"] = []
                        league_game["pve"] = []
                        for game in games:
                            one_game_dict = dict()
                            one_game_dict["game_type"] = "cup32to16"
                            one_game_dict["club_id"] = ",".join([str(game[0].id), str(game[1].id)])
                            if game[0].id == self.save_model.player_club_id or \
                                    game[1].id == self.save_model.player_club_id:
                                league_game["pve"].append(one_game_dict)
                            else:
                                league_game["eve"].append(one_game_dict)
                        self.add_dict(str(date), league_game)
                        date.plus_days(1)
        elif game_type == "16to8":
            for league_model in self.save_model.leagues:
                if not league_model.upper_league:
                    # 生成一个联赛的16进8杯赛赛事
                    # TODO 将筛选胜者的具体逻辑放在computed_data_app中
                    query_str = "and_(models.Game.season=='{}', models.Game.type=='{}')".format(
                        self.save_model.season, 'cup32to16')
                    games: List[models.Game] = crud.get_games_by_attri(db=self.db, query_str=query_str)
                    clubs_id: List[int] = []  # 参赛俱乐部
                    for game in games:
                        team1 = game.teams[0]
                        team2 = game.teams[0]
                        if team1.score > team2.score:
                            clubs_id.append(team1.club_id)
                        elif team1.score < team2.score:
                            clubs_id.append(team2.club_id)
                        else:
                            logger.error("淘汰赛平局！")
                    if len(clubs_id) != 16:
                        logger.error("参赛俱乐部不是16支！")

                    clubs_a = random.sample(clubs_id, 16)  # 随机挑一半
                    clubs_b = list(set(clubs_id) ^ set(clubs_a))  # 剩下另一半
                    two_days_schedule = [game for game in zip(clubs_a, clubs_b)]
                    one_day_schedule = [two_days_schedule[:8], two_days_schedule[8:]]
                    date = Date(int(year), 12, 7)
                    for schedule in one_day_schedule:
                        for games in schedule:
                            league_game = dict()
                            league_game["eve"] = []
                            league_game["pve"] = []
                            for game in games:
                                one_game_dict = dict()
                                one_game_dict["game_type"] = "cup16to8"
                                one_game_dict["club_id"] = ",".join([str(game[0]), str(game[1])])
                                if game[0] == self.save_model.player_club_id or \
                                        game[1] == self.save_model.player_club_id:
                                    league_game["pve"].append(one_game_dict)
                                else:
                                    league_game["eve"].append(one_game_dict)
                            self.add_dict(str(date), league_game)
                        date.plus_days(1)
        elif game_type == "cup8to4":
            pass
        elif game_type == "cup4to2":
            pass
        elif game_type == "cup2to1":
            pass
        else:
            logger.error("无{}赛程".format(game_type))

    def generate_champions_league_games(self, game_type: str):
        """
        生成冠军联赛赛程
        :param game_type: 比赛类型
        :return:
        """
        year, month, day = self.save_model.time.split('-')
        if game_type == "champions_league_group":
            # TODO 欸，没写呢
            # 一般是在赛季开始初始化日程表时，生成32进16的赛事
            for league_model in self.save_model.leagues:
                if not league_model.upper_league:
                    # 生成一个联赛的杯赛赛事
                    lower_league = crud.get_league_by_id(db=self.db, league_id=self.save_model.lower_league)

                    clubs: List[models.Club] = league_model.clubs  # 参赛俱乐部
                    for club in lower_league.clubs:
                        # 把参赛俱乐部数量填充到32支：所有一级联赛俱乐部+部分二级联赛俱乐部
                        clubs.append(club)
                        if len(clubs) == 32:
                            break
                    clubs_a = random.sample(clubs, 16)  # 随机挑一半
                    clubs_b = list(set(clubs) ^ set(clubs_a))  # 剩下另一半
                    two_days_schedule = [game for game in zip(clubs_a, clubs_b)]
                    one_day_schedule = [two_days_schedule[:8], two_days_schedule[8:]]
                    date = Date(int(year), 8, 24)
                    for schedule in one_day_schedule:
                        for games in schedule:
                            league_game = dict()
                            league_game["eve"] = []
                            league_game["pve"] = []
                            for game in games:
                                one_game_dict = dict()
                                one_game_dict["game_type"] = "cup32to16"
                                one_game_dict["club_id"] = ",".join([str(game[0].id), str(game[1].id)])
                                if game[0].id == self.save_model.player_club_id or \
                                        game[1].id == self.save_model.player_club_id:
                                    league_game["pve"].append(one_game_dict)
                                else:
                                    league_game["eve"].append(one_game_dict)
                            self.add_dict(str(date), league_game)
                        date.plus_days(1)

    def generate_transfer_days(self):
        """
        生成转会日
        :return:
        """
        year, month, day = self.save_model.time.split('-')
        # 夏窗
        date_range = utils.date_range(int(year), 6, 1, int(year), 8, 31)
        for date_str in date_range:
            transfer_dict = {"transfer": []}
            self.add_dict(date_str, transfer_dict)
        # 冬窗
        date_range = utils.date_range(int(year) + 1, 1, 1, int(year) + 1, 1, 31)
        for date_str in date_range:
            transfer_dict = {"transfer": []}
            self.add_dict(date_str, transfer_dict)

    def save_in_db(self):
        """
        将生成的日程表数据存至数据库
        """
        for key, value in self.data.items():
            data_schemas = schemas.CalendarCreate(created_time=datetime.datetime.now(),
                                                  date=key, event_str=value)
            calendar_model = crud.create_calendar(db=self.db, calendar=data_schemas)
            crud.update_calendar(db=self.db, calendar_id=calendar_model.id,
                                 attri={"save_id": self.save_id})
