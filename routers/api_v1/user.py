import datetime
from typing import List

import crud
import models
import schemas
import utils
from core.db import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from modules import generate_app
from pydantic import BaseModel
from sqlalchemy.orm import Session
from utils import logger

router = APIRouter()


@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    注册用户
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


# 不要在路径中加入user_id,因为user_id的传入依赖于token,前端难以直接将user_id返回
@router.get("/save", response_model=List[schemas.SaveShow], dependencies=[Depends(utils.verify_token)])
async def get_saves_by_user(current_user: models.User = Depends(utils.get_current_user)) -> List[models.Save]:
    """
    获取用户存档
    """
    return current_user.saves


@router.get("/save/me", response_model=schemas.SaveShow, dependencies=[Depends(utils.verify_token)])
async def get_save_by_user(save_model: models.User = Depends(utils.get_current_save)) -> models.Save:
    """
    获取玩家现在的存档信息
    """
    return save_model


class SaveData(BaseModel):
    type: str = "five_leagues"
    player_club_name: str = "阿森纳"


@router.post("/save", response_model=schemas.SaveShow, dependencies=[Depends(utils.verify_token)])
async def create_save(
    save_data: SaveData, current_user: models.User = Depends(utils.get_current_user), db: Session = Depends(get_db)
):
    """
    生成存档
    :param save_data: 存档信息
    :param current_user: 用户
    :return: 生成的存档信息
    """
    try:
        # 检查联赛模式名字合法性
        eval("game_configs.{}".format(save_data.type))
    except AttributeError as e:
        logger.error("请求联赛模式名不合法! ".format(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect league type name",
            headers={"WWW-Authenticate": "Bearer"},
        )

    save_generator = generate_app.SaveGenerator(db)
    save_schema = schemas.SaveCreate(created_time=datetime.datetime.now())
    save_model = save_generator.generate(save_schema, current_user.id, save_data.type)
    break_flag = False
    for league in save_model.leagues:
        for club in league.clubs:
            if club.name == save_data.player_club_name:
                break_flag = True
                current_club_id = club.id
                current_club = {"player_club_id": current_club_id}
                crud.update_save(db, save_model.id, current_club)  # 玩家俱乐部ID加入save
    if not break_flag:
        # 无法找不到正确的俱乐部名 删除save
        crud.delete_save_by_id(db=db, save_id=save_model.id)
        logger.info("请求俱乐部名不合法！")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect club name",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成日程表
    calendar_generator = generate_app.CalendarGenerator(db=db, save_id=save_model.id)
    calendar_generator.generate()
    logger.info("日程表生成")
    return save_model


@router.get("/save/date", dependencies=[Depends(utils.verify_token)])
def get_save_date(save_id: int, db: Session = Depends(get_db)):
    """
    获取当前存档内的时间
    """
    save_model = crud.get_save_by_id(db, save_id)
    return {"date": str(save_model.date)}
