import datetime
from typing import List
import schemas
import models
import crud
from fm import Coach, Player, PlayerGenerator
from utils import logger


class Club:
    def __init__(self, init_type=1, club_data: dict = None, club_id: int = 0):
        self.id = club_id
        self.club_model = None
        self.data = dict()
        if init_type == 1:
            # 新建
            self.generate(club_data)
            self.import_data()
        elif init_type == 2:
            # 导入数据
            self.import_data()
        else:
            logger.error('球员初始化错误！')

    def generate(self, club_data: dict):
        self.data['created_time'] = datetime.datetime.now()
        self.data['name'] = club_data['name']
        self.data['finance'] = club_data['finance']
        self.save_in_db(init=True)
        # 随机初始化教练和球员
        generator = PlayerGenerator()
        coach = Coach(generator=generator, gen_type="init")
        coach.switch_club(self.id)
        for _ in range(11):
            player = Player(generator=generator, gen_type="init")
            player.switch_club(self.id)

    def import_data(self):
        self.club_model = crud.get_club_by_id(self.id)

    def update_club(self):
        """
        更新俱乐部数据，并保存至数据库
        使用时，将待修改的值送入self.data中，然后调用此函数即可
        """
        self.save_in_db(init=False)

    def export_data(self) -> schemas.Club:
        """
        将初始化的俱乐部数据转换为schemas格式
        :return: schemas.Club
        """
        data_model = schemas.Club(**self.data)
        return data_model

    def save_in_db(self, init: bool):
        """
        导出数据至数据库
        """
        if init:
            data_schemas = self.export_data()
            club_model = crud.create_club(data_schemas)
            self.id = club_model.id
        else:
            # 更新
            crud.update_club(club_id=self.id, attri=self.data)
        print('成功导出俱乐部数据！')

    def switch_league(self, league_id: int):
        crud.update_club(club_id=self.id, attri={'league_id': league_id})

    # def get_game_data(self):
    #     data = dict()

    def select_players(self) -> (List[models.Player], List[str]):
        coach = Coach(gen_type="db", coach_id=self.club_model.coach.id)
        players_model, locations_list = coach.select_players(self.club_model.players)
        return players_model, locations_list
