import crud
import models
from core.db import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from utils import get_current_user, oauth2_scheme

#
# async def verify_token(token: str = Depends(oauth2_scheme),
#                        db: Session = Depends(get_db)):
#     """
#     验证token
#     """
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, game_configs.SECRET_KEY, algorithms=[game_configs.ALGORITHM])
#         decoded_email: str = payload.get("sub")  # 从token得到邮箱
#         if decoded_email is None:
#             raise credentials_exception
#         token_data = TokenData(email=decoded_email)
#     except JWTError:
#         raise credentials_exception
#     user_model = crud.get_user_by_email(db, token_data.email)
#     if user_model is None:
#         raise credentials_exception
#     return user_model

async def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    验证token, 调用get_current_user, 只是换了个名字好听一点罢了。。
    """
    await get_current_user(token=token, db=db)


def get_current_save(save_id: int, db: Session = Depends(get_db)) -> models.Save:
    """
    获取save_id对应的存档实例
    """
    return crud.get_save_by_id(db=db, save_id=save_id)
