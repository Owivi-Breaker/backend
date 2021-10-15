import crud
import models
import schemas
from modules import computed_data_app
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
        self.generate_champions_league_games(game_type='champions_group')
        self.generate_transfer_days()
        self.generate_next_calendar()
        self.generate_uncertain_games()
        self.generate_promote_n_relegate_day()

        self.save_in_db()

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
        """
        将self.data中的字典数据转换成字符
        """
        for key, value in self.data.items():
            self.data[key] = json.dumps(
                value, ensure_ascii=False).encode('utf8')

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
                    one_game_dict['game_name'] = league_model.name
                    one_game_dict["game_type"] = 'league'
                    one_game_dict["club_id"] = ",".join(
                        [str(game[0].id), str(game[1].id)])
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
                if league_model.name == '欧洲地区联赛' or league_model.name == '其他地区联赛':
                    continue
                if not league_model.upper_league:
                    # 生成一个联赛的杯赛赛事
                    lower_league = crud.get_league_by_id(
                        db=self.db, league_id=league_model.lower_league)

                    # 把参赛俱乐部数量填充到32支：所有一级联赛俱乐部+部分二级联赛俱乐部
                    if self.save_model.season == 1:
                        # 如果是初始赛季
                        # 甲级联赛的所有俱乐部
                        clubs: List[models.Club] = league_model.clubs.copy()
                        # 低级联赛的12支队伍随便选
                        clubs.extend(random.sample(
                            lower_league.clubs, 12))
                    else:
                        computed_game = computed_data_app.ComputedGame(
                            db=self.db, save_id=self.save_id)
                        # 选择去年在甲级的所有俱乐部
                        top_clubs = computed_game.get_top_clubs_model(
                            num=20,
                            game_season=self.save_model.season - 1,
                            game_name=league_model.name,
                        )
                        clubs: List[models.Club] = top_clubs
                        # 按去年排名选择二级联赛的队伍
                        top_clubs = computed_game.get_top_clubs_model(
                            num=12,
                            game_season=self.save_model.season - 1,
                            game_name=lower_league.name,
                        )
                        clubs.extend(top_clubs)
                    if len(clubs) != 32:
                        logger.error('{} cup32to16 数量错误!'.format(league_model.name))
                    clubs_a = random.sample(clubs, 16)  # 随机挑一半
                    clubs_b = list(set(clubs) ^ set(clubs_a))  # 剩下另一半
                    two_days_schedule = [
                        game for game in zip(clubs_a, clubs_b)]
                    one_day_schedule = [
                        two_days_schedule[:8], two_days_schedule[8:]]
                    date = Date(int(year), 8, 24)
                    for games in one_day_schedule:
                        league_game = dict()
                        league_game["eve"] = []
                        league_game["pve"] = []
                        for game in games:
                            one_game_dict = dict()
                            one_game_dict["game_name"] = league_model.cup
                            one_game_dict["game_type"] = "cup32to16"
                            one_game_dict["club_id"] = ",".join(
                                [str(game[0].id), str(game[1].id)])
                            if game[0].id == self.save_model.player_club_id or \
                                    game[1].id == self.save_model.player_club_id:
                                league_game["pve"].append(one_game_dict)
                            else:
                                league_game["eve"].append(one_game_dict)
                        self.add_dict(str(date), league_game)
                        date.plus_days(1)
        elif game_type == "cup16to8":
            # 一般是在结束所有32进16的比赛后运行(8/26)
            for league_model in self.save_model.leagues:
                if league_model.name == '欧洲地区联赛' or league_model.name == '其他地区联赛':
                    continue
                if not league_model.upper_league:
                    # 生成一个联赛的16进8杯赛赛事
                    computed_game = computed_data_app.ComputedGame(
                        db=self.db, save_id=self.save_id)
                    clubs_id = computed_game.get_game_winners(
                        season=self.save_model.season,
                        game_type='cup32to16',
                        game_name=league_model.cup
                    )
                    if len(clubs_id) != 16:
                        logger.error('cup16to8 数量错误!')
                    clubs_a = random.sample(clubs_id, 8)  # 随机挑一半
                    clubs_b = list(set(clubs_id) ^ set(clubs_a))  # 剩下另一半
                    two_days_schedule = [
                        game for game in zip(clubs_a, clubs_b)]
                    one_day_schedule = [
                        two_days_schedule[:4], two_days_schedule[4:]]
                    date = Date(int(year), 12, 7)
                    for games in one_day_schedule:
                        league_game = dict()
                        league_game["eve"] = []
                        league_game["pve"] = []
                        for game in games:
                            one_game_dict = dict()
                            one_game_dict["game_name"] = league_model.cup
                            one_game_dict["game_type"] = "cup16to8"
                            one_game_dict["club_id"] = ",".join(
                                [str(game[0]), str(game[1])])
                            if game[0] == self.save_model.player_club_id or \
                                    game[1] == self.save_model.player_club_id:
                                league_game["pve"].append(one_game_dict)
                            else:
                                league_game["eve"].append(one_game_dict)
                        self.add_dict(str(date), league_game)
                        date.plus_days(1)
        elif game_type == "cup8to4":
            # 一般是在结束所有16进8的比赛后运行(12/9)
            for league_model in self.save_model.leagues:
                if league_model.name == '欧洲地区联赛' or league_model.name == '其他地区联赛':
                    continue
                if not league_model.upper_league:
                    # 生成一个联赛的8进4杯赛赛事
                    computed_game = computed_data_app.ComputedGame(
                        db=self.db, save_id=self.save_id)
                    clubs_id = computed_game.get_game_winners(
                        season=self.save_model.season,
                        game_type='cup16to8',
                        game_name=league_model.cup
                    )
                    if len(clubs_id) != 8:
                        logger.error('cup8to4 数量错误!')
                    clubs_a = random.sample(clubs_id, 4)  # 随机挑一半
                    clubs_b = list(set(clubs_id) ^ set(clubs_a))  # 剩下另一半
                    two_days_schedule = [
                        game for game in zip(clubs_a, clubs_b)]
                    one_day_schedule = [
                        two_days_schedule[:2], two_days_schedule[2:]]
                    date = Date(int(year) + 1, 2, 1)  # 注意是下一年了！
                    for games in one_day_schedule:
                        league_game = dict()
                        league_game["eve"] = []
                        league_game["pve"] = []
                        for game in games:
                            one_game_dict = dict()
                            one_game_dict["game_name"] = league_model.cup
                            one_game_dict["game_type"] = "cup8to4"
                            one_game_dict["club_id"] = ",".join(
                                [str(game[0]), str(game[1])])
                            if game[0] == self.save_model.player_club_id or \
                                    game[1] == self.save_model.player_club_id:
                                league_game["pve"].append(one_game_dict)
                            else:
                                league_game["eve"].append(one_game_dict)
                        self.add_dict(str(date), league_game)
                        date.plus_days(1)
        elif game_type == "cup4to2":
            # 一般是在结束所有8进4的比赛后运行(2/3)
            for league_model in self.save_model.leagues:
                if league_model.name == '欧洲地区联赛' or league_model.name == '其他地区联赛':
                    continue
                if not league_model.upper_league:
                    # 生成一个联赛的4进2杯赛赛事
                    computed_game = computed_data_app.ComputedGame(
                        db=self.db, save_id=self.save_id)
                    clubs_id = computed_game.get_game_winners(
                        season=self.save_model.season,
                        game_type='cup8to4',
                        game_name=league_model.cup
                    )
                    if len(clubs_id) != 4:
                        logger.error('cup4to2 数量错误!')
                    clubs_a = random.sample(clubs_id, 2)  # 随机挑一半
                    clubs_b = list(set(clubs_id) ^ set(clubs_a))  # 剩下另一半
                    two_days_schedule = [
                        game for game in zip(clubs_a, clubs_b)]
                    one_day_schedule = [
                        two_days_schedule[:1], two_days_schedule[1:]]
                    date = Date(int(year), 3, 15)
                    for games in one_day_schedule:
                        league_game = dict()
                        league_game["eve"] = []
                        league_game["pve"] = []
                        for game in games:
                            one_game_dict = dict()
                            one_game_dict["game_name"] = league_model.cup
                            one_game_dict["game_type"] = "cup4to2"
                            one_game_dict["club_id"] = ",".join(
                                [str(game[0]), str(game[1])])
                            if game[0] == self.save_model.player_club_id or \
                                    game[1] == self.save_model.player_club_id:
                                league_game["pve"].append(one_game_dict)
                            else:
                                league_game["eve"].append(one_game_dict)
                        self.add_dict(str(date), league_game)
                        date.plus_days(1)
        elif game_type == "cup2to1":
            # 一般是在结束所有4进2的比赛后运行(3/17)
            for league_model in self.save_model.leagues:
                if league_model.name == '欧洲地区联赛' or league_model.name == '其他地区联赛':
                    continue
                if not league_model.upper_league:
                    # 生成一个联赛的2进1杯赛赛事
                    computed_game = computed_data_app.ComputedGame(
                        db=self.db, save_id=self.save_id)
                    clubs_id = computed_game.get_game_winners(
                        season=self.save_model.season,
                        game_type='cup4to2',
                        game_name=league_model.cup
                    )
                    if len(clubs_id) != 2:
                        logger.error('cup2to1 数量错误!')
                    date = Date(int(year), 4, 20)
                    league_game = dict()
                    league_game["eve"] = []
                    league_game["pve"] = []

                    one_game_dict = dict()
                    one_game_dict["game_name"] = league_model.cup
                    one_game_dict["game_type"] = "cup2to1"
                    one_game_dict["club_id"] = ",".join(
                        [str(clubs_id[0]), str(clubs_id[1])])
                    if clubs_id[0] == self.save_model.player_club_id or \
                            clubs_id[1] == self.save_model.player_club_id:
                        league_game["pve"].append(one_game_dict)
                    else:
                        league_game["eve"].append(one_game_dict)
                    self.add_dict(str(date), league_game)
        else:
            logger.error("无{}赛程".format(game_type))
        logger.info('{}比赛日程表生成'.format(game_type))

    def generate_champions_league_games(self, game_type: str):
        """
        生成冠军联赛赛程
        :param game_type: 比赛类型
        :return:
        """
        year, month, day = self.save_model.time.split('-')
        if game_type == "champions_group":
            if self.save_model.season == 1:
                # 第一赛季无欧冠
                logger.debug("第一赛季无欧冠")
                return
            # 选32支俱乐部
            else:
                clubs_model_list: List[models.Club] = []
                computed_game = computed_data_app.ComputedGame(
                    db=self.db, save_id=self.save_id)
                lower_the_first: List[models.Club] = []
                for league_model in self.save_model.leagues:
                    if league_model.name == '其他地区联赛':
                        continue
                    if league_model.name == '欧洲地区联赛':
                        # 欧洲地区联赛前五名
                        top_clubs = computed_game.get_top_clubs_model(
                            num=5,
                            game_season=self.save_model.season - 1,
                            game_name=league_model.name,
                        )
                        clubs_model_list.extend(top_clubs)
                    elif not league_model.upper_league and league_model.lower_league:
                        # 每个甲级联赛前五名
                        top_clubs = computed_game.get_top_clubs_model(
                            num=5,
                            game_season=self.save_model.season - 1,
                            game_name=league_model.name,
                        )
                        clubs_model_list.extend(top_clubs)
                    else:
                        # 保存每个乙级联赛第一名
                        top_clubs = computed_game.get_top_clubs_model(
                            num=1,
                            game_season=self.save_model.season - 1,
                            game_name=league_model.name,
                        )
                        lower_the_first.append(top_clubs[-1])
                # 乙级联赛声望最高的两个第一名
                lower_the_first = sorted(
                    lower_the_first, key=lambda x: x.reputation, reverse=True)
                clubs_model_list.extend(lower_the_first[:2])
            if len(clubs_model_list) != 32:
                logger.error("champions_league_group 数量错误!")
            # 添加赛程
            random.shuffle(clubs_model_list)  # 乱序
            for i in range(8):
                # 八个小组，每组四支队伍
                group = clubs_model_list[(i * 4):(i * 4 + 4)]
                # 构建比赛日程
                group_a = group[:2]
                group_b = group[2:]
                schedule = []  # 比赛赛程
                for _ in range((len(group) - 1)):
                    # 前半赛季的比赛
                    schedule.append([game for game in zip(group_a, group_b)])
                    group_a.insert(1, group_b.pop(0))
                    group_b.append(group_a.pop(-1))
                schedule_reverse = []  # 主客场对调的后半赛季赛程
                for games in schedule:
                    schedule_reverse.append(
                        [tuple(list(x)[::-1]) for x in games])
                schedule.extend(schedule_reverse)

                date = Date(int(year), 9, 15)
                for games in schedule:
                    league_game = dict()
                    league_game["eve"] = []
                    league_game["pve"] = []
                    for game in games:
                        one_game_dict = dict()
                        one_game_dict["game_name"] = 'champions_league'
                        one_game_dict["game_type"] = "champions_group{}".format(
                            i + 1)
                        one_game_dict["club_id"] = ",".join(
                            [str(game[0].id), str(game[1].id)])
                        if game[0].id == self.save_model.player_club_id or \
                                game[1].id == self.save_model.player_club_id:
                            league_game["pve"].append(one_game_dict)
                        else:
                            league_game["eve"].append(one_game_dict)
                    self.add_dict(str(date), league_game)
                    date.plus_days(14)
        elif game_type == "champions16to8":
            if self.save_model.season == 1:
                # 第一赛季无欧冠
                return
            # 一般是在结束所有小组赛比赛后运行(11/25)
            computed_game = computed_data_app.ComputedGame(
                db=self.db, save_id=self.save_id)
            clubs: List[models.Club] = []
            for i in range(8):
                # 八个小组头两名出线
                top_clubs = computed_game.get_top_clubs_model(
                    num=2,
                    game_season=self.save_model.season,
                    game_name='champions_league',
                    game_type='champions_group{}'.format(i + 1),
                )
                clubs.extend(top_clubs)
            if len(clubs) != 16:
                logger.error('champions16to8 数量错误!')

            clubs_a = random.sample(clubs, 8)  # 随机挑一半
            clubs_b = list(set(clubs) ^ set(clubs_a))  # 剩下另一半
            schedule = [game for game in zip(clubs_a, clubs_b)]

            count = 1
            for i in range(4):
                league_game = dict()
                league_game["eve"] = []
                league_game["pve"] = []
                for game in schedule[(i * 2):(i * 2 + 2)]:
                    one_game_dict = dict()
                    one_game_dict["game_name"] = 'champions_league'
                    one_game_dict["game_type"] = "champions16to8_{}".format(
                        count)
                    one_game_dict["club_id"] = ",".join(
                        [str(game[0].id), str(game[1].id)])
                    if game[0].id == self.save_model.player_club_id or \
                            game[1].id == self.save_model.player_club_id:
                        league_game["pve"].append(one_game_dict)
                    else:
                        league_game["eve"].append(one_game_dict)
                    count += 1
                if i == 0:
                    self.add_dict(str(Date(int(year), 12, 29)), league_game)
                elif i == 1:
                    self.add_dict(str(Date(int(year), 12, 30)), league_game)
                elif i == 2:
                    self.add_dict(str(Date(int(year) + 1, 1, 5)), league_game)
                elif i == 3:
                    self.add_dict(str(Date(int(year) + 1, 1, 6)), league_game)
                else:
                    logger.error('日期错误！')
            # 两队反一反，打第二轮的比赛
            count = 1
            for i in range(4):
                league_game = dict()
                league_game["eve"] = []
                league_game["pve"] = []
                for game in schedule[(i * 2):(i * 2 + 2)]:
                    one_game_dict = dict()
                    one_game_dict["game_name"] = 'champions_league'
                    one_game_dict["game_type"] = "champions16to8_{}".format(
                        count)
                    one_game_dict["club_id"] = ",".join(
                        [str(game[1].id), str(game[0].id)])
                    if game[0].id == self.save_model.player_club_id or \
                            game[1].id == self.save_model.player_club_id:
                        league_game["pve"].append(one_game_dict)
                    else:
                        league_game["eve"].append(one_game_dict)
                    count += 1
                if i == 0:
                    self.add_dict(str(Date(int(year) + 1, 1, 12)), league_game)
                elif i == 1:
                    self.add_dict(str(Date(int(year) + 1, 1, 13)), league_game)
                elif i == 2:
                    self.add_dict(str(Date(int(year) + 1, 1, 19)), league_game)
                elif i == 3:
                    self.add_dict(str(Date(int(year) + 1, 1, 20)), league_game)
                else:
                    logger.error('日期错误！')
        elif game_type == "champions8to4":
            if self.save_model.season == 1:
                # 第一赛季无欧冠
                return
            # 一般是在结束16to8比赛后运行(1/21)
            # computed_game = computed_data_app.ComputedGame(db=self.db, save_id=self.save_id)
            clubs: List[int] = []
            for i in range(8):
                # TODO 把挑选两场比赛的分数最高者的逻辑写进ComputedGame中
                query_str = "and_(models.Game.save_id=='{}',models.Game.season=='{}', models.Game.type=='{}')".format(
                    self.save_id, self.save_model.season, 'champions16to8_{}'.format(i + 1))
                games = crud.get_games_by_attri(
                    db=self.db, query_str=query_str)
                score_dict = dict()
                for game in games:
                    score_dict[game.teams[0].club_id] = score_dict.get(
                        game.teams[0].club_id, 0)
                    score_dict[game.teams[0].club_id] += game.teams[0].score
                    score_dict[game.teams[1].club_id] = score_dict.get(
                        game.teams[1].club_id, 0)
                    score_dict[game.teams[1].club_id] += game.teams[1].score
                if score_dict[games[0].teams[0].club_id] > score_dict[games[0].teams[1].club_id]:
                    clubs.append(games[0].teams[0].club_id)
                else:
                    clubs.append(games[0].teams[1].club_id)
            if len(clubs) != 8:
                logger.error('champions8to4" 数量错误!')

            clubs_a = random.sample(clubs, 4)  # 随机挑一半
            clubs_b = list(set(clubs) ^ set(clubs_a))  # 剩下另一半
            schedule = [game for game in zip(clubs_a, clubs_b)]

            count = 1
            for i in range(2):
                league_game = dict()
                league_game["eve"] = []
                league_game["pve"] = []
                for game in schedule[(i * 2):(i * 2 + 2)]:
                    one_game_dict = dict()
                    one_game_dict["game_name"] = 'champions_league'
                    one_game_dict["game_type"] = "champions8to4_{}".format(
                        count)
                    one_game_dict["club_id"] = ",".join(
                        [str(game[0]), str(game[1])])
                    if game[0] == self.save_model.player_club_id or \
                            game[1] == self.save_model.player_club_id:
                        league_game["pve"].append(one_game_dict)
                    else:
                        league_game["eve"].append(one_game_dict)
                    count += 1
                if i == 0:
                    self.add_dict(str(Date(int(year), 2, 23)), league_game)
                elif i == 1:
                    self.add_dict(str(Date(int(year), 2, 24)), league_game)
                else:
                    logger.error('日期错误！')
            # 两队反一反，打第二轮的比赛
            count = 1
            for i in range(2):
                league_game = dict()
                league_game["eve"] = []
                league_game["pve"] = []
                for game in schedule[(i * 2):(i * 2 + 2)]:
                    one_game_dict = dict()
                    one_game_dict["game_name"] = 'champions_league'
                    one_game_dict["game_type"] = "champions8to4_{}".format(
                        count)
                    one_game_dict["club_id"] = ",".join(
                        [str(game[1]), str(game[0])])
                    if game[0] == self.save_model.player_club_id or \
                            game[1] == self.save_model.player_club_id:
                        league_game["pve"].append(one_game_dict)
                    else:
                        league_game["eve"].append(one_game_dict)
                    count += 1
                if i == 0:
                    self.add_dict(str(Date(int(year), 3, 2)), league_game)
                elif i == 1:
                    self.add_dict(str(Date(int(year), 3, 3)), league_game)
                else:
                    logger.error('日期错误！')
        elif game_type == "champions4to2":
            if self.save_model.season == 1:
                # 第一赛季无欧冠
                return
            # 一般是在结束8to4比赛后运行(3/4)
            # computed_game = computed_data_app.ComputedGame(db=self.db, save_id=self.save_id)
            clubs: List[int] = []
            for i in range(4):
                # TODO 把挑选两场比赛的分数最高者的逻辑写进ComputedGame中
                query_str = "and_(models.Game.save_id=='{}',models.Game.season=='{}', models.Game.type=='{}')".format(
                    self.save_id, self.save_model.season, 'champions8to4_{}'.format(i + 1))
                games = crud.get_games_by_attri(
                    db=self.db, query_str=query_str)
                score_dict = dict()
                for game in games:
                    score_dict[game.teams[0].club_id] = score_dict.get(
                        game.teams[0].club_id, 0)
                    score_dict[game.teams[0].club_id] += game.teams[0].score
                    score_dict[game.teams[1].club_id] = score_dict.get(
                        game.teams[1].club_id, 0)
                    score_dict[game.teams[1].club_id] += game.teams[1].score
                if score_dict[games[0].teams[0].club_id] > score_dict[games[0].teams[1].club_id]:
                    clubs.append(games[0].teams[0].club_id)
                else:
                    clubs.append(games[0].teams[1].club_id)
            if len(clubs) != 4:
                logger.error('champions4to2" 数量错误!')

            clubs_a = random.sample(clubs, 2)  # 随机挑一半
            clubs_b = list(set(clubs) ^ set(clubs_a))  # 剩下另一半
            schedule = [game for game in zip(clubs_a, clubs_b)]

            count = 1
            for game in schedule:
                # 每天打一场
                league_game = dict()
                league_game["eve"] = []
                league_game["pve"] = []
                one_game_dict = dict()
                one_game_dict["game_name"] = 'champions_league'
                one_game_dict["game_type"] = "champions4to2_{}".format(count)
                one_game_dict["club_id"] = ",".join(
                    [str(game[0]), str(game[1])])
                if game[0] == self.save_model.player_club_id or \
                        game[1] == self.save_model.player_club_id:
                    league_game["pve"].append(one_game_dict)
                else:
                    league_game["eve"].append(one_game_dict)

                if count == 1:
                    self.add_dict(str(Date(int(year), 3, 30)), league_game)
                elif count == 2:
                    self.add_dict(str(Date(int(year), 3, 31)), league_game)
                count += 1

            # 两队反一反，打第二轮的比赛
            count = 1
            for game in schedule:
                # 每天打一场
                league_game = dict()
                league_game["eve"] = []
                league_game["pve"] = []
                one_game_dict = dict()
                one_game_dict["game_name"] = 'champions_league'
                one_game_dict["game_type"] = "champions4to2_{}".format(count)
                one_game_dict["club_id"] = ",".join(
                    [str(game[1]), str(game[0])])
                if game[0] == self.save_model.player_club_id or \
                        game[1] == self.save_model.player_club_id:
                    league_game["pve"].append(one_game_dict)
                else:
                    league_game["eve"].append(one_game_dict)

                if count == 1:
                    self.add_dict(str(Date(int(year), 4, 6)), league_game)
                elif count == 2:
                    self.add_dict(str(Date(int(year), 4, 7)), league_game)
                count += 1
        elif game_type == "champions2to1":
            if self.save_model.season == 1:
                # 第一赛季无欧冠
                return
            # 一般是在结束4to2比赛后运行(4/8)
            clubs: List[int] = []
            for i in range(2):
                # TODO 把挑选两场比赛的分数最高者的逻辑写进ComputedGame中
                query_str = "and_(models.Game.save_id=='{}',models.Game.season=='{}', models.Game.type=='{}')".format(
                    self.save_id, self.save_model.season, 'champions4to2_{}'.format(i + 1))
                games = crud.get_games_by_attri(
                    db=self.db, query_str=query_str)
                score_dict = dict()
                for game in games:
                    score_dict[game.teams[0].club_id] = score_dict.get(
                        game.teams[0].club_id, 0)
                    score_dict[game.teams[0].club_id] += game.teams[0].score
                    score_dict[game.teams[1].club_id] = score_dict.get(
                        game.teams[1].club_id, 0)
                    score_dict[game.teams[1].club_id] += game.teams[1].score
                if score_dict[games[0].teams[0].club_id] > score_dict[games[0].teams[1].club_id]:
                    clubs.append(games[0].teams[0].club_id)
                else:
                    clubs.append(games[0].teams[1].club_id)
            if len(clubs) != 2:
                logger.error('champions2to1" 数量错误!')

            league_game = dict()
            league_game["eve"] = []
            league_game["pve"] = []
            one_game_dict = dict()
            one_game_dict["game_name"] = 'champions_league'
            one_game_dict["game_type"] = "champions2to1"
            one_game_dict["club_id"] = ",".join([str(clubs[0]), str(clubs[1])])
            if clubs[0] == self.save_model.player_club_id or \
                    clubs[1] == self.save_model.player_club_id:
                league_game["pve"].append(one_game_dict)
            else:
                league_game["eve"].append(one_game_dict)
            self.add_dict(str(Date(int(year), 5, 7)), league_game)
        else:
            logger.error("无{}赛程".format(game_type))
        logger.info('{}比赛日程表生成'.format(game_type))

    def generate_transfer_days(self):
        """
        生成转会日
        """
        year, month, day = self.save_model.time.split('-')
        # 夏窗
        date_range = utils.date_range(int(year), 6, 1, int(year), 8, 31)
        for date_str in date_range:
            transfer_dict = {"transfer": []}
            self.add_dict(date_str, transfer_dict)
        # 冬窗
        date_range = utils.date_range(
            int(year) + 1, 1, 1, int(year) + 1, 1, 31)
        for date_str in date_range:
            transfer_dict = {"transfer": []}
            self.add_dict(date_str, transfer_dict)

    def generate_next_calendar(self):
        """
        生成下赛季的日程表日
        """
        year, month, day = self.save_model.time.split('-')
        date = Date(int(year) + 1, 5, 29)
        next_calendar_dict = {'next_calendar': []}
        self.add_dict(str(date), next_calendar_dict)

    def generate_uncertain_games(self):
        """
        生成未决定的赛事日
        """
        year, month, day = self.save_model.time.split('-')
        # 杯赛
        date = Date(int(year), 8, 26)  # cup16to8
        game_dict = {'game_generation': ['cup16to8']}
        self.add_dict(str(date), game_dict)
        date = Date(int(year), 12, 9)  # cup8to4
        game_dict = {'game_generation': ['cup8to4']}
        self.add_dict(str(date), game_dict)
        date = Date(int(year) + 1, 2, 3)  # cup4to2
        game_dict = {'game_generation': ['cup4to2']}
        self.add_dict(str(date), game_dict)
        date = Date(int(year) + 1, 3, 17)  # cup2to1
        game_dict = {'game_generation': ['cup2to1']}
        self.add_dict(str(date), game_dict)
        # 冠军联赛
        if self.save_model.season != 1:
            date = Date(int(year), 11, 25)  # champions16to8
            game_dict = {'game_generation': ['champions16to8']}
            self.add_dict(str(date), game_dict)
            date = Date(int(year) + 1, 1, 21)  # champions8to4
            game_dict = {'game_generation': ['champions8to4']}
            self.add_dict(str(date), game_dict)
            date = Date(int(year) + 1, 3, 4)  # champions4to2
            game_dict = {'game_generation': ['champions4to2']}
            self.add_dict(str(date), game_dict)
            date = Date(int(year) + 1, 4, 8)  # champions2to1
            game_dict = {'game_generation': ['champions2to1']}
            self.add_dict(str(date), game_dict)

    def generate_promote_n_relegate_day(self):
        """
        生成联赛升降日
        """
        year, month, day = self.save_model.time.split('-')
        date = Date(int(year) + 1, 5, 20)
        promote_n_relegate_dict = {'promote_n_relegate': []}
        self.add_dict(str(date), promote_n_relegate_dict)

    def save_in_db(self):
        """
        将生成的日程表数据存至数据库
        """
        self.turn_dict2str()
        for key, value in self.data.items():
            data_schemas = schemas.CalendarCreate(created_time=datetime.datetime.now(),
                                                  date=key, event_str=value)
            calendar_model = crud.create_calendar(
                db=self.db, calendar=data_schemas)
            crud.update_calendar(db=self.db, calendar_id=calendar_model.id,
                                 attri={"save_id": self.save_id})
        self.data = dict()  # 清空数据
