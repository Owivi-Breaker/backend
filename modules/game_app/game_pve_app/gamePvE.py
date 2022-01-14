from utils import utils, logger
import models
import schemas
import game_configs
from modules.game_app import game_eve_app
from modules.game_app import game_pve_app

from typing import Dict, List, Sequence, Set, Tuple, Optional
from sqlalchemy.orm import Session
import datetime


class GamePvE(game_eve_app.GameEvE):
    def __init__(self, db: Session, club1_id: int, club2_id: int,
                 date: str, game_type: str, game_name: str, season: int, save_id: int,
                 club1_model: models.Club = None, club2_model: models.Club = None):
        # super().__init__(db=db, club1_id=club1_id, club2_id=club2_id, date=date,
        #                  game_type=game_type, game_name=game_name, season=season, save_id=save_id,
        #                  club1_model=club1_model, club2_model=club2_model)
        self.db = db
        self.season = season
        self.date = date
        self.script = ''
        self.type = game_type
        self.name = game_name
        self.save_id = save_id
        self.winner_id = 0
        self.lteam = game_eve_app.Team(db=self.db, game=self, club_id=club1_id, club_model=club1_model,
                                       season=self.season, date=self.date)
        self.rteam = game_eve_app.Team(db=self.db, game=self, club_id=club2_id, club_model=club2_model,
                                       season=self.season, date=self.date)
