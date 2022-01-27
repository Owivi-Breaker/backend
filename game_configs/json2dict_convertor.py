import json

with open("./game_configs/data/super_leagues.json", encoding='utf-8') as f_obj:
    super_leagues = json.load(f_obj)

with open("./game_configs/data/five_leagues.json", encoding='utf-8') as f_obj:
    five_leagues = json.load(f_obj)

with open("./game_configs/data/country_potential.json", encoding='utf-8') as f_obj:
    country_potential = json.load(f_obj)

# with open("./game_configs/data/location_capability.json", encoding='utf-8') as f_obj:
#     location_capability = json.load(f_obj)
location_capability = [
    {
        "name": "ST",
        "weight": {
            "shooting": 0.45,
            "passing": 0,
            "dribbling": 0.05,
            "interception": 0,
            "pace": 0.05,
            "strength": 0.15,
            "aggression": 0,
            "anticipation": 0.15,
            "free_kick": 0,
            "stamina": 0.15,
            "goalkeeping": 0
        }
    },
    {
        "name": "LW",
        "weight": {
            "shooting": 0.2,
            "passing": 0.2,
            "dribbling": 0.4,
            "interception": 0,
            "pace": 0.2,
            "strength": 0,
            "aggression": 0,
            "anticipation": 0,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0
        }
    },
    {
        "name": "RW",
        "weight": {
            "shooting": 0.2,
            "passing": 0.2,
            "dribbling": 0.4,
            "interception": 0,
            "pace": 0.2,
            "strength": 0,
            "aggression": 0,
            "anticipation": 0,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0
        }
    },
    {
        "name": "CM",
        "weight": {
            "shooting": 0.2,
            "passing": 0.7,
            "dribbling": 0,
            "interception": 0,
            "pace": 0,
            "strength": 0,
            "aggression": 0,
            "anticipation": 0,
            "free_kick": 0,
            "stamina": 0.1,
            "goalkeeping": 0
        }
    },
    {
        "name": "CB",
        "weight": {
            "shooting": 0,
            "passing": 0,
            "dribbling": 0,
            "interception": 0.5,
            "pace": 0,
            "strength": 0.25,
            "aggression": 0,
            "anticipation": 0.25,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0
        }
    },
    {
        "name": "LB",
        "weight": {
            "shooting": 0,
            "passing": 0.2,
            "dribbling": 0.1,
            "interception": 0.3,
            "pace": 0.4,
            "strength": 0,
            "aggression": 0,
            "anticipation": 0,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0
        }
    },
    {
        "name": "RB",
        "weight": {
            "shooting": 0,
            "passing": 0.2,
            "dribbling": 0.1,
            "interception": 0.3,
            "pace": 0.4,
            "strength": 0,
            "aggression": 0,
            "anticipation": 0,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0
        }
    },
    {
        "name": "GK",
        "weight": {
            "shooting": 0,
            "passing": 0.05,
            "dribbling": 0,
            "interception": 0,
            "pace": 0,
            "strength": 0,
            "aggression": 0,
            "anticipation": 0,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0.95
        }
    },
    {
        "name": "CAM",
        "weight": {
            "shooting": 0.4,
            "passing": 0.5,
            "dribbling": 0,
            "interception": 0,
            "pace": 0,
            "strength": 0.05,
            "aggression": 0,
            "anticipation": 0.05,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0
        }
    },
    {
        "name": "LM",
        "weight": {
            "shooting": 0.1,
            "passing": 0.5,
            "dribbling": 0.2,
            "interception": 0,
            "pace": 0.2,
            "strength": 0,
            "aggression": 0,
            "anticipation": 0,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0
        }
    },
    {
        "name": "RM",
        "weight": {
            "shooting": 0.1,
            "passing": 0.5,
            "dribbling": 0.2,
            "interception": 0,
            "pace": 0.2,
            "strength": 0,
            "aggression": 0,
            "anticipation": 0,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0
        }
    },
    {
        "name": "CDM",
        "weight": {
            "shooting": 0,
            "passing": 0.5,
            "dribbling": 0,
            "interception": 0.3,
            "pace": 0,
            "strength": 0.1,
            "aggression": 0,
            "anticipation": 0.1,
            "free_kick": 0,
            "stamina": 0,
            "goalkeeping": 0
        }
    }
]

with open("./game_configs/data/formations.json", encoding='utf-8') as f_obj:
    formations = json.load(f_obj)

with open("./game_configs/data/capa_potential.json", encoding='utf-8') as f_obj:
    capa_potential = json.load(f_obj)

with open("./game_configs/data/avatar.json", encoding='utf-8') as f_obj:
    avatar_style = json.load(f_obj)
