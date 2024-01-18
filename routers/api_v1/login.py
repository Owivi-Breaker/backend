import datetime

import game_configs
import utils
from core.db import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


class Token(BaseModel):
    """
    token的返回格式
    """

    access_token: str
    token_type: str


@router.post("/", response_model=Token)
async def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user_model = utils.authenticate_user(form_data.username, form_data.password, db)
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=game_configs.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(data={"sub": user_model.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


# @router.get("/users/me", response_model=list)  # 返回用户名、帐号状态
# async def read_users_me(current_user: models.User = Depends(get_current_user)):  # models中的user类
#     return current_user.email, current_user.is_active
