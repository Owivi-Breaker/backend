from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from utils import logger


def create_target_player(db: Session, target_player: schemas.Target_PlayerCreate):
    db_target = models.Target_player(**target_player.dict())
    db.add(db_target)
    return db_target


def update_target_player(db: Session, target_id: int, attri: dict):
    db_target = db.query(models.Target_player).filter(models.Target_player.id == target_id).first()
    for key, value in attri.items():
        setattr(db_target, key, value)
    db.commit()
    return db_target


def get_target__by_save_id(db: Session, save_id: int) -> List[models.Target_player]:
    """
    获取指定存档id中的所有目标球员表项
    """
    db_targets = db.query(models.Target_player).filter(models.Target_player.save_id == save_id).all()
    return db_targets


def get_target_by_attri(db: Session, attri: str) -> List[models.Target_player]:
    db_targets = db.query(models.Target_player).filter(eval(attri)).all()
    return db_targets