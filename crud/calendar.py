from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import List

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


def get_calendar_by_save_id(db: Session, save_id: int) -> List[models.Calendar]:
    """
    获取指定存档id中的所有日程表项
    """
    db_calendars = db.query(models.Calendar).filter(models.Calendar.save_id == save_id).all()
    return db_calendars


def get_calendars_by_attri(db: Session, query_str: str, only_one: bool = False) -> List[models.Calendar]:
    if only_one:
        db_calendar = db.query(models.Calendar).filter(eval(query_str)).first()
        return db_calendar
    else:
        db_calendars = db.query(models.Calendar).filter(eval(query_str)).all()
        return db_calendars
