from typing import List, Optional
from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import game_configs
from modules import generate_app, game_app, computed_data_app
from core.db import SessionLocal, engine, get_db
import models
import schemas
import crud
from utils import logger, Date


class SaveData(BaseModel):
    type: str
    player_club_id: int


router = APIRouter()

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
"""
加密格式
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt  # token


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        decoded_email: str = payload.get("sub")  # 从token得到邮箱
        if decoded_email is None:
            raise credentials_exception
        token_data = TokenData(email=decoded_email)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, token_data.email)
    if user is None:
        raise credentials_exception
    return user


def authenticate_user(email: str, password: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


@router.post("/create-user/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@router.post("/", response_model=Token)
async def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    print("1")
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=list)  # 返回用户名、帐号状态
async def read_users_me(current_user: list = Depends(get_current_user)):  # models中的user类
    return current_user.email, current_user.is_active


@router.post("/users/create-save/", response_model=schemas.SaveCreate)
async def create_save(save_data: SaveData, current_user: models.User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    # save_model = crud.create_save(db=db, save=save_schema)
    # save_model.user_id = current_user.id
    # db.commit()
    # return save_model
    save_generator = generate_app.SaveGenerator(db)
    league_generator = generate_app.LeagueGenerator(db)
    club_generator = generate_app.ClubGenerator(db)
    player_generator = generate_app.PlayerGenerator(db)
    coach_generator = generate_app.CoachGenerator(db)
    # 生成存档

    save_schema = schemas.SaveCreate()

    save_model = crud.create_save(db=db, save=save_schema)
    save_model.user_id = current_user.id
    db.commit()
    save_schema.player_club_id = save_data.player_club_id
    save_schema.created_time = datetime.now()

    save_model = save_generator.generate(save_schema)
    logger.info("存档生成")
    # 生成联赛
    league_list = eval("game_configs.{}".format(save_data.type))
    for league in league_list:
        league_create_schemas = schemas.LeagueCreate(created_time=datetime.now(),
                                                     name=league['name'],
                                                     points=league['points'],
                                                     cup=league['cup'])
        league_model = league_generator.generate(league_create_schemas)
        crud.update_league(db=db, league_id=league_model.id, attri={"save_id": save_model.id})
        league['id'] = league_model.id
        logger.info("联赛{}生成".format(league['name']))

        for club in league["clubs"]:
            # 生成俱乐部
            club_create_schemas = schemas.ClubCreate(created_time=datetime.now(),
                                                     name=club['name'],
                                                     finance=club['finance'],
                                                     reputation=club['reputation'])
            club_model = club_generator.generate(club_create_schemas)
            crud.update_club(db=db, club_id=club_model.id, attri={"league_id": league_model.id})
            logger.info("俱乐部{}生成".format(club['name']))

            # 随机生成教练
            coach_model = coach_generator.generate()
            crud.update_coach(db=db, coach_id=coach_model.id, attri={"club_id": club_model.id})

            # 随机生成球员
            # 随机生成11名适配阵型位置的成年球员
            formation_dict = game_configs.formations[coach_model.formation]
            player_model_list: List[models.Player] = []
            for lo, num in formation_dict.items():
                for i in range(num):
                    player_model = player_generator.generate(ori_mean_capa=club['ori_mean_capa'],
                                                             ori_mean_potential_capa=game_configs.ori_mean_potential_capa,
                                                             average_age=26, location=lo)
                    player_model_list.append(player_model)
                    # crud.update_player(db=db, player_id=player_model.id, attri={"club_id": club_model.id})

            for _ in range(7):
                # 随机生成7名任意位置成年球员
                player_model = player_generator.generate(ori_mean_capa=club['ori_mean_capa'],
                                                         ori_mean_potential_capa=game_configs.ori_mean_potential_capa,
                                                         average_age=26)
                player_model_list.append(player_model)
                # crud.update_player(db=db, player_id=player_model.id, attri={"club_id": club_model.id})
            for _ in range(6):
                # 随机生成6名年轻球员
                player_model = player_generator.generate()
                player_model_list.append(player_model)
                # crud.update_player(db=db, player_id=player_model.id, attri={"club_id": club_model.id})
            # 统一提交24名球员的修改
            attri = {"club_id": club_model.id}
            for player_model in player_model_list:
                for key, value in attri.items():
                    setattr(player_model, key, value)
            db.commit()
    for league in league_list:
        # 标记上下游联赛关系
        if league['upper_league']:
            for target_league in league_list:
                if target_league['name'] == league['upper_league']:
                    crud.update_league(db=db, league_id=league['id'], attri={"upper_league": target_league['id']})
        if league['lower_league']:
            for target_league in league_list:
                if target_league['name'] == league['lower_league']:
                    crud.update_league(db=db, league_id=league['id'], attri={"lower_league": target_league['id']})
    logger.info("联赛上下游关系标记完成")
    # 生成日程表
    calendar_generator = generate_app.CalendarGenerator(db=db, save_id=save_model.id)
    calendar_generator.generate()
    logger.info("日程表生成")
    return save_schema



@router.get("/users/show-saves/", response_model=List[schemas.Save])
async def show_saves(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_save_by_user(db=db, user_id=current_user.id)


@router.get("/protocol")
async def show_protocol():
    p = "这是<br>一个<br>string，<br>我也<br>不知道<br>里面<br>要写什么，<br>反正挺<br>长的"
    return p
