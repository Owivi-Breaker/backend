import schemas
from utils import logger
import models
import crud

from sqlalchemy.orm import Session
from typing import Optional


class ComputedClub:
    def __init__(self, club_id: int, db: Session, club_model: Optional[models.Club] = None):
        self.db = db
        self.club_id = club_id

        if club_model:
            # 为了减少数据的读操作，可以传入现成的club_model
            self.club_model = club_model
        else:
            self.club_model = crud.get_club_by_id(db=self.db, club_id=self.club_id)

    def get_show_data(self) -> schemas.ClubShow:
        """
        获取返回给前端的俱乐部信息
        :return: schemas.PlayerShow
        """
        data = dict()
        data['id'] = self.club_model.id
        data['name'] = self.club_model.name
        data['finance'] = self.club_model.finance
        data['reputation'] = self.club_model.reputation
        data['assistant'] = self.club_model.assistant
        data['doctor'] = self.club_model.doctor
        data['scout'] = self.club_model.scout
        data['negotiator'] = self.club_model.negotiator

        data['formation'] = self.club_model.coach.formation
        data['wing_cross'] = self.club_model.coach.wing_cross
        data['under_cutting'] = self.club_model.coach.under_cutting
        data['pull_back'] = self.club_model.coach.pull_back
        data['middle_attack'] = self.club_model.coach.middle_attack
        data['counter_attack'] = self.club_model.coach.counter_attack
        logger.debug(data)
        return schemas.ClubShow(**data)




