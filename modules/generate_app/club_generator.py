import crud
import schemas
import models

from sqlalchemy.orm import Session


class ClubGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.data = dict()

    def generate(self, club_data: schemas.ClubCreate) -> models.Club:
        """
        初始化俱乐部
        :param club_data: 俱乐部基本信息
        :return: 俱乐部实例
        """
        self.data = club_data
        club_model = self.save_in_db()
        return club_model

    def save_in_db(self) -> models.Club:
        """
        将生成的俱乐部数据存至数据库
        :return: 俱乐部实例
        """
        data_schemas = schemas.ClubCreate(**self.data)
        club_model = crud.create_club(db=self.db, club=data_schemas)
        return club_model
