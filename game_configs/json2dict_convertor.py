import json

with open("./game_configs/data/leagues.json") as f_obj:
    leagues = json.load(f_obj)

with open("./game_configs/data/leagues.json") as f_obj:
    country_potential = json.load(f_obj)

with open("./game_configs/data/location_capability.json") as f_obj:
    location_capability = json.load(f_obj)

with open("./game_configs/data/formations.json") as f_obj:
    formations = json.load(f_obj)

with open("./game_configs/data/rating_potential.json") as f_obj:
    rating_potential = json.load(f_obj)
