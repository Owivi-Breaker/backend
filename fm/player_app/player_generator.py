from faker import Faker
from collections import OrderedDict
from utils.translator import Translator
from utils import utils
from config import country_potential
from assets.country_names import country_names
import config
import random
from utils.utils import select_by_pro


# locales = OrderedDict(
#     [
#         ("en-US", 6),
#         ("zh_CN", 5),
#         ("ja_JP", 4),
#         ("en_GB", 5),
#         ("es_ES", 3),
#         ("fr_FR", 3),
#         ("it_IT", 1),
#         ("ko_KR", 3),
#         ("pt_BR", 1),
#         ("de_DE", 3),
#         ("ar_EG", 1),
#         ("el_GR", 1),
#         ("hi_IN", 1),
#         ("ko_KR", 1),
#         ("nl_NL", 1),
#         ("ru_RU", 1),
#         ("no_NO", 1),
#         ("ne_NP", 1),
#         ("tr_TR", 1),
#         ("sv_SE", 1)
#
#     ]
# )


class PlayerGenerator:
    def __init__(self):
        self.cn_names = []
        self.en_names = []
        self.jp_names = []
        self.country_names = country_names
        self.import_names()
        # self.name_fake = Faker(locales)
        self.fake = Faker()
        self.translator = Translator()

    def import_names(self):
        with open(config.CWD_URL + '/assets/English_names.txt', encoding='utf-8') as file_obj:
            for line in file_obj:
                self.en_names.append(line.rstrip().split('|')[:2])
        with open(config.CWD_URL + '/assets/Chinese_names.txt', encoding='utf-8') as file_obj:
            for line in file_obj:
                self.cn_names.append(line.rstrip())
        with open(config.CWD_URL + '/assets/Japanese_names.txt', encoding='utf-8') as file_obj:
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
        pro = {'cn': 20, 'jp': 5, 'en': 975}
        nation = select_by_pro(pro)
        if nation == 'cn':
            return 'cn', *self.get_cn_name()
        elif nation == 'en':
            return 'en', *self.get_en_name()
        else:
            return 'jp', *self.get_jp_name()

    # def get_name(self):
    #     while True:
    #         name = self.name_fake.name().replace(' ', '·')
    #         result, flag = self.check_translation(name)
    #         if flag:
    #             return name

    def get_nationality(self):
        # nationality = self.fake.country()
        # return nationality
        translated_nationality = random.choice([x for x in self.country_names.keys()])
        nationality = self.country_names[translated_nationality]
        return nationality, translated_nationality

    def check_translation(self, text: str, target_lang: str = 'zh-CN'):
        result, flag = self.translator.translate(text, target_lang=target_lang)
        if flag and result != text:
            return result, True
        else:
            return result, False

    def translate(self, text: str, target_lang: str = 'zh-CN'):
        result, flag = self.translator.translate(text, target_lang=target_lang)
        return result

    def get_birthday(self):
        return self.fake.date(pattern='%m-%d')

    @staticmethod
    def get_height():
        return int(utils.normalvariate(175, 10))

    @staticmethod
    def get_weight():
        return int(utils.normalvariate(75, 5))

    @staticmethod
    def get_rating_potential(local_nationality: str = ''):
        mean_rating = 80
        if local_nationality in country_potential.keys():
            return int(utils.normalvariate(mean_rating + country_potential[local_nationality], 5))
        else:
            return int(utils.normalvariate(mean_rating, 5))

    @staticmethod
    def get_rating(local_nationality: str = ''):
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
