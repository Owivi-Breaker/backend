from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from utils import logger


def add_user_finance(db: Session, user_finance: schemas.UserFinanceCreate):
    db_user_finance = models.UserFinance(**user_finance.dict())
    db.add(db_user_finance)
    return db_user_finance


def get_user_finance_by_save(db: Session, save_id: int) -> List[models.UserFinance]:
    db_user_finances = db.query(models.UserFinance).filter(
        and_(models.UserFinance.save_id == save_id)).all()
    return db_user_finances
