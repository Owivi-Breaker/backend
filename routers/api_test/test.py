from typing import List
from fastapi import APIRouter, Depends, FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from core.db import engine, get_db, drop_all
from pydantic import BaseModel
import datetime
import random
import string
import schemas
import models
import crud
import game_configs
from modules import generate_app, game_app, computed_data_app, next_turn_app, transfer_app
from utils import logger, Date
import utils

router = APIRouter()


@router.get("/protocol")
async def show_protocol():
    """
    展示协议内容
    """
    p = "这是<br>一个<br>string，<br>我也<br>不知道<br>里面<br>要写什么，<br>反正挺<br>长的"
    return p


@router.get('/clear-db')
def clear_db():
    """
    清空数据库中的所有内容
    """
    drop_all()
    return 'successfully clear db'


@router.get('/game-process-demo')
async def quick_game(fake_season=1, save_id=1, db: Session = Depends(get_db)):
    """
    展示一场 eve 比赛的过程，
    默认为曼城与曼联的英超比赛
    """
    game_eve = game_app.GameEvE(db=db, club1_id=1, club2_id=2, date=Date(2021, 8, 30), game_name='英超',
                                game_type='league', season=int(fake_season), save_id=save_id)
    result = game_eve.start()
    query_str = "and_(models.Game.season=='{}', models.Game.type=='{}', models.Game.date=='{}')".format(fake_season,
                                                                                                        'league',
                                                                                                        Date(2021, 8,
                                                                                                             30))
    game = crud.get_games_by_attri(db=db, query_str=query_str)
    process = game[-1].script
    temp_events = process.split("\n")
    events = [i for i in temp_events if i != '']
    return events


