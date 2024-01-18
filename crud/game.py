from typing import List
from sqlalchemy.orm import Session

import models
import schemas
from utils import logger
from core.db import engine


def create_game(db: Session, game: schemas.GameCreate):
    """
    创建比赛表
    """
    db_game = models.Game(**game.dict())
    db.add(db_game)
    # db.commit()
    # db.refresh(db_game)
    return db_game


def create_game_team_info(db: Session, game_team_info: schemas.GameTeamInfoCreate):
    """
    创建比赛队伍信息表
    """
    db_game_team_info = models.GameTeamInfo(**game_team_info.dict())
    db.add(db_game_team_info)
    # db.commit()
    # db.refresh(db_game_team_info)
    return db_game_team_info


def create_game_team_data(db: Session, game_team_data: schemas.GameTeamDataCreate) -> models.GameTeamData:
    """
    创建比赛队伍数据表
    """
    db_game_team_data = models.GameTeamData(**game_team_data.dict())
    db.add(db_game_team_data)
    # db.commit()
    # db.refresh(db_game_team_data)
    return db_game_team_data


def create_game_player_data(db: Session, game_player_data: schemas.GamePlayerDataCreate) -> models.GamePlayerData:
    """
    创建比赛球员信息表
    """
    db_game_player_data = models.GamePlayerData(**game_player_data.dict())
    db.add(db_game_player_data)
    # 为加快速度，不在函数里commit，在具体代码处统一commit
    # db.commit()
    # db.refresh(db_game_player_data)
    return db_game_player_data


def create_game_player_data_bulk(game_player_data: List[schemas.GamePlayerDataCreate], game_team_info_id: int):
    """
    批量创建比赛球员信息表，需要提供game_team_info_id以免去更新步骤
    """

    def add_game_team_info_id(p):
        p = p.dict()
        p['game_team_info_id'] = game_team_info_id
        return p

    game_player_data = list(map(add_game_team_info_id, game_player_data))

    engine.execute(
        models.GamePlayerData.__table__.insert(),
        game_player_data
    )


def get_game_player_data_by_attri(db: Session, attri: str, only_one: bool = False):
    if only_one:
        db_game_player_data = db.query(models.GamePlayerData).filter(eval(attri)).first()
        return db_game_player_data
    else:
        db_game_player_data = db.query(models.GamePlayerData).filter(eval(attri)).all()
        return db_game_player_data


def update_game_team_info(db: Session, game_team_info_id: int, attri: dict) -> models.GameTeamInfo:
    db_game_team_info = db.query(models.GameTeamInfo).filter(models.GameTeamInfo.id == game_team_info_id).first()
    for key, value in attri.items():
        setattr(db_game_team_info, key, value)
    db.commit()
    return db_game_team_info


def get_game_team_info_by_club(db: Session, club_id: int, season: int) -> list[models.GameTeamInfo]:
    db_game_team_info = db.query(models.GameTeamInfo).filter(models.GameTeamInfo.club_id == club_id
                                                             and models.GameTeamInfo.season == season).all()
    return db_game_team_info


def update_game_team_data(db: Session, game_team_data_id: int, attri: dict) -> models.GameTeamData:
    db_game_team_data = db.query(models.GameTeamData).filter(models.GameTeamData.id == game_team_data_id).first()
    for key, value in attri.items():
        setattr(db_game_team_data, key, value)
    db.commit()
    return db_game_team_data


def update_game_player_data(db: Session, game_player_data_id: int, attri: dict) -> models.GamePlayerData:
    db_game_player_data = db.query(models.GamePlayerData).filter(
        models.GamePlayerData.id == game_player_data_id).first()
    for key, value in attri.items():
        setattr(db_game_player_data, key, value)
    db.commit()
    return db_game_player_data


def get_games_by_attri(db: Session, query_str: str, only_one: bool = False) -> List[models.Game]:
    if only_one:
        db_game = db.query(models.Game).filter(eval(query_str)).first()
        return db_game
    else:
        db_games = db.query(models.Game).filter(eval(query_str)).all()
        return db_games


def get_game_by_id(db: Session, game_id: int) -> models.Game:
    db_game = db.query(models.Game).filter(models.Game.id == game_id).first()
    return db_game


def delete_game_by_attri(db: Session, query_str: str):
    db_games = db.query(models.Game).filter(eval(query_str)).all()
    if not db_games:
        logger.info('无比赛表可删！')
    for db_game in db_games:
        db_game_teams_info = db.query(models.GameTeamInfo).filter(
            models.GameTeamInfo.game_id == db_game.id).all()
        for db_game_team_info in db_game_teams_info:
            db_game_team_data = db.query(models.GameTeamData).filter(
                models.GameTeamData.game_team_info_id == db_game_team_info.id).first()
            db.delete(db_game_team_data)
            db_game_players_data = db.query(models.GamePlayerData).filter(
                models.GamePlayerData.game_team_info_id == db_game_team_info.id).all()
            for db_game_player_data in db_game_players_data:
                db.delete(db_game_player_data)
            db.delete(db_game_team_info)
        db.delete(db_game)
        db.commit()
