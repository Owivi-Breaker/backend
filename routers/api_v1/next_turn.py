from fastapi import APIRouter, Depends, FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from core.db import engine, get_db, drop_all
from pydantic import BaseModel

import schemas
import models
import crud
import game_configs
from modules import generate_app, game_app, computed_data_app, next_turn_app
from utils import logger, Date

router = APIRouter()


@router.get('/')
def next_turn(save_id: int, turn_num: int, db: Session = Depends(get_db)):
    next_turner = next_turn_app.NextTurner(db=db, save_id=save_id)
    for i in range(turn_num):
        logger.info('第{}回合'.format(str(i + 1)))
        next_turner.check()
