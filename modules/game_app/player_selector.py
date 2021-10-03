"""
选人算法
"""

import models
import crud
import game_configs
from utils import logger
from modules.computed_data_app import ComputedPlayer

from typing import List, Dict
from fastapi import Depends
from core.db import get_db
from sqlalchemy.orm import Session


class PlayerSelector:
    def __init__(self, club_id: int, db: Session):
        self.db = db
        self.club_id = club_id
        self.club_model = crud.get_club_by_id(db=self.db, club_id=self.club_id)

    def select_players(self) -> (List[models.Player], List[str]):
        """
        选人
        :return: (选定球员, 选定球员对应的位置)
        """
        players_model, locations_list = self.select_players1(self.club_model.players, self.club_model.coach.formation)
        return players_model, locations_list

    def select_players1(self, players: List[models.Player], formation: str) -> (List[models.Player], List[str]):
        """
        以球员最高位置能力值为标准，选择11名球员
        :param players: 球员列表
        :param formation: 阵型中每个位置所需人数
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
