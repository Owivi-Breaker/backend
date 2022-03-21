from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from utils import logger


def create_offer(db: Session, offer: schemas.OfferCreate):
    db_offer = models.Offer(**offer.dict())
    db.add(db_offer)
    # db.commit()
    # db.refresh(db_offer)
    return db_offer


def get_offer_by_id(offer_id: int, db: Session) -> models.Offer:
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    return db_offer


def update_offer(db: Session, offer_id: int, attri: dict):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    for key, value in attri.items():
        setattr(db_offer, key, value)
    db.commit()
    return db_offer


def get_offer__by_save_id(db: Session, save_id: int) -> List[models.Offer]:
    """
    获取指定存档id中的所有报价项
    """
    db_offer = db.query(models.Offer).filter(models.Offer.save_id == save_id).all()
    return db_offer


def get_offer_by_attri(db: Session, attri: str) -> List[models.Offer]:
    db_offer = db.query(models.Offer).filter(eval(attri)).all()
    return db_offer


def get_offers_by_buyer(db: Session, save_id: int, buyer_id: int, season: int) -> List[models.Offer]:
    """
    获取指定俱乐部id为买家的报价
    :param save_id: 存档id
    :param buyer_id: 买家家俱乐部id
    :param season: 赛季
    """
    db_offers = db.query(models.Offer).filter(
        and_(models.Offer.save_id == save_id,
             models.Offer.buyer_id == buyer_id,
             models.Offer.season == season)).all()
    return db_offers


def get_offers_by_target_club(db: Session, save_id: int, target_club_id: int, season: int) -> List[models.Offer]:
    """
    获取指定俱乐部id为卖家的报价
    :param save_id: 存档id
    :param target_club_id: 买家家俱乐部id
    :param season: 赛季
    """
    db_offers = db.query(models.Offer).filter(
        and_(models.Offer.save_id == save_id,
             models.Offer.target_club_id == target_club_id,
             models.Offer.season == season,
             models.Offer.status != 's')).all()
    return db_offers


def get_active_offers_by_club(db: Session, save_id: int, buyer_id: int, season: int) -> List[models.Offer]:
    """
    获取指定俱乐部id为买家的有效报价
    :param save_id: 存档id
    :param buyer_id: 买家家俱乐部id
    :param season: 赛季
    """
    db_offers = db.query(models.Offer).filter(
        and_(models.Offer.save_id == save_id,
             models.Offer.buyer_id == buyer_id,
             models.Offer.season == season,
             models.Offer.status != 's')).all()
    return db_offers


def get_offers_from_player_by_status(db: Session, save_id: int, buyer_id: int, season: int, status: str) -> List[
    models.Offer]:
    """
    根据状态获取玩家报价
    :param save_id: 存档id
    :param buyer_id: 买家家俱乐部id
    :param season: 赛季
    :param status: 状态 r,s,w,u
    """
    db_offers = db.query(models.Offer).filter(
        and_(models.Offer.save_id == save_id,
             models.Offer.buyer_id == buyer_id,
             models.Offer.season == season,
             models.Offer.status == status)).all()
    return db_offers


def get_rejected_offers_by_player(db: Session, save_id: int, buyer_id: int, season: int) -> List[models.Offer]:
    """
    获取玩家被拒绝的报价
    :param save_id: 存档id
    :param buyer_id: 买家家俱乐部id
    :param season: 赛季
    """
    db_offers = db.query(models.Offer).filter(
        and_(models.Offer.save_id == save_id,
             models.Offer.buyer_id == buyer_id,
             models.Offer.season == season,
             models.Offer.status == 'r')).all()
    return db_offers


def delete_offer_by_id(db: Session, offer_id: int):
    db_offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    db.delete(db_offer)
    db.commit()
