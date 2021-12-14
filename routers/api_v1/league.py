from typing import List, Union
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from core.db import get_db
from modules import computed_data_app
import schemas
import models
import crud
import utils
from utils import logger

router = APIRouter()


@router.get('/', response_model=List[schemas.LeagueShow])
def get_leagues(save_model=Depends(utils.get_current_save),
                db: Session = Depends(get_db)) -> List[schemas.LeagueShow]:
    """
    获取指定存档中的所有俱乐部信息
    """
    return [computed_data_app.ComputedLeague(
        league_id=league_model.id, db=db, league_model=league_model).get_show_data()
            for league_model in save_model.leagues]


@router.get('/{league_id}', response_model=schemas.LeagueShow)
def get_league_by_id(league_id: int, db: Session = Depends(get_db)) -> schemas.LeagueShow:
    """
    获取指定联赛的信息
    """
    league_model = crud.get_league_by_id(db=db, league_id=league_id)
    return computed_data_app.ComputedLeague(
        league_id=league_model.id, db=db, league_model=league_model).get_show_data()


@router.get('/{league_id}/club', response_model=List[schemas.ClubShow], tags=['club api'])
def get_clubs_by_league(league_id: int, db: Session = Depends(get_db)) -> List[schemas.ClubShow]:
    """
    获取指定联赛的所有俱乐部信息
    """
    league_model = crud.get_league_by_id(db=db, league_id=league_id)
    return [computed_data_app.ComputedClub(
        club_id=club_model.id, db=db, club_model=club_model).get_show_data()
            for club_model in league_model.clubs]


@router.get('/{league_id}/points-table')
def get_points_table(save_id: int, game_season: int,
                     league_id: Union[int, str],
                     db: Session = Depends(get_db)) -> dict:
    """
    获取指定赛季指定联赛的积分榜
    :param save_id: 存档id
    :param game_season: 赛季
    :param league_id: 联赛id
    :return:
    """
    if isinstance(league_id, int):
        game_name = crud.get_league_by_id(db=db, league_id=league_id).name
    else:
        game_name = league_id
    computed_game = computed_data_app.ComputedGame(db=db, save_id=save_id)
    df = computed_game.get_season_points_table(game_season, game_name)
    return computed_game.switch2json(df)


@router.get('/{league_id}/player-chart')
def get_player_chart(save_id: int, game_season: int,
                     league_id: Union[int, str], db: Session = Depends(get_db)):
    """
    获取指定赛季指定联赛的球员数据榜
    :param save_id: 存档id
    :param game_season: 赛季
    :param league_id: 联赛id
    """
    if isinstance(league_id, int):
        game_name = crud.get_league_by_id(db=db, league_id=league_id).name
    else:
        game_name = league_id
    computed_game = computed_data_app.ComputedGame(db=db, save_id=save_id)
    df = computed_game.get_season_player_chart(game_season, game_name)
    return computed_game.switch2json(df)
