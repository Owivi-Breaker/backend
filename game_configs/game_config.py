import enum


class Location(str, enum.Enum):
    ST = 'ST'
    LW = 'LW'
    RW = 'RW'
    CM = 'CM'
    CB = 'CB'
    LB = 'LB'
    RB = 'RB'
    GK = 'GK'

    CAM = 'CAM'
    LM = 'LM'
    RM = 'RM'
    CDM = 'CDM'


class Tactic(str, enum.Enum):
    wing_cross = 'wing_cross'
    under_cutting = 'under_cutting'
    pull_back = 'pull_back'
    middle_attack = 'middle_attack'
    counter_attack = 'counter_attack'


ori_mean_potential_capa = 80  # 初始潜力均值
ori_mean_capa = 15  # 初始能力均值
