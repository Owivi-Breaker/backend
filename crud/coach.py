from sqlalchemy.orm import Session
import models
import schemas
from utils import logger


def create_coach(coach: schemas.Coach, db: Session):
    db_coach = models.Coach(**coach.dict())
    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)
    return db_coach


def update_coach(coach_id: int, attri: dict, db: Session):
    db_coach = db.query(models.Coach).filter(models.Coach.id == coach_id).first()
    for key, value in attri.items():
        setattr(db_coach, key, value)
    db.commit()
    return db_coach


def get_coach_by_id(coach_id: int, db: Session):
    db_coach = db.query(models.Coach).filter(models.Coach.id == coach_id).first()
    return db_coach
