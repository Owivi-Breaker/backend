from fm import League, Info
from game_configs import leagues
import crud
from core.db import get_db
from fastapi import Depends


class LeagueSystem:
    """
    世超、世冠联赛系统
    """

    def __init__(self, init_leagues=False):
        if init_leagues:
            self.init_leagues()
        self.l1 = League(gen_type='import', league_id=1)
        self.l2 = League(gen_type='import', league_id=2)

    @staticmethod
    def init_leagues():
        for league in leagues:
            c = League(league_data=league, gen_type='init')

    def start_season(self, start_year, years=1):
        for _ in range(years):
            self.l1.start(start_year, save_in_db=True)
            self.l2.start(start_year, save_in_db=True)
            self.promote_n_relegate(year=start_year)
            # 更新联赛数据
            self.l1.import_data()
            self.l2.import_data()
            start_year += 1

    def promote_n_relegate(self, year):
        """
        联赛升降级设置，根据赛季积分榜，在数据库中修改应升级/降级的球队的联赛级别
        :param year: 赛季开始年份
        """
        info = Info()
        df1 = info.get_points_table(year, self.l1.league_model.name)  # 世超
        df2 = info.get_points_table(year, self.l2.league_model.name)  # 世冠
        relegate_df = df1.sort_values(by=['积分', '净胜球', '胜球'], ascending=[False, False, False])
        relegate_club_id = relegate_df[-4:]['id'].to_list()
        for club_id in relegate_club_id:
            # 降级
            crud.update_club(db=Depends(get_db), club_id=club_id, attri={'league_id': 2})
        promote_df = df2.sort_values(by=['积分', '净胜球', '胜球'], ascending=[False, False, False])
        promote_club_id = promote_df[:4]['id'].to_list()
        for club_id in promote_club_id:
            # 升级
            crud.update_club(db=Depends(get_db), club_id=club_id, attri={'league_id': 1})
