import config
import random
import datetime
from utils.date import Date
from sql_app import schemas, crud, models
from club_app import Club
from game_app import Game
from info_app import Info


class League:
    def __init__(self, init_type=1, league_data: dict = None, league_id: int = 0):
        self.id = league_id
        self.league_model = None
        self.data = dict()
        if init_type == 1:
            # 新建
            self.generate(league_data)
            self.import_data()
        elif init_type == 2:
            # 导入数据
            self.import_data()
        else:
            config.logger.error('球员初始化错误！')

    def generate(self, league_data: dict):
        self.data['created_time'] = datetime.datetime.now()
        self.data['name'] = league_data['name']
        self.save_in_db(init=True)
        for club_data in league_data['clubs']:
            club = Club(init_type=1, club_data=club_data)
            club.switch_league(self.id)

    def update_league(self):
        """
        更新联赛数据，并保存至数据库
        使用时，将待修改的值送入self.data中，然后调用此函数即可
        """
        self.save_in_db(init=False)

    def import_data(self):
        """
        导入league_model类，一旦实例对应的联赛类发生改变，都应该调用此函数以刷新数据
        """
        self.league_model = crud.get_league_by_id(self.id)

    def export_data(self) -> schemas.League:
        """
        将初始化的联赛数据转换为schemas格式
        :return: schemas.League
        """
        data_model = schemas.League(**self.data)
        return data_model

    def save_in_db(self, init: bool):
        """
        导出数据至数据库
        """
        if init:
            data_schemas = self.export_data()
            league_model = crud.create_league(data_schemas)
            self.id = league_model.id
        else:
            # 更新
            crud.update_league(league_id=self.id, attri=self.data)
        print('成功导出联赛数据！')

    def play_game(self, club_model1: models.Club, club_model2: models.Club, date: Date):
        game = Game(club_model1, club_model2, date, self.league_model.name)
        scores = game.start()
        print("{} {}:{} {}".format(club_model1.name, scores[0], scores[1], club_model2.name))

    def play_games(self, date: Date):
        """
        进行新赛季的比
        :param date: 赛季时间
        """
        # 删除数据库中同赛季的数据
        crud.delete_game_by_attri(
            query_str='and_(models.Game.season=="{}", models.Game.type=="{}")'.format(date.year,
                                                                                      self.league_model.name))

        clubs = self.league_model.clubs

        clubs_a = random.sample(clubs, len(clubs) // 2)  # 随机挑一半
        clubs_b = list(set(clubs) ^ set(clubs_a))  # 剩下另一半
        schedule = []  # 比赛赛程
        for _ in range((len(clubs) - 1)):
            # 前半赛季的比赛
            schedule.append([game for game in zip(clubs_a, clubs_b)])
            clubs_a.insert(1, clubs_b.pop(0))
            clubs_b.append(clubs_a.pop(-1))
        schedule_reverse = []  # 主客场对调的后半赛季赛程
        for games in schedule:
            schedule_reverse.append([tuple(list(x)[::-1]) for x in games])
        schedule.extend(schedule_reverse)

        for games in schedule:
            # 进行每一轮比赛
            print('{} 的比赛'.format(str(date)))
            for game in games:
                self.play_game(game[0], game[1], date)
            date.plus_days(7)

    def start(self, start_year: int = 2022, save_in_db: bool = False):
        """
        进行一个赛季的比
        :param start_year: 开始年份
        :param save_in_db: 是否把赛季数据保存至数据库
        """
        info = Info()
        # 比赛
        self.play_games(Date(start_year, 2, random.randint(1, 28)))
        # 保存数据
        info.save(info.get_season_player_chart(
            str(start_year), self.league_model.name), filename='output_data/{}{}赛季球员数据榜.csv'.format(
            self.league_model.name, str(start_year)), file_format='csv')
        info.save(info.get_points_table(
            str(start_year), self.league_model.name), filename='output_data/{}{}赛季积分榜.csv'.format(
            self.league_model.name, str(start_year)), file_format='csv')
        if save_in_db:
            info.save_in_db(info.get_season_player_chart(str(start_year), self.league_model.name),
                            '{}{}赛季球员数据榜'.format(
                                self.league_model.name, str(start_year)))
            info.save_in_db(info.get_points_table(str(start_year), self.league_model.name),
                            '{}{}赛季积分榜'.format(
                                self.league_model.name, str(start_year)))
