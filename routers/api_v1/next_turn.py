from core.db import get_db
from fastapi import APIRouter, BackgroundTasks, Depends
from modules import next_turn_app
from sqlalchemy.orm import Session
from utils import logger

router = APIRouter()


@router.get("/holiday")
def next_turns_for_holiday(save_id: int, turn_num: int, db: Session = Depends(get_db)):
    """
    专门用于度假的下一回合api
    """
    next_turner = next_turn_app.NextTurner(db=db, save_id=save_id, skip=True)
    for i in range(turn_num):
        logger.info("第{}回合".format(str(i + 1)))
        next_turner.plus_days()
        next_turner.check()


def next_turn_background_task(next_turner: next_turn_app.NextTurner):
    next_turner.check()


@router.get("/")
def next_turn_with_background_tasks(save_id: int, background_task: BackgroundTasks, db: Session = Depends(get_db)):
    """
    开启后台任务的下一回合
    """
    next_turner = next_turn_app.NextTurner(db=db, save_id=save_id)
    next_turner.plus_days()
    msg = {"state": "null"}
    if next_turner.check_if_exists_pve():
        msg["state"] = "pve"
    background_task.add_task(next_turn_background_task, next_turner=next_turner)
    return msg
