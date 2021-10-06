"""
选人算法
"""

import models
import crud
import game_configs
from utils import logger, utils
from modules.computed_data_app import ComputedPlayer

from typing import List, Dict
from fastapi import Depends
from core.db import get_db
from sqlalchemy.orm import Session
import random


class PlayerSelector:
    def __init__(self, club_id: int, db: Session):
        self.db = db
        self.club_id = club_id
        self.club_model = crud.get_club_by_id(db=self.db, club_id=self.club_id)

    def select_players(self, is_random: bool = True) -> (List[models.Player], List[str]):
        """
        选人
        :return: (选定球员, 选定球员对应的位置)
        """
        if is_random:
            a = random.choice([1, 2])
            if a == 1:
                players_model, locations_list = self.select_players1(self.club_model.players,
                                                                     self.club_model.coach.formation)
            else:
                players_model, locations_list = self.select_players2(self.club_model.players,
                                                                     self.club_model.coach.formation)
        else:
            players_model1, locations_list1 = self.select_players1(self.club_model.players,
                                                                   self.club_model.coach.formation)
            players_model2, locations_list2 = self.select_players2(self.club_model.players,
                                                                   self.club_model.coach.formation)

            capa1 = self.get_total_capa(players_model1, locations_list1)
            capa2 = self.get_total_capa(players_model2, locations_list2)
            if capa1 >= capa2:
                players_model, locations_list = players_model1, locations_list1
            else:
                players_model, locations_list = players_model2, locations_list2

        return players_model, locations_list

    def select_players1(self, players: List[models.Player], formation: str) -> (List[models.Player], List[str]):
        """
        以球员最高位置能力值为标准，选择11名球员
        :param players: 球员列表
        :param formation: 阵型名
        :return: (选定球员, 选定球员对应的位置)
        """

        final_players = []  # 最终人选
        final_locations = []  # 最终人选对应的位置
        location_dict: Dict[str, float] = game_configs.formations[formation].copy()  # 这里一定要copy()！因为涉及变量的改变
        # 生成筛选后的、每个球员的位置能力倒序字典，作为待选区
        players_lo_capa_dict: Dict[models.Player, List[List[str, float]]] = {
            player: self.filter_formation_capa(player, formation) for player in players}
        while True:
            # 选择队伍中拥有（某位置上）最高能力值的球员及位置名
            player, lo_name = self.get_highest_capa_player(players_lo_capa_dict)
            if not lo_name:
                print(len(final_players))
            if location_dict[lo_name]:
                # 若此位置仍有空，添加
                location_dict[lo_name] -= 1
                final_players.append(player)
                final_locations.append(lo_name)
                # 从待选区移除已选进的球员
                del players_lo_capa_dict[player]
            else:
                # 若此位置已满，将此位置从此球员的倒序能力表中删除
                players_lo_capa_dict[player].pop(0)
            if len(final_players) == 11:
                break
            # DEBUG
            # print('名单：')
            # for x in zip(final_players, final_locations):
            #     print('{}: {}, {}'.format(x[1], x[0].translated_name, self.get_location_rating(x[0], x[1])))
            # print('---------------------------------')
            # for p in players:
            #     self.get_sorted_location_rating(p)
        return final_players, final_locations

    def filter_formation_capa(self, player: models.Player, formation: str) -> List[List]:
        """
        获取球员在各个位置的综合能力值，倒序排列，然后将阵型不包含的位置筛选掉
        :param player: 球员实例
        :param formation: 阵型名
        :return: 筛选后的位置综合能力值列表
        """
        # 这代码越来越怪了。。。
        location_dict: Dict[str, int] = game_configs.formations[formation]  # 记录阵型中各个位置人数
        location_list: List[str] = [name for name in location_dict.keys()]  # 拿到阵型包含的位置列表

        computed_player = ComputedPlayer(player.id, self.db)
        sorted_location_capa_list = computed_player.get_sorted_location_capa()
        sorted_location_capa_list_filter_by_formation = []  # 筛选后的位置综合能力值列表
        for x in sorted_location_capa_list:
            if x[0] in location_list:
                # 若阵型中存在此位置，选进
                sorted_location_capa_list_filter_by_formation.append(x)
        return sorted_location_capa_list_filter_by_formation

    @staticmethod
    def get_highest_capa_player(players_location_capa_dict: Dict[models.Player, List[List]]) -> (
            models.Player, str):
        """
        获取队伍中拥有最高位置综合值的球员实例及其位置
        :param players_location_capa_dict: 所有球员各项位置综合能力表
        :return: Tuple(best_player, best_lo_name)
        """
        best_player = None
        best_lo_capa_list = []
        for player, lo_capa_list in players_location_capa_dict.items():
            if not lo_capa_list:
                logger.error('球员能力列表为空！')
                continue
            if not best_player or lo_capa_list[0][1] > best_lo_capa_list[0][1]:
                best_player = player
                best_lo_capa_list = lo_capa_list
        best_lo_name = best_lo_capa_list[0][0] if best_lo_capa_list else None
        return best_player, best_lo_name

    def select_players2(self, players: List[models.Player], formation: str) -> (List[models.Player], List[str]):
        """
        以每个位置最高能力为标准，选择11名球员
        :param players: 球员列表
        :param formation: 阵型名
        :return: (选定球员, 选定球员对应的位置)
        """
        final_players = []  # 最终人选
        final_locations = []  # 最终人选对应的位置
        location_dict: Dict[str, float] = game_configs.formations[formation].copy()  # 这里一定要copy()！因为涉及变量的改变
        location_dict = {key: value for key, value in location_dict.items() if value > 0}
        # 像切肉一样一层一层（一个人一个人）把位置切下来
        layers_location_list = []
        while True:
            one_layer = []
            count = 0
            for key, value in location_dict.items():
                if value > 0:
                    one_layer.append(key)
                    location_dict[key] -= 1
                    value -= 1
                if value == 0:
                    count += 1
            layers_location_list.append(one_layer)
            if count == len(location_dict):
                break

        selecting_players = players.copy()
        for locations in layers_location_list:
            # 对每一层位置进行挑选
            lo_rank = {x: dict() for x in locations}  # 每个位置倒序排序的球员综合能力
            # 构建lo_rank
            for player in selecting_players:
                computed_player = ComputedPlayer(player_id=player.id, db=self.db, player_model=player)
                sorted_location_capa = computed_player.get_sorted_location_capa()
                for x in sorted_location_capa:
                    if x[0] in locations:
                        lo_rank[x[0]][player] = x[1]

            while True:
                # 拿到拥有最高综合能力值球员的位置名

                # 拿到每个位置中综合能力最高的数值
                lo_max_capa = dict()
                for key, value in lo_rank.items():
                    max_key = utils.get_key_with_max_value(value)
                    lo_max_capa[key] = value[max_key]

                max_capa_location = utils.get_key_with_max_value(lo_max_capa)

                target_player = utils.get_key_with_max_value(lo_rank[max_capa_location])
                # 放球员，放位置
                final_players.append(target_player)
                final_locations.append(max_capa_location)
                # 删球员，删位置
                selecting_players.remove(target_player)
                lo_rank.pop(max_capa_location)
                if not lo_rank:
                    break
                for key, value in lo_rank.items():
                    if target_player in value.keys():
                        value.pop(target_player)
        # # DEBUG
        # print('名单：')
        # for x in zip(final_players, final_locations):
        #     print('{}: {}'.format(x[1], x[0].translated_name))
        # print('---------------------------------')
        return final_players, final_locations

    def get_total_capa(self, players: List[models.Player], locations: List[str]) -> float:
        """
        获取队伍总分
        :param players: 球员实例
        :param locations: 对应的位置
        :return: 分数
        """
        result = 0
        for x in zip(players, locations):
            computed_player = ComputedPlayer(player_id=x[0].id, db=self.db, player_model=x[0])
            result += computed_player.get_location_capa(lo_name=x[1])
        return result
