from typing import List, Optional
from fastapi import APIRouter
import datetime
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import game_configs
from modules import generate_app, game_app, computed_data_app
from core.db import get_db
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


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
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
    user_model = crud.get_user_by_email(db, token_data.email)
    if user_model is None:
        raise credentials_exception
    return user_model


def authenticate_user(email: str, password: str, db: Session = Depends(get_db)) -> Optional[models.User]:
    user_model = crud.get_user_by_email(db, email)
    if not user_model:
        return None
    if not verify_password(password, user_model.hashed_password):
        return None
    return user_model


@router.post("/create-user/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@router.post("/", response_model=Token)
async def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    print("1")
    user_model = authenticate_user(form_data.username, form_data.password, db)
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_model.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=list)  # 返回用户名、帐号状态
async def read_users_me(current_user: models.User = Depends(get_current_user)):  # models中的user类
    return current_user.email, current_user.is_active


@router.post("/users/create-save/", response_model=schemas.SaveCreate)
async def create_save(save_data: SaveData, current_user: models.User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """
    生成存档
    :param save_data: 存档信息
    :param current_user: 用户
    :return: 生成的存档信息
    """
    save_generator = generate_app.SaveGenerator(db)
    save_schema = schemas.SaveCreate(player_club_id=save_data.player_club_id, created_time=datetime.datetime.now())
    save_model = save_generator.generate(save_schema, current_user.id, save_data.type)

    return save_model


@router.get("/users/show-saves/", response_model=List[schemas.Save])
async def show_saves(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_save_by_user(db=db, user_id=current_user.id)


@router.get("/protocol")
async def show_protocol():
    p = "这是<br>一个<br>string，<br>我也<br>不知道<br>里面<br>要写什么，<br>反正挺<br>长的"
    return p
