import datetime
from datetime import timedelta
from typing import List

import crud
import models
import schemas
import utils
from core.db import get_db
from fastapi import APIRouter, Depends
from modules import computed_data_app
from sqlalchemy.orm import Session
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
    best_shooter = best_assistant = best_passer = best_tackler = best_dribbler = best_player = -1
    for i in range(0, len(game_players_data)):  # 遍历得到六个最佳球员的id
        player_info = game_players_data[i]
        if player_info.goals >= most_score:
            best_shooter = player_info.id
            most_score = player_info.goals
        if player_info.assists >= most_assistant:
            best_assistant = player_info.id
            most_assistant = player_info.assists
        if player_info.passes > 0 and player_info.pass_success / player_info.passes >= highest_passing:
            best_passer = player_info.id
            highest_passing = player_info.pass_success / player_info.passes
        if player_info.tackles > 0 and player_info.tackle_success / player_info.tackles >= highest_tackle:
            best_tackler = player_info.id
            highest_tackle = player_info.tackle_success / player_info.tackles
        if player_info.dribbles > 0 and player_info.dribble_success / player_info.dribbles >= highest_dribble:
            best_dribbler = player_info.id
            highest_dribble = player_info.dribble_success / player_info.dribbles
        if player_info.final_rating >= highest_rate:
            best_player = player_info.id
            highest_rate = player_info.final_rating
    #  处理球员 id
    if best_shooter == -1:
        best_shooter = club_model.players[0]
        best_shooter_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_shooter.id, db=db,
            player_model=best_shooter, season=save_model.season, date=save_model.date).get_show_data()
    else:
        best_shooter = crud.get_player_by_id(player_id=best_shooter, db=db)
        best_shooter_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_shooter.id, db=db,
            player_model=best_shooter, season=save_model.season, date=save_model.date).get_show_data()
    if best_assistant == -1:
        best_assistant = club_model.players[0]
        best_assistant_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_assistant.id, db=db,
            player_model=best_assistant, season=save_model.season, date=save_model.date).get_show_data()
    else:
        best_assistant = crud.get_player_by_id(player_id=best_assistant, db=db)
        best_assistant_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_assistant.id, db=db,
            player_model=best_assistant, season=save_model.season, date=save_model.date).get_show_data()
    if best_passer == -1:
        best_passer = club_model.players[0]
        best_passer_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_passer.id, db=db,
            player_model=best_passer, season=save_model.season, date=save_model.date).get_show_data()
    else:
        best_passer = crud.get_player_by_id(player_id=best_passer, db=db)
        best_passer_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_passer.id, db=db,
            player_model=best_passer, season=save_model.season, date=save_model.date).get_show_data()
    if best_tackler == -1:
        best_tackler = club_model.players[0]
        best_tackler_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_tackler.id, db=db,
            player_model=best_tackler, season=save_model.season, date=save_model.date).get_show_data()
    else:
        best_tackler = crud.get_player_by_id(player_id=best_tackler, db=db)
        best_tackler_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_tackler.id, db=db,
            player_model=best_tackler, season=save_model.season, date=save_model.date).get_show_data()
    if best_dribbler == -1:
        best_dribbler = club_model.players[0]
        best_dribbler_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_dribbler.id, db=db,
            player_model=best_dribbler, season=save_model.season, date=save_model.date).get_show_data()
    else:
        best_dribbler = crud.get_player_by_id(player_id=best_dribbler, db=db)
        best_dribbler_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_dribbler.id, db=db,
            player_model=best_dribbler, season=save_model.season, date=save_model.date).get_show_data()
    if best_player == -1:
        best_player = club_model.players[0]
        best_player_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_player.id, db=db,
            player_model=best_player, season=save_model.season, date=save_model.date).get_show_data()
    else:
        best_player = crud.get_player_by_id(player_id=best_player, db=db)
        best_player_show: schemas.PlayerShow = computed_data_app.ComputedPlayer(
            player_id=best_player.id, db=db,
            player_model=best_player, season=save_model.season, date=save_model.date).get_show_data()

    return {"最佳射手": best_shooter_show,
            "进球": most_score,
            "平均评分最高": best_player_show,
            "评分": highest_rate,
            "助攻最多": best_assistant_show,
            "助攻": most_assistant,
            "传球成功率最高": best_passer_show,
            "传球成功率": highest_passing,
            "拦截成功率最高": best_tackler_show,
            "拦截成功率": highest_tackle,
            "过人成功率最高": best_dribbler_show,
            "过人成功率": highest_dribble}


