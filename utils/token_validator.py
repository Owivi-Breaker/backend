from typing import List, Optional
import datetime
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import game_configs

from core.db import get_db
import models
import schemas
import crud

# 加密格式, 参数tokenUrl只是为了方便fastapi的文档网页的认证使用, 在前后端实际项目中并不会起到作用
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


class TokenData(BaseModel):
    """
    token中存储的信息
    """
    email: str = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """
    验证密码
    :param: 密码原文
    :param: 密码哈希值
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    """
    生成token
    :param data: 待加密的内容
    :param expires_delta: token有效时间
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        # 默认15min有效时间
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, game_configs.SECRET_KEY, algorithm=game_configs.ALGORITHM)  # 用指定密钥和算法加密
    return encoded_jwt  # token


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)) -> models.User:
    """
    根据token获取相应的user_model
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, game_configs.SECRET_KEY, algorithms=[game_configs.ALGORITHM])
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


def authenticate_user(
        email: str, password: str, db: Session = Depends(get_db)) -> Optional[models.User]:
    """
    根据账号和密码验证用户合法性
    :param email: 邮箱账号
    :param password: 密码
    """
    user_model = crud.get_user_by_email(db, email)
    if not user_model:
        return None
    if not verify_password(password, user_model.hashed_password):
        return None
    return user_model
