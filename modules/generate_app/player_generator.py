import models
from utils import utils, logger
import game_configs
import crud
import schemas
from modules import computed_data_app
import copy
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

        self.ori_mean_capa = game_configs.ori_mean_capa
        self.ori_mean_potential_capa = game_configs.ori_mean_potential_capa

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

    def get_capa_potential(self, local_nationality: str = '', ) -> int:
        """
        获能力属性的潜力值
        :param local_nationality: 国籍
        :return: 潜力值
        """
        ori_mean_potential_capa = self.ori_mean_potential_capa
        if local_nationality in game_configs.country_potential.keys():
            return int(
                utils.normalvariate(ori_mean_potential_capa + game_configs.country_potential[local_nationality], 5))
        else:
            return int(utils.normalvariate(ori_mean_potential_capa, 5))

    def get_capa(self, local_nationality: str = ''):
        """
        获取初始能力值
        :param local_nationality: 国籍
        :return: 初始能力值
        """
        ori_mean_capa = self.ori_mean_capa
        if local_nationality in game_configs.country_potential.keys():
            return int(utils.normalvariate(ori_mean_capa + game_configs.country_potential[local_nationality], 5))
        else:
            return float(utils.retain_decimal(int(utils.normalvariate(ori_mean_capa, 6))))

    def generate(self, ori_mean_capa: int = None, ori_mean_potential_capa: int = None,
                 average_age: int = None, location: str = '') -> schemas.PlayerCreate:
        """
        随机生成一名球员
        若传入除location外的三个参数，则生成随机位置的成年球员
        若传入四个参数，则生成指定位置的成年球员
        若不传入参数，则生成年轻球员
        :param ori_mean_capa: 指定的平均能力
        :param ori_mean_potential_capa: 指定的平均潜力
        :param average_age: 指定的平均年龄
        :param location: 指定位置，若未指定位置，随机指定
        :return: 球员实例
        """

        if ori_mean_capa and ori_mean_potential_capa and average_age:
            # 若在generate函数中传入平均值，则生成成年球员
            self.generate_data(average_age)
            # 生成初级能力值后，再修改平均能力和潜力值，这样可以避免出现全能球员
            self.ori_mean_capa = ori_mean_capa
            self.ori_mean_potential_capa = ori_mean_potential_capa
            # 选择一个位置
            original_location = dict()
            if location:
                for x in game_configs.location_capability:
                    if x['name'] == location:
                        original_location = x
                        break
            else:
                original_location = random.choice(game_configs.location_capability)
            self.data[original_location['name'] + '_num'] = 1
            # 重写一遍位置对应的能力与潜力

            # 正态分布获取一个预期的综合能力值
            target_lo_capa = min(self.get_capa(self.data['translated_nationality']), 88)

            while True:
                # 模拟球员按照位置权重成长的过程
                capa_name = utils.select_by_pro(original_location['weight'])
                if self.data[capa_name] <= 90:
                    # 防止溢出
                    self.data[capa_name] += 1
                # 获取综合能力值
                lo_capa = 0
                for capa, weight in original_location['weight'].items():
                    lo_capa += self.data[capa] * weight
                if lo_capa >= target_lo_capa:
                    # logger.info("综合能力为{}".format(lo_capa))
                    break

            for capa in original_location['weight'].keys():
                # 把这个位置相应的潜力设置以ori_mean_potential_capa正态分布的值
                self.data[capa + '_limit'] = max(self.get_capa_potential(
                    self.data['translated_nationality']), int(self.data[capa]) + 1)
                # 保证能力不超过上限
                self.data[capa] = self.adjust_capa(
                    self.data[capa], self.data[capa + '_limit'])
            # 额外设置体力
            self.data['stamina'] = self.adjust_capa(
                self.get_capa(self.data['translated_nationality']),
                self.data['stamina_limit'])

        else:
            # 生成年轻球员
            self.generate_data()
            # 为球员选择先天位置，并增强相应能力
            original_location = random.choice(game_configs.capa_potential)
            self.data[original_location['name'] + '_num'] = 1
            for key, value in original_location['offset'].items():
                # 先把相应能力值+5，再乘上偏移量
                self.data[key] = self.adjust_capa(
                    utils.get_offset(self.data[key] + 5, value), self.data[key + '_limit'])
        # player_model = self.save_in_db() # 不在computed类里写入数据库
        player_create_schemas = schemas.PlayerCreate(**self.data)
        self.data = dict()  # 清空数据
        return player_create_schemas

    def generate_data(self, average_age: int = None):
        """
        随机生成一例球员数据，保存在self.data中
        :param average_age: 指定的平均年龄
        """
        # 保证在这个函数里，球员生成的能力是年轻球员的能力
        self.ori_mean_capa = game_configs.ori_mean_capa
        self.ori_mean_potential_capa = game_configs.ori_mean_potential_capa

        self.data['created_time'] = datetime.datetime.now()
        nation, self.data['name'], self.data['translated_name'] = self.get_name()
        # 判断国籍
        if nation == 'cn':
            self.data['nationality'], self.data['translated_nationality'] = 'China', '中国'
        elif nation == 'jp':
            self.data['nationality'], self.data['translated_nationality'] = 'Japan', '日本'
        else:
            self.data['nationality'], self.data['translated_nationality'] = self.get_nationality()
        # 年龄
        if average_age:
            self.data['age'] = utils.get_mean_range(average_age, per_range=0.2)
        else:
            self.data['age'] = 15
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

    def save_in_db(self) -> models.Player:
        """
        将生成的球员数据存至数据库
        :return: 球员实例
        """
        data_schemas = schemas.PlayerCreate(**self.data)
        player_model = crud.create_player(db=self.db, player=data_schemas)
        return player_model

    @staticmethod
    def adjust_capa(capa: float, capa_limit: int) -> int:
        """
        调整能力值至正确的范围
        :param capa: 待调整的能力值
        :param capa_limit: 此能力的潜力值
        :return: 调整好的能力值
        """
        capa = capa if capa > 0 else 1  # 底限为1
        capa = capa if capa <= capa_limit else capa_limit  # 上限为潜力
        return capa
