import json

with open("./game_configs/data/leagues.json") as f_obj:
    leagues = json.load(f_obj)

with open("./game_configs/data/leagues.json") as f_obj:
    country_potential = json.load(f_obj)

with open("./game_configs/data/location_selector.json") as f_obj:
    location_selector = json.load(f_obj)

with open("./game_configs/data/tactics.json") as f_obj:
    tactics = json.load(f_obj)

with open("./game_configs/data/rating_potential.json") as f_obj:
    rating_potential = json.load(f_obj)
