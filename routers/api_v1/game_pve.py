import schemas
import models
import crud
import utils.utils
from core.db import engine, get_db
from modules import game_app

from typing import List, Dict, Union, Optional
import json
from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

router = APIRouter()


@router.post('/start-game')
def commit_lineup_n_start_game(lineup: Optional[Dict[int, str]] = None,
                               tactic_weight: Optional[Dict[str, int]] = None,
                               db: Session = Depends(get_db),
                               save_model: models.Save = Depends(utils.get_current_save)):
    """
    保存阵容选择并且准备开始pve比赛
    """
    if not lineup:
        # 自动选人
        player_selector = game_app.PlayerSelector(
            club_id=save_model.player_club_id, db=db, season=save_model.season, date=save_model.date)
        lineup_str = player_selector.select_players(is_random=True, is_save_mode=True)
        save_model.lineup = lineup_str
    else:
        lineup_str = utils.utils.turn_dict2str(lineup)
        save_model.lineup = lineup_str
    # TODO 保存战术比重
    if not tactic_weight:
        pass
    else:
        pass
    return 'successfully save lineup n tactic_weight n ready to start pve game'
