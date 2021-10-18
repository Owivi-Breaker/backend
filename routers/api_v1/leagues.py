from typing import List, Union
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from core.db import get_db
from modules import computed_data_app
import schemas
import models
import crud
from utils import logger

router = APIRouter()


@router.get('/{league_id}/points-table')
def get_points_table(save_id: int, game_season: int, league_id: Union[int, str], game_type: str = None,
                     db: Session = Depends(get_db)):
    if isinstance(league_id, int):
        game_name = crud.get_league_by_id(db=db, league_id=league_id).name
    else:
        game_name = league_id
    computed_game = computed_data_app.ComputedGame(db=db, save_id=save_id)
    df = computed_game.get_season_points_table(game_season, game_name, game_type)
    return computed_game.switch2json(df)


@router.get('/{league_id}/player-chart')
def get_player_chart(save_id: int, game_season: int, league_id: Union[int, str], db: Session = Depends(get_db)):
    if isinstance(league_id, int):
        game_name = crud.get_league_by_id(db=db, league_id=league_id).name
    else:
        game_name = league_id
    computed_game = computed_data_app.ComputedGame(db=db, save_id=save_id)
    df = computed_game.get_season_player_chart(game_season, game_name)
    return computed_game.switch2json(df)
