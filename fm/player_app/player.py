import datetime
import random
import crud
import schemas
from fm.player_app import PlayerGenerator
from game_configs import rating_potential
from utils import utils, logger
from core.db import get_db
from fastapi import Depends


class Player:
    def __init__(self, gen_type: str = "init", generator: PlayerGenerator = None, player_id: int = 0):
        self.id = player_id
        self.player_model = None
        self.data = dict()  # 初始化或待修改的数据
        self.generator = generator  # 从外部导入生成器以加快运行速度
        if gen_type == "init":
            # 随机生成
            self.generate()
            self.import_data()
        elif gen_type == "db":
            # 导入数据
            self.import_data()
        else:
            logger.error('球员初始化错误！')

    def generate(self):
        self.data['created_time'] = datetime.datetime.now()
        nation, self.data['name'], self.data['translated_name'] = self.generator.get_name()
        # 判断国籍
        if nation == 'cn':
            self.data['nationality'], self.data['translated_nationality'] = 'China', '中国'
        elif nation == 'jp':
            self.data['nationality'], self.data['translated_nationality'] = 'Japan', '日本'
        else:
            self.data['nationality'], self.data['translated_nationality'] = self.generator.get_nationality()

        self.data['height'] = self.generator.get_height()
        self.data['weight'] = self.generator.get_weight()
        self.data['birth_date'] = self.generator.get_birthday()
        # rating limit generation
        self.data['shooting_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['passing_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['dribbling_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['interception_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['pace_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['strength_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['aggression_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['anticipation_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['free_kick_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['stamina_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        self.data['goalkeeping_limit'] = self.generator.get_rating_potential(self.data['translated_nationality'])
        # rating generation
        self.data['shooting'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['shooting_limit'])
        self.data['passing'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['passing_limit'])
        self.data['dribbling'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['dribbling_limit'])
        self.data['interception'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['interception_limit'])
        self.data['pace'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['pace_limit'])
        self.data['strength'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['strength_limit'])
        self.data['aggression'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['aggression_limit'])
        self.data['anticipation'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['anticipation_limit'])
        self.data['free_kick'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['free_kick_limit'])
        self.data['stamina'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['stamina_limit'])
        self.data['goalkeeping'] = self.adjust_rating(
            self.generator.get_rating(self.data['translated_nationality']), self.data['goalkeeping_limit'])
        # 为球员选择先天位置，并增强相应能力
        original_location = random.choice(rating_potential)
        self.data[original_location['name'] + '_num'] = 1
        for key, value in original_location['offset'].items():
            self.data[key] = utils.get_offset(self.data[key], value)
        self.save_in_db(init=True)

    def update_player(self):
        """
        更新球员数据，并保存至数据库
        使用时，将待修改的值送入self.data中，然后调用此函数即可
        """
        self.save_in_db(init=False)

    def import_data(self):
        self.player_model = crud.get_player_by_id(db=Depends(get_db), player_id=self.id)

    def export_data(self) -> schemas.Player:
        """
        将初始化的球员数据转换为schemas格式
        :return: schemas.Player
        """
        data_model = schemas.Player(**self.data)
        return data_model

    def save_in_db(self, init: bool):
        """
        导出数据至数据库
        """
        if init:
            data_schemas = self.export_data()
            player_model = crud.create_player(db=Depends(get_db), player=data_schemas)
            self.id = player_model.id

        else:
            # 更新
            crud.update_player(db=Depends(get_db), player_id=self.id, attri=self.data)
        print('成功导出球员数据！')

    def switch_club(self, club_id: int):
        crud.update_player(db=Depends(get_db), player_id=self.id, attri={'club_id': club_id})

    @staticmethod
    def adjust_rating(rating: int, rating_limit: int):
        rating = rating if rating > 0 else 1
        rating = rating if rating <= rating_limit else rating_limit
        return rating

    def get_location_rating(self):
        pass


if __name__ == "__main__":
    for _ in range(200):
        p = Player()
        print(p.export_data())
