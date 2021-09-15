from typing import List
from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

import schemas
import models
from core.db import SessionLocal, engine, get_db
import crud

router = APIRouter()


@router.get('/{club_id}/players', response_model=List[schemas.Player],
            response_model_exclude={"game_data"}, tags=['get players'])
async def get_players_by_club(club_id: int, db: Session = Depends(get_db)) -> list:
    """
    获取全部球员
    :param club_id: 俱乐部 id
    :param db: 数据库
    :return: list of schemas.player
    """
    attri = "models.Player.club_id=={}".format(club_id)
    return crud.get_players_by_attri(db, attri=attri)
