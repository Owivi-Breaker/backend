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


@router.get('/', response_model=List[schemas.Player], response_model_exclude={"game_data"})
def get_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list:
    """
    获取全部球员
    :param db: database
    :param skip: offset
    :param limit: number of players
    :return: list of schemas.player
    """

    return crud.get_player(db, skip, limit)
