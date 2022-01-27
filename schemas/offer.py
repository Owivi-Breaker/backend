import string
from datetime import datetime
from typing import List
from pydantic import BaseModel
import schemas


class Offer_Create(BaseModel):
    save_id: int
    buyer_id: int
    target_id: int
    target_club_id: int
    offer_price: int
    season: int
    status: str

    class Config:
        orm_mode = True


class Offer(Offer_Create):
    id: int

