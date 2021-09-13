from sqlalchemy.orm import Session
import models
import schemas
from utils import logger


# region 比赛操作
# TODO 需要重构
def crud_create_game(game: schemas.Game, db: Session):
    """
    创建比赛表
    """
    db_game = models.Game(created_time=game.created_time, date=game.date, script=game.script, season=game.season,
                          mvp=game.mvp, type=game.type)
    # 提交数据库，生成id
    db.add(db_game)
    db.commit()

    for team_info in game.teams:
        crud_create_game_team_info(db_game.id, team_info)
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def crud_create_game_team_info(game_id: int, game_team_info: schemas.GameTeamInfo, db: Session):
    db_game_team_info = models.GameTeamInfo(
        game_id=game_id,
        club_id=game_team_info.club_id,
        created_time=game_team_info.created_time,
        name=game_team_info.name,
        score=game_team_info.score)
    # 提交数据库，生成id
    db.add(db_game_team_info)
    db.commit()

    crud_create_game_team_data(db_game_team_info.id, game_team_info.team_data)
    for player_datum in game_team_info.player_data:
        crud_create_game_player_data(db_game_team_info.id, player_datum)

    db.add(db_game_team_info)
    db.commit()
    db.refresh(db_game_team_info)
    return db_game_team_info


def crud_create_game_team_data(game_team_info_id: int, game_team_data: schemas.GameTeamData, db: Session):
    db_game_team_data = models.GameTeamData(game_team_info_id=game_team_info_id, **game_team_data.dict())
    db.add(db_game_team_data)
    db.commit()
    db.refresh(db_game_team_data)
    return db_game_team_data


def crud_create_game_player_data(game_team_info_id: int, game_player_data: schemas.GamePlayerData, db: Session):
    db_game_player_data = models.GamePlayerData(game_team_info_id=game_team_info_id, **game_player_data.dict())
    db.add(db_game_player_data)
    db.commit()
    db.refresh(db_game_player_data)
    return db_game_player_data


def crud_get_games_by_attri(query_str: str, db: Session, only_one: bool = False):
    if only_one:
        db_game = db.query(models.Game).filter(eval(query_str)).first()
        return db_game
    else:
        db_games = db.query(models.Game).filter(eval(query_str)).all()
        return db_games


def crud_delete_game_by_attri(query_str: str, db: Session):
    db_games = db.query(models.Game).filter(eval(query_str)).all()
    if not db_games:
        logger.info('无比赛表可删！')
    for db_game in db_games:
        db_game_teams_info = db.query(models.GameTeamInfo).filter(
            models.GameTeamInfo.game_id == db_game.id).all()
        for db_game_team_info in db_game_teams_info:
            db_game_team_data = db.query(models.GameTeamData).filter(
                models.GameTeamData.game_team_info_id == db_game_team_info.id).first()
            db.delete(db_game_team_data)
            db_game_players_data = db.query(models.GamePlayerData).filter(
                models.GamePlayerData.game_team_info_id == db_game_team_info.id).all()
            for db_game_player_data in db_game_players_data:
                db.delete(db_game_player_data)
            db.delete(db_game_team_info)
        db.delete(db_game)
        db.commit()

# endregion
