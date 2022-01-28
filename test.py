import time
from modules import next_turn_app, transfer_app
from core.db import get_session
from utils import logger
import crud

db = get_session()
save_model = crud.get_save_by_id(db=db, save_id=1)
clubs = crud.get_clubs_by_save(db=db, save_id=1)

# s = time.time()
# logger.info('开始adjust_finance')
# for club in clubs:
#     # logger.info('{}'.format(club.name))
#     transfer_club = transfer_app.Club(db=db, club_id=club.id, date=save_model.date, season=save_model.season)
#     transfer_club.adjust_finance()
#
# logger.info('开始judge_on_sale')
# for club in clubs:
#     # logger.info('{}'.format(club.name))
#     transfer_club = transfer_app.Club(db=db, club_id=club.id, date=save_model.date, season=save_model.season)
#     transfer_club.judge_on_sale()
#
# logger.info('开始judge_buy')
# for club in clubs:
#     # logger.info('{}'.format(club.name))
#     transfer_club = transfer_app.Club(db=db, club_id=club.id, date=save_model.date, season=save_model.season)
#     transfer_club.judge_buy(save_id=1)
# e = time.time()
# logger.info('共耗时{}s'.format(e - s))
#
# db.commit()
# logger.info('commit完成')

s = time.time()
logger.info('开始receive_offer')
for club in clubs:
    transfer_club = transfer_app.Club(db=get_session(), club_id=club.id, date=save_model.date, season=save_model.season)
    transfer_club.receive_offer(save_id=1)

logger.info('开始make_offer')
for club in clubs:
    transfer_club = transfer_app.Club(db=get_session(), club_id=club.id, date=save_model.date, season=save_model.season)
    transfer_club.make_offer(save_id=1)

e = time.time()
logger.info('共耗时{}s'.format(e - s))

db.commit()
logger.info('commit完成')
