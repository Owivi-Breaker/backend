from typing import List
from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

import schemas
import models
from modules import computed_data_app
import crud
import utils
from core.db import get_db

router = APIRouter()


@router.get("/{game_id}", response_model=schemas.GameShow)
def get_game_by_id(game_id: int, db: Session = Depends(get_db),
                   save_model: models.Save = Depends(utils.get_current_save)):
    game = crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    computed_game = computed_data_app.ComputedGame(db=db, save_id=save_model.id)
    return computed_game.get_show_data(game_id=game_id)
