import json
from typing import List, Union

import crud
import models
import pandas as pd
import schemas
from core.db import engine
from sqlalchemy.orm import Session, joinedload
from utils import logger, utils


class ComputedGame:
    def __init__(self, db: Session, save_id: int):
        self.db = db
        self.save_id = save_id

    @staticmethod
    def switch2df(data: List[dict]) -> pd.DataFrame:
        return pd.DataFrame(data)

    @staticmethod
    def switch2json(data) -> Union[str, dict]:
        if isinstance(data, list):
            return json.dumps(data)
        elif isinstance(data, pd.DataFrame):
            # 直接返回字典给前端，感觉非常奇怪，但是能用
            # 或 return json.loads(data.to_json(orient='records'))
            return data.to_dict(orient="records")

    @staticmethod
    def switch2csv(data: pd.DataFrame) -> str:
        return data.to_csv(index=False)

    def get_season_points_table(self, game_season: int, game_name: str, game_type: str = None) -> pd.DataFrame:
        """
        获取赛季积分榜
        :param game_name: 比赛名
        :param game_season: 赛季序号
        :param game_type: 比赛类型
        :return: df
        """
        if game_type:
            query_str = "and_(models.Game.save_id=='{}', models.Game.season=='{}', models.Game.name=='{}', models.Game.type=='{}')".format(
                self.save_id, int(game_season), game_name, game_type
            )
        else:
            query_str = "and_(models.Game.save_id=='{}', models.Game.season=='{}', models.Game.name=='{}')".format(
                self.save_id, int(game_season), game_name
            )
        # 使用eager load一次性查询到所有子表
        games = (
            self.db.query(models.Game)
            .options(joinedload(models.Game.teams, innerjoin=True))
            .filter(eval(query_str))
            .all()
        )

        # games = crud.get_games_by_attri(db=self.db, query_str=query_str)
        points_dict = dict()
        for game in games:
            team1 = game.teams[0]
            team2 = game.teams[1]
            club1_name = team1.club.name
            club2_name = team2.club.name
            if team1.club.name not in points_dict.keys():
                points_dict[club1_name] = dict()
                points_dict[club1_name]["id"] = team1.club_id
                points_dict[club1_name]["名称"] = team1.club.name
                points_dict[club1_name]["胜"] = 0
                points_dict[club1_name]["平"] = 0
                points_dict[club1_name]["负"] = 0
                points_dict[club1_name]["胜球"] = 0
                points_dict[club1_name]["输球"] = 0
                points_dict[club1_name]["积分"] = 0

            if team2.club.name not in points_dict.keys():
                points_dict[club2_name] = dict()
                points_dict[club2_name]["id"] = team2.club_id
                points_dict[club2_name]["名称"] = team2.club.name
                points_dict[club2_name]["胜"] = 0
                points_dict[club2_name]["平"] = 0
                points_dict[club2_name]["负"] = 0
                points_dict[club2_name]["胜球"] = 0
                points_dict[club2_name]["输球"] = 0
                points_dict[club2_name]["积分"] = 0

            points_dict[club1_name]["胜球"] += team1.score
            points_dict[club1_name]["输球"] += team2.score
            points_dict[club2_name]["胜球"] += team2.score
            points_dict[club2_name]["输球"] += team1.score

            if team1.score > team2.score:
                points_dict[club1_name]["胜"] += 1
                points_dict[club2_name]["负"] += 1
                points_dict[club1_name]["积分"] += 3
            elif team1.score < team2.score:
                points_dict[club2_name]["胜"] += 1
                points_dict[club1_name]["负"] += 1
                points_dict[club2_name]["积分"] += 3
            else:
                points_dict[club1_name]["平"] += 1
                points_dict[club2_name]["平"] += 1
                points_dict[club1_name]["积分"] += 1
                points_dict[club2_name]["积分"] += 1
        points_list = [team for team in points_dict.values()]
        df = self.switch2df(points_list)
        if df.empty:
            return pd.DataFrame([])
        s = df.apply(lambda row: row["胜球"] - row["输球"], axis=1)
        df.insert(7, "净胜球", s)

        return df.sort_values(by=["积分", "净胜球", "胜球"], ascending=[False, False, False])

    def get_season_player_chart(self, game_season: int, game_name: str) -> pd.DataFrame:
        """
        获取赛季球员数据
        :param game_name: 比赛类型
        :param game_season: 赛季序号
        :return: df
        """
        query_str = "and_(models.Game.save_id=='{}',models.Game.season=='{}', models.Game.name=='{}')".format(
            self.save_id, game_season, game_name
        )
        # 使用eager load一次性查询到所有子表
        games = (
            self.db.query(models.Game)
            .options(
                joinedload(models.Game.teams, innerjoin=True).joinedload(
                    models.GameTeamInfo.player_data, innerjoin=True
                )
            )
            .filter(eval(query_str))
            .all()
        )
        # games = crud.get_games_by_attri(db=self.db, query_str=query_str, load_type='joined')
        player_data_list = [
            player_data for game in games for game_team_info in game.teams for player_data in game_team_info.player_data
        ]
        filtered_list = []
        for player_data in player_data_list:
            one_piece = {
                "id": player_data.player_id,
                "姓名": player_data.player.translated_name,
                "俱乐部": player_data.game_team_info.club.name,
                "进球数": player_data.goals,
                "助攻数": player_data.assists,
                "传球数": player_data.passes,
                "传球成功数": player_data.pass_success,
                "过人数": player_data.dribbles,
                "过人成功数": player_data.dribble_success,
                "抢断数": player_data.tackles,
                "抢断成功数": player_data.tackle_success,
                "争顶数": player_data.aerials,
                "争顶成功数": player_data.aerial_success,
                "扑救数": player_data.saves,
                "扑救成功数": player_data.save_success,
            }
            filtered_list.append(one_piece)
        df = self.switch2df(filtered_list)
        if df.empty:
            return pd.DataFrame([])
        df = df.groupby(by=["id", "姓名", "俱乐部"]).agg(
            {
                "进球数": "sum",
                "助攻数": "sum",
                "传球数": "sum",
                "传球成功数": "sum",
                "过人数": "sum",
                "过人成功数": "sum",
                "抢断数": "sum",
                "抢断成功数": "sum",
                "争顶数": "sum",
                "争顶成功数": "sum",
                "扑救数": "sum",
                "扑救成功数": "sum",
            }
        )
        s = df.apply(
            lambda row: float(utils.retain_decimal(row["传球成功数"] / row["传球数"]) * 100) if row["传球数"] != 0 else 0, axis=1
        )
        df.insert(2, "传球成功率", s)

        s = df.apply(
            lambda row: float(utils.retain_decimal(row["过人成功数"] / row["过人数"]) * 100) if row["过人数"] != 0 else 0, axis=1
        )
        df.insert(3, "过人成功率", s)

        s = df.apply(
            lambda row: float(utils.retain_decimal(row["抢断成功数"] / row["抢断数"]) * 100) if row["抢断数"] != 0 else 0, axis=1
        )
        df.insert(4, "抢断成功率", s)

        s = df.apply(
            lambda row: float(utils.retain_decimal(row["争顶成功数"] / row["争顶数"]) * 100) if row["争顶数"] != 0 else 0, axis=1
        )
        df.insert(5, "争顶成功率", s)

        s = df.apply(
            lambda row: float(utils.retain_decimal(row["扑救成功数"] / row["扑救数"]) * 100) if row["扑救数"] != 0 else 0, axis=1
        )
        df.insert(6, "扑救成功率", s)
        df = df.reset_index()  # 将groupby()的分组结果转换成DataFrame对象
        return df

    @staticmethod
    def save_in_db(df, filename: str):
        # df.to_csv(path + '/' + filename)
        df.to_sql(filename, engine)

    def get_top_clubs_id(self, num: int, game_season: int, game_name: str, game_type: str = None) -> List[int]:
        """
        获取积分榜的前num名
        :param num: 返回的数量
        :param game_season: 赛季
        :param game_name: 比赛名
        :param game_type: 比赛类型
        :return: 前num名的club_id
        """
        df = self.get_season_points_table(game_season=game_season, game_name=game_name, game_type=game_type)
        return [x[0] for x in df.iloc[0:num, 0:1].values.tolist()]

    def get_top_clubs_model(
        self, num: int, game_season: int, game_name: str, game_type: str = None
    ) -> List[models.Club]:
        """
        获取积分榜的前num名
        :param num: 返回的数量
        :param game_season: 赛季
        :param game_name: 比赛名
        :param game_type: 比赛类型
        :return: 前num名的club_model
        """
        id_list = self.get_top_clubs_id(num=num, game_season=game_season, game_name=game_name, game_type=game_type)
        return [crud.get_club_by_id(db=self.db, club_id=club_id) for club_id in id_list]

    def get_game_winners(self, season: int, game_type: str, game_name: str) -> List[int]:
        """
        获取指定比赛中的(一批)胜者 用于创建淘汰赛日程
        :param season: 赛季
        :param game_type: 比赛性质
        :param game_name: 比赛名
        :return: 胜者club_id数组
        """
        query_str = "and_(models.Game.save_id=='{}',models.Game.season=='{}', models.Game.type=='{}', models.Game.name=='{}')".format(
            self.save_id, season, game_type, game_name
        )
        games: List[models.Game] = crud.get_games_by_attri(db=self.db, query_str=query_str)
        clubs_id: List[int] = []  # 参赛俱乐部
        for game in games:
            team1 = game.teams[0]
            team2 = game.teams[1]
            if team1.score >= team2.score:  # TODO 删掉等于号
                clubs_id.append(team1.club_id)
            elif team1.score < team2.score:
                clubs_id.append(team2.club_id)
            else:
                logger.error("淘汰赛平局！")
        return clubs_id

    def get_show_data(self, game_id: int) -> schemas.GameShow:
        """
        获取一场比赛的数据
        """
        game: models.Game = crud.get_game_by_id(db=self.db, game_id=game_id)
        g_data = dict()
        g_data["id"] = game.id
        g_data["season"] = game.season
        g_data["name"] = game.name
        g_data["type"] = game.type
        g_data["date"] = game.date
        g_data["script"] = game.script
        g_data["mvp"] = game.mvp
        g_data["winner_id"] = game.winner_id
        g_data["goal_record"] = [schemas.GoalRecord(**g) for g in json.loads(game.goal_record)]
        teams: List[schemas.GameTeamShow] = []
        for team in game.teams:
            t_data = dict()
            t_data["score"] = team.score
            t_data["club_id"] = team.club_id
            t_data["club_name"] = team.club.name

            t_data["attempts"] = team.team_data.attempts
            t_data["wing_cross"] = team.team_data.wing_cross
            t_data["wing_cross_success"] = team.team_data.wing_cross_success
            t_data["under_cutting"] = team.team_data.under_cutting
            t_data["under_cutting_success"] = team.team_data.under_cutting_success
            t_data["pull_back"] = team.team_data.pull_back
            t_data["pull_back_success"] = team.team_data.pull_back_success
            t_data["middle_attack"] = team.team_data.middle_attack
            t_data["middle_attack_success"] = team.team_data.middle_attack_success
            t_data["counter_attack"] = team.team_data.counter_attack
            t_data["counter_attack_success"] = team.team_data.counter_attack_success
            players: List[schemas.GamePlayerShow] = []
            for player in team.player_data:
                p_data = dict()
                p_data["player_id"] = player.player_id
                p_data["player_name"] = player.player.translated_name
                p_data["location"] = player.location
                p_data["final_rating"] = player.final_rating
                p_data["actions"] = player.actions
                p_data["shots"] = player.shots
                p_data["goals"] = player.goals
                p_data["assists"] = player.assists
                p_data["passes"] = player.passes
                p_data["pass_success"] = player.pass_success
                p_data["dribbles"] = player.dribbles
                p_data["dribble_success"] = player.dribble_success
                p_data["tackles"] = player.tackles
                p_data["tackle_success"] = player.tackle_success
                p_data["aerials"] = player.aerials
                p_data["aerial_success"] = player.aerial_success
                p_data["saves"] = player.saves
                p_data["save_success"] = player.save_success
                p_data["original_stamina"] = player.original_stamina
                p_data["final_stamina"] = player.final_stamina
                players.append(schemas.GamePlayerShow(**p_data))
            t_data["players_info"] = players
            teams.append(schemas.GameTeamShow(**t_data))
        g_data["teams_info"] = teams
        return schemas.GameShow(**g_data)
