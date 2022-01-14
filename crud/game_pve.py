from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

import models
import schemas
from utils import logger
from core.db import engine


def create_game_pve(db: Session, game_pve: schemas.GamePvECreate) -> models.GamePvE:
    """
    创建比赛表
    """
    db_game_pve = models.GamePvE(**game_pve.dict())
    db.add(db_game_pve)
    db.commit()
    db.refresh(db_game_pve)
    return db_game_pve


def get_game_pve_by_club_id(db: Session, player_club_id: int, computer_club_id: int) -> models.GamePvE:
    db_game_pve = db.query(models.GamePvE).filter(
        models.GamePvE.player_club_id == player_club_id,
        models.GamePvE.club_id == computer_club_id).first()
    if db_game_pve:
        return db_game_pve
    else:
        logger.error("Can't find models.GamePvE")


def create_team_pve(db: Session, team_pve: schemas.TeamPvECreate) -> models.TeamPvE:
    db_team_pve = models.TeamPvE(**team_pve.dict())
    db.add(db_team_pve)
    return db_team_pve


def create_player_pve(db: Session, player_pve: schemas.PlayerPvECreate) -> models.PlayerPvE:
    db_player_pve = models.PlayerPvE(**player_pve.dict())
    db.add(db_player_pve)
    return db_player_pve
