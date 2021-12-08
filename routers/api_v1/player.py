from typing import List
from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from core.db import engine, get_db
from modules import computed_data_app

import schemas
import models
import crud

router = APIRouter()


@router.get('/', response_model=List[schemas.PlayerShow])
def get_player(save_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[
    schemas.PlayerShow]:
    """
    获取指定存档的全部球员
    :param save_id: 存档id
    :param skip: 偏移量
    :param limit: 一次性返回的数量
    :return: list of schemas.player
    """

    db_players: List[models.Player] = crud.get_player(db=db, save_id=save_id, skip=skip, limit=limit)
    player_shows: List[schemas.PlayerShow] = [
        computed_data_app.ComputedPlayer(
            player_id=player_model.id, db=db, player_model=player_model).get_show_data()
        for player_model in db_players]
    return player_shows


@router.get('/{player_id}', response_model=schemas.PlayerShow)
def get_player_by_id(player_id: int, db: Session = Depends(get_db)) -> schemas.PlayerShow:
    """
    获取指定id的球员
    :param player_id: 球员id
    :return: schemas.player
    """

    db_player: models.Player = crud.get_player_by_id(player_id=player_id, db=db)
    player_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(player_id=db_player.id, db=db,
                                                                       player_model=db_player).get_show_data()
    return player_show
