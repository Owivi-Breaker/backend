from datetime import date

from pydantic import BaseModel


class UserFinanceCreate(BaseModel):
    save_id: int
    amount: int
    event: str
    date: date

    class Config:
        orm_mode = True


class UserFinance(UserFinanceCreate):
    id: int
