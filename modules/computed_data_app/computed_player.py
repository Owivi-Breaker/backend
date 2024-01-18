import random
from typing import Dict, List, Optional, Tuple

import crud
import game_configs
import models
import schemas
import utils
import utils.utils
from sqlalchemy.orm import Session
from utils import logger, utils


class ComputedPlayer:
    def __init__(
        self, player_id: int, db: Session, season: int, date: str, player_model: Optional[models.Player] = None
    ):
        self.db = db
        self.player_id = player_id
        self.season = season
        self.date = date
        # 为了减少数据的读操作，可以传入现成的player_model
        self.player_model = (
            player_model if player_model else crud.get_player_by_id(db=self.db, player_id=self.player_id)
        )
        self.age = self.player_model.age

        # with open("./game_configs/data/location_capability.json", encoding='utf-8') as f_obj:
        #     self.location_capability = json.load(f_obj)
        self.location_capability = game_configs.location_capability
        self.capa = dict()
        self.init_capa()

    def init_capa(self):
        self.capa["shooting"] = self.player_model.shooting
        self.capa["passing"] = self.player_model.passing
        self.capa["dribbling"] = self.player_model.dribbling
        self.capa["interception"] = self.player_model.interception
        self.capa["pace"] = self.player_model.pace
        self.capa["strength"] = self.player_model.strength
        self.capa["aggression"] = self.player_model.aggression
        self.capa["anticipation"] = self.player_model.anticipation
        self.capa["free_kick"] = self.player_model.free_kick
        self.capa["stamina"] = self.player_model.stamina
        self.capa["goalkeeping"] = self.player_model.goalkeeping

    def get_show_data(self) -> schemas.PlayerShow:
        """
        获取返回给前端的球员信息
        :return: schemas.PlayerShow
        """
        data = dict()
        data["id"] = self.player_model.id
        data["club_id"] = self.player_model.club_id
        data["club_name"] = self.player_model.club.name
        data["name"] = self.player_model.name
        data["translated_name"] = self.player_model.translated_name
        data["translated_nationality"] = self.player_model.translated_nationality
        data["age"] = self.get_age()
        data["height"] = self.player_model.height
        data["weight"] = self.player_model.weight
        data["birth_date"] = self.player_model.birth_date
        data["wages"] = self.player_model.wages
        data["values"] = self.get_values()
        data["number"] = random.randint(1, 50)  # TODO 号码
        data["avatar"] = utils.turn_str2dict(self.player_model.avatar)
        data["real_stamina"] = self.get_real_stamina()
        data["location_num"] = self.get_location_num()
        data["capa"] = self.get_all_capa(is_retain_decimal=True)
        data["top_location"] = self.get_top_lo_n_capa()[0]
        data["superior_location"] = self.get_superior_location()
        data["top_capa"] = self.get_top_lo_n_capa()[1]
        data["location_capa"] = {a[0]: a[1] for a in self.get_sorted_location_capa(True)}
        data["style_tag"] = self.get_style_tag()
        data["talent_tag"] = self.get_talent_tag()
        data["recent_ratings"] = self.get_ratings_in_recent_games()
        data["on_sale"] = self.player_model.on_sale
        return schemas.PlayerShow(**data)

    def get_talent_tag(self) -> List[str]:
        """
        根据球员能力值上线计算天赋
        """
        talent_tag = []
        if self.player_model.goalkeeping_limit > 85:
            talent_tag.append("壁垒")
        if self.player_model.height > 185:
            talent_tag.append("高塔")
        if self.player_model.strength_limit > 85 and self.player_model.aggression_limit > 85:
            talent_tag.append("推土机")
        if self.player_model.pace_limit > 85:
            talent_tag.append("猎豹")
        if self.player_model.dribbling_limit > 85:
            talent_tag.append("魔术师")
        if self.player_model.passing_limit > 85:
            talent_tag.append("发动机")
        if self.player_model.shooting_limit > 85:
            talent_tag.append("重炮手")
        if self.player_model.shooting_limit > 83 and self.player_model.aggression_limit > 83:
            talent_tag.append("偷猎者")
        if self.player_model.stamina_limit > 85:
            talent_tag.append("大心脏")
        if self.player_model.free_kick_limit > 85:
            talent_tag.append("任意球大师")
        if self.player_model.interception_limit > 87:
            talent_tag.append("扫荡者")
        if len(talent_tag) == 0:
            talent_tag.append("普通一员")
        return talent_tag

    def get_style_tag(self) -> List[str]:
        """
        根据球员当前能力值计算偏好
        """
        style_tag = []
        if self.player_model.passing > 50 and self.player_model.interception > 50:
            style_tag.append("就地反抢")
        if self.player_model.pace > 50 and self.player_model.shooting > 50:
            style_tag.append("前插攻击")
        if self.player_model.aggression < 50 and self.player_model.interception > 50:
            style_tag.append("防守内收")
        if self.player_model.aggression > 50:
            style_tag.append("高位压迫")
        if self.player_model.pace > 50 and self.player_model.passing > 50:
            style_tag.append("套边传中")
        if self.player_model.strength > 50 and self.player_model.pace < 40:
            style_tag.append("站桩护球")
        if self.player_model.passing > 60 and self.player_model.anticipation > 60:
            style_tag.append("传球组织")
        if self.player_model.aggression > 50 and self.player_model.anticipation < 50:
            style_tag.append("利用身体")
        if self.player_model.dribbling > 60:
            style_tag.append("盘带过人")
        if self.player_model.shooting > 60:
            style_tag.append("远射得分")
        if len(style_tag) == 0:
            style_tag.append("听从指挥")
        return style_tag

    def get_location_num(self) -> Dict[str, int]:
        """
        获取球员各个位置的比赛次数
        """
        data = dict()
        data["ST_num"] = self.player_model.ST_num
        data["CM_num"] = self.player_model.CM_num
        data["LW_num"] = self.player_model.LW_num
        data["RW_num"] = self.player_model.RW_num
        data["CB_num"] = self.player_model.CB_num
        data["LB_num"] = self.player_model.LB_num
        data["RB_num"] = self.player_model.RB_num
        data["GK_num"] = self.player_model.GK_num
        data["CAM_num"] = self.player_model.CAM_num
        data["LM_num"] = self.player_model.LM_num
        data["RM_num"] = self.player_model.RM_num
        data["CDM_num"] = self.player_model.CDM_num
        return data

    def get_all_capa(self, is_retain_decimal: bool = False) -> dict:
        """
        获取所有能力值
        :return: 能力值字典
        :param is_retain_decimal: 是否保留小数
        """
        data = dict()
        data["shooting"] = self.get_capa("shooting")
        data["passing"] = self.get_capa("passing")
        data["dribbling"] = self.get_capa("dribbling")
        data["interception"] = self.get_capa("interception")
        data["pace"] = self.get_capa("pace")
        data["strength"] = self.get_capa("strength")
        data["aggression"] = self.get_capa("aggression")
        data["anticipation"] = self.get_capa("anticipation")
        data["free_kick"] = self.get_capa("free_kick")
        data["stamina"] = self.get_capa("stamina")  # 注意，这个是体力“能力”，不是真正的体力！
        data["goalkeeping"] = self.get_capa("goalkeeping")
        if is_retain_decimal:
            return {k: float(utils.retain_decimal(v)) for k, v in data.items()}
        return data

    def get_capa(self, capa_name: str, is_retain_decimal: bool = False, is_filtered_by_stamina: bool = False) -> float:
        """
        获取年龄滤镜过的能力值
        :param capa_name: 能力名
        :param is_retain_decimal: 是否保留小数
        :param is_filtered_by_stamina: 是否考虑体力因素，专门用于ai选人策略中
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
        if is_retain_decimal:
            return float(utils.retain_decimal(ori_capa * weight))
        return ori_capa * weight

    def get_location_capa(self, lo_name: str, is_retain_decimal: bool = False) -> float:
        """
        获取球员指定位置的综合能力
        :param lo_name: 位置名
        :return: 位置能力值
        :param is_retain_decimal: 是否保留小数
        """
        weight_dict = dict()
        for lo in self.location_capability:
            # 拿到指定位置的能力比重
            if lo["name"] == lo_name:
                weight_dict = lo["weight"]
                break
        location_capa = 0
        if not weight_dict:
            logger.error("没有找到对应位置！")
        for capa_name, weight in weight_dict.items():
            location_capa += self.get_capa(capa_name) * weight
        if is_retain_decimal:
            return float(utils.retain_decimal(location_capa))
        return location_capa

    def get_sorted_location_capa(self, is_retain_decimal: bool = False) -> List[List]:
        """
        获取各个位置能力的降序列表
        :return: List[List[lo_name, lo_capa]]
        :param is_retain_decimal: 是否保留小数
        """
        location_capa = []
        if is_retain_decimal:
            for location in self.location_capability:
                location_capa.append([location["name"], self.get_location_capa(location["name"], True)])
        else:
            for location in self.location_capability:
                location_capa.append([location["name"], self.get_location_capa(location["name"])])
        location_capa = sorted(location_capa, key=lambda x: -x[1])
        return location_capa

    def get_top_lo_n_capa(self, is_retain_decimal: bool = False) -> Tuple[str, float]:
        """
        获取最佳位置以及该位置的综合能力
        :return: (位置名, 能力值)
        :param is_retain_decimal: 是否保留小数
        """
        lo_name, top_capa = self.get_sorted_location_capa()[0]
        if is_retain_decimal:
            top_capa = float(utils.retain_decimal(top_capa))
        return lo_name, top_capa

    def get_ratings_in_recent_games(self, game_num: int = 5) -> List[float]:
        """
        获取近n场比赛的评分列表 排序由远到近
        :param game_num: 欲获取的比赛次数
        """
        game_player_data: List[models.GamePlayerData] = self.get_game_player_data(
            start_season=self.season, end_season=self.season
        )
        if not game_player_data:
            return []
        game_player_data_sorted = sorted(game_player_data, key=lambda x: x.id, reverse=True)
        ratings = [x.final_rating for x in game_player_data_sorted]
        return ratings[:game_num][::-1] if len(ratings) >= game_num else ratings[::-1]

    def get_avg_rating_in_recent_year(self) -> float:
        """
        获取近一年比赛的评分数据
        """
        start_season = self.season - 1 if self.season - 1 != 0 else self.season
        game_player_data: List[models.GamePlayerData] = self.get_game_player_data(
            start_season=start_season, end_season=self.season
        )
        if not game_player_data:
            return 6.0
        rating = float(utils.retain_decimal(sum([p.real_rating for p in game_player_data]) / len(game_player_data)))
        rating = rating if rating <= 10 else 10
        return rating

    def get_real_stamina(self) -> int:
        """
        获取真实体力值
        """
        if not self.player_model.last_game_date:
            return 100
        last_stamina = self.player_model.real_stamina
        days: int = (utils.Date(self.date).date - utils.Date(self.player_model.last_game_date).date).days
        re = int(days * 3 + last_stamina) if int(days * 3 + last_stamina) <= 100 else 100
        return re

    def get_age(self) -> int:
        """
        获取年龄
        :return: 年龄
        """
        if self.season:
            return self.age + self.season - 1
        else:
            return self.age + self.player_model.club.league.save.season - 1

    def get_game_player_data(self, start_season: int = None, end_season: int = None) -> List[models.GamePlayerData]:
        """
        获取指定球员某赛季的比赛信息
        :param start_season: 开始赛季，若为空，默认1开始
        :param end_season: 结束赛季，若为空，默认当前赛季
        """
        s_season = start_season if start_season else 1
        e_season = end_season if end_season else self.season
        game_player_data: List[models.GamePlayerData] = [
            game_data for game_data in self.player_model.game_data if s_season <= int(game_data.season) <= e_season
        ]

        return game_player_data

    def get_total_game_player_data(
        self, start_season: int = None, end_season: int = None
    ) -> schemas.TotalGamePlayerDataShow:
        """
        获取指定球员某赛季的统计比赛信息
        :param start_season: 开始赛季，若为空，默认1开始
        :param end_season: 结束赛季，若为空，默认当前赛季
        """
        game_player_data: List[models.GamePlayerData] = self.get_game_player_data(
            start_season=start_season, end_season=end_season
        )
        if not game_player_data:
            return schemas.TotalGamePlayerDataShow()
        result = dict()
        result["id"] = self.player_id
        result["appearance"] = len(game_player_data)
        result["final_rating"] = float(
            utils.retain_decimal(sum([p.final_rating for p in game_player_data]) / len(game_player_data))
        )
        result["actions"] = sum([p.actions for p in game_player_data])
        result["shots"] = sum([p.shots for p in game_player_data])
        result["goals"] = sum([p.goals for p in game_player_data])
        result["assists"] = sum([p.assists for p in game_player_data])
        result["passes"] = sum([p.passes for p in game_player_data])
        result["pass_success"] = sum([p.pass_success for p in game_player_data])
        result["dribbles"] = sum([p.dribbles for p in game_player_data])
        result["dribble_success"] = sum([p.dribble_success for p in game_player_data])
        result["tackles"] = sum([p.tackles for p in game_player_data])
        result["tackle_success"] = sum([p.tackle_success for p in game_player_data])
        result["aerials"] = sum([p.aerials for p in game_player_data])
        result["aerial_success"] = sum([p.aerial_success for p in game_player_data])
        result["saves"] = sum([p.saves for p in game_player_data])
        result["save_success"] = sum([p.save_success for p in game_player_data])
        return schemas.TotalGamePlayerDataShow(**result)

    def get_values(self) -> int:
        """
        获取身价
        """
        top_capa = self.get_top_lo_n_capa()[1]
        basic_values = top_capa**3 / 70.0
        avg_rating = self.get_avg_rating_in_recent_year()
        extra_values = avg_rating * 2000 - 12000
        real_values = int(basic_values + extra_values)
        if real_values < 10:
            real_values = 10
        return real_values

    def get_superior_location(self) -> List[str]:
        """
        获取优势位置
        暂时的策略是返回能力前三的位置
        TODO 优化算法
        """
        return [x[0] for x in self.get_sorted_location_capa()[:3]]
