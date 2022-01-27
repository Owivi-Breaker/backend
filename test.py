
from modules import computed_data_app, generate_app, game_app

from modules import next_turn_app,transfer_app

from core.db import get_session
import crud
import time


save_model = crud.get_save_by_id(db=get_session(), save_id=1)
player_club_model = crud.get_club_by_id(db=get_session(), club_id=save_model.player_club_id)
computer_club_model = crud.get_club_by_id(db=get_session(), club_id=12)


calendar_game = {
    'club_id': '1,2',
    'game_name': 'test',
    'game_type': 'test'
}


player_selector = game_app.PlayerSelector(
    club_id=save_model.player_club_id, db=get_session(), season=save_model.season, date=save_model.date)
lineup_str = player_selector.select_players(is_random=True, is_save_mode=True)
save_model.lineup = lineup_str
get_session().commit()

game = {'game_name': 'test', 'game_type': 'league'}
game_pve_generator = generate_app.GamePvEGenerator(
    db=get_session(),
    save_model=save_model)
game_pve_generator.create_game_pve(
    player_club_id=player_club_model.id,
    computer_club_id=computer_club_model.id,
    game=game, date=save_model.date, season=save_model.season)
cur_attacker = game_pve_generator.create_team_n_player_pve()

flag = True
while flag:
    game_pve_models = crud.get_game_pve_by_save_id(db=get_session(), save_id=1)
    game_pve = game_app.GamePvE(game_pve_models=game_pve_models, db=get_session(), player_tactic='wing_cross')
    flag = game_pve.start_one_turn()
