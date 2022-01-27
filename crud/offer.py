from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from utils import logger


def create_offer(db: Session, offer: schemas.Offer_Create):
    db_offer = models.offer(**offer.dict())
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    return db_offer


def update_offer(db: Session, offer_id: int, attri: dict):
    db_offer = db.query(models.offer).filter(models.offer.id == offer_id).first()
    for key, value in attri.items():
        setattr(db_offer, key, value)
    db.commit()
    return db_offer


def get_offer__by_save_id(db: Session, save_id: int) -> List[models.offer]:
    """
    获取指定存档id中的所有报价项
    """
    db_offer = db.query(models.offer).filter(models.offer.save_id == save_id).all()
    return db_offer


def get_offer_by_attri(db: Session, attri: str) -> List[models.offer]:
    db_offer = db.query(models.offer).filter(eval(attri)).all()
    return db_offer


def del_offer_by_attri(db: Session, attri: str):
    db_offer = db.query(models.offer).filter(eval(attri)).first()
    db.delete(db_offer)
    db.commit()
