import pandas as pd
from typing import List
import crud
from utils import utils
from core.db import get_db
from fastapi import Depends
from core.db import engine


class Info:
    def __init__(self):
        pass

    @staticmethod
    def switch2df(data: List[dict]):
        return pd.DataFrame(data)

    def get_points_table(self, year: str, game_type: str) -> pd.DataFrame:
        """
        获取赛季积分榜
        :param game_type: 比赛类型
        :param year: 赛季年份
        :return: df
        """
        query_str = "and_(models.Game.season=='{}', models.Game.type=='{}')".format(year, game_type)
        games = crud.get_games_by_attri(db=Depends(get_db), query_str=query_str)
        points_dict = dict()
        for game in games:
            team1 = game.teams[0]
            team2 = game.teams[1]
            if team1.name not in points_dict.keys():
                points_dict[team1.name] = dict()
                points_dict[team1.name]['id'] = team1.club_id
                points_dict[team1.name]['名称'] = team1.name
                points_dict[team1.name]['胜'] = 0
                points_dict[team1.name]['平'] = 0
                points_dict[team1.name]['负'] = 0
                points_dict[team1.name]['胜球'] = 0
                points_dict[team1.name]['输球'] = 0
                points_dict[team1.name]['积分'] = 0

            if team2.name not in points_dict.keys():
                points_dict[team2.name] = dict()
                points_dict[team2.name]['id'] = team2.club_id
                points_dict[team2.name]['名称'] = team2.name
                points_dict[team2.name]['胜'] = 0
                points_dict[team2.name]['平'] = 0
                points_dict[team2.name]['负'] = 0
                points_dict[team2.name]['胜球'] = 0
                points_dict[team2.name]['输球'] = 0
                points_dict[team2.name]['积分'] = 0

            points_dict[team1.name]['胜球'] += team1.score
            points_dict[team1.name]['输球'] += team2.score
            points_dict[team2.name]['胜球'] += team2.score
            points_dict[team2.name]['输球'] += team1.score

            if team1.score > team2.score:
                points_dict[team1.name]['胜'] += 1
                points_dict[team2.name]['负'] += 1
                points_dict[team1.name]['积分'] += 3
            elif team1.score < team2.score:
                points_dict[team2.name]['胜'] += 1
                points_dict[team1.name]['负'] += 1
                points_dict[team2.name]['积分'] += 3
            else:
                points_dict[team1.name]['平'] += 1
                points_dict[team2.name]['平'] += 1
                points_dict[team1.name]['积分'] += 1
                points_dict[team2.name]['积分'] += 1
        points_list = [team for team in points_dict.values()]
        df = self.switch2df(points_list)
        s = df.apply(lambda row: row['胜球'] - row['输球'], axis=1)
        df.insert(7, '净胜球', s)
        return df.sort_values(by=['积分', '净胜球', '胜球'], ascending=[False, False, False])

    def get_season_player_chart(self, year: str, game_type: str) -> pd.DataFrame:
        """
        获取赛季球员数据
        :param game_type: 比赛类型
        :param year: 赛季年份
        :return: df
        """
        query_str = "and_(models.Game.season=='{}', models.Game.type=='{}')".format(year, game_type)
        games = crud.get_games_by_attri(query_str=query_str)
        player_data_list = [player_data for game in games for game_team_info in game.teams for player_data in
                            game_team_info.player_data]
        filtered_list = []
        for player_data in player_data_list:
            one_piece = {
                'id': player_data.player_id,
                '姓名': player_data.name,
                '俱乐部': player_data.game_team_info.name,
                '进球数': player_data.goals,
                '助攻数': player_data.assists,
                '传球数': player_data.passes,
                '传球成功数': player_data.pass_success,
                '过人数': player_data.dribbles,
                '过人成功数': player_data.dribble_success,
                '抢断数': player_data.tackles,
                '抢断成功数': player_data.tackle_success,
                '争顶数': player_data.aerials,
                '争顶成功数': player_data.aerial_success,
                '扑救数': player_data.saves,
                '扑救成功数': player_data.save_success
            }
            filtered_list.append(one_piece)
        df = self.switch2df(filtered_list)
        df = df.groupby(by=['id', '姓名', '俱乐部']).agg(
            {
                '进球数': 'sum', '助攻数': 'sum',
                '传球数': 'sum', '传球成功数': 'sum',
                '过人数': 'sum', '过人成功数': 'sum',
                '抢断数': 'sum', '抢断成功数': 'sum',
                '争顶数': 'sum', '争顶成功数': 'sum',
                '扑救数': 'sum', '扑救成功数': 'sum', })
        s = df.apply(
            lambda row: float(utils.retain_decimal(row['传球成功数'] / row['传球数']) * 100) if row['传球数'] != 0 else 0, axis=1)
        df.insert(2, '传球成功率', s)

        s = df.apply(
            lambda row: float(utils.retain_decimal(row['过人成功数'] / row['过人数']) * 100) if row['过人数'] != 0 else 0, axis=1)
        df.insert(3, '过人成功率', s)

        s = df.apply(
            lambda row: float(utils.retain_decimal(row['抢断成功数'] / row['抢断数']) * 100) if row['抢断数'] != 0 else 0, axis=1)
        df.insert(4, '抢断成功率', s)

        s = df.apply(
            lambda row: float(utils.retain_decimal(row['争顶成功数'] / row['争顶数']) * 100) if row['争顶数'] != 0 else 0, axis=1)
        df.insert(5, '争顶成功率', s)

        s = df.apply(
            lambda row: float(utils.retain_decimal(row['扑救成功数'] / row['扑救数']) * 100) if row['扑救数'] != 0 else 0, axis=1)
        df.insert(6, '扑救成功率', s)
        return df

    @staticmethod
    def save_in_db(df, filename: str):
        # df.to_csv(path + '/' + filename)
        df.to_sql(filename, engine)

    # @staticmethod
    # def save(df, filename: str, file_format: str = 'json', path: str = config.CWD_URL):
    #     if file_format == 'json':
    #         df.to_json(path + '/' + filename)
    #     elif file_format == 'csv':
    #         df.to_csv(path + '/' + filename)
