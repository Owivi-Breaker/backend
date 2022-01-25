from sqlalchemy.orm import Session
import models
import schemas
from utils import logger


def create_coach(db: Session, coach: schemas.CoachCreate):
    db_coach = models.Coach(**coach.dict())
    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)
    return db_coach


def update_coach(db: Session, coach_id: int, attri: dict):
    db_coach = db.query(models.Coach).filter(models.Coach.id == coach_id).first()
    for key, value in attri.items():
        setattr(db_coach, key, value)
    db.commit()
    return db_coach


def get_coach_by_id(db: Session, coach_id: int):
    db_coach = db.query(models.Coach).filter(models.Coach.id == coach_id).first()
    return db_coach


def get_coach_by_club(db: Session, club_id: int):
    db_coach = db.query(models.Coach).filter(models.Coach.club_id == club_id).first()
    return db_coach
