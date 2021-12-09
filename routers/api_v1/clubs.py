from typing import List
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import schemas
import models
from core.db import get_db
import crud
from modules import computed_data_app
from utils import logger

router = APIRouter()


@router.get('/{club_id}', response_model=schemas.ClubShow)
def get_club_by_id(club_id: int, db: Session = Depends(get_db)) -> schemas.ClubShow:
    """
    获取指定id的俱乐部信息
    :param club_id: 俱乐部 id
    """
    pass

@router.get('/', response_model=List[schemas.ClubShow])
def get_club(save_id: int, db: Session = Depends(get_db)) -> List[schemas.ClubShow]:
    """
    获取指定存档地所有俱乐部信息
    :param club_id: 俱乐部 id
    """
    db_clubs: List[models.Club] = crud.get_club(db=db, save_id=save_id)
    club_shows: List[schemas.ClubShow] = [
        computed_data_app.ComputedClub(
            club_id=club_model.id, db=db, club_model=club_model).get_show_data()
        for club_model in db_clubs]
    return club_shows


@router.get('/{club_id}/player', response_model=List[schemas.Player])
def get_players_by_club(club_id: int, db: Session = Depends(get_db)) -> List[schemas.PlayerShow]:
    """
    获取指定俱乐部的球员信息
    :param club_id: 俱乐部 id
    :return: list of schemas.player
    """
    attri = "models.Player.club_id=={}".format(club_id)
    return crud.get_players_by_attri(db, attri=attri)
