from datetime import date

from pydantic import BaseModel


class OfferCreate(BaseModel):
    save_id: int
    buyer_id: int
    target_id: int
    target_club_id: int
    offer_price: int
    season: int
    status: str = "w"
    date: date

    class Config:
        orm_mode = True


class Offer(OfferCreate):
    id: int
