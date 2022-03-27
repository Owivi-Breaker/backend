from typing import List
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

import schemas
import models
from core.db import get_db
import crud
import utils
from modules import computed_data_app
from utils import logger

router = APIRouter()


@router.get('/', response_model=List[schemas.ClubShow])
def get_clubs(save_id: int, db: Session = Depends(get_db)) -> List[schemas.ClubShow]:
    """
    获取指定存档的所有俱乐部信息
    :param save_id: 存档 id
    """
    db_clubs: List[models.Club] = crud.get_clubs_by_save(db=db, save_id=save_id)
    club_shows: List[schemas.ClubShow] = [
        computed_data_app.ComputedClub(
            club_id=club_model.id, db=db, club_model=club_model).get_show_data()
        for club_model in db_clubs]
    return club_shows


@router.get('/me', response_model=schemas.ClubShow, tags=['me api'])
def get_club_by_user(save_model=Depends(utils.get_current_save), db: Session = Depends(get_db)) -> schemas.ClubShow:
    """
    获取玩家俱乐部信的信息
    """
    club_model: models.Club = crud.get_club_by_id(db=db, club_id=save_model.player_club_id)

    return computed_data_app.ComputedClub(
        club_id=club_model.id, db=db).get_show_data()


@router.get('/{club_id}', response_model=schemas.ClubShow)
def get_club_by_id(club_id: int, db: Session = Depends(get_db)) -> schemas.ClubShow:
    """
    获取指定id的俱乐部信息
    """
    club_model = crud.get_club_by_id(db=db, club_id=club_id)
    return computed_data_app.ComputedClub(
        club_id=club_model.id, db=db, club_model=club_model).get_show_data()


@router.get('/me/player', response_model=List[schemas.PlayerShow], tags=['player api', 'me api'])
def get_players_by_user(
        db: Session = Depends(get_db),
        save_model=Depends(utils.get_current_save)) -> List[schemas.PlayerShow]:
    """
    获取玩家俱乐部的球员信息
    :param save_model: 存档实例
    :return: list of schemas.PlayerShow
    """

    club_model = crud.get_club_by_id(db=db, club_id=save_model.player_club_id)
    return [computed_data_app.ComputedPlayer(
        player_id=player_model.id, db=db, player_model=player_model,
        season=save_model.season, date=save_model.date).get_show_data()
            for player_model in club_model.players]


@router.get('/{club_id}/player', response_model=List[schemas.PlayerShow], tags=['player api'])
def get_players_by_club(
        club_id: int, db: Session = Depends(get_db),
        save_model=Depends(utils.get_current_save), is_player_club: bool = False) -> List[schemas.PlayerShow]:
    """
    获取指定俱乐部的球员信息
    :param club_id: 俱乐部 id
    :param save_model: 存档实例
    :param is_player_club: 是否是玩家俱乐部
    :return: list of schemas.PlayerShow
    """
    if is_player_club:
        club_model = crud.get_club_by_id(db=db, club_id=save_model.player_club_id)
    else:
        club_model = crud.get_club_by_id(db=db, club_id=club_id)
    return [computed_data_app.ComputedPlayer(
        player_id=player_model.id, db=db, player_model=player_model,
        season=save_model.season, date=save_model.date).get_show_data()
            for player_model in club_model.players]


@router.get('/me/player/total-game-data', response_model=List[schemas.TotalGamePlayerDataShow], tags=['player api'])
def get_total_game_players_data_by_user(
        start_season: int = None, end_season: int = None,
        db: Session = Depends(get_db),
        save_model=Depends(utils.get_current_save)) -> List[schemas.TotalGamePlayerDataShow]:
    """
    获取玩家俱乐部所有球员的赛季比赛信息
    :param start_season: 开始赛季，若为空，默认1开始
    :param end_season: 结束赛季，若为空，默认当前赛季
    """
    club_model = crud.get_club_by_id(db=db, club_id=save_model.player_club_id)

    game_players_data = [
        computed_data_app.ComputedPlayer(
            player_id=player_model.id, db=db,
            season=save_model.season, date=save_model.date,
            player_model=player_model).get_total_game_player_data(start_season=start_season, end_season=end_season)
        for player_model in club_model.players]
    logger.info(game_players_data[0])
    return game_players_data


