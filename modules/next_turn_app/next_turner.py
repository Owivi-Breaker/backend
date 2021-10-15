import json
from typing import List
from sqlalchemy.orm import Session
import threading

import crud
import models
from utils import Date, utils, logger
from modules import game_app, generate_app, computed_data_app


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
        # logger.debug(total_events)
        if 'pve' in total_events.keys():
            self.pve_starter(total_events['pve'])
        if 'eve' in total_events.keys():
            self.eve_starter(total_events['eve'])
        if 'transfer' in total_events.keys():
            self.transfer_starter(total_events['transfer'])
        if 'game_generation' in total_events.keys():
            self.game_generation_starter(total_events['game_generation'])
        if 'next_calendar' in total_events.keys():
            self.next_calendar_starter()
        if 'promote_n_relegate' in total_events.keys():
            self.promote_n_relegate_starter()

    def eve_starter(self, eve: list):
        for game in eve:
            self.play_game(game)

    def play_game(self, calendar_game):
        clubs_id = calendar_game['club_id'].split(',')
        tactic_adjustor = game_app.TacticAdjustor(db=self.db,
                                                  club1_id=clubs_id[0], club2_id=clubs_id[1],
                                                  player_club_id=self.save_model.player_club_id,
                                                  save_id=self.save_model.id)
        tactic_adjustor.adjust()
        # 开始模拟比赛
        game_eve = game_app.GameEvE(db=self.db,
                                    club1_id=clubs_id[0], club2_id=clubs_id[1],
                                    date=self.date,
                                    game_name=calendar_game['game_name'],
                                    game_type=calendar_game['game_type'],
                                    season=self.save_model.season,
                                    save_id=self.save_model.id)
        name1, name2, score1, score2 = game_eve.start()
        logger.info(
            "{} {}: {} {}:{} {}".format(calendar_game['game_name'], calendar_game['game_type'], name1, score1, score2,
                                        name2))

    def pve_starter(self, pve: list):
        # 暂时跟eve作相同处理
        self.eve_starter(pve)

    def transfer_starter(self, transfer: list):
        pass

    def game_generation_starter(self, game_generation):
        calendar_generator = generate_app.CalendarGenerator(db=self.db, save_id=self.save_id)
        for game_event in game_generation:
            if 'cup' in game_event:
                calendar_generator.generate_cup_games(game_type=game_event)
                calendar_generator.save_in_db()
            if 'champions' in game_event:
                calendar_generator.generate_champions_league_games(game_type=game_event)
                calendar_generator.save_in_db()

    def promote_n_relegate_starter(self):
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
