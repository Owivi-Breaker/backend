import datetime
import random
from typing import List

import numpy as np
from sqlalchemy.orm import Session

import crud
import models
import schemas
from modules import transfer_app, computed_data_app
from utils import utils, logger


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
        for player_model in self.team_model.players:
            self.players.append(
                transfer_app.Player(
                    db=self.db, player_id=player_model.id,
                    player_model=player_model, season=self.season,
                    date=self.date))

    def adjust_finance(self):
        """
        全队球员工资更新; 若财政不足,最贵挂牌,其余球员降薪20%
        """
        wage_chart = {}
        for player in self.players:
            player_wage = {player: player.wanna_wage()}
            wage_chart.update(player_wage)
        wage_diff = self.team_model.finance - (sum(wage_chart.values()) * 52)  # 球队资金 - 今年工资
        if wage_diff > 0:
            for player in self.players:
                actual_wage = round(np.random.normal(wage_chart[player], 2), 3)  # 工资正态分布，保留三位
                if actual_wage <= 0:
                    actual_wage = wage_chart[player]
                player.adjust_wage(actual_wage)
        else:
            # 钱不够咯 挂牌
            sorted(wage_chart.items(), key=lambda x: x[1], reverse=True)  # 工资降序
            exp_player: transfer_app.Player = list(wage_chart.keys())[0]  # 工资最高的球员 挂牌
            exp_player.player_model.on_sale = True
            for player in self.players:
                # 其余球员 降薪20%
                actual_wage = round(np.random.normal(wage_chart[player] * 0.8, 2), 3)
                if actual_wage <= 0:
                    actual_wage = wage_chart[player]
                player.adjust_wage(actual_wage)  # TODO 如果降薪20%还不够
        # self.db.commit()

    def judge_on_sale(self):
        """
        全队球员判断是否挂牌
        """
        for player in self.players:
            if player.want_leave():  # ai球队，球员想走就挂牌
                player.player_model.on_sale = True
            else:
                player.player_model.on_sale = False

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
            top_lo, top_capa = player.computed_player.get_top_lo_n_capa()
            if top_lo == pos:
                info = {player: top_capa}
                cap_chart.update(info)
        sorted(cap_chart.items(), key=lambda x: x[1], reverse=True)  # 能力值降序
        return list(cap_chart.values())[0]

    def compare_best2(self, pos: str):
        """
        比较队伍中最擅长位置为指定位置的所有球员中前两名的能力值
        差距大于7，返回TRUE
        """
        cap_chart = {}
        for player in self.players:
            top_lo, top_capa = player.computed_player.get_top_lo_n_capa()
            if top_lo == pos:
                data = top_capa
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

        # 寻找目标球队
        target_club_list = []  # 范围内的球队
        for club in crud.get_clubs_by_save(db=self.db, save_id=save_id):
            if self.team_model.reputation - 15 < club.reputation < self.team_model.reputation + 15 \
                    and int(club.id) != int(self.club_id):
                target_club_list.append(club)
        if len(target_club_list) > 5:
            target_club_list = random.sample(target_club_list, 5)  # 少挑几只队

        # 寻找目标球员
        target_players: List[transfer_app.Player] = []  # 目标球员,临时列表
        for club in target_club_list:
            for player in club.players:
                transfer_player = transfer_app.Player(db=self.db, player_id=player.id, season=self.season,
                                                      date=self.date, player_model=player)
                top_lo, top_capa = transfer_player.computed_player.get_top_lo_n_capa()
                if top_lo in lo_list \
                        and transfer_player.computed_player.get_values() < finance and \
                        top_capa >= self.best_cap_in_team(top_lo) - 2:
                    target_players.append(transfer_player)  # 满足筛选条件的球员

        # 将对多三个球员作为转会目标
        for sorting_player in target_players:
            if sorting_player.on_sale:
                self.target_players.append(sorting_player)  # 挂牌优先
                target_players.remove(sorting_player)

        if len(self.target_players) > 3:
            self.target_players = random.sample(self.target_players, 3)
        elif len(self.target_players) < 3:
            # 挂牌球员还不够
            diff = 3 - len(self.target_players)
            if len(target_players) < diff:
                self.target_players.extend(target_players)
            else:
                # 补满
                for player in random.sample(target_players, diff):
                    self.target_players.append(player)

        for export_player in self.target_players:
            crud.create_target_player(
                self.db,
                self.exported_target_player_schemas(player=export_player, save_id=save_id))
        # self.db.commit()

    def exported_target_player_schemas(
            self, save_id, player: transfer_app.Player) -> schemas.TargetPlayerCreate:
        """
        导出目标球员 schemas
        """
        data = {
            'buyer_id': self.club_id,
            'target_id': player.player_model.id,
            'season': self.season,
            'save_id': save_id
        }
        target_data = schemas.TargetPlayerCreate(**data)
        return target_data

    def exported_offer_player_schemas(
            self, save_id, offer_price, player: transfer_app.Player) -> schemas.OfferCreate:
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
        offer_data = schemas.OfferCreate(**data)
        return offer_data

    def exported_offer_player_schemas_for_user(
            self, save_id, offer_price, player: transfer_app.Player) -> schemas.OfferCreate:
        """
        导出专用于玩家的报价 schemas
        """
        data = {
            'buyer_id': self.club_id,
            'target_id': player.player_model.id,
            'target_club_id': player.player_model.club_id,
            'offer_price': offer_price,
            'season': self.season,
            'save_id': save_id,
            'status': 'u'
        }
        offer_data = schemas.OfferCreate(**data)
        return offer_data

    def make_offer(self, save_id: int):
        """
        挑选目标发出报价，存至报价表
        """
        # 获取目标球员列表
        target_list = crud.get_targets_by_club(
            db=self.db, save_id=save_id, club_id=self.club_id, season=self.season)
        now_date = utils.Date(self.date)
        # 剔除拒绝时间小于7天的目标球员
        target_list: List[models.TargetPlayer] = [
            t for t in target_list if
            not t.rejected_date or utils.Date(t.rejected_date).date + datetime.timedelta(days=7) < now_date.date
        ]

        if len(target_list) > 0:  # 有目标球员
            # 查找本赛季的有效报价
            offer_list: List[models.Offer] = crud.get_active_offers_by_club(
                db=self.db, save_id=save_id, buyer_id=self.club_id, season=self.season)

            if len(offer_list) == 0:
                # 还没做过报价
                offer_player = transfer_app.Player(
                    db=self.db,
                    player_id=target_list[0].target_id,
                    season=self.season,
                    date=self.date)
                offer_price = offer_player.get_offer_price(self.club_id)
                crud.create_offer(
                    self.db,
                    self.exported_offer_player_schemas(
                        save_id=save_id,
                        player=offer_player,
                        offer_price=offer_price))  # 发出报价
                logger.info(str(self.name) + "报价" + str(offer_player.player_model.name) + " " + str(offer_price) + "w")
            else:
                for offer in offer_list:
                    if offer.status == 'r':
                        target_player: models.TargetPlayer = crud.get_target_by_player_id_n_buyer_id(
                            db=self.db, target_id=offer.target_id, buyer_id=self.club_id)
                        if target_player in target_list:
                            # 被拒绝 且可以报价
                            crud.delete_offer_by_id(db=self.db, offer_id=offer.id)  # 删掉上一次的报价
                            if offer.offer_price * 1.2 < self.team_model.finance * 0.75:
                                # 重新报价
                                offer_player = transfer_app.Player(
                                    db=self.db,
                                    player_id=offer.target_id,
                                    season=self.season,
                                    date=self.date)
                                crud.create_offer(
                                    self.db,
                                    self.exported_offer_player_schemas(
                                        save_id=save_id,
                                        player=offer_player,
                                        offer_price=offer.offer_price * 1.2))  # 发出报价
                                logger.info(str(self.name) + "再次报价" + str(offer_player.player_model.name) + " " + str(
                                    offer.offer_price * 1.2) + "w")

    def make_offer_by_user(self, save_id: int, target_player_id: int, offer_price: int):
        """
        玩家向特定球员发出报价，存至报价表
        """
        target_player = transfer_app.Player(
            db=self.db,
            player_id=target_player_id,
            season=self.season,
            date=self.date)
        crud.create_offer(
            self.db,
            self.exported_offer_player_schemas_for_user(
                save_id=save_id,
                player=target_player,
                offer_price=offer_price))  # 发出报价
        logger.info(str(self.name) + "报价" + str(target_player.player_model.name) + " " + str(offer_price) + "u")

    def receive_offer(self, save_id):
        """
        决定是否接受报价
        """
        offer_dict = {}  # 报价字典，球员id:最终会接受的offer
        waiting_offer = []  # 待处理offer

        # 查找本赛季收到的offer
        offer_list: List[models.Offer] = crud.get_offers_by_target_club(
            db=self.db, save_id=save_id, target_club_id=self.club_id, season=self.season)

        for offer in offer_list:
            if offer.status == 's':
                pass
            elif offer.status == 'r':
                pass
            elif offer.status == 'w' or offer.status == 'u':  # w:待处理的offer，u:玩家的offer
                waiting_offer.append(offer)
                # 根据身价判断是否接受报价
                player = computed_data_app.ComputedPlayer(
                    player_id=offer.target_id, db=self.db,
                    season=self.season, date=self.date)
                values = player.get_values()
                if offer.offer_price >= np.random.normal(values * 1.1, values // 10):
                    # 接受报价
                    player_id = offer.target_id
                    if player_id not in offer_dict:
                        offer_dict.update({player_id: offer})
                    else:
                        pre_buyer = offer_dict[player_id].buyer_id
                        now_club = crud.get_club_by_id(db=self.db, club_id=offer.buyer_id)  # 当前买家
                        pre_club = crud.get_club_by_id(db=self.db, club_id=pre_buyer)  # 前一个买家
                        pre_price = offer_dict[player_id].offer_price
                        if offer.offer_price > pre_price:
                            # 报价更高
                            offer_dict[player_id] = offer  # 更新报价字典中的offer
                        elif offer.offer_price == pre_price and now_club.reputation > pre_club.reputation:
                            # 报价相等 但新俱乐部名气更高
                            offer_dict[player_id] = offer  # 更新报价字典中的offer
        # 在此统一处理所有报价
        for offer in waiting_offer:
            if offer not in offer_dict.values():
                print(str(offer.id) + str(offer.status))
                # 拒绝报价
                if offer.status == 'w':
                    target_player: models.TargetPlayer = crud.get_target_by_player_id_n_buyer_id(
                        db=self.db, target_id=offer.target_id, buyer_id=offer.buyer_id)
                    target_player.rejected_date = str(self.date)  # 设置买方目标球员的拒绝时间
                offer.status = 'r'

                logger.info("{}拒绝了{}对{}的报价".format(
                    str(crud.get_club_by_id(db=self.db, club_id=offer.target_club_id).name),
                    str(crud.get_club_by_id(db=self.db, club_id=offer.buyer_id).name),
                    str(crud.get_player_by_id(player_id=offer.target_id, db=self.db).name)
                ))
            else:
                # 接受电脑球员报价
                # 修改球员状态
                if offer.status == 'w':  # 买方俱乐部不是玩家
                    crud.update_player(
                        db=self.db, player_id=offer.target_id,
                        attri={"club_id": offer.buyer_id,
                               "on_sale": False})  # 修改球员所属俱乐部
                    crud.delete_target_by_player_id_n_buyer_id(
                        db=self.db, target_id=offer.target_id, buyer_id=offer.buyer_id)  # 从target表中删除
                    logger.info(str(crud.get_player_by_id(player_id=offer.target_id, db=self.db).name) +
                                " 从 " + str(self.name) + " 转会至 " +
                                str(crud.get_club_by_id(db=self.db, club_id=offer.buyer_id).name) +
                                " " + str(offer.offer_price) + "w!")
                    #  加钱扣钱
                    self.team_model.finance += offer.offer_price
                    buyer = crud.get_club_by_id(db=self.db, club_id=offer.buyer_id)
                    buyer.finance -= offer.offer_price
                    p = transfer_app.Player(
                        db=self.db, player_id=offer.target_id, season=self.season, date=self.date)
                    wage = round(np.random.normal(p.wanna_wage(), 2), 3)
                    if wage < 0:
                        wage = p.wanna_wage()
                    p.adjust_wage(wage)  # 调整球员工资
                    offer.status = 's'  # 交易完成
                elif offer.status == 'u':  # 买方俱乐部是玩家
                    # 加钱 给钱
                    offer.status = 'n'  # 转到球员处工资谈判

    def improve_crew(self):
        """
        职员更新
        """
        willingness = random.randint(0, 1)  # 随机一个是否愿意升级
        if self.team_model.finance > 3000 and willingness == 1:  # TODO 具体升级要求再议
            crew = {'a': self.team_model.assistant,
                    'd': self.team_model.doctor,
                    's': self.team_model.scout,
                    'n': self.team_model.negotiator}
            sorted_crew = sorted(crew.items(), key=lambda kv: (kv[1], kv[0]))
            num = 1
            for i in range(len(sorted_crew)):
                if sorted_crew[i][1] == sorted_crew[0][1]:
                    num = i + 1  # 并列最低的个数
            if num == 1:  # 升级最低的
                target = sorted_crew[0][0]
            else:  # 随机挑选最低的
                target_num = random.randint(0, num - 1)
                target = sorted_crew[target_num][0]
            if target == 'a':
                self.team_model.assistant += 1
            elif target == 'd':
                self.team_model.doctor += 1
            elif target == 's':
                self.team_model.scout += 1
            elif target == 'n':
                self.team_model.negotiator += 1
            #  TODO 扣钱
