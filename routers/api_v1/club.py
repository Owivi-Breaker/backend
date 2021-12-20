from typing import List
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

import schemas
import models
from core.db import get_db
import crud
import utils
from modules import computed_data_app
from utils import logger

router = APIRouter()


@router.get('/{club_id}', response_model=schemas.ClubShow)
def get_club_by_id(club_id: int, db: Session = Depends(get_db)) -> schemas.ClubShow:
    """
    获取指定id的俱乐部信息
    :param club_id: 俱乐部 id
    """
    club_model = crud.get_club_by_id(db=db, club_id=club_id)
    return computed_data_app.ComputedClub(
        club_id=club_model.id, db=db, club_model=club_model).get_show_data()


@router.get('/', response_model=List[schemas.ClubShow])
def get_club(save_id: int, db: Session = Depends(get_db)) -> List[schemas.ClubShow]:
    """
    获取指定存档的所有俱乐部信息
    :param save_id: 存档 id
    """
    db_clubs: List[models.Club] = crud.get_clubs_by_save(db=db, save_id=save_id)
    club_shows: List[schemas.ClubShow] = [
        computed_data_app.ComputedClub(
            club_id=club_model.id, db=db, club_model=club_model).get_show_data()
        for club_model in db_clubs]
    return club_shows


@router.get('/{club_id}/player', response_model=List[schemas.PlayerShow], tags=['player api'])
def get_players_by_club(
        club_id: int, db: Session = Depends(get_db),
        save_model=Depends(utils.get_current_save), is_player_club: bool = False) -> List[schemas.PlayerShow]:
    """
    获取指定俱乐部的球员信息
    :param club_id: 俱乐部 id
    :param save_model: 存档实例
    :param is_player_club: 是否是玩家俱乐部
    :return: list of schemas.PlayerShow
    """
    if is_player_club:
        club_model = crud.get_club_by_id(db=db, club_id=save_model.player_club_id)
    else:
        club_model = crud.get_club_by_id(db=db, club_id=club_id)
    return [computed_data_app.ComputedPlayer(
        player_id=player_model.id, db=db, player_model=player_model,
        season=save_model.season).get_show_data()
            for player_model in club_model.players]
