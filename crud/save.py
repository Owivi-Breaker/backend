from sqlalchemy.orm import Session
import models
import schemas
from utils import logger


def create_save(db: Session, save: schemas.SaveCreate):
    db_save = models.Save(**save.dict())
    db.add(db_save)
    db.commit()
    db.refresh(db_save)
    return db_save


def update_save(db: Session, save_id: int, attri: dict):
    db_save = db.query(models.Save).filter(models.Save.id == save_id).first()
    for key, value in attri.items():
        setattr(db_save, key, value)
    db.commit()
    return db_save


def get_save_by_id(db: Session, save_id: int) -> models.Save:
    db_save = db.query(models.Save).filter(models.Save.id == save_id).first()
    return db_save


def get_save_by_user(db: Session, user_id: int):
    db_save = db.query(models.Save).filter(models.Save.user_id == user_id).offset(0).limit(100).all()
    return db_save
