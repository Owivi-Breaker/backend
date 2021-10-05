import schemas
import models
import crud

from sqlalchemy.orm import Session


class SaveGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.data = dict()

    def generate(self, save_data: schemas.SaveCreate) -> models.Save:
        """
        初始化存档
        :param save_data: 存档信息
        :return: 存档实例
        """
        self.data = dict(save_data)
        save_model = self.save_in_db()
        self.data = dict()  # 清空数据
        return save_model

    def save_in_db(self) -> models.Save:
        """
        将生成的俱乐部数据存至数据库
        :return: 俱乐部实例
        """
        data_schemas = schemas.SaveCreate(**self.data)
        save_model = crud.create_save(db=self.db, save=data_schemas)
        return save_model