@router.get('/all-try-sell')
def all_try_sell(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    clubs = crud.get_clubs_by_save(db=db, save_id=save_model.id)
    for club in clubs:
        transfer_club = transfer_app.Club(db=db, club_id=club.id, date=save_model.date, season=save_model.season)
        transfer_club.judge_on_sale()
        print(str(club.name) + "完成")


@router.get('/all-adjust-wage')
def all_adjust_wage(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    clubs = crud.get_clubs_by_save(db=db, save_id=save_model.id)
    for club in clubs:
        transfer_club = transfer_app.Club(db=db, club_id=club.id, date=save_model.date, season=save_model.season)
        transfer_club.adjust_finance()
        print(str(club.name) + "完成")


@router.get('/all-judge-buy')
def all_judge_buy(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    clubs = crud.get_clubs_by_save(db=db, save_id=save_model.id)
    for club in clubs:
        transfer_club = transfer_app.Club(db=db, club_id=club.id, date=save_model.date, season=save_model.season)
        transfer_club.judge_buy(save_id=save_model.id)
        print(str(club.name) + "完成")


@router.get('/all-make-offer')
def all_make_offer(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    clubs = crud.get_clubs_by_save(db=db, save_id=save_model.id)
    for club in clubs:
        transfer_club = transfer_app.Club(db=db, club_id=club.id, date=save_model.date, season=save_model.season)
        transfer_club.make_offer(save_id=save_model.id)
        print(str(club.name) + "完成")


@router.get('/all-receive-offer')
def all_receive_offer(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    clubs = crud.get_clubs_by_save(db=db, save_id=save_model.id)
    for club in clubs:
        transfer_club = transfer_app.Club(db=db, club_id=club.id, date=save_model.date, season=save_model.season)
        transfer_club.receive_offer(save_id=save_model.id)
        print(str(club.name) + "完成")


@router.get('/incoming-games-info')
async def get_incoming_games_info(db: Session = Depends(get_db),
                                  save_model=Depends(utils.get_current_save)):
    """
    获取即将到来的比赛信息
    """
    computed_calendar = computed_data_app.ComputedCalendar(save_id=save_model.id, db=db, save_model=save_model)
    return computed_calendar.get_incoming_games(cur_date_str=save_model.date)
#
# def start_season_game(league_model: models.League, save_model: models.Save, db: Session):
#     """
#     快速进行一个赛季的比赛
#     """
#
#     clubs = league_model.clubs
#     clubs_a = random.sample(clubs, len(clubs) // 2)  # 随机挑一半
#     clubs_b = list(set(clubs) ^ set(clubs_a))  # 剩下另一半
#     schedule = []  # 比赛赛程
#     for _ in range((len(clubs) - 1)):
#         # 前半赛季的比赛
#         schedule.append([game for game in zip(clubs_a, clubs_b)])
#         clubs_a.insert(1, clubs_b.pop(0))
#         clubs_b.append(clubs_a.pop(-1))
#     schedule_reverse = []  # 主客场对调的后半赛季赛程
#     for games in schedule:
#         schedule_reverse.append([tuple(list(x)[::-1]) for x in games])
#     schedule.extend(schedule_reverse)
#
#     date = Date(2021, 8, 14)
#     for games in schedule:
#         # 进行每一轮比赛
#         logger.info('{} 的比赛'.format(str(date)))
#         for game in games:
#             # 调整战术比重
#             tactic_adjustor = game_app.TacticAdjustor(db=db, club1_id=game[0].id, club2_id=game[1].id,
#                                                       player_club_id=save_model.player_club_id,
#                                                       save_id=save_model.id)
#             tactic_adjustor.adjust()
#             # 开始模拟比赛
#             game_eve = game_app.GameEvE(db=db, club1_id=game[0].id, club2_id=game[1].id, date=date,
#                                         game_name=league_model.name, game_type='league',
#                                         season=save_model.season, save_id=save_model.id)
#             score1, score2 = game_eve.start()
#             logger.info("{} {}:{} {}".format(game[0].name, score1, score2, game[1].name))
#         date.plus_days(7)
#
#
# def promote_n_relegate(save_model: models.Save, db: Session):
#     """
#     联赛升降级设置，根据赛季积分榜，在数据库中修改应升级/降级的球队的联赛级别
#     """
#     for league_model in save_model.leagues:
#         if not league_model.upper_league:
#             lower_league = crud.get_league_by_id(db=db, league_id=league_model.lower_league)
#             computed_game = computed_data_app.ComputedGame(db, save_id=save_model.id)
#             df1 = computed_game.get_season_points_table(
#                 game_season=save_model.season, game_name=league_model.name)
#             df2 = computed_game.get_season_points_table(
#                 game_season=save_model.season, game_name=lower_league.name)
#
#             relegate_df = df1.sort_values(by=['积分', '净胜球', '胜球'], ascending=[False, False, False])
#             relegate_club_id = relegate_df[-4:]['id'].to_list()
#             for club_id in relegate_club_id:
#                 # 降级
#                 crud.update_club(db=db, club_id=club_id, attri={'league_id': lower_league.id})
#             promote_df = df2.sort_values(by=['积分', '净胜球', '胜球'], ascending=[False, False, False])
#             promote_club_id = promote_df[:4]['id'].to_list()
#             for club_id in promote_club_id:
#                 # 升级
#                 crud.update_club(db=db, club_id=club_id, attri={'league_id': league_model.id})
#
#
# def start_season_games(db: Session, save_id: int, years: int = 0):
#     """
#     进行存档中所有联赛一个赛季的比赛
#     """
#     save_model = crud.get_save_by_id(db=db, save_id=save_id)
#
#     crud.delete_game_by_attri(db=db,
#                               query_str='and_(models.Game.season=="{}", models.Game.save_id=="{}")'.format(
#                                   save_model.season, save_model.id))
#
#     for _ in range(years):
#         for league_model in save_model.leagues:
#             start_season_game(league_model, save_model, db)
#         promote_n_relegate(save_model=save_model, db=db)
#         save_model.season += 1
#         db.commit()
#
#
# @router.get('/quick_game')
# async def make_50_games(db: Session = Depends(get_db), save_id=1):
#     for s in range(50):
#         print('正在进行第' + str(s) + '场')
#         game = quick_game(db, s, save_id)
#
#
# @router.get('/imitate_game_season')
# async def imitate_game_season(background_tasks: BackgroundTasks, save_id: int, years: int = 1,
#                               db: Session = Depends(get_db)):
#     """
#     模拟指定存档中一个赛季的比赛
#     :param years: 赛季数
#     :param background_tasks: 后台任务参数
#     :param save_id: 存档id
#     :param db: database
#     :return:
#     """
#     background_tasks.add_task(start_season_games, db=db, save_id=save_id, years=years)
#     return {"message": "正在比赛..."}
