import models
from utils import utils
import game_configs
import crud
import schemas

import random
import json
from faker import Faker
import datetime
from typing import Tuple
from sqlalchemy.orm import Session


class PlayerGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.data = dict()  # 初始化的数据

        self.country_names = {}
        self.cn_names = []
        self.en_names = []
        self.jp_names = []
        self.import_names()
        self.fake = Faker()

    def import_names(self):
        """
        导入人名文件
        """
        with open('./assets/country_names.json', encoding='utf-8') as file_obj:
            self.country_names = json.load(file_obj)
        with open('./assets/English_names.txt', encoding='utf-8') as file_obj:
            for line in file_obj:
                self.en_names.append(line.rstrip().split('|')[:2])
        with open('./assets/Chinese_names.txt', encoding='utf-8') as file_obj:
            for line in file_obj:
                self.cn_names.append(line.rstrip())
        with open('./assets/Japanese_names.txt', encoding='utf-8') as file_obj:
            for line in file_obj:
                self.jp_names.append(line.rstrip())

    def get_cn_name(self) -> Tuple[str, str]:
        """
        随机获取一个中文人名
        :return: (中文名, 中文名)
        """
        name: str = random.choice(self.cn_names)
        translated_name: str = name
        return name, translated_name

    def get_jp_name(self) -> Tuple[str, str]:
        """
        随机获取一个日文人名
        :return: (日文名, 译名)
        """
        name: str = random.choice(self.jp_names)
        translated_name: str = name
        return name, translated_name

    def get_en_name(self) -> Tuple[str, str]:
        """
        随机获取一个英文人名
        :return: (英文名, 译名)
        """
        name_tuple = random.choice(self.en_names)
        name: str = name_tuple[-1]
        translated_name: str = name_tuple[0]
        return name, translated_name

    def get_name(self) -> Tuple:
        """
        按概率获取一个中文、英文或日文名
        :return: (语言, 人名, 译名)
        """
        pro = {'cn': 12, 'jp': 3, 'en': 985}
        nation = utils.select_by_pro(pro)
        if nation == 'cn':
            return 'cn', *self.get_cn_name()
        elif nation == 'en':
            return 'en', *self.get_en_name()
        else:
            return 'jp', *self.get_jp_name()

    def get_nationality(self) -> Tuple[str, str]:
        """
        随机选取国籍
        :return: (国籍, 国籍中文翻译)
        """
        translated_nationality = random.choice([x for x in self.country_names.keys()])
        nationality = self.country_names[translated_nationality]
        return nationality, translated_nationality

    def get_birthday(self) -> str:
        """
        随机获取生日
        :return: 生日字符串
        """
        return self.fake.date(pattern='%m-%d')

    @staticmethod
    def get_height() -> int:
        """
        随机获取身高
        :return: 身高
        """
        return int(utils.normalvariate(175, 10))

    @staticmethod
    def get_weight() -> int:
        """
        随机获取体重
        :return: 体重
        """
        return int(utils.normalvariate(75, 5))

    @staticmethod
    def get_capa_potential(local_nationality: str = '') -> int:
        """
        获能力属性的潜力值
        :param local_nationality: 国籍
        :return: 潜力值
        """
        ori_mean_potential_capa = game_configs.ori_mean_potential_capa
        if local_nationality in game_configs.country_potential.keys():
            return int(
                utils.normalvariate(ori_mean_potential_capa + game_configs.country_potential[local_nationality], 5))
        else:
            return int(utils.normalvariate(ori_mean_potential_capa, 5))

    @staticmethod
    def get_capa(local_nationality: str = ''):
        """
        获取初始能力值
        :param local_nationality: 国籍
        :return: 初始能力值
        """
        ori_mean_capa = game_configs.ori_mean_capa
        if local_nationality in game_configs.country_potential.keys():
            return int(utils.normalvariate(ori_mean_capa + game_configs.country_potential[local_nationality], 6))
        else:
            return float(utils.retain_decimal(int(utils.normalvariate(ori_mean_capa, 6))))

    def generate(self) -> models.Player:
        """
        随机生成一名球员
        :return: 球员实例
        """
        self.data['created_time'] = datetime.datetime.now()
        nation, self.data['name'], self.data['translated_name'] = self.get_name()
        # 判断国籍
        if nation == 'cn':
            self.data['nationality'], self.data['translated_nationality'] = 'China', '中国'
        elif nation == 'jp':
            self.data['nationality'], self.data['translated_nationality'] = 'Japan', '日本'
        else:
            self.data['nationality'], self.data['translated_nationality'] = self.get_nationality()

        self.data['height'] = self.get_height()
        self.data['weight'] = self.get_weight()
        self.data['birth_date'] = self.get_birthday()
        # capa limit generation
        self.data['shooting_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['passing_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['dribbling_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['interception_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['pace_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['strength_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['aggression_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['anticipation_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['free_kick_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['stamina_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        self.data['goalkeeping_limit'] = self.get_capa_potential(self.data['translated_nationality'])
        # capa generation
        self.data['shooting'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['shooting_limit'])
        self.data['passing'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['passing_limit'])
        self.data['dribbling'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['dribbling_limit'])
        self.data['interception'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['interception_limit'])
        self.data['pace'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['pace_limit'])
        self.data['strength'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['strength_limit'])
        self.data['aggression'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['aggression_limit'])
        self.data['anticipation'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['anticipation_limit'])
        self.data['free_kick'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['free_kick_limit'])
        self.data['stamina'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['stamina_limit'])
        self.data['goalkeeping'] = self.adjust_capa(
            self.get_capa(self.data['translated_nationality']), self.data['goalkeeping_limit'])
        # 为球员选择先天位置，并增强相应能力
        original_location = random.choice(game_configs.capa_potential)
        self.data[original_location['name'] + '_num'] = 1
        for key, value in original_location['offset'].items():
            self.data[key] = utils.get_offset(self.data[key], value)
        player_model = self.save_in_db()
        return player_model

    def save_in_db(self) -> models.Player:
        """
        将生成的球员数据存至数据库
        :return: 球员实例
        """
        data_schemas = schemas.PlayerCreate(**self.data)
        player_model = crud.create_player(db=self.db, player=data_schemas)
        return player_model

    @staticmethod
    def adjust_capa(capa: int, capa_limit: int) -> int:
        """
        调整能力值至正确的范围
        :param capa: 待调整的能力值
        :param capa_limit: 此能力的潜力值
        :return: 调整好的能力值
        """
        capa = capa if capa > 0 else 1  # 底限为1
        capa = capa if capa <= capa_limit else capa_limit  # 上限为潜力
        return capa
