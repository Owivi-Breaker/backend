import string
from datetime import datetime
from typing import List
from pydantic import BaseModel
import schemas


class OfferCreate(BaseModel):
    save_id: int
    buyer_id: int
    target_id: int
    target_club_id: int
    offer_price: int
    season: int
    status: str = 'w'

    class Config:
        orm_mode = True


class Offer(OfferCreate):
    id: int
