from typing import List, Union
from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from utils import logger
from core.db import engine, get_db
from modules import computed_data_app
import schemas
import models
import crud
import utils

router = APIRouter()


@router.get('/', response_model=List[schemas.PlayerShow])
def get_player(save_id: int, skip: int = 0, limit: int = 100,
               db: Session = Depends(get_db),
               save_model=Depends(utils.get_current_save)) -> List[schemas.PlayerShow]:
    """
    获取指定存档的全部球员
    :param save_id: 存档id
    :param skip: 偏移量
    :param limit: 一次性返回的数量
    :return: list of schemas.player
    """

    db_players: List[models.Player] = crud.get_players_by_save(db=db, save_id=save_id, skip=skip, limit=limit)
    player_shows: List[schemas.PlayerShow] = [
        computed_data_app.ComputedPlayer(
            player_id=player_model.id, db=db, player_model=player_model,
            season=save_model.season, date=save_model.date).get_show_data()
        for player_model in db_players]
    return player_shows


@router.get('/{player_id}', response_model=schemas.PlayerShow)
def get_player_by_id(player_id: int, db: Session = Depends(get_db),
                     save_model=Depends(utils.get_current_save)) -> schemas.PlayerShow:
    """
    获取指定id的球员
    :param player_id: 球员id
    :return: schemas.playerShow
    """
    db_player: models.Player = crud.get_player_by_id(player_id=player_id, db=db)
    player_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
        player_id=db_player.id, db=db,
        player_model=db_player, season=save_model.season, date=save_model.date).get_show_data()
    return player_show


@router.get('/{player_id}/game-data',
            response_model=List[schemas.GamePlayerDataShow])
def get_game_player_data(player_id: int,
                         start_season: int = None, end_season: int = None,
                         db: Session = Depends(get_db),
                         save_model=Depends(utils.get_current_save)) \
        -> List[schemas.GamePlayerData]:
    """
    获取指定球员某赛季的比赛信息
    :param player_id: 球员id
    :param start_season: 开始赛季，若为空，默认1开始
    :param end_season: 结束赛季，若为空，默认当前赛季
    """
    computed_player = computed_data_app.ComputedPlayer(
        player_id=player_id, db=db,
        season=save_model.season, date=save_model.date)

    game_player_data: List[schemas.GamePlayerData] = computed_player.get_game_player_data(
        start_season=start_season, end_season=end_season)
    return game_player_data


@router.get('/{player_id}/total-game-data',
            response_model=schemas.GamePlayerDataShow,
            response_model_exclude={'location'})
def get_total_game_player_data(player_id: int, start_season: int = None, end_season: int = None,
                               db: Session = Depends(get_db),
                               save_model=Depends(utils.get_current_save)) \
        -> schemas.GamePlayerDataShow:
    """
    获取指定球员某赛季的统计比赛信息
    :param player_id: 球员id
    :param start_season: 开始赛季，若为空，默认1开始
    :param end_season: 结束赛季，若为空，默认当前赛季
    """
    computed_player = computed_data_app.ComputedPlayer(
        player_id=player_id, db=db, season=save_model.season, date=save_model.date)

    total_game_player_data: schemas.GamePlayerDataShow = computed_player.get_total_game_player_data(
        start_season=start_season, end_season=end_season)
    return total_game_player_data
