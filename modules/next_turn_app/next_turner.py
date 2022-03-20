import datetime
import json
import time
from typing import List
from sqlalchemy.orm import Session, joinedload
import threading

import crud
import models
import schemas
from modules.computed_data_app import computed_game
from utils import Date, utils, logger
from modules import game_app, generate_app, computed_data_app, transfer_app


def crew_salary_check(db: Session, club_id: int):
    sum_salary = 0
    club = crud.get_club_by_id(db=db, club_id=club_id)
    sum_salary += 2 ** (club.assistant - 1) * 5
    sum_salary += 2 ** (club.doctor - 1) * 5
    sum_salary += 2 ** (club.negotiator - 1) * 5
    sum_salary += 2 ** (club.scout - 1) * 5
    return sum_salary


class NextTurner:
    """
    回合行进的入口类
    """

    def __init__(self, db: Session, save_id: int, skip: bool = False):
        self.db = db
        self.save_id = save_id
        self.save_model = crud.get_save_by_id(db=self.db, save_id=self.save_id)
        self.date: str = ''
        self.skip = skip

    def plus_days(self):
        """
        世界时间加一天
        """
        date = Date(self.save_model.date)
        date.plus_days(1)
        self.save_model.date = str(date)
        self.db.commit()
        self.date = str(date)

    def get_total_events(self) -> dict:
        """
        获取字典格式的日程表
        """
        # 一天的事项不一定只存在一条calendar记录中
        query_str = "and_(models.Calendar.save_id=='{}', models.Calendar.date=='{}')".format(
            self.save_model.id, self.date)
        calendars: List[models.Calendar] = crud.get_calendars_by_attri(db=self.db, query_str=query_str)
        total_events = dict()
        for calendar in calendars:
            event = json.loads(calendar.event_str)
            total_events = utils.merge_dict_with_list_items(total_events, event)
        return total_events

    def check_if_exists_pve(self) -> bool:
        """
        检查是否有pve比赛
        """
        total_events = self.get_total_events()
        if 'pve' in total_events.keys():
            return True
        return False

    def check(self):
        logger.info(self.date)

        total_events = self.get_total_events()
        # logger.debug(total_events)
        if 'pve' in total_events.keys():
            self.pve_starter(total_events['pve'])
        if 'eve' in total_events.keys():
            self.eve_starter(total_events['eve'])
        if 'transfer prepare' in total_events.keys():
            self.transfer_prepare_starter(total_events['transfer prepare'])
        if 'crew improve' in total_events.keys():
            self.crew_improve_starter(total_events['crew improve'])
        if 'offer expire' in total_events.keys():
            self.offer_expire_starter(total_events['offer expire'])
        if 'transfer' in total_events.keys():
            self.transfer_starter(total_events['transfer'])
        if 'transfer end' in total_events.keys():
            self.transfer_end_starter(total_events['transfer end'])
        if 'rank and tv' in total_events.keys():
            self.rank_n_tv_income()
        if 'ad income' in total_events.keys():
            self.ad_income()
        if 'salary day' in total_events.keys():
            self.salary_day()
        if 'game_generation' in total_events.keys():
            self.game_generation_starter(total_events['game_generation'])
        if 'next_calendar' in total_events.keys():
            self.next_calendar_starter()
        if 'promote_n_relegate' in total_events.keys():
            self.promote_n_relegate_starter()

    def eve_starter(self, eve: list):
        """
        eve入口
        """
        s = time.time()
        for game in eve:
            self.play_game(game)
        e = time.time()
        logger.debug('共耗时{}s'.format(e - s))

    def play_game(self, calendar_game):
        """
        进行一场比赛，包括战术调整
        :param calendar_game: 日程表中的比赛信息
        """
        # 战术调整
        clubs_id = calendar_game['club_id'].split(',')

        club1_model = self.db.query(models.Club).filter(
            models.Club.id == clubs_id[0]).first()
        club2_model = self.db.query(models.Club).filter(
            models.Club.id == clubs_id[1]).first()

        tactic_adjustor = game_app.TacticAdjustor(db=self.db,
                                                  club1_id=clubs_id[0], club2_id=clubs_id[1],
                                                  player_club_id=self.save_model.player_club_id,
                                                  save_id=self.save_model.id,
                                                  club1_model=club1_model, club2_model=club2_model,
                                                  season=self.save_model.season,
                                                  date=self.date)
        tactic_adjustor.adjust()
        # 开始模拟比赛
        game_eve = game_app.GameEvE(db=self.db,
                                    club1_id=clubs_id[0], club2_id=clubs_id[1],
                                    date=self.date,
                                    game_name=calendar_game['game_name'],
                                    game_type=calendar_game['game_type'],
                                    season=self.save_model.season,
                                    save_id=self.save_model.id,
                                    club1_model=club1_model, club2_model=club2_model)
        name1, name2, score1, score2 = game_eve.start()
        logger.info(
            "{} {}: {} {}:{} {}".format(calendar_game['game_name'], calendar_game['game_type'], name1, score1, score2,
                                        name2))

    def pve_starter(self, pve: list):
        """
        pve入口 创建game_pve表
        """
        if self.skip:
            self.eve_starter(pve)
        else:
            game = pve[0]
            clubs_id = game['club_id'].split(',')
            if int(clubs_id[0]) != self.save_model.player_club_id:
                computer_club_id = int(clubs_id[0])
            else:
                computer_club_id = int(clubs_id[1])
            game_pve_generator = generate_app.GamePvEGenerator(
                db=self.db,
                save_model=self.save_model)
            game_pve_generator.create_game_pve(
                player_club_id=self.save_model.player_club_id,
                computer_club_id=computer_club_id,
                game=game, date=self.save_model.date, season=self.save_model.season)

    def transfer_prepare_starter(self, transfer_prepare: list):
        logger.info("转会窗准备日")
        transfer_club_list = []
        clubs: List[models.Club] = crud.get_clubs_by_save(db=self.db, save_id=self.save_id)
        for club in clubs:
            if club.id != self.save_model.player_club_id:
                transfer_club = transfer_app.Club(
                    db=self.db, club_id=club.id,
                    date=self.save_model.date, season=self.save_model.season,
                    club_model=club)
                transfer_club_list.append(transfer_club)
        for transfer_club in transfer_club_list:
            transfer_club.adjust_finance()
        for transfer_club in transfer_club_list:
            transfer_club.judge_on_sale()
        for transfer_club in transfer_club_list:
            transfer_club.judge_buy(self.save_id)  # 按照顺序：调整工资、挂牌、寻找目标 TODO：1`50
        self.db.commit()

    def crew_improve_starter(self, crew_improve: list):
        logger.info("职员升级日")
        transfer_club_list = []
        clubs: List[models.Club] = crud.get_clubs_by_save(db=self.db, save_id=self.save_id)
        for club in clubs:
            if club.id != self.save_model.player_club_id:
                transfer_club = transfer_app.Club(
                    db=self.db, club_id=club.id,
                    date=self.save_model.date, season=self.save_model.season,
                    club_model=club)
                transfer_club_list.append(transfer_club)
        for transfer_club in transfer_club_list:
            transfer_club.improve_crew()

    def offer_expire_starter(self, offer_expire: list):
        logger.info("未谈判offer过期")
        target_offers = crud.get_offers_from_player_by_status(db=self.db, save_id=self.save_id,
                                                              buyer_id=self.save_model.player_club_id,
                                                              season=self.save_model.season, status='n')
        for offer in target_offers:
            offer.status = 'r'  # 状态改为r
        target_offers = crud.get_offers_from_player_by_status(db=self.db, save_id=self.save_id,
                                                              buyer_id=self.save_model.player_club_id,
                                                              season=self.save_model.season, status='w')
        for offer in target_offers:
            offer.status = 'r'  # 状态改为r
        target_offers = crud.get_offers_from_player_by_status(db=self.db, save_id=self.save_id,
                                                              buyer_id=self.save_model.player_club_id,
                                                              season=self.save_model.season, status='u')
        for offer in target_offers:
            offer.status = 'r'  # 状态改为r

    def transfer_starter(self, transfer: list):
        """
        转会入口
        """
        logger.info("转会窗开放")
        transfer_club_list: List[transfer_app.Club] = []
        clubs = crud.get_clubs_by_save(db=self.db, save_id=self.save_id)
        # 剔除玩家俱乐部
        for club in clubs:
            if club.id != self.save_model.player_club_id:
                transfer_club = transfer_app.Club(db=self.db, club_id=club.id,
                                                  date=self.save_model.date, season=self.save_model.season)
                transfer_club_list.append(transfer_club)
        for transfer_club in transfer_club_list:
            transfer_club.receive_offer(self.save_id)
            transfer_club.make_offer(self.save_id)

    def transfer_end_starter(self, transfer: list):
        """
        转会入口
        """
        logger.info("转会窗最后一日")
        transfer_club_list: List[transfer_app.Club] = []
        clubs = crud.get_clubs_by_save(db=self.db, save_id=self.save_id)
        # 剔除玩家俱乐部
        for club in clubs:
            if club.id != self.save_model.player_club_id:
                transfer_club = transfer_app.Club(db=self.db, club_id=club.id,
                                                  date=self.save_model.date, season=self.save_model.season)
                transfer_club_list.append(transfer_club)
        for transfer_club in transfer_club_list:
            transfer_club.receive_offer(self.save_id)  # 转会窗最后一天，只接受offer，不发新的。

    def rank_n_tv_income_base(self, league: models.League,
                              game: computed_data_app.computed_game, first_bonus,
                              second_bonus, rest_bonus):
        df = game.get_season_points_table(game_season=self.save_model.season, game_name=league.name)
        point_table = [tuple(x) for x in df.values]
        first_club = crud.get_club_by_id(db=self.db, club_id=point_table[0][0])
        first_club.finance += first_bonus  # 转播奖金
        first_club.finance += 2500  # 联赛排名
        second = crud.get_club_by_id(db=self.db, club_id=point_table[1][0])
        second.finance += second_bonus
        second.finance += 1500
        third = crud.get_club_by_id(db=self.db, club_id=point_table[2][0])
        third.finance += second_bonus
        for i in range(3, len(point_table)):
            club = crud.get_club_by_id(db=self.db, club_id=point_table[i][0])
            club.finance += rest_bonus

    def rank_n_tv_income(self):
        leagues = self.save_model.leagues
        game = computed_data_app.ComputedGame(db=self.db, save_id=self.save_id)
        for league in leagues:
            if league.name == "英超":
                self.rank_n_tv_income_base(league=league, game=game, first_bonus=15000,
                                           second_bonus=9000, rest_bonus=4800)
                logger.info("英超发钱")
            elif league.name == "西甲":
                self.rank_n_tv_income_base(league=league, game=game, first_bonus=12500,
                                           second_bonus=7500, rest_bonus=4000)
                logger.info("西甲发钱")
            elif league.name == "德甲":
                self.rank_n_tv_income_base(league=league, game=game, first_bonus=10200,
                                           second_bonus=6200, rest_bonus=3550)
                logger.info("德甲发钱")
            elif league.name == "意甲":
                self.rank_n_tv_income_base(league=league, game=game, first_bonus=10000,
                                           second_bonus=6000, rest_bonus=3200)
                logger.info("意甲发钱")
            elif league.name == "法甲":
                self.rank_n_tv_income_base(league=league, game=game, first_bonus=8750,
                                           second_bonus=5250, rest_bonus=2800)
                logger.info("法甲发钱")
            elif league.name == "英冠":
                self.rank_n_tv_income_base(league=league, game=game, first_bonus=6250,
                                           second_bonus=3750, rest_bonus=2000)
                logger.info("英冠发钱")
            elif league.name == "西乙":
                self.rank_n_tv_income_base(league=league, game=game, first_bonus=5625,
                                           second_bonus=3375, rest_bonus=1800)
                logger.info("西医发钱")
            else:
                self.rank_n_tv_income_base(league=league, game=game, first_bonus=5000,
                                           second_bonus=3000, rest_bonus=1600)
                logger.info(league.name + "发钱")

    def ad_income(self):
        leagues = self.save_model.leagues
        for league in leagues:
            for club in league.clubs:
                club.finance += club.reputation ** 3 * 0.02 + 500  # 广告
            logger.info(league.name + "广告")

    def salary_day(self):
        leagues = self.save_model.leagues
        for league in leagues:
            for club in league.clubs:
                sum_salary = 0
                for player in club.players:
                    sum_salary += player.wages
                sum_salary += crew_salary_check(db=self.db, club_id=club.id)
                club.finance -= sum_salary
            logger.info(league.name + "扣除工资")

    def game_generation_starter(self, game_generation):
        """
        后续比赛生成入口
        """
        calendar_generator = generate_app.CalendarGenerator(db=self.db, save_id=self.save_id)
        for game_event in game_generation:
            if 'cup' in game_event:
                calendar_generator.generate_cup_games(game_type=game_event)
                calendar_generator.save_in_db()
            if 'champions' in game_event:
                calendar_generator.generate_champions_league_games(game_type=game_event)
                calendar_generator.save_in_db()

    def promote_n_relegate_starter(self):
        """
        联赛升降级入口
        """
        for league_model in self.save_model.leagues:
            if not league_model.upper_league and league_model.lower_league:
                lower_league = crud.get_league_by_id(db=self.db, league_id=league_model.lower_league)
                computed_game = computed_data_app.ComputedGame(self.db, save_id=self.save_model.id)
                df1 = computed_game.get_season_points_table(
                    game_season=self.save_model.season, game_name=league_model.name)
                df2 = computed_game.get_season_points_table(
                    game_season=self.save_model.season, game_name=lower_league.name)

                relegate_df = df1.sort_values(by=['积分', '净胜球', '胜球'], ascending=[False, False, False])
                relegate_club_id = relegate_df[-4:]['id'].to_list()
                for club_id in relegate_club_id:
                    # 降级
                    crud.update_club(db=self.db, club_id=club_id, attri={'league_id': lower_league.id})
                promote_df = df2.sort_values(by=['积分', '净胜球', '胜球'], ascending=[False, False, False])
                promote_club_id = promote_df[:4]['id'].to_list()
                for club_id in promote_club_id:
                    # 升级
                    crud.update_club(db=self.db, club_id=club_id, attri={'league_id': league_model.id})
        logger.info('{}赛季的联赛升降级完成'.format(str(self.save_model.season)))

    def next_calendar_starter(self):
        """
        生成下赛季的日程表
        """
        self.save_model.season += 1  # 赛季+1
        self.db.commit()
        calendar_generator = generate_app.CalendarGenerator(db=self.db, save_id=self.save_model.id)
        calendar_generator.generate()
        logger.info('{}赛季的日程表生成完成'.format(str(self.save_model.season)))
