from typing import List
from sqlalchemy.orm import Session

import models
import schemas
from utils import logger


def create_game(db: Session, game: schemas.GameCreate):
    """
    创建比赛表
    """
    db_game = models.Game(**game.dict())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def create_game_team_info(db: Session, game_team_info: schemas.GameTeamInfoCreate):
    """
    创建比赛队伍信息表
    """
    db_game_team_info = models.GameTeamInfo(**game_team_info.dict())
    db.add(db_game_team_info)
    db.commit()
    db.refresh(db_game_team_info)
    return db_game_team_info


def create_game_team_data(db: Session, game_team_data: schemas.GameTeamDataCreate) -> models.GameTeamData:
    """
    创建比赛队伍数据表
    """
    db_game_team_data = models.GameTeamData(**game_team_data.dict())
    db.add(db_game_team_data)
    db.commit()
    db.refresh(db_game_team_data)
    return db_game_team_data


def create_game_player_data(db: Session, game_player_data: schemas.GamePlayerDataCreate) -> models.GamePlayerData:
    """
    创建比赛球员信息表
    """
    db_game_player_data = models.GamePlayerData(**game_player_data.dict())
    db.add(db_game_player_data)
    db.commit()
    db.refresh(db_game_player_data)
    return db_game_player_data


def update_game_team_info(db: Session, game_team_info_id: int, attri: dict) -> models.GameTeamInfo:
    db_game_team_info = db.query(models.GameTeamInfo).filter(models.GameTeamInfo.id == game_team_info_id).first()
    for key, value in attri.items():
        setattr(db_game_team_info, key, value)
    db.commit()
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
