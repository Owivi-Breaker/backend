import models
import schemas
from sqlalchemy.orm import Session


def create_league(league: schemas.LeagueCreate, db: Session):
    db_league = models.League(**league.dict())
    db.add(db_league)
    db.commit()
    db.refresh(db_league)
    return db_league


def get_league_by_id(db: Session, league_id: int):
    db_league = db.query(models.League).filter(models.League.id == league_id).first()
    return db_league


def get_league_by_save(db: Session, save_id: int):
    db_league = db.query(models.League).filter(models.League.save.id == save_id).first()
    return db_league


def update_league(db: Session, league_id: int, attri: dict):
    db_league = db.query(models.League).filter(models.League.id == league_id).first()
    for key, value in attri.items():
        setattr(db_league, key, value)
    db.commit()
    return db_league
