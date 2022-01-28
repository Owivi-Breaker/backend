from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from utils import logger


def create_target_player(db: Session, target_player: schemas.TargetPlayerCreate):
    db_target = models.TargetPlayer(**target_player.dict())
    db.add(db_target)
    return db_target


def update_target_player(db: Session, target_id: int, attri: dict):
    db_target = db.query(models.TargetPlayer).filter(models.TargetPlayer.id == target_id).first()
    for key, value in attri.items():
        setattr(db_target, key, value)
    db.commit()
    return db_target


def get_target__by_save_id(db: Session, save_id: int) -> List[models.TargetPlayer]:
    """
    获取指定存档id中的所有目标球员表项
    """
    db_targets = db.query(models.TargetPlayer).filter(models.TargetPlayer.save_id == save_id).all()
    return db_targets


def get_target_by_attri(db: Session, attri: str) -> List[models.TargetPlayer]:
    db_targets = db.query(models.TargetPlayer).filter(eval(attri)).all()
    return db_targets


def get_target_by_player_id_n_buyer_id(db: Session, target_id: int, buyer_id: int) -> models.TargetPlayer:
    """
    根据指定球员id和买房俱乐部id获取目标球员实例
    """
    db_target = db.query(models.TargetPlayer).filter(
        and_(models.TargetPlayer.target_id == target_id,
             models.TargetPlayer.buyer_id == buyer_id)).first()
    return db_target


def get_targets_by_club(db: Session, save_id: int, club_id: int, season: int) -> List[models.TargetPlayer]:
    db_targets = db.query(models.TargetPlayer).filter(
        and_(models.TargetPlayer.save_id == save_id,
             models.TargetPlayer.buyer_id == club_id,
             models.TargetPlayer.season == season)).all()
    return db_targets


def delete_target_by_player_id_n_buyer_id(db: Session, target_id: int, buyer_id: int):
    """
    根据指定球员id和买房俱乐部id删除目标球员实例
    """
    db_target = db.query(models.TargetPlayer).filter(
        and_(models.TargetPlayer.target_id == target_id,
             models.TargetPlayer.buyer_id == buyer_id)).first()
    db.delete(db_target)
