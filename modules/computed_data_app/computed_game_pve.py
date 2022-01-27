from sqlalchemy.orm import Session

import crud
import models
import schemas


class ComputedGamePvE:
    def __init__(self, db: Session, save_id: int, game_pve_model: models.GamePvE = None):
        self.db = db
        self.save_id = save_id
        self.game_pve_model = game_pve_model \
            if game_pve_model else crud.get_game_pve_by_save_id(db=self.db, save_id=self.save_id)

    @staticmethod
    def get_player_pve_show(player_pve_model: models.PlayerPvE) -> schemas.PlayerPvEShow:
        data = dict()
        data['player_id'] = player_pve_model.player_id
        data['ori_location'] = player_pve_model.ori_location
        data['real_location'] = player_pve_model.real_location
        data['real_rating'] = player_pve_model.real_rating
        data['final_rating'] = player_pve_model.final_rating
        data['actions'] = player_pve_model.actions
        data['shots'] = player_pve_model.shots
        data['goals'] = player_pve_model.goals
        data['assists'] = player_pve_model.assists
        data['passes'] = player_pve_model.passes
        data['pass_success'] = player_pve_model.pass_success
        data['dribbles'] = player_pve_model.dribbles
        data['dribble_success'] = player_pve_model.dribble_success
        data['tackles'] = player_pve_model.tackles
        data['tackle_success'] = player_pve_model.tackle_success
        data['aerials'] = player_pve_model.aerials
        data['aerial_success'] = player_pve_model.aerial_success
        data['saves'] = player_pve_model.saves
        data['save_success'] = player_pve_model.save_success
        data['original_stamina'] = player_pve_model.original_stamina
        data['final_stamina'] = player_pve_model.final_stamina
        return schemas.PlayerPvEShow(**data)

    @staticmethod
    def get_team_pve_show(team_pve_model: models.TeamPvE) -> schemas.TeamPvEShow:
        data = dict()
        data['club_id'] = team_pve_model.club_id
        data['score'] = team_pve_model.score
        data['is_player'] = team_pve_model.is_player
        data['attempts'] = team_pve_model.attempts
        data['wing_cross'] = team_pve_model.wing_cross
        data['wing_cross_success'] = team_pve_model.wing_cross_success
        data['under_cutting'] = team_pve_model.under_cutting
        data['under_cutting_success'] = team_pve_model.under_cutting_success
        data['pull_back'] = team_pve_model.pull_back
        data['pull_back_success'] = team_pve_model.pull_back_success
        data['middle_attack'] = team_pve_model.middle_attack
        data['middle_attack_success'] = team_pve_model.middle_attack_success
        data['counter_attack'] = team_pve_model.counter_attack
        data['counter_attack_success'] = team_pve_model.counter_attack_success
        return schemas.TeamPvEShow(**data)

    @staticmethod
    def get_game_pve_show(game_pve_model: models.GamePvE) -> schemas.GamePvEShow:
        data = dict()
        data['player_club_id'] = game_pve_model.player_club_id
        data['computer_club_id'] = game_pve_model.computer_club_id
        data['home_club_id'] = game_pve_model.home_club_id
        data['name'] = game_pve_model.name
        data['type'] = game_pve_model.type
        data['date'] = game_pve_model.date
        data['season'] = game_pve_model.season
        data['cur_attacker'] = game_pve_model.cur_attacker
        data['turns'] = game_pve_model.turns
        data['script'] = game_pve_model.script
        data['new_script'] = game_pve_model.new_script
        data['counter_attack_permitted'] = game_pve_model.counter_attack_permitted
        return schemas.GamePvEShow(**data)

    def get_show_data(self) -> schemas.GamePvEInfo:
        game_pve_show = self.get_game_pve_show(self.game_pve_model)

        if self.game_pve_model.teams[0].is_player:
            p = self.game_pve_model.teams[0]
            e = self.game_pve_model.teams[1]
        else:
            p = self.game_pve_model.teams[1]
            e = self.game_pve_model.teams[0]

        data = dict()
        data['game_info'] = game_pve_show
        data['player_team_info'] = self.get_team_pve_show(p)
        data['computer_team_info'] = self.get_team_pve_show(e)
        data['player_players_info'] = [self.get_player_pve_show(player) for player in p.players]
        data['computer_players_info'] = [self.get_player_pve_show(player) for player in e.players]
        return schemas.GamePvEInfo(**data)
