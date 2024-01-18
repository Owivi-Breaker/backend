import models
import schemas
from sqlalchemy.orm import Session
from utils import logger


def create_game_pve(db: Session, game_pve: schemas.GamePvECreate) -> models.GamePvE:
    """
    创建比赛表
    """
    db_game_pve = models.GamePvE(**game_pve.dict())
    db.add(db_game_pve)
    db.commit()
    db.refresh(db_game_pve)
    return db_game_pve


def delete_all_game_temp_table(db: Session, save_id: int):
    """
    删除指定存档中所有比赛临时表
    """
    db_games_pve = db.query(models.GamePvE).filter(models.GamePvE.save_id == save_id).all()
    [db.delete(x) for x in db_games_pve]
    db.commit()


def get_game_pve_by_save_id(db: Session, save_id: int) -> models.GamePvE:
    """
    获取指定存档下的临时比赛表
    由于一个存档只严格存在一张临时比赛表 故此法可行 且比较快捷
    """
    db_game_pve = db.query(models.GamePvE).filter(models.GamePvE.save_id == save_id).first()
    # if not db_game_pve:
    #     logger.error("Can't find models.GamePvE")
    return db_game_pve


def get_game_pve_by_club_id(db: Session, player_club_id: int, computer_club_id: int) -> models.GamePvE:
    db_game_pve = (
        db.query(models.GamePvE)
        .filter(models.GamePvE.player_club_id == player_club_id, models.GamePvE.club_id == computer_club_id)
        .first()
    )
    if not db_game_pve:
        logger.error("Can't find models.GamePvE")
    return db_game_pve


def create_team_pve(db: Session, team_pve: schemas.TeamPvECreate) -> models.TeamPvE:
    db_team_pve = models.TeamPvE(**team_pve.dict())
    db.add(db_team_pve)
    return db_team_pve


def create_player_pve(db: Session, player_pve: schemas.PlayerPvECreate) -> models.PlayerPvE:
    db_player_pve = models.PlayerPvE(**player_pve.dict())
    db.add(db_player_pve)
    return db_player_pve
