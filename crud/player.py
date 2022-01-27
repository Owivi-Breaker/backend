import time
from typing import List

from sqlalchemy import and_
from sqlalchemy.orm import Session
import models
import schemas
from utils import logger
from core.db import engine
import crud


# region 球员操作
def create_player(db: Session, player: schemas.PlayerCreate):
    db_player = models.Player(**player.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def create_player_bulk(players: List[schemas.PlayerCreate], club_id: int):
    """
    批量创建球员, 提供club_id一并提交
    专用于创建大量球员时
    这个函数跳过ORM过程，直接对sql引擎进行操作，所以不需要db会话
    """

    def add_club_id(p):
        p = p.dict()
        p['club_id'] = club_id
        return p

    players = list(map(add_club_id, players))
    # db.bulk_save_objects(db_players) # 不要用这个啦，这个是基于ORM的
    engine.execute(
        models.Player.__table__.insert(),
        players
    )


def update_player(db: Session, player_id: int, attri: dict):
    db_player = db.query(models.Player).filter(models.Player.id == player_id).first()
    for key, value in attri.items():
        setattr(db_player, key, value)
    # db.commit()
    return db_player


def get_player_by_id(player_id: int, db: Session) -> models.Player:
    db_player = db.query(models.Player).filter(models.Player.id == player_id).first()
    return db_player


def get_players_by_save(db: Session, save_id: int, skip: int, limit: int) -> List[models.Player]:
    """
    获取指定存档的球员db实例
    """
    db_clubs = crud.get_clubs_by_save(db=db, save_id=save_id)
    player_list: List[models.Player] = []
    for club in db_clubs:
        player_list.extend(club.players)
    # db_player = db.query(models.Player) \
    #     .filter(models.Player.club.league.save.id == save_id) \
    #     .offset(skip).limit(limit).all()
    return player_list[skip:skip + limit]


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
    db.commit()


def get_player_game_data(
        player_id: int, db: Session, start_season: int, end_season: int) -> List[models.GamePlayerData]:
    """
    获取指定球员某赛季的比赛信息
    """
    s = time.time()
    db_game_player_data: List[models.GamePlayerData] = db.query(models.GamePlayerData).filter(
        and_(models.GamePlayerData.player_id == player_id,
             models.GamePlayerData.season >= start_season,
             models.GamePlayerData.season <= end_season)).all()
    e = time.time()
    print(e - s)
    return db_game_player_data

# endregion
