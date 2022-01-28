import numpy as np

from utils import utils, logger
import models
import schemas
import game_configs
from modules import computed_data_app
import crud
from typing import Dict, List, Sequence, Set, Tuple, Optional
import datetime
from sqlalchemy.orm import Session


class Player:
    # 球员类
    def __init__(self, db: Session, player_id: int, season: int, date: str, player_model: models.Player = None):
        self.db = db
        self.season = season
        self.date = date
        self.player_id = player_id
        self.player_model = player_model if player_model else crud.get_player_by_id(db=self.db, player_id=player_id)
        self.computed_player = computed_data_app.ComputedPlayer(
            player_id=self.player_model.id, db=self.db,
            player_model=self.player_model, season=self.season, date=self.date)
        self.age = self.player_model.age
        self.on_sale = self.player_model.on_sale

    def get_appearance_pre_year(self) -> int:
        """
        获取每赛季出场次数
        """
        age_diff = self.computed_player.get_age() - self.age if \
            (self.computed_player.get_age() - self.age) > 1 else 1  # 职业生涯年数
        appearance = self.get_total_appearance()
        ratio = (appearance // age_diff) + 1  # 出场次数除年数，计算每赛季出场次数
        return ratio

    def want_leave(self) -> bool:
        """
        判断要求转会
        TODO: 士气判断
        """
        # 不同年龄段的球员 根据出场次数满意程度判断是否要求转会
        ratio = self.get_appearance_pre_year()
        if 22 > self.computed_player.get_age() > 28:
            if ratio < 10:
                return True
            else:
                return False
        elif self.computed_player.get_age() < 18:
            return False
        else:
            if ratio < 5:
                return True
            else:
                return False

    def get_total_appearance(self) -> int:
        """
        获取总出场次数
        """
        total = self.player_model.ST_num + \
                self.player_model.CM_num + \
                self.player_model.LW_num + \
                self.player_model.RW_num + \
                self.player_model.CB_num + \
                self.player_model.LB_num + \
                self.player_model.RB_num + \
                self.player_model.GK_num + \
                self.player_model.CAM_num + \
                self.player_model.LM_num + \
                self.player_model.RM_num + \
                self.player_model.CDM_num
        return total

    def wanna_wage(self):
        """
        预期工资,身价/ 500
        TODO: 创建球员的时候工资不正确
        """
        proper_wage = self.computed_player.get_values() / 500
        return proper_wage

    def adjust_wage(self, real_wage):
        """
        修改球员工资
        """
        self.player_model.wages = real_wage
        # crud.update_player(self.db, self.player_model.id, attri={"wages": real_wage})

    def get_offer_price(self, buyer_id) -> float:
        """
        获取计算目标成交价
        :param buyer_id: 买方俱乐部id
        """
        club1 = crud.get_club_by_id(db=self.db, club_id=self.player_model.club_id)  # 卖方俱乐部
        club2 = crud.get_club_by_id(db=self.db, club_id=buyer_id)
        n1 = int(club1.negotiator)  # 卖方谈判水平
        n2 = int(club2.negotiator)
        if self.get_appearance_pre_year() > 25:
            offer_price = ((n1 - n2) * 10 + 200) * 0.01 * self.computed_player.get_values()
        else:
            offer_price = ((n1 - n2) * 10 + 120) * 0.01 * self.computed_player.get_values()
        offer_price = np.random.normal(offer_price, offer_price // 6)
        return offer_price