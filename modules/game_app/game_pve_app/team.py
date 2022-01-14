from utils import utils, logger
import models
import schemas
import game_configs
from modules.game_app import game_eve_app

from typing import Dict, List, Sequence, Set, Tuple, Optional
import datetime
from sqlalchemy.orm import Session


class Team(game_eve_app.Team):
    def __init__(self, db: Session, game, club_id: int,
                 season: int, date: str,
                 club_model: models.Club = None):
        super().__init__(db, game, club_id, season, date, club_model)
