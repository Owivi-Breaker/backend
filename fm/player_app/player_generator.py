from faker import Faker
from utils import Translator, utils
from game_configs import country_potential
import random
import json


class PlayerGenerator:
    def __init__(self):
        self.country_names = {}
        self.cn_names = []
        self.en_names = []
        self.jp_names = []
        self.import_names()
        self.fake = Faker()
        self.translator = Translator()

    def import_names(self):
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

    def get_cn_name(self):
        name = translated_name = random.choice(self.cn_names)
        return name, translated_name

    def get_jp_name(self):
        name = translated_name = random.choice(self.jp_names)
        return name, translated_name

    def get_en_name(self):
        name_tuple = random.choice(self.en_names)
        name = name_tuple[-1]
        translated_name = name_tuple[0]
        return name, translated_name

    def get_name(self):
        pro = {'cn': 12, 'jp': 3, 'en': 985}
        nation = utils.select_by_pro(pro)
        if nation == 'cn':
            return 'cn', *self.get_cn_name()
        elif nation == 'en':
            return 'en', *self.get_en_name()
        else:
            return 'jp', *self.get_jp_name()

    def get_nationality(self):
        translated_nationality = random.choice([x for x in self.country_names.keys()])
        nationality = self.country_names[translated_nationality]
        return nationality, translated_nationality

    def get_birthday(self):
        return self.fake.date(pattern='%m-%d')

    @staticmethod
    def get_height():
        return int(utils.normalvariate(175, 10))

    @staticmethod
    def get_weight():
        return int(utils.normalvariate(75, 5))

    @staticmethod
    def get_rating_potential(local_nationality: str = '') -> int:
        """
        获能力属性的潜力值
        :param local_nationality: 国籍
        :return: 潜力值
        """
        mean_rating = 80
        if local_nationality in country_potential.keys():
            return int(utils.normalvariate(mean_rating + country_potential[local_nationality], 5))
        else:
            return int(utils.normalvariate(mean_rating, 5))

    @staticmethod
    def get_rating(local_nationality: str = ''):
        """
        获取初始能力值
        :param local_nationality: 国籍
        :return: 初始能力值
        """
        mean_rating = 15
        if local_nationality in country_potential.keys():
            return int(utils.normalvariate(mean_rating + country_potential[local_nationality], 6))
        else:
            return float(utils.retain_decimal(int(utils.normalvariate(mean_rating, 6))))


if __name__ == '__main__':
    g = PlayerGenerator()
    for _ in range(20):
        # g = PlayerGenerator()
        print(g.get_nationality())
