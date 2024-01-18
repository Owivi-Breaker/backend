from pydantic import BaseModel


class TargetPlayerCreate(BaseModel):
    buyer_id: int
    target_id: int
    season: int
    save_id: int
    rejected_date: str = ""

    class Config:
        orm_mode = True


class TargetPlayer(TargetPlayerCreate):
    id: int
