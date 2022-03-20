import string
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
import crud
import utils
from core.db import get_db, drop_all
from modules import game_app, computed_data_app, transfer_app
from utils import Date

router = APIRouter()


@router.get('/make-offer-by-user')  # 玩家向球员报价
def make_offer_by_user(target_player_id: int, offer_price: int, db: Session = Depends(get_db),
                       save_model=Depends(utils.get_current_save)):
    negotiate_list = crud.get_offers_from_player_by_status(db=db, save_id=save_model.id,
                                                           buyer_id=save_model.player_club_id,
                                                           season=save_model.season, status='s')
    for offer in negotiate_list:
        if offer.target_id == target_player_id:
            return {'status': 'repeat offer'}
    negotiate_list = crud.get_offers_from_player_by_status(db=db, save_id=save_model.id,
                                                           buyer_id=save_model.player_club_id,
                                                           season=save_model.season, status='n')
    for offer in negotiate_list:
        if offer.target_id == target_player_id:
            return {'status': 'repeat offer'}
    negotiate_list = crud.get_offers_from_player_by_status(db=db, save_id=save_model.id,
                                                           buyer_id=save_model.player_club_id,
                                                           season=save_model.season, status='u')
    for offer in negotiate_list:
        if offer.target_id == target_player_id:
            return {'status': 'repeat offer'}
    user_transfer_club = transfer_app.Club(db=db, club_id=save_model.player_club_id, date=save_model.date,
                                           season=save_model.season)
    if user_transfer_club.team_model.finance < offer_price:
        return {'status': 'can not afford'}
    user_transfer_club.make_offer_by_user(save_id=save_model.id, target_player_id=target_player_id,
                                          offer_price=offer_price)
    return {'status': 'succeed'}


@router.get('/negotiate-wage')
# 玩家与球员协商工资
def negotiate_wage(target_player_id: int, offer_wage: float, db: Session = Depends(get_db),
                   save_model=Depends(utils.get_current_save)):
    target_player = transfer_app.Player(
        db=db,
        player_id=target_player_id,
        season=save_model.season,
        date=save_model.date)
    player_status = target_player.negotiate_wage(offer_wage=offer_wage, save_id=save_model.id,
                                                 buyer_club_id=save_model.player_club_id)
    if player_status == 1:
        return {'status': 'success'}  # 返回true则已完成转会
    elif player_status == 0:
        return {'status': 'fail'}
    else:
        return {'status': 'no offer'}


@router.get('/get-on-sale-players')
def get_on_sale_players(offset: int, limit: int, attri: str = "id", order=0,
                        db: Session = Depends(get_db),
                        save_model=Depends(utils.get_current_save)) -> List[schemas.PlayerShow]:
    """
    获取所有被挂牌的球员
    attri：排序标签
    order：0升序，1降序
    """
    db_players: List[models.Player] = crud.get_on_sale_players_by_save(db=db, save_id=save_model.id,
                                                                       offset=offset, limit=limit, order=order,
                                                                       attri=attri)
    player_show: List[schemas.PlayerShow] = []
    for player_model in db_players:
        player_info = computed_data_app.ComputedPlayer(player_id=player_model.id,
                                                       db=db,
                                                       season=save_model.season,
                                                       date=save_model.date).get_show_data()
        player_show.append(player_info)
    return player_show


@router.get('/get-players-by-attri')
def get_players_by_attri(offset: int, limit: int, attri: str = "club_name", value="曼彻斯特城",
                         db: Session = Depends(get_db),
                         save_model=Depends(utils.get_current_save)) -> List[schemas.PlayerShow]:
    """
    根据属性获取一定量的球员
    :param offset：偏移
    :param limit：条数
    :param attri：translated_name, club_name, translated_nationality, location
    :param value：中文名，中文俱乐部名，中文国家名，大写位置名
    """
    db_players: List[models.Player] = crud.get_all_players_by_save_n_attri(db=db,
                                                                           save_id=save_model.id, attri=attri,
                                                                           value=value, offset=offset, limit=limit)
    player_show: List[schemas.PlayerShow] = []
    if db_players:
        for player_model in db_players:
            player_info = computed_data_app.ComputedPlayer(player_id=player_model.id,
                                                           db=db,
                                                           season=save_model.season,
                                                           date=save_model.date).get_show_data()
            player_show.append(player_info)
    return player_show


@router.get('/negotiate-failed')
def negotiate_failed(target_id: int, db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    negotiate_list = crud.get_offers_from_player_by_status(db=db, save_id=save_model.id,
                                                           buyer_id=save_model.player_club_id,
                                                           season=save_model.season, status='n')
    for offer in negotiate_list:
        if offer.target_id == target_id:
            offer.status = 'r'
            return {'status': 'set complete'}


@router.get('/get-negotiate-list')
# 获取待谈判列表
def get_negotiate_list(db: Session = Depends(get_db),
                       save_model=Depends(utils.get_current_save)):
    result_show = []
    negotiate_list = crud.get_offers_from_player_by_status(db=db, save_id=save_model.id,
                                                           buyer_id=save_model.player_club_id,
                                                           season=save_model.season, status='n')
    for offer in negotiate_list:
        player_info = computed_data_app.ComputedPlayer(player_id=offer.target_id,
                                                       db=db,
                                                       season=save_model.season,
                                                       date=save_model.date).get_show_data()
        result_show.append({'player_info': player_info, 'offer': offer})
    return result_show


@router.get('/get-rejected-offers')
# 获取被拒绝列表
def get_rejected_offers(db: Session = Depends(get_db),
                        save_model=Depends(utils.get_current_save)):
    result_show = []
    negotiate_list = crud.get_offers_from_player_by_status(db=db, save_id=save_model.id,
                                                           buyer_id=save_model.player_club_id,
                                                           season=save_model.season, status='r')
    for offer in negotiate_list:
        player_info = computed_data_app.ComputedPlayer(player_id=offer.target_id,
                                                       db=db,
                                                       season=save_model.season,
                                                       date=save_model.date).get_show_data()
        result_show.append({'player_info': player_info, 'offer': offer})
    return result_show
