from typing import List
from fastapi import APIRouter, Depends, FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from core.db import engine, get_db, drop_all
from pydantic import BaseModel
import datetime
import random

import schemas
import models
import crud
import game_configs
from modules import generate_app, game_app, computed_data_app, next_turn_app
from utils import logger, Date

router = APIRouter()


def quick_game(db: Session, fake_season, save_id):
    game_eve = game_app.GameEvE(db=db, club1_id=1, club2_id=2, date=Date(2021, 8, 14),
                                game_name='国王杯', game_type='cup4to2',
                                season=fake_season, save_id=save_id)
    score = game_eve.start()


def start_season_game(league_model: models.League, save_model: models.Save, db: Session):
    """
    快速进行一个赛季的比赛
    """

    clubs = league_model.clubs
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

    date = Date(2021, 8, 14)
    for games in schedule:
        # 进行每一轮比赛
        logger.info('{} 的比赛'.format(str(date)))
        for game in games:
            # 调整战术比重
            tactic_adjustor = game_app.TacticAdjustor(db=db, club1_id=game[0].id, club2_id=game[1].id,
                                                      player_club_id=save_model.player_club_id,
                                                      save_id=save_model.id)
            tactic_adjustor.adjust()
            # 开始模拟比赛
            game_eve = game_app.GameEvE(db=db, club1_id=game[0].id, club2_id=game[1].id, date=date,
                                        game_name=league_model.name, game_type='league',
                                        season=save_model.season, save_id=save_model.id)
            score1, score2 = game_eve.start()
            logger.info("{} {}:{} {}".format(game[0].name, score1, score2, game[1].name))
        date.plus_days(7)


def promote_n_relegate(save_model: models.Save, db: Session):
    """
    联赛升降级设置，根据赛季积分榜，在数据库中修改应升级/降级的球队的联赛级别
    """
    for league_model in save_model.leagues:
        if not league_model.upper_league:
            lower_league = crud.get_league_by_id(db=db, league_id=league_model.lower_league)
            computed_game = computed_data_app.ComputedGame(db, save_id=save_model.id)
            df1 = computed_game.get_season_points_table(
                game_season=save_model.season, game_name=league_model.name)
            df2 = computed_game.get_season_points_table(
                game_season=save_model.season, game_name=lower_league.name)

            relegate_df = df1.sort_values(by=['积分', '净胜球', '胜球'], ascending=[False, False, False])
            relegate_club_id = relegate_df[-4:]['id'].to_list()
            for club_id in relegate_club_id:
                # 降级
                crud.update_club(db=db, club_id=club_id, attri={'league_id': lower_league.id})
            promote_df = df2.sort_values(by=['积分', '净胜球', '胜球'], ascending=[False, False, False])
            promote_club_id = promote_df[:4]['id'].to_list()
            for club_id in promote_club_id:
                # 升级
                crud.update_club(db=db, club_id=club_id, attri={'league_id': league_model.id})


def start_season_games(db: Session, save_id: int, years: int = 0):
    """
    进行存档中所有联赛一个赛季的比赛
    """
    save_model = crud.get_save_by_id(db=db, save_id=save_id)

    crud.delete_game_by_attri(db=db,
                              query_str='and_(models.Game.season=="{}", models.Game.save_id=="{}")'.format(
                                  save_model.season, save_model.id))

    for _ in range(years):
        for league_model in save_model.leagues:
            start_season_game(league_model, save_model, db)
        promote_n_relegate(save_model=save_model, db=db)
        save_model.season += 1
        db.commit()


@router.get('/quick_game')
async def make_50_games(db: Session = Depends(get_db), save_id=1):
    for s in range(50):
        print('正在进行第' +str(s)  + '场')
        game = quick_game(db, s, save_id)


@router.get('/imitate_game_season')
async def imitate_game_season(background_tasks: BackgroundTasks, save_id: int, years: int = 1,
                              db: Session = Depends(get_db)):
    """
    模拟指定存档中一个赛季的比赛
    :param years: 赛季数
    :param background_tasks: 后台任务参数
    :param save_id: 存档id
    :param db: database
    :return:
    """
    background_tasks.add_task(start_season_games, db=db, save_id=save_id, years=years)
    return {"message": "正在比赛..."}


@router.get('/points-table')
def get_points_table(save_id: int, game_season: int, game_type: str, db: Session = Depends(get_db)):
    # TODO 此处有sql注入问题
    computed_game = computed_data_app.ComputedGame(db=db, save_id=save_id)
    df = computed_game.get_season_points_table(game_season, game_type)
    return computed_game.switch2json(df)


@router.get('/player-chart')
def get_player_chart(save_id: int, game_season: int, game_type: str, db: Session = Depends(get_db)):
    # TODO 此处有sql注入问题
    computed_game = computed_data_app.ComputedGame(db=db, save_id=save_id)
    df = computed_game.get_season_player_chart(game_season, game_type)
    return computed_game.switch2json(df)


@router.get('/next-turn')
def next_turn(save_id: int, turn_num: int, db: Session = Depends(get_db)):
    next_turner = next_turn_app.NextTurner(db=db, save_id=save_id)
    for i in range(turn_num):
        logger.info('第{}回合'.format(i))
        next_turner.check()


@router.get('/clear_db')
def clear_db():
    drop_all()
