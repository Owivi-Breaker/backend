import models
from utils import utils
import game_configs
import schemas
import crud

from sqlalchemy.orm import Session
import datetime
from faker import Faker
import random
from typing import Tuple
import json


class CoachGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.data = dict()

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

    def generate(self) -> models.Coach:
        """
        随机生成一名教练
        :return: 教练实例
        """
        self.data['created_time'] = datetime.datetime.now()

        nation, self.data['name'], self.data['translated_name'] = self.get_name()
        if nation == 'cn':
            self.data['nationality'], self.data['translated_nationality'] = 'China', '中国'
        elif nation == 'jp':
            self.data['nationality'], self.data['translated_nationality'] = 'Japan', '日本'
        else:
            self.data['nationality'], self.data['translated_nationality'] = self.get_nationality()

        self.data['birth_date'] = self.get_birthday()
        # tactic
        self.data['formation'] = random.choice([x for x in game_configs.formations.keys()])
        self.data['wing_cross'] = utils.get_mean_range(50, per_range=0.9)
        self.data['under_cutting'] = utils.get_mean_range(50, per_range=0.9)
        self.data['pull_back'] = utils.get_mean_range(50, per_range=0.9)
        self.data['middle_attack'] = utils.get_mean_range(50, per_range=0.9)
        self.data['counter_attack'] = utils.get_mean_range(50, per_range=0.9)
        coach_model = self.save_in_db()
        return coach_model

    def save_in_db(self) -> models.Coach:
        """
        将生成的教练数据存至数据库
        :return: 教练实例
        """
        data_schemas = schemas.CoachCreate(**self.data)
        coach_model = crud.create_coach(db=self.db, coach=data_schemas)
        return coach_model
