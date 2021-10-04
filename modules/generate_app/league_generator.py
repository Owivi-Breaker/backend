import models
import schemas
import crud

from sqlalchemy.orm import Session


class LeagueGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.data = dict()

    def generate(self, league_data: schemas.LeagueCreate) -> models.League:
        """
        初始化联赛
        :param league_data: 联赛信息
        :return: 联赛实例
        """
        self.data = dict(league_data)
        league_model = self.save_in_db()
        self.data = dict()  # 清空数据
        return league_model

    def save_in_db(self) -> models.League:
        """
        将生成的俱乐部数据存至数据库
        :return: 俱乐部实例
        """
        data_schemas = schemas.LeagueCreate(**self.data)
        league_model = crud.create_league(db=self.db, league=data_schemas)
        return league_model
