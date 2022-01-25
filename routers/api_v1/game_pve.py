import json
from typing import List, Dict, Union, Optional
from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import random

import schemas
import models
import crud
from utils import logger, utils
import utils
from core.db import engine, get_db
from modules import game_app, generate_app, computed_data_app
import game_configs

router = APIRouter()


def commit_lineup_n_tactic_weight(db: Session,
                                  save_model: models.Save,
                                  lineup: Optional[Dict[int, str]] = None,
                                  tactic_weight: Optional[Dict[str, int]] = None):
    """
    保存玩家阵容和战术比重
    """
    if not lineup:
        # 自动选人
        player_selector = game_app.PlayerSelector(
            club_id=save_model.player_club_id, db=db, season=save_model.season, date=save_model.date)
        lineup_str = player_selector.select_players(is_random=True, is_save_mode=True)
        save_model.lineup = lineup_str
    else:
        lineup_str = utils.turn_dict2str(lineup)
        save_model.lineup = lineup_str

    if not tactic_weight:
        pass
    else:
        # 保存战术比重
        coach_model = crud.get_coach_by_club(db=db, club_id=save_model.player_club_id)
        coach_model.wing_cross = tactic_weight['wing_cross']
        coach_model.under_cutting = tactic_weight['under_cutting']
        coach_model.pull_back = tactic_weight['pull_back']
        coach_model.middle_attack = tactic_weight['middle_attack']
        coach_model.counter_attack = tactic_weight['counter_attack']
        db.commit()


@router.post('/skip')
def skip_game_pve(
        lineup: Optional[Dict[int, str]] = None,
        tactic_weight: Optional[Dict[str, int]] = None,
        db: Session = Depends(get_db),
        save_model: models.Save = Depends(utils.get_current_save)):
    """
    保存玩家阵容和战术比重 并且跳过pve比赛
    """
    commit_lineup_n_tactic_weight(lineup=lineup, tactic_weight=tactic_weight, db=db, save_model=save_model)
    # 创建附属的球队和球员临时表
    game_pve_generator = generate_app.GamePvEGenerator(
        db=db, save_model=save_model)
    game_pve_generator.create_team_n_player_pve()
    flag = True
    while flag:
        game_pve = game_app.GamePvE(save_id=save_model.id, db=db, player_tactic='')
        flag = game_pve.start_one_turn()

    # 返回数据
    computed_game_pve = computed_data_app.ComputedGamePvE(db=db, save_id=save_model.id)
    return computed_game_pve.get_show_data()


@router.post('/start')
def start_game_pve(
        lineup: Optional[Dict[int, str]] = None,
        tactic_weight: Optional[Dict[str, int]] = None,
        db: Session = Depends(get_db),
        save_model: models.Save = Depends(utils.get_current_save)):
    """
    保存玩家阵容和战术比重 并且准备开始pve比赛
    :return: 进攻方club_id
    """
    commit_lineup_n_tactic_weight(lineup=lineup, tactic_weight=tactic_weight, db=db, save_model=save_model)

    # 创建附属的球队和球员临时表
    game_pve_generator = generate_app.GamePvEGenerator(
        db=db, save_model=save_model)
    cur_attacker = game_pve_generator.create_team_n_player_pve()
    return {'attacker_club_id': cur_attacker}


@router.get('/next-turn')
def next_turn(tactic: str = None,
              db: Session = Depends(get_db),
              save_model: models.Save = Depends(utils.get_current_save)) -> schemas.GamePvEInfo:
    """
    下一回合
    :param tactic: 玩家球队的进攻战术名
    """

    # 开始回合
    game_pve = game_app.GamePvE(save_id=save_model.id, db=db, player_tactic=tactic)
    is_finished = game_pve.start_one_turn()
    # 返回数据
    computed_game_pve = computed_data_app.ComputedGamePvE(db=db, save_id=save_model.id)
    return computed_game_pve.get_show_data()
