import game_configs
from utils import logger
import models
import crud

from sqlalchemy.orm import Session
from fastapi import Depends
from core.db import get_db
from typing import Dict, List


class ComputedPlayer:
    def __init__(self, player_id: int, db: Session):
        self.db = db
        self.player_id = player_id
        self.player_model = crud.get_player_by_id(db=self.db, player_id=self.player_id)

    def get_location_capa(self, lo_name: str) -> float:
        """
        获取球员指定位置的综合能力
        :param lo_name: 位置名
        :return: 位置能力值
        """
        weight_dict = dict()
        player_dict = self.player_model.__dict__
        for lo in game_configs.location_capability:
            # 拿到指定位置的能力比重
            if lo['name'] == lo_name:
                weight_dict = lo['weight']
                break
        location_capa = 0
        if not weight_dict:
            logger.error('没有找到对应位置！')
        for lo, weight in weight_dict.items():
            location_capa += player_dict[lo] * weight
        return location_capa

    def get_sorted_location_capa(self) -> List[List[str, float]]:
        """
        获取各个位置能力的降序列表
        :return: List[lo_name, lo_capa]
        """
        location_capa = []
        for location in game_configs.location_capability:
            location_capa.append(
                [location['name'], self.get_location_capa(location['name'])]
            )
            location_capa = sorted(location_capa, key=lambda x: -x[1])
        return location_capa