@router.get('/me/finance-history')
def get_finance_history(days: int, db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    """
    获取指定天数内玩家收支情况
    """
    year, month, day = save_model.date.split('-')
    limit_date = datetime.date(int(year), int(month), int(day)) + timedelta(-days)
    finance_history = crud.get_user_finance_by_save(db=db, save_id=save_model.id, limit_date=limit_date)
    return finance_history


@router.get('/me/season-finance')
def get_season_finance(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    """
    获取当前赛季收益情况
    """
    season = save_model.season
    year = 2019 + season
    limit_date = datetime.date(int(year), 7, 31)
    finance_history = crud.get_user_finance_by_save(db=db, save_id=save_model.id, limit_date=limit_date)
    total_amount = 0
    for event in finance_history:
        total_amount += event.amount
    return total_amount


@router.get('/me/player-statistics')
def get_players_statistics(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    sum_age = 0
    sum_players = 0
    highest_wage: float = 0
    lowest_wage: float = 30
    user_club = crud.get_club_by_id(db=db, club_id=save_model.player_club_id)
    highest_wage_player = lowest_wage_player = user_club.players[0].translated_name
    for player in user_club.players:
        sum_age += player.age
        sum_players += 1
        if player.wages > highest_wage:
            highest_wage = player.wages
            highest_wage_player = player.translated_name
        if player.wages < lowest_wage:
            lowest_wage = player.wages
            lowest_wage_player = player.translated_name
    average_age: float = sum_age / sum_players

    return {"平均年龄": average_age,
            "最高工资": highest_wage,
            "最高工资球员": highest_wage_player,
            "最低工资": lowest_wage,
            "最低工资球员": lowest_wage_player}


@router.get('/me/season-goal-statistics')
def get_season_goal_statistics(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    computed_game = computed_data_app.ComputedGame(db=db, save_id=save_model.id)
    user_club = crud.get_club_by_id(db=db, club_id=save_model.player_club_id)
    league = crud.get_league_by_id(db=db, league_id=user_club.league_id)
    goal = lost = 0
    df = computed_game.get_season_points_table(save_model.season, league.name)
    point_table = [tuple(x) for x in df.values]
    if point_table:
        for rank in range(0, len(point_table)):
            if point_table[rank][1] == user_club.name:
                goal = point_table[rank][5]
                lost = point_table[rank][6]
                return {"进球": goal,
                        "失球": lost}
    else:
        return {"进球": goal,
                "失球": lost}


@router.get('/me/season-tactics-statistics')
def get_season_tactics_statistics(db: Session = Depends(get_db), save_model=Depends(utils.get_current_save)):
    """
    获取当前赛季俱乐部各战术成功率
    """
    game_infos = crud.get_game_team_info_by_club(db=db, club_id=save_model.player_club_id, season=save_model.season)

    wing_cross = wing_success = wing_rate = 0
    pull_back = pull_back_success = pull_rate = 0
    middle = middle_success = middle_rate = 0
    under_cut = under_cut_success = under_rate = 0
    counter = counter_success = counter_rate = 0
    game_datas = [game_info.team_data
                  for game_info in game_infos]
    if game_datas:
        for game_data in game_datas:
            wing_cross += game_data.wing_cross
            wing_success += game_data.wing_cross_success
            pull_back += game_data.pull_back
            pull_back_success += game_data.pull_back_success
            middle += game_data.middle_attack
            middle_success += game_data.middle_attack_success
            under_cut += game_data.under_cutting
            under_cut_success += game_data.under_cutting_success
            counter += game_data.counter_attack
            counter_success += game_data.counter_attack_success
        wing_rate = wing_success / wing_cross * 100
        pull_rate = pull_back_success / pull_back * 100
        middle_rate = middle_success / middle * 100
        under_rate = under_cut_success / under_cut * 100
        counter_rate = counter_success / counter * 100
    return {
        "下底传中": wing_cross,
        "下底传中成功": wing_success,
        "下底传中成功率": wing_rate,
        "倒三角": pull_back,
        "倒三角成功": pull_back_success,
        "倒三角成功率": pull_rate,
        "中路渗透": middle,
        "中路渗透成功": middle_success,
        "中路渗透成功率": middle_rate,
        "边路内切": under_cut,
        "边路内切成功": under_cut_success,
        "边路内切成功率": under_rate,
        "防守反击": counter,
        "防守反击成功": counter_success,
        "防守反击成功率": counter_rate
    }
