from sqlalchemy.orm import Session


class CalendarGenerator:
    def __init__(self, db: Session):
        self.db = db

    def generate(self, save_id: int):
        pass
