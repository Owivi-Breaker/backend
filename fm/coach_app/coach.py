from utils import utils, logger
from fm.player_app import PlayerGenerator
import datetime
import schemas
import models
import crud
from typing import List
import random
from game_configs import tactics, location_selector
from core.db import get_db
from fastapi import Depends


class Coach:
    def __init__(self, gen_type: str = "init", generator: PlayerGenerator = None, coach_id: int = 0):
        self.id = coach_id
        self.coach_model = None
        self.data = dict()
        self.generator = generator  # 从外部导入生成器以加快运行速度
        if gen_type == "init":
            # 随机生成
            self.generate()
            self.import_data()
        elif gen_type == "db":
            # 导入数据
            self.import_data()
        else:
            logger.error('教练初始化错误！')

    def generate(self):
        self.data['created_time'] = datetime.datetime.now()

        nation, self.data['name'], self.data['translated_name'] = self.generator.get_name()
        if nation == 'cn':
            self.data['nationality'], self.data['translated_nationality'] = 'China', '中国'
        elif nation == 'jp':
            self.data['nationality'], self.data['translated_nationality'] = 'Japan', '日本'
        else:
            self.data['nationality'], self.data['translated_nationality'] = self.generator.get_nationality()

        self.data['birth_date'] = self.generator.get_birthday()
        # tactic
        self.data['tactic'] = random.choice([x for x in tactics.keys()])
        self.data['wing_cross'] = utils.get_mean_range(50, per_range=0.9)
        self.data['under_cutting'] = utils.get_mean_range(50, per_range=0.9)
        self.data['pull_back'] = utils.get_mean_range(50, per_range=0.9)
        self.data['middle_attack'] = utils.get_mean_range(50, per_range=0.9)
        self.data['counter_attack'] = utils.get_mean_range(50, per_range=0.9)
        self.save_in_db(init=True)

    def import_data(self):
        self.coach_model = crud.get_coach_by_id(db=Depends(get_db), coach_id=self.id)

    def update_coach(self):
        """
        更新教练数据，并保存至数据库
        使用时，将待修改的值送入self.data中，然后调用此函数即可
        """
        self.save_in_db(init=False)

    def export_data(self) -> schemas.Coach:
        data_model = schemas.Coach(**self.data)
        return data_model

    def save_in_db(self, init: bool):
        """
        导出数据至数据库
        """
        if init:
            data_schemas = self.export_data()
            coach_model = crud.create_coach(db=Depends(get_db), coach=data_schemas)
            self.id = coach_model.id
        else:
            # 更新
            crud.update_coach(db=Depends(get_db), coach_id=self.id, attri=self.data)
        print('成功导出教练数据！')

    def switch_club(self, club_id: int):
        crud.update_coach(db=Depends(get_db), coach_id=self.id, attri={'club_id': club_id})

    def select_players(self, players: List[models.Player]):

        # 依据球员擅长位置选人
        final_players = []
        final_locations = []
        location_dict = tactics[self.coach_model.tactic].copy()  # 这里一定要copy()！因为涉及变量的改变

        players_location_rating_dict = {
            player: self.get_tactical_sorted_location_rating(player, self.coach_model.tactic) for player in players}
        while True:
            # 选择队伍中拥有（某位置上）最高能力值的球员及位置名
            player, lo_name = self.get_highest_rating_player(players_location_rating_dict)
            if not lo_name:
                print(len(final_players))
            if location_dict[lo_name]:
                # 若此位置仍有空，添加
                location_dict[lo_name] -= 1
                final_players.append(player)
                final_locations.append(lo_name)
                # 从待选区移除已选进的球员
                del players_location_rating_dict[player]
            else:
                players_location_rating_dict[player].pop(0)
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

    def get_fittest_player(self, players: List[models.Player], lo_name: str):
        sort_list = []
        for player in players:
            sort_list.append([player, self.get_location_rating(player, lo_name)])
        fittest_player = max(sort_list, key=lambda x: x[1])[0]
        return fittest_player

    #  TODO 应该放在Player类中
    @staticmethod
    def get_location_rating(player: models.Player, lo_name: str):
        weight_dict = dict()
        player_dict = player.__dict__
        for lo in location_selector:
            if lo['name'] == lo_name:
                weight_dict = lo['weight']
                break
        location_rating = 0
        if not weight_dict:
            logger.error('没有找到对应位置！')
        for lo, weight in weight_dict.items():
            location_rating += player_dict[lo] * weight
        return location_rating

    #  TODO 应该放在Player类中
    def get_sorted_location_rating(self, player):
        location_rating_list = []
        for location in location_selector:
            location_rating_list.append([location['name'], self.get_location_rating(player, location['name'])])
        location_rating_list = sorted(location_rating_list, key=lambda x: -x[1])
        return location_rating_list

    def get_tactical_sorted_location_rating(self, player, lo_name):
        """
        获取指定位置的球员综合能力信息
        """
        # 这代码越来越怪了。。。
        location_dict = tactics[lo_name]
        location_list = [name for name in location_dict.keys()]

        location_rating_list = self.get_sorted_location_rating(player)
        tactical_rating_list = []
        for x in location_rating_list:
            if x[0] in location_list:
                tactical_rating_list.append(x)
        return tactical_rating_list

    @staticmethod
    def get_highest_rating_player(players_location_rating_dict):
        """
        获取队伍中拥有最高位置综合值的球员实例及其位置
        """
        best_player = None
        best_rating_list = []
        for player, rating_list in players_location_rating_dict.items():
            if not rating_list:
                logger.error('球员能力列表为空！')
                continue
            if not best_player or rating_list[0][1] > best_rating_list[0][1]:
                best_player = player
                best_rating_list = rating_list
        best_rating_list = best_rating_list[0][0] if best_rating_list else None
        return best_player, best_rating_list


if __name__ == "__main__":
    for _ in range(20):
        p = Coach()
        print(p.export_data())
