from utils import utils, logger
import models
import schemas
import game_configs
from modules.game_app import game_eve_app

from typing import Dict, List, Sequence, Set, Tuple, Optional
import datetime
from sqlalchemy.orm import Session


class Player(game_eve_app.Player):
    def __init__(self,
                 db: Session, player_model: models.Player, location: str, season: int, date: str):
        super().__init__(db=db, player_model=player_model, location=location, season=season, date=date)
