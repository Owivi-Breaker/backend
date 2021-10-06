from sqlalchemy.orm import Session
import models
import schemas
from utils import logger


def create_club(db: Session, club: schemas.ClubCreate):
    db_club = models.Club(**club.dict())
    db.add(db_club)
    db.commit()
    db.refresh(db_club)
    return db_club


def update_club(db: Session, club_id: int, attri: dict):
    db_club: models.Club = db.query(models.Club).filter(models.Club.id == club_id).first()
    for key, value in attri.items():
        setattr(db_club, key, value)
    db.commit()
    return db_club


def get_club_by_id(db: Session, club_id: int):
    db_club = db.query(models.Club).filter(models.Club.id == club_id).first()
    return db_club
