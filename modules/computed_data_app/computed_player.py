from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Optional

import game_configs
import schemas
import utils
from utils import logger, utils
import models
import crud


class ComputedPlayer:
    def __init__(self, player_id: int, db: Session, player_model: Optional[models.Player] = None, season: int = None):
        self.db = db
        self.player_id = player_id
        if not season:
            raise ValueError("season is zero")
        self.season = season
        # 为了减少数据的读操作，可以传入现成的player_model
        self.player_model = player_model \
            if player_model \
            else crud.get_player_by_id(db=self.db, player_id=self.player_id)
        self.age = self.player_model.age
        self.capa = dict()
        self.init_capa()

    def init_capa(self):
        self.capa['shooting'] = self.player_model.shooting
        self.capa['passing'] = self.player_model.passing
        self.capa['dribbling'] = self.player_model.dribbling
        self.capa['interception'] = self.player_model.interception
        self.capa['pace'] = self.player_model.pace
        self.capa['strength'] = self.player_model.strength
        self.capa['aggression'] = self.player_model.aggression
        self.capa['anticipation'] = self.player_model.anticipation
        self.capa['free_kick'] = self.player_model.free_kick
        self.capa['stamina'] = self.player_model.stamina
        self.capa['goalkeeping'] = self.player_model.goalkeeping

    def get_show_data(self) -> schemas.PlayerShow:
        """
        获取返回给前端的球员信息
        :return: schemas.PlayerShow
        """

        data = dict()
        data['id'] = self.player_model.id
        data['club_id'] = self.player_model.club_id
        data['name'] = self.player_model.name
        data['translated_name'] = self.player_model.translated_name
        data['translated_nationality'] = self.player_model.translated_nationality
        data['age'] = self.get_age()
        data['height'] = self.player_model.height
        data['weight'] = self.player_model.weight
        data['birth_date'] = self.player_model.birth_date
        data['wages'] = self.player_model.wages
        data['real_stamina'] = self.player_model.real_stamina
        data.update(self.get_location_num())
        data.update(self.get_all_capa())
        data['top_location'] = self.get_top_capa_n_location()[0]
        data['top_capa'] = self.get_top_capa_n_location()[1]
        data['location_capa'] = {a[0]: a[1] for a in self.get_sorted_location_capa()}
        return schemas.PlayerShow(**data)

    def get_location_num(self) -> Dict[str, int]:
        """
        获取球员各个位置的比赛次数
        """
        data = dict()
        data['ST_num'] = self.player_model.ST_num
        data['CM_num'] = self.player_model.CM_num
        data['LW_num'] = self.player_model.LW_num
        data['RW_num'] = self.player_model.RW_num
        data['CB_num'] = self.player_model.CB_num
        data['LB_num'] = self.player_model.LB_num
        data['RB_num'] = self.player_model.RB_num
        data['GK_num'] = self.player_model.GK_num
        data['CAM_num'] = self.player_model.CAM_num
        data['LM_num'] = self.player_model.LM_num
        data['RM_num'] = self.player_model.RM_num
        data['CDM_num'] = self.player_model.CDM_num
        return data

    def get_all_capa(self) -> dict:
        """
        获取所有能力值
        :return: 能力值字典
        """
        data = dict()
        data['shooting'] = self.get_capa('shooting')
        data['passing'] = self.get_capa('passing')
        data['dribbling'] = self.get_capa('dribbling')
        data['interception'] = self.get_capa('interception')
        data['pace'] = self.get_capa('pace')
        data['strength'] = self.get_capa('strength')
        data['aggression'] = self.get_capa('aggression')
        data['anticipation'] = self.get_capa('anticipation')
        data['free_kick'] = self.get_capa('free_kick')
        data['stamina'] = self.get_capa('stamina')  # 注意，这个是体力“能力”，不是真正的体力！
        data['goalkeeping'] = self.get_capa('goalkeeping')
        return data

    def get_capa(self, capa_name: str) -> float:
        """
        获取年龄滤镜过的能力值
        :param capa_name: 能力名
        :return: 能力值
        """
        ori_capa = self.capa[capa_name]
        age = self.get_age()
        start_age = 30
        if age >= start_age:
            weight = 1 - (age - 30 + 1) * 0.05
            if weight <= 0:
                weight = 0.05
        else:
            weight = 1
        return float(utils.retain_decimal(ori_capa * weight))

    def get_location_capa(self, lo_name: str) -> float:
        """
        获取球员指定位置的综合能力
        :param lo_name: 位置名
        :return: 位置能力值
        """
        weight_dict = dict()
        for lo in game_configs.location_capability:
            # 拿到指定位置的能力比重
            if lo['name'] == lo_name:
                weight_dict = lo['weight']
                break
        location_capa = 0
        if not weight_dict:
            logger.error('没有找到对应位置！')
        for capa_name, weight in weight_dict.items():
            location_capa += self.get_capa(capa_name) * weight
        return float(utils.retain_decimal(location_capa))

    def get_sorted_location_capa(self) -> List[List]:
        """
        获取各个位置能力的降序列表
        :return: List[List[lo_name, lo_capa]]
        """
        location_capa = []
        for location in game_configs.location_capability:
            location_capa.append(
                [location['name'], self.get_location_capa(location['name'])]
            )
        location_capa = sorted(location_capa, key=lambda x: -x[1])
        return location_capa

    def get_top_capa_n_location(self) -> Tuple[str, float]:
        """
        获取最佳位置的综合能力以及该位置
        :return: (能力值, 位置名)
        """
        lo_name, top_capa = self.get_sorted_location_capa()[0]
        return lo_name, top_capa

    def get_value(self) -> int:
        """
        获取球员身价
        :return: 身价
        """
        pass

    def get_age(self) -> int:
        """
        获取年龄
        :return: 年龄
        """
        if self.season:
            return self.age + self.season - 1
        else:
            return self.age + self.player_model.club.league.save.season - 1

    def get_game_player_data(self, start_season: int = None, end_season: int = None) \
            -> List[schemas.GamePlayerData]:
        """
        获取指定球员某赛季的比赛信息
        :param start_season: 开始赛季，若为空，默认1开始
        :param end_season: 结束赛季，若为空，默认当前赛季
        """
        s_season = start_season if start_season else 1
        e_season = end_season if end_season else self.season
        game_player_data: List[models.GamePlayerData] = [
            game_data for game_data in self.player_model.game_data if \
            s_season <= game_data.season <= e_season]

        return game_player_data

    def get_total_game_player_data(self, start_season: int = None, end_season: int = None) \
            -> schemas.GamePlayerDataShow:
        """
        获取指定球员某赛季的统计比赛信息
        :param start_season: 开始赛季，若为空，默认1开始
        :param end_season: 结束赛季，若为空，默认当前赛季
        """
        game_player_data: List[models.GamePlayerData] = self.get_game_player_data(
            start_season=start_season, end_season=end_season)
        result = dict()
        result["final_rating"] = float(
            utils.retain_decimal(sum([p.final_rating for p in game_player_data]) / len(game_player_data)))
        result['actions'] = sum([p.actions for p in game_player_data])
        result['shots'] = sum([p.shots for p in game_player_data])
        result['goals'] = sum([p.goals for p in game_player_data])
        result['assists'] = sum([p.assists for p in game_player_data])
        result['passes'] = sum([p.passes for p in game_player_data])
        result['pass_success'] = sum([p.pass_success for p in game_player_data])
        result['dribbles'] = sum([p.dribbles for p in game_player_data])
        result['dribble_success'] = sum([p.dribble_success for p in game_player_data])
        result['tackles'] = sum([p.tackles for p in game_player_data])
        result['tackle_success'] = sum([p.tackle_success for p in game_player_data])
        result['aerials'] = sum([p.aerials for p in game_player_data])
        result['aerial_success'] = sum([p.aerial_success for p in game_player_data])
        result['saves'] = sum([p.saves for p in game_player_data])
        result['save_success'] = sum([p.save_success for p in game_player_data])
        result['location'] = 'ST'  # 这里随便填一个进去，在API里剔除
        logger.debug(result)
        return schemas.GamePlayerDataShow(**result)
