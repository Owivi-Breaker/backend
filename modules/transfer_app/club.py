import functools
import numpy as np
from sqlalchemy.orm import Session

from modules import transfer_app
from utils import utils, logger
import game_configs
import crud
import schemas
from modules.game_app import game_eve_app
from modules.game_app.player_selector import PlayerSelector
import models

import random
from typing import Dict, List, Sequence, Set, Tuple, Optional
import datetime


class Club:
    def __init__(self, db: Session, club_id: int, season: int, date: str,
                 club_model: models.Club = None):
        self.db = db
        self.club_id = club_id
        self.season = season
        self.date = date
        self.team_model = club_model if club_model else crud.get_club_by_id(db=self.db, club_id=self.club_id)
        self.name = self.team_model.name
        self.players: List[transfer_app.Player] = []  # 球员列表
        self.target_players = []
        self.init_players()

    def init_players(self):
        """
        写入球员
        """
        db_club = crud.get_club_by_id(db=self.db, club_id=self.club_id)
        player_models: List[models.Player] = []
        player_models.extend(db_club.players)
        for player_model in player_models:
            self.players.append(
                transfer_app.Player(db=self.db, player_model=player_model, season=self.season, date=self.date))

    def adjust_finance(self):
        """
        全队球员工资更新,财政不足最贵挂牌
        """
        wage_chart = {}
        for player in self.players:
            player_wage = {player: player.wanna_wage()}
            wage_chart.update(player_wage)
        wage_diff = self.team_model.finance - (sum(wage_chart.values()) * 52)  # 球队资金 - 今年工资
        if wage_diff > 0:
            for player in self.players:
                actual_wage = round(np.random.normal(player.wanna_wage(), 2), 3)  # 工资正态分布，保留三位
                if actual_wage <= 0:
                    actual_wage = player.wanna_wage()
                player.adjust_wage(actual_wage)
        else:
            sorted(wage_chart.items(), key=lambda x: x[1], reverse=True)  # 工资降序
            exp_player = list(wage_chart.keys())[0]  # 工资最高的球员，挂牌
            crud.update_player(self.db, exp_player.player_model.id, attri={"on_sale": True})
            for player in self.players:
                actual_wage = round(np.random.normal(player.wanna_wage() * 0.8, 2), 3)
                if actual_wage <= 0:
                    actual_wage = player.wanna_wage()
                player.adjust_wage(actual_wage)  # TODO 如果降薪20%还不够

    def on_sale(self):
        """
        全队球员判断是否挂牌
        """
        for player in self.players:
            if player.want_leave():  # ai球队，球员想走就挂牌
                crud.update_player(self.db, player.player_model.id, attri={"on_sale": True})
            else:
                crud.update_player(self.db, player.player_model.id, attri={"on_sale": False})

    def judge_improve_lo(self):
        """
        单个位置能力值最强的球员 其能力值高于第二名 7 点及以上，进行补强操作
        返回待补强位置列表
        """
        lo_list = []
        for lo in ["ST", "CM", "LW", "RW", "CB", "LB", "RB", "GK", "CAM", "LM", "RM", "CDM"]:
            if self.compare_best2(lo):
                lo_list.append(lo)
        return lo_list

    def best_cap_in_team(self, pos):
        """
        返回球队中指定位置能力最高的能力值
        """
        cap_chart = {}
        for player in self.players:
            if player.computed_player.get_top_capa_n_location()[0] == pos:
                data = player.computed_player.get_top_capa_n_location()[1]
                info = {player: data}
                cap_chart.update(info)
        sorted(cap_chart.items(), key=lambda x: x[1], reverse=True)  # 能力值降序
        return list(cap_chart.values())[0]

    def compare_best2(self, pos):
        """
        比较队伍中最擅长位置为指定位置的所有球员中前两名的能力值
        差距大于7，返回TRUE
        """
        cap_chart = {}
        for player in self.players:
            if player.computed_player.get_top_capa_n_location()[0] == pos:
                data = player.computed_player.get_top_capa_n_location()[1]
                info = {player: data}
                cap_chart.update(info)
        if len(cap_chart) < 2:
            pass
        else:
            sorted(cap_chart.items(), key=lambda x: x[1], reverse=True)  # 能力值降序
            if list(cap_chart.values())[0] - list(cap_chart.values())[1] > 7:  # 能力值前两名差7
                return True

    def judge_buy(self, save_id):
        """
        挑选三名目标球员加入转会目标表
        """
        self.target_players = []
        finance = self.team_model.finance * 0.75  # 转会窗可用资金
        lo_list = self.judge_improve_lo()  # 待补强位置列表
        target_club_list = []  # 范围内的球队
        target_players = []  # 目标球员,临时列表
        for club in crud.get_clubs_by_save(db=self.db, save_id=save_id):
            if self.team_model.reputation - 15 < club.reputation < self.team_model.reputation + 15 \
                    and int(club.id) != int(self.club_id):
                target_club_list.append(club)
        target_club_list = random.sample(target_club_list, 5)  # 少挑几只队
        for club in target_club_list:
            for player in club.players:
                transfer_player = transfer_app.Player(db=self.db, player_model=player, season=self.season,
                                                      date=self.date)
                if transfer_player.computed_player.get_top_capa_n_location()[0] in lo_list and \
                        transfer_player.computed_player.get_values() < finance and \
                        transfer_player.computed_player.get_top_capa_n_location()[1] >= self.best_cap_in_team(
                    transfer_player.computed_player.get_top_capa_n_location()[0]) - 2:
                    target_players.append(transfer_player)  # 满足筛选条件的球员
        for sorting_player in target_players:
            if sorting_player.on_sale:
                self.target_players.append(sorting_player)  # 挂牌优先
        if len(self.target_players) > 3:
            self.target_players = random.sample(self.target_players, 3)
        elif len(self.target_players) < 3:
            diff = 3 - len(self.target_players)
            if len(target_players) < diff:
                pass
            else:
                for player in random.sample(target_players, diff):
                    self.target_players.append(player)
        for export_player in self.target_players:
            crud.create_target_player(self.db,
                                      self.exported_target_player_schemas(player=export_player, save_id=save_id))
        self.db.commit()

    def exported_target_player_schemas(self, save_id, player: transfer_app.Player) -> schemas.Target_PlayerCreate:
        """
        导出目标球员 schemas
        """
        data = {
            'buyer_id': self.club_id,
            'target_id': player.player_model.id,
            'season': self.season,
            'save_id': save_id
        }
        target_data = schemas.Target_PlayerCreate(**data)
        return target_data

    def exported_offer_player_schemas(self, save_id, offer_price, player: transfer_app.Player) -> schemas.Offer_Create:
        """
        导出报价 schemas
        """
        data = {
            'buyer_id': self.club_id,
            'target_id': player.player_model.id,
            'target_club_id': player.player_model.club_id,
            'offer_price': offer_price,
            'season': self.season,
            'save_id': save_id,
            'status': 'w'
        }
        offer_data = schemas.Offer_Create(**data)
        return offer_data

    def make_offer(self, save_id):
        """
        挑选目标发出报价，存至报价表
        """
        query_str = "and_(models.Target_player.save_id=='{}', models.Target_player.buyer_id=='{}',models.offer.season=='{}')".format \
            (save_id, self.club_id, self.season)
        target_list = crud.get_target_by_attri(db=self.db,attri=query_str)  # 目标球员列表，从数据库中查
        if len(target_list) != 0:  # 有目标球员
            query_str = "and_(models.offer.save_id=='{}', models.offer.buyer_id=='{}',models.offer.season=='{}')".format \
                (save_id, self.club_id, self.season)
            offer_list = crud.get_offer_by_attri(db=self.db, attri=query_str)  # 查找本赛季已发过的offer
            if len(offer_list) == 0:  # 还没做过报价
                offer_player = transfer_app.Player(db=self.db,
                                                   player_model=crud.get_player_by_id(target_list[0].target_id,
                                                                                      db=self.db), season=self.season,
                                                   date=self.date)
                offer_price = offer_player.offer_price(self.club_id)
                crud.create_offer(self.db,
                                  self.exported_offer_player_schemas(save_id=save_id,
                                                                     player=offer_player,
                                                                     offer_price=offer_price))  # 发出报价
                print(str(self.name) + "报价" + str(offer_player.player_model.name) + " " + str(offer_price) + "w!")
            else:
                for offer in offer_list:
                    if offer.status == 's':  # 交易成功
                        # TODO 扣钱
                        self.init_players()  # 更新球员
                        self.adjust_finance()  # TODO: 慢
                    if offer.status == 'r':  # 被拒绝
                        query_str = "and_(models.offer.id=='{}')".format(offer.id)
                        crud.del_offer_by_attri(db=self.db, attri=query_str)  # 删掉上一次的报价
                        if offer.offer_price < self.team_model.finance * 0.75:  # 重新报价
                            offer_player = transfer_app.Player(db=self.db,
                                                               player_model=crud.get_player_by_id(
                                                                   target_list[0].target_id,
                                                                   db=self.db), season=self.season,
                                                               date=self.date)
                            crud.create_offer(self.db,
                                              self.exported_offer_player_schemas(save_id=save_id,
                                                                                 player=offer_player,
                                                                                 offer_price=offer.offer_price))  # 发出报价
                            print(str(self.name) + "报价" + str(offer_player.player_model.name) + " " + str(
                                offer.offer_price) + "w!")
                    if offer.status == 'w':  # 等待回应
                        pass

    def receive_offer(self, save_id):
        offer_dict = {}  # 报价字典，球员id：最终会接受的offer
        waiting_offer = []  # 待处理offer
        query_str = "and_(models.offer.save_id=='{}', models.offer.target_club_id=='{}',models.offer.season=='{}')".format \
            (save_id, self.club_id, self.season)
        offer_list = crud.get_offer_by_attri(db=self.db, attri=query_str)  # 查找本赛季收到的offer
        for offer in offer_list:
            if offer.status == 's':
                pass
            elif offer.status == 'r':
                pass
            elif offer.status == 'w':
                # TODO 不要必接受？
                waiting_offer.append(offer)
                player_id = offer.target_id
                if player_id not in offer_dict:
                    offer_dict.update({player_id: offer})
                else:
                    pre_buyer = offer_dict[player_id].buyer_id
                    now_club = crud.get_club_by_id(db=self.db, club_id=offer.buyer_id)  # 当前买家
                    pre_club = crud.get_club_by_id(db=self.db, club_id=pre_buyer)  # 前一个买家
                    pre_price = offer_dict[player_id].offer_price
                    if offer.offer_price > pre_price or now_club.reputation > pre_club.reputation:  # 报价更高或者俱乐部名气更高
                        offer_dict[player_id] = offer  # 更新报价字典中的offer
        for offer in waiting_offer:
            if offer not in offer_dict.values():
                crud.update_offer(db=self.db, offer_id=offer.id, attri={"offer_price": 999999})  # 拒绝报价，给买家返回一个不可能接受的报价
                crud.update_offer(db=self.db, offer_id=offer.id, attri={"status": 'r'})
            else:
                crud.update_offer(db=self.db, offer_id=offer.id, attri={"status": 's'})  # 接受报价
                crud.update_player(db=self.db, player_id=offer.target_id, attri={"club_id": offer.buyer_id})
                crud.update_player(db=self.db, player_id=offer.target_id, attri={"on_sale": False})
                self.init_players()
                print(str(crud.get_player_by_id(player_id=offer.target_id, db=self.db).name) +
                      " 从 " + str(self.name) + " 转会至 " +
                      str(crud.get_club_by_id(db=self.db, club_id=offer.buyer_id).name) +
                      " " + str(offer.offer_price) + "w!")
                # TODO  加钱
