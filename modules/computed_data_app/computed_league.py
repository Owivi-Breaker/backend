from typing import Optional

import crud
import models
import schemas
from sqlalchemy.orm import Session


class ComputedLeague:
    def __init__(self, league_id: int, db: Session, league_model: Optional[models.League] = None):
        self.db = db
        self.league_id = league_id

        if league_model:
            # 为了减少数据的读操作，可以传入现成的club_model
            self.league_model = league_model
        else:
            self.league_model = crud.get_league_by_id(db=self.db, league_id=self.league_id)

    def get_show_data(self) -> schemas.LeagueShow:
        """
        获取返回给前端的俱乐部信息
        :return: schemas.LeagueShow
        """
        data = dict()
        data["id"] = self.league_model.id
        data["name"] = self.league_model.name
        data["cup"] = self.league_model.cup
        data["points"] = self.league_model.points

        return schemas.LeagueShow(**data)
