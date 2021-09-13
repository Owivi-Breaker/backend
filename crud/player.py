from sqlalchemy.orm import Session
import models
import schemas
from utils import logger


# region 球员操作
def crud_create_player(player: schemas.PlayerCreate, db: Session):
    db_player = models.Player(**player.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def crud_update_player(player_id: int, attri: dict, db: Session):
    db_player = db.query(models.Player).filter(models.Player.id == player_id).first()
    for key, value in attri.items():
        setattr(db_player, key, value)
    db.commit()
    return db_player


def crud_get_player_by_id(player_id: int, db: Session):
    db_player = db.query(models.Player).filter(models.Player.id == player_id).first()
    return db_player


def crud_get_player(db: Session, skip: int, limit: int):
    db_player = db.query(models.Player).offset(skip).limit(limit).all()
    return db_player


# TODO 需要重写
def crud_get_players_by_attri(attri: str, db: Session, only_one: bool = False):
    if only_one:
        db_player = db.query(models.Player).filter(eval(attri)).first()
        return db_player
    else:
        db_players = db.query(models.Player).filter(eval(attri)).all()
        return db_players


def crud_delete_player(player_id: int, db: Session):
    db_player = db.query(models.Player).filter(models.Player.id == player_id).first()
    db.delete(db_player)

# endregion
