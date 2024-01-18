from sqlalchemy.orm import Session
from game_configs import formations
import random
from modules.ml_app.base_game.base_game import BaseGame
from typing import Dict
import pandas as pd
import os
from core.db import get_session
from utils import logger

pos_formations = {
    'ST': ("4-4-2", "4-1-4-1",
           "4-1-2-3", "3-5-2",
           "4-3-1-2", "4-3-3"),
    'LW': ("4-1-2-3", "4-3-3"),
    'RW': ("4-1-2-3", "4-3-3"),
    'CAM': ("4-1-2-3", "4-3-1-2"),
    'CM': ("4-4-2", "4-1-4-1",
           "3-5-2", "4-3-3"),
    'LM': ("4-4-2", "4-1-4-1",
           "3-5-2", "4-3-3"),
    'RM': ("4-4-2", "4-1-4-1",
           "3-5-2", "4-3-3"),
    'CDM': ("4-1-4-1", "4-1-2-3",
            "3-5-2", "4-3-1-2"),
    'CB': ("4-4-2", "4-1-4-1",
           "4-1-2-3", "3-5-2",
           "4-3-1-2", "4-3-3"),
    'LB': ("4-4-2", "4-1-4-1",
           "4-1-2-3", "4-3-1-2"
           , "4-3-3"),
    'RB': ("4-4-2", "4-1-4-1",
           "4-1-2-3", "4-3-1-2",
           "4-3-3"),
    'GK': ("4-4-2", "4-1-4-1",
           "4-1-2-3", "3-5-2",
           "4-3-1-2", "4-3-3"),
}


class Starter:
    def __init__(self, pos: str, db: Session):
        self.pos = pos
        self.db = db
        self.data = []
        self.path = os.getcwd()

    def start(self, num: int):
        self.simulate_games(num)
        df = self.switch2df()
        self.save_to_path(df)

    def simulate_games(self, num: int):
        base_game = BaseGame(self.db, self.pos)
        l, r = 0, 0
        for _ in range(num):
            capa = self.get_random_capa()
            formation_name = random.choice(pos_formations[self.pos])
            ls, rs = base_game.start(capa, formations[formation_name])
            self.data.append([self.pos, formation_name, *self.get_ordered_capa_list(capa), ls, rs])
            l += ls
            r += rs
        logger.info('{}:{}'.format(l, r))

    def switch2df(self) -> pd.DataFrame:
        col = ['pos', 'formations', 'shooting', 'passing', 'dribbling', 'interception', 'pace', 'strength',
               'aggression', 'anticipation', 'free_kick', 'stamina', 'goalkeeping',
               'left_score', 'right_score']
        df = pd.DataFrame(self.data, columns=col)
        return df

    def save_to_path(self, df):
        """
        保存球员信息表
        :param df:球员信息表
        """
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        df.to_csv(self.path + '/{}_records.csv'.format(self.pos),
                  index=False,
                  encoding="utf-8-sig")
        print('已保存至' + self.path + '\\{}_records.csv'.format(self.pos))

    @staticmethod
    def get_random_capa() -> Dict:
        capa = dict()
        capa_range = (10, 100)
        capa['shooting'] = random.randint(*capa_range)
        capa['passing'] = random.randint(*capa_range)
        capa['dribbling'] = random.randint(*capa_range)
        capa['interception'] = random.randint(*capa_range)
        capa['pace'] = random.randint(*capa_range)
        capa['strength'] = random.randint(*capa_range)
        capa['aggression'] = random.randint(*capa_range)
        capa['anticipation'] = random.randint(*capa_range)
        capa['free_kick'] = random.randint(*capa_range)
        capa['stamina'] = random.randint(*capa_range)
        capa['goalkeeping'] = random.randint(*capa_range)
        return capa

    @staticmethod
    def get_ordered_capa_list(capa: dict):
        return [capa['shooting'], capa['passing'], capa['dribbling'],
                capa['interception'], capa['pace'], capa['strength'],
                capa['aggression'], capa['anticipation'], capa['free_kick'],
                capa['stamina'], capa['goalkeeping']]


if __name__ == '__main__':
    starter = Starter('ST', db=get_session())
    starter.start(100)
