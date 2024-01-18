from datetime import datetime
from pydantic import BaseModel


class CalendarCreate(BaseModel):
    created_time: datetime

    date: str
    event_str: str


class Calendar(CalendarCreate):
    id: int
    save_id: int
