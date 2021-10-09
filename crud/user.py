from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models
import schemas


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):  # 加密过程
    return pwd_context.hash(password)


def create_user(db: Session, user: schemas.UserCreate):
    secret_password = get_password_hash(user.password)  # 加密后的密码
    db_user = models.User(email=user.email, hashed_password=secret_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
