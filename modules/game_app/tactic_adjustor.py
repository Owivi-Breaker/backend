from sqlalchemy.orm import Session

import models
from utils import utils, Date, logger
from modules import game_app
import crud


class TacticAdjustor:
    """
    战术调整类
    最终结果，修改Coach表中的战术比重
    """

    def __init__(self, db: Session, club1_id: int, club2_id: int, player_club_id: int, save_id: int,
                 club1_model: models.Club, club2_model: models.Club,
                 season: int, date: str):
        self.db = db
        self.season = season
        self.date = date
        self.club1_id = club1_id
        self.club2_id = club2_id
        self.player_club_id = player_club_id
        self.save_id = save_id
        self.club1_model = club1_model
        self.club2_model = club2_model

    def adjust(self):
        """
        调整战术比重
        """
        game = game_app.GameEvE(db=self.db,
                                club1_id=self.club1_id, club2_id=self.club2_id,
                                date=self.date, game_type='test', game_name='test',
                                season=self.season, save_id=self.save_id,
                                club1_model=self.club1_model, club2_model=self.club2_model)
        lteam_data, rteam_data = game.tactical_start(num=10)

        tactic_pro1 = dict()
        tactic_pro1['wing_cross'] = int((lteam_data['wing_cross_success'] / lteam_data['wing_cross'] + 0.01) * 1000) + 5
        tactic_pro1['under_cutting'] = int(
            (lteam_data['under_cutting_success'] / (lteam_data['under_cutting'] + 0.01)) * 1000) + 5
        tactic_pro1['pull_back'] = int((lteam_data['pull_back_success'] / (lteam_data['pull_back'] + 0.01)) * 1000) + 5
        tactic_pro1['middle_attack'] = int(
            (lteam_data['middle_attack_success'] / (lteam_data['middle_attack'] + 0.01)) * 1000) + 5
        tactic_pro1['counter_attack'] = int(
            (lteam_data['counter_attack_success'] / (lteam_data['counter_attack'] + 0.01)) * 1000) + 5

        tactic_pro2 = dict()
        tactic_pro2['wing_cross'] = int(
            (rteam_data['wing_cross_success'] / (rteam_data['wing_cross'] + 0.01)) * 1000) + 5
        tactic_pro2['under_cutting'] = int(
            (rteam_data['under_cutting_success'] / (rteam_data['under_cutting'] + 0.01)) * 1000) + 5
        tactic_pro2['pull_back'] = int((rteam_data['pull_back_success'] / (rteam_data['pull_back'] + 0.01)) * 1000) + 5
        tactic_pro2['middle_attack'] = int(
            (rteam_data['middle_attack_success'] / (rteam_data['middle_attack'] + 0.01)) * 1000) + 5
        tactic_pro2['counter_attack'] = int(
            (rteam_data['counter_attack_success'] / (rteam_data['counter_attack'] + 0.01)) * 1000) + 5

        if self.club1_id != self.player_club_id:
            for key, value in tactic_pro1.items():
                setattr(self.club1_model.coach, key, value)

        if self.club2_id != self.player_club_id:
            for key, value in tactic_pro2.items():
                setattr(self.club2_model.coach, key, value)
            # coach_id = crud.get_club_by_id(db=self.db, club_id=self.club2_id).coach.id
            # crud.update_coach(db=self.db, coach_id=coach_id, attri=tactic_pro2)
        # self.db.commit()
