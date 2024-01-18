from core.db import get_session
from modules.ml_app.starter import Starter

if __name__ == '__main__':
    pos_list = ['ST', 'LW', 'CAM', 'CM', 'CDM', 'LM', 'RB', 'CB', 'GK']
    for pos in pos_list:
        starter = Starter(pos, db=get_session())
        starter.start(10000)
