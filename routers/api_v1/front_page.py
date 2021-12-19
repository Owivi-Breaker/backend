from typing import List
from fastapi import APIRouter, Depends, FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from core.db import engine, get_db, drop_all
from pydantic import BaseModel
import datetime
import random
import string
import schemas
import models
import crud
import game_configs
from modules import generate_app, game_app, computed_data_app, next_turn_app
from utils import logger, Date

router = APIRouter()

@router.get('/get_date')
def get_save_date(save_id: int, db: Session = Depends(get_db)):
    """
    获取当前存档内的时间
    """
    save_model = crud.get_save_by_id(db, save_id)
    return  str(save_model.time)