@router.get('/{club_id}/player/total-game-data', response_model=List[schemas.TotalGamePlayerDataShow],
            tags=['player api'])
def get_total_game_players_data_by_club(
        club_id: int,
        start_season: int = None, end_season: int = None,
        db: Session = Depends(get_db),
        save_model=Depends(utils.get_current_save)) -> List[schemas.TotalGamePlayerDataShow]:
    """
    获取指定俱乐部所有球员的赛季比赛信息
    :param club_id: 俱乐部id
    :param start_season: 开始赛季，若为空，默认1开始
    :param end_season: 结束赛季，若为空，默认当前赛季
    """
    club_model = crud.get_club_by_id(db=db, club_id=club_id)

    game_players_data = [
        computed_data_app.ComputedPlayer(
            player_id=player_model.id, db=db,
            season=save_model.season, date=save_model.date,
            player_model=player_model).get_total_game_player_data(start_season=start_season, end_season=end_season)
        for player_model in club_model.players]

    return game_players_data


@router.get('/me/estimate-finance')
def get_estimate_finance(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    """
    获取玩家俱乐部的预计收入与支出
    """
    user_club = crud.get_club_by_id(db=db, club_id=save_model.player_club_id)
    tickets = user_club.reputation * 8  # 门票
    ad = user_club.reputation ** 3 * 0.02 + 500  # 广告
    tv = 0  # 转播
    bonus = 0  # 奖金
    player_wage = 0
    crew_wage = 0
    game = computed_data_app.ComputedGame(db=db, save_id=save_model.id)
    league = crud.get_league_by_id(db=db, league_id=user_club.league_id)
    df = game.get_season_points_table(game_season=save_model.season, game_name=league.name)
    point_table = [tuple(x) for x in df.values]
    user_rank = 20
    if point_table:
        for i in range(0, len(point_table)):
            if point_table[i][0] == user_club.name:
                user_rank = i + 1
                break
    else:
        for club in league.clubs:
            point_table.append(club.name)
        for i in range(0, len(point_table)):
            if point_table[i] == user_club.name:
                user_rank = i + 1
                break
    if league.name == "英超":
        if user_rank == 1:
            tv += 15000
            bonus += 2500
        elif user_rank == 2:
            tv += 9000
            bonus += 1500
        elif user_rank == 3:
            tv += 9000
        else:
            tv += 4800
    elif league.name == "西甲":
        if user_rank == 1:
            tv += 12500
            bonus += 2500
        elif user_rank == 2:
            tv += 7500
            bonus += 1500
        elif user_rank == 3:
            tv += 7500
        else:
            tv += 4000
    elif league.name == "德甲":
        if user_rank == 1:
            tv += 10200
            bonus += 2500
        elif user_rank == 2:
            tv += 6000
            bonus += 1500
        elif user_rank == 3:
            tv += 6000
        else:
            tv += 3200
    elif league.name == "法甲":
        if user_rank == 1:
            tv += 8750
            bonus += 2500
        elif user_rank == 2:
            tv += 5250
            bonus += 1500
        elif user_rank == 3:
            tv += 5250
        else:
            tv += 2800
    elif league.name == "意甲":
        if user_rank == 1:
            tv += 10000
            bonus += 2500
        elif user_rank == 2:
            tv += 6000
            bonus += 1500
        elif user_rank == 3:
            tv += 6000
        else:
            tv += 3200
    elif league.name == "英冠":
        if user_rank == 1:
            tv += 6250
            bonus += 2500
        elif user_rank == 2:
            tv += 3750
            bonus += 1500
        elif user_rank == 3:
            tv += 3750
        else:
            tv += 2000
    elif league.name == "西乙":
        if user_rank == 1:
            tv += 5625
            bonus += 2500
        elif user_rank == 2:
            tv += 3375
            bonus += 1500
        elif user_rank == 3:
            tv += 3375
        else:
            tv += 1800
    else:
        if user_rank == 1:
            tv += 5000
            bonus += 2500
        elif user_rank == 2:
            tv += 3000
            bonus += 1500
        elif user_rank == 3:
            tv += 3000
        else:
            tv += 1600
    for player in user_club.players:
        player_wage += player.wages
    crew_wage += 2 ** (user_club.assistant - 1) * 5
    crew_wage += 2 ** (user_club.doctor - 1) * 5
    crew_wage += 2 ** (user_club.negotiator - 1) * 5
    crew_wage += 2 ** (user_club.scout - 1) * 5
    return {"门票": tickets, "广告": ad, "转播": tv, "赛事奖金": bonus, "球员工资": player_wage, "职员工资": crew_wage}


@router.get('/me/best-players')
def get_best_players(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    """
    获取玩家俱乐部中数据最好的一些球员
    """
    club_model = crud.get_club_by_id(db=db, club_id=save_model.player_club_id)
    game_players_data = [
        computed_data_app.ComputedPlayer(
            player_id=player_model.id, db=db,
            season=save_model.season, date=save_model.date,
            player_model=player_model).get_total_game_player_data(start_season=save_model.season,
                                                                  end_season=save_model.season)
        for player_model in club_model.players]
    most_score = 0
    highest_rate = 0
    most_assistant = 0
    highest_passing = 0
    highest_tackle = 0
    highest_dribble = 0
    for i in range(0, len(game_players_data)):
        player_info = game_players_data[i]
        if player_info.goals >= most_score:
            best_shooter = player_info.id
            most_score = player_info.goals
        if player_info.assists >= most_assistant:
            best_assistant = player_info.id
            most_assistant = player_info.assists
        if player_info.pass_success >= highest_passing:
            best_passer = player_info.id
            highest_passing = player_info.pass_success
        if player_info.tackle_success >= highest_tackle:
            best_tackler = player_info.id
            highest_tackle = player_info.tackle_success
        if player_info.dribble_success >= highest_dribble:
            best_dribbler = player_info.id
            highest_dribble = player_info.dribble_success
        if player_info.final_rating >= highest_rate:
            best_player = player_info.id
            highest_rate = player_info.final_rating
    if best_shooter == -1:
            best_shooter = club_model.players[i].translated_name
    else:
            best_shooter = crud.get_player_by_id(player_id=best_shooter, db=db).translated_name
    if best_assistant == -1:
            best_assistant = club_model.players[i].translated_name
    else:
            best_assistant = crud.get_player_by_id(player_id=best_assistant, db=db).translated_name
    if best_passer == -1:
            best_passer = club_model.players[i].translated_name
    else:
            best_passer = crud.get_player_by_id(player_id=best_passer, db=db).translated_name
    if best_tackler == -1:
            best_tackler = club_model.players[i].translated_name
    else:
            best_tackler = crud.get_player_by_id(player_id=best_tackler, db=db).translated_name
    if best_dribbler == -1:
            best_dribbler = club_model.players[i].translated_name
    else:
            best_dribbler = crud.get_player_by_id(player_id=best_dribbler, db=db).translated_name
    if best_player == -1:
            best_player = club_model.players[i].translated_name
    else:
            best_player = crud.get_player_by_id(player_id=best_player, db=db).translated_name

    return {"最佳射手": best_shooter,
            "进球": most_score,
            "平均评分最高": best_player,
            "评分": highest_rate,
            "助攻最多": best_assistant,
            "助攻": most_assistant,
            "传球成功率最高": best_passer,
            "传球成功率": highest_passing,
            "拦截成功率最高": best_tackler,
            "拦截成功率": highest_tackle,
            "过人成功率最高": best_dribbler,
            "过人成功率": highest_dribble}
