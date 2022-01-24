from modules import computed_data_app
from core.db import get_session
import crud
import time

save_model = crud.get_save_by_id(db=get_session(), save_id=1)
club_model = crud.get_club_by_id(db=get_session(), club_id=save_model.player_club_id)

s = time.time()
# game_players_data = [
#     crud.get_player_game_data(
#         db=get_session(), player_id=player_model.id, start_season=1, end_season=2
#     ) for player_model in club_model.players]

game_players_data = [
    computed_data_app.ComputedPlayer(
        player_id=player_model.id, db=get_session(),
        season=save_model.season, date=save_model.date,
        player_model=player_model).get_show_data()
    for player_model in club_model.players]

e = time.time()
print('共耗时{}s'.format(e - s))

# print(game_players_data)
