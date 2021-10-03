import json

with open("./game_configs/data/super_leagues.json") as f_obj:
    super_leagues = json.load(f_obj)

with open("./game_configs/data/five_leagues.json") as f_obj:
    five_leagues = json.load(f_obj)

with open("./game_configs/data/country_potential.json") as f_obj:
    country_potential = json.load(f_obj)

with open("./game_configs/data/location_capability.json") as f_obj:
    location_capability = json.load(f_obj)

with open("./game_configs/data/formations.json") as f_obj:
    formations = json.load(f_obj)

with open("./game_configs/data/capa_potential.json") as f_obj:
    capa_potential = json.load(f_obj)
