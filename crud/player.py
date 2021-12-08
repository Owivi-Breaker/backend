from typing import List

from sqlalchemy.orm import Session
import models
import schemas
from utils import logger


# region 球员操作
def create_player(db: Session, player: schemas.PlayerCreate):
    db_player = models.Player(**player.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def update_player(db: Session, player_id: int, attri: dict):
    db_player = db.query(models.Player).filter(models.Player.id == player_id).first()
    for key, value in attri.items():
        setattr(db_player, key, value)
    db.commit()
    return db_player


def get_player_by_id(player_id: int, db: Session) -> models.Player:
    db_player = db.query(models.Player).filter(models.Player.id == player_id).first()
    return db_player


def get_player(db: Session, save_id: int, skip: int, limit: int) -> List[models.Player]:
    """
    获取指定存档的球员db实例
    """
    db_player = db.query(models.Player).filter(models.Save.id == save_id).offset(skip).limit(limit).all()
    return db_player


# TODO 需要重写
def get_players_by_attri(db: Session, attri: str, only_one: bool = False):
    """
    一个非常宽泛的“根据指定条件获取球员”，需要自己写入筛选条件
    :param db: 数据库
    :param attri: 筛选条件，SQL语句字符串
    :param only_one: 是否只返回一个
    :return: models.Player
    """
    if only_one:
        db_player = db.query(models.Player).filter(eval(attri)).first()
        return db_player
    else:
        db_players = db.query(models.Player).filter(eval(attri)).all()
        return db_players


def delete_player(player_id: int, db: Session):
    db_player = db.query(models.Player).filter(models.Player.id == player_id).first()
    db.delete(db_player)

# endregion
