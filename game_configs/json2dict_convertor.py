import json

with open("./game_configs/data/super_leagues.json", encoding="utf-8") as f_obj:
    super_leagues = json.load(f_obj)

with open("./game_configs/data/five_leagues.json", encoding="utf-8") as f_obj:
    five_leagues = json.load(f_obj)

with open("./game_configs/data/country_potential.json", encoding="utf-8") as f_obj:
    country_potential = json.load(f_obj)

with open("./game_configs/data/location_capability.json", encoding="utf-8") as f_obj:
    location_capability = json.load(f_obj)

with open("./game_configs/data/formations.json", encoding="utf-8") as f_obj:
    formations = json.load(f_obj)

with open("./game_configs/data/capa_potential.json", encoding="utf-8") as f_obj:
    capa_potential = json.load(f_obj)

with open("./game_configs/data/avatar.json", encoding="utf-8") as f_obj:
    avatar_style = json.load(f_obj)
