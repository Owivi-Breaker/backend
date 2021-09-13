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
