import crud
import models
import schemas
import utils
from core.db import get_db
from fastapi import APIRouter, Depends, HTTPException
from modules import computed_data_app
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/{game_id}", response_model=schemas.GameShow)
def get_game_by_id(game_id: int, db: Session = Depends(get_db),
                   save_model: models.Save = Depends(utils.get_current_save)):
    game = crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    computed_game = computed_data_app.ComputedGame(db=db, save_id=save_model.id)
    return computed_game.get_show_data(game_id=game_id)
