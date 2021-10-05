from sqlalchemy.orm import Session
import models
import schemas
from utils import logger


def create_calendar(db: Session, calendar: schemas.CalendarCreate):
    db_calendar = models.Calendar(**calendar.dict())
    db.add(db_calendar)
    db.commit()
    db.refresh(db_calendar)
    return db_calendar


def update_calendar(db: Session, calendar_id: int, attri: dict):
    db_calendar = db.query(models.Calendar).filter(models.Calendar.id == calendar_id).first()
    for key, value in attri.items():
        setattr(db_calendar, key, value)
    db.commit()
    return db_calendar


def get_calendar_by_id(db: Session, calendar_id: int):
    db_calendar = db.query(models.Calendar).filter(models.Calendar.id == calendar_id).first()
    return db_calendar