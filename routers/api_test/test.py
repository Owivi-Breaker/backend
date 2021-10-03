from typing import List
from fastapi import APIRouter, Depends, FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from core.db import SessionLocal, engine, get_db
from pydantic import BaseModel
import datetime
import random

import schemas
import models
import crud
import game_configs
from modules import generate_app, game_app
from utils import logger, Date


class SaveData(BaseModel):
    type: str


router = APIRouter()


@router.post('/init_save')
def init_save(save_data: SaveData, db: Session = Depends(get_db)) -> schemas.Save:
    """
    初始化新存档
    :param save_data: 初始化存档的一些参数
    :param db: database
    :return: 存档实例
    """
    # 初始化生成器
    save_generator = generate_app.SaveGenerator(db)
    league_generator = generate_app.LeagueGenerator(db)
    club_generator = generate_app.ClubGenerator(db)
    player_generator = generate_app.PlayerGenerator(db)
    coach_generator = generate_app.CoachGenerator(db)
    calendar_generator = generate_app.CalendarGenerator(db)
    # 生成存档
    save_create_schemas = schemas.SaveCreate(created_time=datetime.datetime.now(),
                                             time='2021-08-01')
    save_model = save_generator.generate(save_create_schemas)
    logger.info("存档生成")
    # 生成联赛
    league_list = eval("game_configs.{}".format(save_data.type))
    for league in league_list:
        league_create_schemas = schemas.LeagueCreate(created_time=datetime.datetime.now(),
                                                     name=league['name'], points=league['points'])
        league_model = league_generator.generate(league_create_schemas)
        crud.update_league(db=db, league_id=league_model.id, attri={"save_id": save_model.id})
        league['id'] = league_model.id
        logger.info("联赛{}生成".format(league['name']))

        for club in league["clubs"]:
            # 生成俱乐部
            club_create_schemas = schemas.ClubCreate(created_time=datetime.datetime.now(),
                                                     name=club['name'],
                                                     finance=club['finance'],
                                                     reputation=club['reputation'])
            club_model = club_generator.generate(club_create_schemas)
            crud.update_club(db=db, club_id=club_model.id, attri={"league_id": league_model.id})
            logger.info("俱乐部{}生成".format(club['name']))

            # 随机生成教练
            coach_model = coach_generator.generate()
            crud.update_coach(db=db, coach_id=coach_model.id, attri={"club_id": club_model.id})
            # logger.info("教练生成")

            # 随机生成球员
            # 随机生成11名适配阵型位置的成年球员
            formation_dict = game_configs.formations[coach_model.formation]
            for lo, num in formation_dict.items():
                for i in range(num):
                    player_model = player_generator.generate(ori_mean_capa=club['ori_mean_capa'],
                                                             ori_mean_potential_capa=game_configs.ori_mean_potential_capa,
                                                             average_age=30, location=lo)
                    crud.update_player(db=db, player_id=player_model.id, attri={"club_id": club_model.id})

            for _ in range(7):
                # 随机生成7名任意位置成年球员
                player_model = player_generator.generate(ori_mean_capa=club['ori_mean_capa'],
                                                         ori_mean_potential_capa=game_configs.ori_mean_potential_capa,
                                                         average_age=30)
                crud.update_player(db=db, player_id=player_model.id, attri={"club_id": club_model.id})
            for _ in range(6):
                # 随机生成6名年轻球员
                player_model = player_generator.generate()
                crud.update_player(db=db, player_id=player_model.id, attri={"club_id": club_model.id})
                # logger.info("第{}个球员生成".format(_ + 1))

            # logger.info("24个球员生成")

    for league in league_list:
        # 标记上下游联赛关系
        if league['upper_league']:
            for target_league in league_list:
                if target_league['name'] == league['upper_league']:
                    crud.update_league(db=db, league_id=league['id'], attri={"upper_league": target_league['id']})
        if league['lower_league']:
            for target_league in league_list:
                if target_league['name'] == league['lower_league']:
                    crud.update_league(db=db, league_id=league['id'], attri={"lower_league": target_league['id']})
    logger.info("联赛上下游关系标记完成")
    # 生成日程表
    calendar_generator.generate(save_id=save_model.id)
    logger.info("日程表生成")

    return crud.get_save_by_id(db=db, save_id=save_model.id)


def start_game(test_num: int, league_id: int, db: Session):
    league_model = crud.get_league_by_id(db=db, league_id=league_id)
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
            logger.info("{}: {}对{}".format(test_num, game[0].name, game[1].name))
            game_eve = game_app.GameEvE(db, game[0].id, game[1].id, date, 'test')
            game_eve.start()
        date.plus_days(7)


@router.get('/imitate_game_season')
async def imitate_game_season(test_num: str, league_id: int, background_tasks: BackgroundTasks,
                              db: Session = Depends(get_db), ):
    """
    模拟指定联赛一个赛季的比赛
    :param league_id: 联赛id
    :param db: database
    :return:
    """
    background_tasks.add_task(start_game, test_num=test_num, league_id=league_id, db=db)
    return {"message": "正在比赛..."}
