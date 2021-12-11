import time
from typing import List
from fastapi import APIRouter, status, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import datetime

from modules import generate_app
from core.db import engine, get_db
import schemas
import models
import crud
import utils
from utils import logger

router = APIRouter()


@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    注册用户
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered")
    return crud.create_user(db=db, user=user)


@router.get("/{user_id}/save/", response_model=List[schemas.SaveShow], dependencies=[Depends(utils.verify_token)])
async def get_saves_by_user(user_id: int, db: Session = Depends(get_db)) -> List[models.Save]:
    """
    获取用户存档
    """
    user_model = crud.get_user_by_id(db=db, user_id=user_id)
    return user_model.saves


class SaveData(BaseModel):
    type: str = 'five_leagues'
    player_club_name: str = '阿森纳'


@router.post("/{user_id}/save/", response_model=schemas.SaveShow, dependencies=[Depends(utils.verify_token)])
async def create_save(save_data: SaveData,
                      current_user: models.User = Depends(utils.get_current_user),
                      db: Session = Depends(get_db)):
    """
    生成存档
    :param save_data: 存档信息
    :param current_user: 用户
    :return: 生成的存档信息
    """
    save_generator = generate_app.SaveGenerator(db)
    save_schema = schemas.SaveCreate(created_time=datetime.datetime.now())
    save_model = save_generator.generate(save_schema, current_user.id, save_data.type)
    break_flag = False
    for league in save_model.leagues:
        for club in league.clubs:
            if club.name == save_data.player_club_name:
                break_flag = True
                current_club_id = club.id
                current_club = {'player_club_id': current_club_id}
                crud.update_save(db, save_model.id, current_club)  # 玩家俱乐部ID加入save
    if not break_flag:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect club name",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return save_model
