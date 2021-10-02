from game_configs.game_config import Location
import random
from utils import Date, utils
from typing import Dict, List, Sequence, Set, Tuple, Optional
from utils import logger
import datetime
import crud
import models
import schemas
from fm import Club
from fastapi import Depends
from core.db import get_db

# 球员标准能力，DEBUG用
DEFAULT_RATING = {
    "shooting": 50,  # 射门
    "passing": 50,  # 传球
    "dribbling": 50,  # 盘带
    "interception": 50,  # 抢断
    "pace": 50,  # 速度
    "strength": 50,  # 力量
    "aggression": 50,  # 侵略
    "anticipation": 50,  # 预判
    "free_kick": 50,  # 任意球/点球
    "stamina": 50,  # 体能
    "goalkeeping": 50  # 守门
}


class Player:
    # 比赛中的球员类
    def __init__(self, player_model: models.Player, location: str, stamina: int = 100):
        self.player_model = player_model
        self.name = player_model.translated_name
        self.location = location
        self.real_location = location  # 记录每个回合变化后的位置
        self.rating = dict()
        self.init_rating()
        self.stamina = stamina
        self.data = {
            "original_stamina": self.stamina,
            "actions": 0,
            "goals": 0,
            "assists": 0,
            "shots": 0,
            "dribbles": 0,
            "dribble_success": 0,
            "passes": 0,
            "pass_success": 0,
            "tackles": 0,
            "tackle_success": 0,
            "aerials": 0,
            "aerial_success": 0,
            "saves": 0,
            "save_success": 0,
            'final_rating': 6.0
        }

    def init_rating(self):
        self.rating['shooting'] = self.player_model.shooting
        self.rating['passing'] = self.player_model.passing
        self.rating['dribbling'] = self.player_model.dribbling
        self.rating['interception'] = self.player_model.interception
        self.rating['pace'] = self.player_model.pace
        self.rating['strength'] = self.player_model.strength
        self.rating['aggression'] = self.player_model.aggression
        self.rating['anticipation'] = self.player_model.anticipation
        self.rating['free_kick'] = self.player_model.free_kick
        self.rating['stamina'] = self.player_model.stamina
        self.rating['goalkeeping'] = self.player_model.goalkeeping

    def export_game_player_data(self, created_time=datetime.datetime.now()) -> schemas.GamePlayerData:
        """
        导出数据
        :param created_time: 创建时间
        :return: 球员比赛数据
        """
        data = {
            'created_time': created_time,
            'player_id': self.player_model.id,
            'name': self.name,
            'location': self.location,
            **self.data,
            'final_stamina': self.stamina
        }
        game_player_data = schemas.GamePlayerData(**data)
        return game_player_data

    def get_rating(self, rating_name: str) -> float:
        """
        获取能力属性
        :param rating_name: 能力名称
        :return: 扣除体力debuff后的数据
        """
        if rating_name == 'stamina':
            return self.rating['stamina']
        return self.rating[rating_name] * (self.stamina / 100)

    def get_data(self, data_name: str):
        return self.data[data_name]

    def plus_data(self, data_name: str, average_stamina: Optional[float] = None):
        if data_name == 'shots' or data_name == 'dribbles' \
                or data_name == 'tackles' \
                or data_name == 'saves' or data_name == 'aerials':
            self.data['actions'] += 1
            if utils.select_by_pro(
                    {False: self.get_rating('stamina'), True: average_stamina}
            ) and average_stamina:
                self.stamina -= 2.5
                if self.stamina < 0:
                    self.stamina = 0
        elif data_name == 'passes':
            self.data['actions'] += 1
            if utils.select_by_pro(
                    {False: self.get_rating('stamina'), True: average_stamina}
            ) and average_stamina:
                self.stamina -= 1
                if self.stamina < 0:
                    self.stamina = 0
        self.data[data_name] += 1

    def shift_location(self):
        """
        确定每次战术的场上位置
        TODO 将概率值抽离出来作为可更改的全局变量
        """
        if self.location == Location.CAM:
            self.real_location = utils.select_by_pro(
                {Location.ST: 40, Location.CM: 60}
            )
        elif self.location == Location.LM:
            self.real_location = utils.select_by_pro(
                {Location.LW: 40, Location.CM: 60}
            )
        elif self.location == Location.RM:
            self.real_location = utils.select_by_pro(
                {Location.RW: 40, Location.CM: 60}
            )
        elif self.location == Location.CDM:
            self.real_location = utils.select_by_pro(
                {Location.CB: 40, Location.CM: 60}
            )
        elif self.location == Location.CM:
            # 中场有概率前压或后撤
            self.real_location = utils.select_by_pro(
                {Location.ST: 10, Location.CB: 10, Location.CM: 80}
            )
        elif self.location == Location.LB:
            self.real_location = utils.select_by_pro(
                {Location.LW: 20, Location.LB: 80}
            )
        elif self.location == Location.RB:
            self.real_location = utils.select_by_pro(
                {Location.RW: 20, Location.RB: 80}
            )
        else:
            self.real_location = self.location

    def get_location(self):
        return self.real_location


class Team:
    def __init__(self, game: 'Game', team_model: models.Club):
        self.game = game
        self.team_model = team_model
        self.name = team_model.name
        self.players: list = []
        self.score: int = 0
        self.tactic = dict()
        self.init_tactic()
        self.data = {
            'attempts': 0,
            "wing_cross": 0,
            "wing_cross_success": 0,
            "under_cutting": 0,
            "under_cutting_success": 0,
            "pull_back": 0,
            "pull_back_success": 0,
            "middle_attack": 0,
            "middle_attack_success": 0,
            "counter_attack": 0,
            "counter_attack_success": 0
        }

        self.init_players()

    def init_tactic(self):
        self.tactic['wing_cross'] = self.team_model.coach.wing_cross
        self.tactic['under_cutting'] = self.team_model.coach.under_cutting
        self.tactic['pull_back'] = self.team_model.coach.pull_back
        self.tactic['middle_attack'] = self.team_model.coach.middle_attack
        self.tactic['counter_attack'] = self.team_model.coach.counter_attack

    def export_game_team_data(self, created_time=datetime.datetime.now()) -> schemas.GameTeamData:
        """
        导出球队数据
        :param created_time: 创建时间
        :return: 球队数据
        """
        data = {
            'created_time': created_time,
            **self.data
        }
        game_team_data = schemas.GameTeamData(**data)
        return game_team_data

    def export_game_team_info(self, created_time=datetime.datetime.now()) -> schemas.GameTeamInfo:
        """
        导出球队赛信息
        :param created_time: 创建时间
        :return: 球队比赛信息
        """
        game_team_data = self.export_game_team_data(created_time)
        player_data = []
        for player in self.players:
            player_data.append(player.export_game_player_data(created_time))
        data = {
            'created_time': created_time,
            'club_id': self.team_model.id,
            'name': self.name,
            'score': self.score,
            'team_data': game_team_data,
            'player_data': player_data
        }
        game_team_info = schemas.GameTeamInfo(**data)
        return game_team_info

    def add_script(self, text: str):
        self.game.add_script(text)

    def set_capa(self, capa_name: str, num):
        for player in self.players:
            player.rating[capa_name] = num

    def init_players(self):
        club = Club(gen_type="db", club_id=self.team_model.id)
        players_model, locations_list = club.select_players()
        for player_model, location in zip(players_model, locations_list):
            self.players.append(Player(player_model, location))

    def get_rival_team(self):
        if self.game.lteam == self:
            return self.game.rteam
        else:
            return self.game.lteam

    def plus_data(self, data_name: str):
        if data_name == "wing_cross" or data_name == "under_cutting" or data_name == "pull_back" \
                or data_name == "middle_attack" or data_name == "counter_attack":
            self.data['attempts'] += 1
        self.data[data_name] += 1

    def select_tactic(self, counter_attack_permitted):
        """
        选择进攻战术
        :param counter_attack_permitted: 是否允许使用防反
        :return: 战术名
        """
        tactic_pro_total = self.tactic.copy()
        tactic_pro = self.tactic.copy()
        tactic_pro.pop("counter_attack")
        while True:
            tactic_name = utils.select_by_pro(tactic_pro_total) if counter_attack_permitted else utils.select_by_pro(
                tactic_pro)
            if tactic_name == 'wing_cross' and not self.get_location_players(
                    (Location.LW, Location.RW, Location.LB, Location.RB)):
                continue
            if tactic_name == 'under_cutting' and not self.get_location_players((Location.LW, Location.RW)):
                continue
            if tactic_name == 'pull_back' and not self.get_location_players((Location.LW, Location.RW)):
                continue
            if tactic_name == 'middle_attack' and not self.get_location_players((Location.CM,)):
                self.shift_location()
            else:
                break

        return tactic_name

    def get_average_capability(self, capa_name: str):
        """
        计算某能力的队内平均值
        :param capa_name: 能力名
        :return: 队内均值
        """
        average_capa = sum([player.get_rating(capa_name) for player in self.players]) / len(self.players)
        return average_capa

    def shift_location(self):
        for player in self.players:
            player.shift_location()

    def get_location_players(self, location_tuple: tuple) -> list:
        """
        获取指定位置上的球员
        :param location_tuple: 位置名
        :return: 球员实例列表
        """
        player_list = []
        for player in self.players:
            if player.get_location() in location_tuple:
                player_list.append(player)
        return player_list

    def attack(self, rival_team: 'Team', counter_attack_permitted=False) -> bool:
        """
        执行战术
        :param rival_team: 防守队伍实例
        :param counter_attack_permitted: 是否允许使用防反战术
        :return: 是否交换球权
        """
        tactic_name = self.select_tactic(counter_attack_permitted)
        exchange_ball = False
        if tactic_name == 'wing_cross':
            exchange_ball = self.wing_cross(rival_team)
        elif tactic_name == 'under_cutting':
            exchange_ball = self.under_cutting(rival_team)
        elif tactic_name == 'pull_back':
            exchange_ball = self.pull_back(rival_team)
        elif tactic_name == 'middle_attack':
            exchange_ball = self.middle_attack(rival_team)
        elif tactic_name == 'counter_attack':
            exchange_ball = self.counter_attack(rival_team)
        else:
            logger.error('战术名称{}错误！'.format(tactic_name))
        return exchange_ball

    def shot_and_save(self, attacker: Player, defender: Player,
                      assister: Optional[Player] = None) -> bool:
        """
        射门与扑救，一对一
        :param attacker: 进攻球员实例
        :param defender: 防守球员（门将）实例
        :param assister: 助攻球员实例
        :return: 进攻是否成功
        """
        self.add_script('{}起脚打门！'.format(attacker.name))
        average_stamina = self.get_rival_team().get_average_capability('stamina')
        attacker.plus_data('shots', average_stamina)
        defender.plus_data('saves', average_stamina)
        win_player = utils.select_by_pro(
            {attacker: attacker.get_rating('shooting'), defender: defender.get_rating('goalkeeping')})
        if win_player == attacker:
            self.score += 1
            attacker.plus_data('goals')
            if assister:
                assister.plus_data('assists')
            self.add_script('球进啦！{} {}:{} {}'.format(
                self.game.lteam.name, self.game.lteam.score, self.game.rteam.score, self.game.rteam.name))
            if attacker.get_data('goals') == 2:
                self.add_script('{}梅开二度！'.format(attacker.name))
            if attacker.get_data('goals') == 3:
                self.add_script('{}帽子戏法！'.format(attacker.name))
            if attacker.get_data('goals') == 4:
                self.add_script('{}大四喜！'.format(attacker.name))
            return True
        else:
            defender.plus_data('save_success')
            self.add_script('{}发挥神勇，扑出这脚劲射'.format(defender.name))
            return False

    def dribble_and_block(self, attacker: Player, defender: Player) -> bool:
        """
        过人与抢断，一对一，发生在内切时
        :param attacker: 进攻球员（边锋）实例
        :param defender: 防守球员（中卫）实例
        :return: 进攻是否成功
        """
        average_stamina = self.get_rival_team().get_average_capability('stamina')
        attacker.plus_data('dribbles', average_stamina)
        defender.plus_data('tackles', average_stamina)

        win_player = utils.select_by_pro(
            {attacker: attacker.get_rating('dribbling'),
             defender: defender.get_rating('interception')})
        if win_player == attacker:
            attacker.plus_data('dribble_success')
            self.add_script('{}过掉了{}'.format(attacker.name, defender.name))
            return True
        else:
            defender.plus_data('tackle_success')
            self.add_script('{}阻截了{}的进攻'.format(defender.name, attacker.name))
            return False

    def sprint_dribble_and_block(self, attackers: List[Player], defenders: List[Player]) -> \
            Tuple[bool, Player]:
        """
        冲刺、过人与抢断，多对多
        :param attackers: 进攻球员组
        :param defenders: 防守球员组
        :return: 进攻是否成功
        """
        average_stamina = self.get_rival_team().get_average_capability('stamina')
        if not defenders:
            return True, random.choice(attackers)
        if not attackers:
            return False, random.choice(defenders)
        while True:
            attacker = random.choice(attackers)
            defender = random.choice(defenders)
            attacker.plus_data('dribbles', average_stamina)
            defender.plus_data('tackles', average_stamina)
            win_player = utils.select_by_pro(
                {attacker: attacker.get_rating('dribbling') + attacker.get_rating('pace'),
                 defender: defender.get_rating('interception') + defender.get_rating('pace')})
            if win_player == attacker:
                attacker.plus_data('dribble_success')
                defenders.remove(defender)
            else:
                defender.plus_data('tackle_success')
                attackers.remove(attacker)
            if not attackers:
                self.add_script('{}抢到皮球'.format(win_player.name))
                return False, win_player
            elif not defenders:
                self.add_script('{}过掉了{}'.format(win_player.name, defender.name))
                return True, win_player
            else:
                pass

    def drop_ball(self, attackers: List[Player], defenders: List[Player]) -> Tuple[bool, Player]:
        """
        争顶
        :param attackers: 进攻球员组
        :param defenders: 防守球员组
        :return: 进攻是否成功、争顶成功的球员
        """
        self.add_script('球员们尝试争顶')
        average_stamina = self.get_rival_team().get_average_capability('stamina')
        while True:
            attacker = random.choice(attackers)
            defender = random.choice(defenders)
            attacker.plus_data('aerials', average_stamina)
            defender.plus_data('aerials', average_stamina)
            win_player = utils.select_by_pro(
                {attacker: attacker.get_rating('anticipation') + attacker.get_rating('strength'),
                 defender: defender.get_rating('anticipation') + defender.get_rating('strength')})
            win_player.plus_data('aerial_success')
            if win_player == attacker:
                defenders.remove(defender)
            else:
                attackers.remove(attacker)
            if not attackers:
                return False, win_player
            elif not defenders:
                self.add_script('{}抢到球权'.format(win_player.name))
                return True, win_player
            else:
                pass

    def pass_ball(self, attacker, defender_average: float, is_long_pass: bool = False) -> bool:
        """
        传球
        :param attacker: 传球球员实例
        :param defender_average: 防守方传球均值
        :param is_long_pass: 是否为长传
        :return: 进攻是否成功
        """
        average_stamina = self.get_rival_team().get_average_capability('stamina')
        attacker.plus_data('passes', average_stamina)
        if is_long_pass:
            win_player = utils.select_by_pro(
                {attacker: attacker.get_rating('passing') / 2,
                 defender_average: defender_average / 2})
        else:
            win_player = utils.select_by_pro(
                {attacker: attacker.get_rating('passing'),
                 defender_average: defender_average / 2})
        if win_player == attacker:
            attacker.plus_data('pass_success')
            return True
        else:
            return False

    def corner_kick(self, attacker: list, defender: list):
        """
        角球
        """
        pass

    def wing_cross(self, rival_team: 'Team'):
        """
        下底传中
        :param rival_team: 防守队伍
        :return: 是否交换球权
        """
        self.plus_data('wing_cross')
        self.add_script('\n{}尝试下底传中'.format(self.name))
        # 边锋或边卫过边卫
        while True:
            flag = utils.is_happened_by_pro(0.5)
            if flag:
                wings = self.get_location_players((Location.LW, Location.LB))
                wing_backs = rival_team.get_location_players((Location.LB,))
                if wings:
                    break
            else:
                wings = self.get_location_players((Location.RW, Location.RB))
                wing_backs = rival_team.get_location_players((Location.RB,))
                if wings:
                    break

        state, win_player = self.sprint_dribble_and_block(wings, wing_backs)  # 一对一或一对多
        if state:
            # 边锋传中
            self.add_script('{}一脚起球传中'.format(win_player.name))
            state = self.pass_ball(win_player, rival_team.get_average_capability('passing'), is_long_pass=True)
            if state:
                # 争顶
                assister = win_player
                strikers = self.get_location_players((Location.ST,))
                centre_backs = rival_team.get_location_players((Location.CB,))
                state, win_player = self.drop_ball(strikers, centre_backs)
                if state:
                    # 射门
                    goal_keeper = rival_team.get_location_players((Location.GK,))[0]
                    state = self.shot_and_save(win_player, goal_keeper, assister)
                    if state:
                        self.plus_data('wing_cross_success')
                else:
                    # 防守球员解围
                    self.add_script('{}将球解围'.format(win_player.name))
                    state = rival_team.pass_ball(win_player, self.get_average_capability('passing'),
                                                 is_long_pass=True)
                    if not state:
                        self.add_script('进攻方仍然持球')
                        return False
                    else:
                        self.add_script('{}拿到球权'.format(rival_team.name))
            else:
                self.add_script('{}抢到球权'.format(rival_team.name))
        return True

    def under_cutting(self, rival_team: 'Team'):
        """
        边路内切
        :param rival_team: 防守队伍
        :return: 是否交换球权
        """
        self.plus_data('under_cutting')
        self.add_script('\n{}尝试边路内切'.format(self.name))
        # 边锋过边卫
        wing = random.choice(self.get_location_players((Location.LW, Location.RW)))
        if wing.get_location() == Location.LW:
            wing_backs = rival_team.get_location_players((Location.RB,))
        elif wing.get_location() == Location.RW:
            wing_backs = rival_team.get_location_players((Location.LB,))
        else:
            raise ValueError('边锋不存在！')
        self.add_script('{}拿球，尝试人'.format(wing.name))
        state, win_player = self.sprint_dribble_and_block([wing], wing_backs)  # 一对一或一对多
        if state:
            # 边锋内切
            self.add_script('{}尝试内切'.format(win_player.name))
            centre_backs = rival_team.get_location_players((Location.CB,))
            # centre_back = random.choice(rival_team.get_location_players((Location.CB,)))
            # state = self.dribble_and_block(win_player, centre_back)
            while len(centre_backs) > 2:
                # 使防守球员上限不超过2个
                player = random.choice(centre_backs)
                centre_backs.remove(player)
            for centre_back in centre_backs:
                state = self.dribble_and_block(win_player, centre_back)
                if not state:
                    return True
            if state:
                # 射门
                goal_keeper = rival_team.get_location_players((Location.GK,))[0]
                state = self.shot_and_save(win_player, goal_keeper, None)
                if state:
                    self.plus_data('under_cutting_success')
        return True

    def pull_back(self, rival_team: 'Team'):
        """
        倒三角
        :param rival_team: 防守队伍
        :return: 是否交换球权
        """
        self.plus_data('pull_back')
        self.add_script('\n{}尝试倒三角传球'.format(self.name))
        # 边锋过边卫
        wing = random.choice(self.get_location_players((Location.LW, Location.RW)))
        if wing.get_location() == Location.LW:
            wing_backs = rival_team.get_location_players((Location.RB,))
        elif wing.get_location() == Location.RW:
            wing_backs = rival_team.get_location_players((Location.LB,))
        else:
            raise ValueError('边锋不存在！')
        self.add_script('{}拿球，尝试过人'.format(wing.name))
        state, win_player = self.sprint_dribble_and_block([wing], wing_backs)  # 一对一或一对多
        if state:
            # 边锋内切
            assister = win_player
            self.add_script('{}尝试内切'.format(win_player.name))
            centre_back = random.choice(rival_team.get_location_players((Location.CB,)))
            state = self.dribble_and_block(win_player, centre_back)
            # for centre_back in centre_backs:
            #     state = self.dribble_and_block(win_player, centre_back)
            #     if not state:
            #         return True
            if state:
                # 倒三角传球
                self.add_script('{}倒三角传中'.format(win_player.name))
                state = self.pass_ball(win_player, rival_team.get_average_capability('passing'))
                if state:
                    shooter = random.choice(self.get_location_players((Location.ST, Location.CM)))
                    goal_keeper = rival_team.get_location_players((Location.GK,))[0]
                    state = self.shot_and_save(shooter, goal_keeper, assister)
                    if state:
                        self.plus_data('pull_back_success')
        return True

    def middle_attack(self, rival_team: 'Team'):
        """
        中路渗透
        :param rival_team: 防守队伍
        :return: 是否交换球权
        """
        self.plus_data('middle_attack')
        self.add_script('\n{}尝试中路渗透'.format(self.name))
        count_dict = {}
        for _ in range(10):
            midfielders = self.get_location_players((Location.CM,))
            while True:
                player = random.choice(midfielders)
                flag = self.pass_ball(player, rival_team.get_average_capability('passing'))
                if flag:
                    count_dict[player] = count_dict.get(player, 0) + 1
                    break
                midfielders.remove(player)
                if not midfielders:
                    self.add_script('{}丢失了球权'.format(self.name))
                    return True
        assister = sorted(count_dict.items(), key=lambda x: x[1], reverse=True)[0][0]
        # 争顶
        strikers = self.get_location_players((Location.ST,))
        centre_backs = rival_team.get_location_players((Location.CB,))
        state, win_player = self.drop_ball(strikers, centre_backs)
        if state:
            # 射门
            goal_keeper = rival_team.get_location_players((Location.GK,))[0]
            state = self.shot_and_save(win_player, goal_keeper, assister)
            if state:
                self.plus_data('middle_attack_success')
        else:
            # 防守球员解围
            self.add_script('{}将球解围'.format(win_player.name))
            state = rival_team.pass_ball(win_player, self.get_average_capability('passing'), is_long_pass=True)
            if state:
                # 外围争顶
                centre_backs = self.get_location_players((Location.CB,))
                strikers = rival_team.get_location_players((Location.ST,))
                state, win_player = rival_team.drop_ball(strikers, centre_backs)
                if state:
                    return True
            self.add_script('进攻方仍然持球')
            return False
        return True

    def counter_attack(self, rival_team: 'Team'):
        """
        防守反击
        :param rival_team: 防守队伍
        :return: 是否交换球权
        """
        self.plus_data('counter_attack')
        self.add_script('\n{}尝试防守反击'.format(self.name))
        passing_player = random.choice(
            self.get_location_players((Location.GK, Location.CB, Location.LB, Location.RB,
                                       Location.CM, Location.LW, Location.RW)))
        state = self.pass_ball(passing_player, rival_team.get_average_capability('passing'))
        self.add_script('{}一脚长传，直击腹地'.format(passing_player.name))
        if state:
            # 过人
            assister = passing_player
            strikers = self.get_location_players((Location.ST,))
            centre_backs = rival_team.get_location_players((Location.CB,))
            if not strikers:
                self.add_script("很可惜，无锋阵容没有中锋进行接应，球权被{}夺去".format(rival_team.name))
                return True
            state, win_player = self.sprint_dribble_and_block(strikers, centre_backs)
            if state:
                # 射门
                goal_keeper = rival_team.get_location_players((Location.GK,))[0]
                state = self.shot_and_save(win_player, goal_keeper, assister)
                if state:
                    self.plus_data('counter_attack_success')
        self.add_script('{}持球'.format(rival_team.name))
        return True


class Game:
    def __init__(self, team1_model: models.Club, team2_model: models.Club, date: Date, game_type: str):
        # TODO game_type 改为联赛 id 或杯赛 id
        self.lteam = Team(self, team1_model)
        self.rteam = Team(self, team2_model)
        self.date = str(date)  # TODO 虚拟日期
        self.script = ''
        self.type = game_type

    def start(self) -> tuple:
        self.add_script('比赛开始！')
        hold_ball_team, no_ball_team = self.init_hold_ball_team()
        counter_attack_permitted = False
        for _ in range(50):
            # 确定本次战术组织每个球员的场上位置
            self.lteam.shift_location()
            self.rteam.shift_location()
            original_score = (self.lteam.score, self.rteam.score)
            # 执行进攻战术
            exchange_ball = hold_ball_team.attack(no_ball_team, counter_attack_permitted)
            if exchange_ball:
                hold_ball_team, no_ball_team = self.exchange_hold_ball_team(hold_ball_team)
            if exchange_ball and original_score == (self.lteam.score, self.rteam.score):
                counter_attack_permitted = True
            else:
                counter_attack_permitted = False
        self.add_script('比赛结束！ {} {}:{} {}'.format(
            self.lteam.name, self.lteam.score, self.rteam.score, self.rteam.name))
        self.rate()  # 球员评分

        self.save_in_db()  # 保存比赛
        self.save_players_data()  # 保存球员数据的改变
        return self.lteam.score, self.rteam.score

    def save_players_data(self):
        """
        保存球员数据的改变
        """
        for player in self.lteam.players:
            self.save_player_data(player)
        for player in self.rteam.players:
            self.save_player_data(player)

    def save_player_data(self, player: Player):
        """
        保存球员数据的改变
        :param player: 球员实例
        """
        player_id = player.player_model.id
        lo = player.location
        # region 记录场上位置数
        if lo == 'ST':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'ST_num': player.player_model.ST_num + 1})
        elif lo == 'CM':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'CM_num': player.player_model.CM_num + 1})
        elif lo == 'LW':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'LW_num': player.player_model.LW_num + 1})
        elif lo == 'RW':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'RW_num': player.player_model.RW_num + 1})
        elif lo == 'CB':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'CB_num': player.player_model.CB_num + 1})
        elif lo == 'LB':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'LB_num': player.player_model.LB_num + 1})
        elif lo == 'RB':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'RB_num': player.player_model.RB_num + 1})
        elif lo == 'GK':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'GK_num': player.player_model.GK_num + 1})
        elif lo == 'CAM':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'CAM_num': player.player_model.CAM_num + 1})
        elif lo == 'LM':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'LM_num': player.player_model.LM_num + 1})
        elif lo == 'RM':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'RM_num': player.player_model.RM_num + 1})
        elif lo == 'CDM':
            crud.update_player(db=Depends(get_db), player_id=player_id,
                               attri={'CDM_num': player.player_model.CDM_num + 1})
        else:
            logger.warning('没有球员对应的位置！')
        # endregion
        # region 能力成长
        if player.data['final_rating'] < 4:
            crud.update_player(Depends(get_db), player_id, self.get_cap_improvement(player, 0.05))
        elif 4 <= player.data['final_rating'] < 5:
            crud.update_player(Depends(get_db), player_id, self.get_cap_improvement(player, 0.1))
        elif 5 <= player.data['final_rating'] < 6:
            crud.update_player(Depends(get_db), player_id, self.get_cap_improvement(player, 0.15))
        elif 6 <= player.data['final_rating'] < 7:
            crud.update_player(Depends(get_db), player_id, self.get_cap_improvement(player, 0.2))
        elif 7 <= player.data['final_rating'] < 8:
            crud.update_player(Depends(get_db), player_id, self.get_cap_improvement(player, 0.25))
        elif 8 <= player.data['final_rating'] < 9:
            crud.update_player(Depends(get_db), player_id, self.get_cap_improvement(player, 0.3))
        elif player.data['final_rating'] >= 9:
            crud.update_player(Depends(get_db), player_id, self.get_cap_improvement(player, 0.35))
        else:
            logger.error('没有球员相对应的评分！')
        # endregion

    @staticmethod
    def get_cap_improvement(player: Player, rating) -> dict:
        """
        根据评分，获取能力的提升值
        :param player: 球员实例
        :param rating: 外部函数传入的提升值
        :return: 记录能力提升的字典
        """
        improvement = []
        if player.location == Location.ST:
            improvement = random.sample(['shooting', 'anticipation', 'strength', 'stamina'], 2)
        elif player.location == Location.LW or player.location == Location.RW:
            improvement = random.sample(['shooting', 'passing', 'dribbling', 'pace', 'stamina'], 2)
        elif player.location == Location.CM:
            improvement = random.sample(['shooting', 'passing', 'stamina'], 2)
        elif player.location == Location.CB:
            improvement = random.sample(['interception', 'anticipation', 'strength', 'stamina'], 2)
        elif player.location == Location.LB or player.location == Location.RB:
            improvement = random.sample(['passing', 'dribbling', 'interception', 'pace', 'stamina'], 2)
        elif player.location == Location.GK:
            rating /= 2
            improvement = random.sample(['goalkeeping', 'stamina','passing'], 2)
        elif player.location == Location.CAM:
            improvement = random.sample(['shooting', 'passing', 'anticipation', 'strength', 'stamina'], 2)
        elif player.location == Location.LM or player.location == Location.RM:
            improvement = random.sample(['shooting', 'passing', 'dribbling', 'pace', 'stamina'], 2)
        elif player.location == Location.CDM:
            improvement = random.sample(['passing', 'interception', 'strength', 'anticipation', 'stamina'], 2)
        else:
            logger.error('球员位置不正确！')
        result = dict()
        for capa in improvement:
            limit = eval('player.player_model.{}_limit'.format(capa))
            if player.rating[capa] + rating <= limit:
                result[capa] = float(utils.retain_decimal(player.rating[capa] + rating))
            else:
                result[capa] = limit
        return result

    def export_game(self) -> schemas.Game:
        created_time = datetime.datetime.now()
        teams = [self.lteam.export_game_team_info(created_time), self.rteam.export_game_team_info(created_time)]

        data = {
            'type': self.type,
            'created_time': created_time,
            'date': self.date,
            'season': self.date[:4],
            'script': self.script,
            'teams': teams,
            'mvp': self.get_highest_rating_player().player_model.id
        }
        game_data = schemas.Game(**data)
        return game_data

    def save_in_db(self):
        game_data = self.export_game()
        crud.create_game(db=Depends(get_db), game=game_data)

    def add_script(self, text: str):
        self.script += text + '\n'

    def init_hold_ball_team(self):
        hold_ball_team = random.choice([self.lteam, self.rteam])
        no_ball_team = self.lteam if hold_ball_team == self.rteam else self.rteam
        return hold_ball_team, no_ball_team

    def exchange_hold_ball_team(self, hold_ball_team: Team):
        hold_ball_team = self.lteam if hold_ball_team == self.rteam else self.rteam
        no_ball_team = self.lteam if hold_ball_team == self.rteam else self.rteam
        return hold_ball_team, no_ball_team

    def rate(self):
        """
        球员评分，写入到每一个球员实例的.data['final_rating']中
        """
        # 动作次数评分
        average_actions = self.get_average_actions()
        for player in self.lteam.players:
            if player.location != Location.GK:
                offset = self.get_offset_per(player.data['actions'], average_actions)
                self.rate_by_actions(player, offset)
        for player in self.rteam.players:
            if player.location != Location.GK:
                offset = self.get_offset_per(player.data['actions'], average_actions)
                self.rate_by_actions(player, offset)
        # 各项动作准确率评分
        average_pass_success = \
            self.get_average_capa('pass_success', action_name='passes') / \
            self.get_average_capa('passes', is_action=True)
        average_dribble_success = \
            self.get_average_capa('dribble_success', action_name='dribbles') / \
            self.get_average_capa('dribbles', is_action=True)
        average_tackle_success = \
            self.get_average_capa('tackle_success', action_name='tackles') / \
            self.get_average_capa('tackles', is_action=True)
        average_aerial_success = \
            self.get_average_capa('aerial_success', action_name='aerials') / \
            self.get_average_capa('aerials', is_action=True)
        for player in self.lteam.players:
            if player.location != Location.GK:
                if player.data['passes'] >= 5:
                    # 动作次数不小于5次，才将其计入评分
                    offset = self.get_offset_per(player.data['pass_success'] / player.data['passes'],
                                                 average_pass_success)
                    self.rate_by_capa(player, offset)
                if player.data['dribbles'] >= 5:
                    offset = self.get_offset_per(player.data['dribble_success'] / player.data['dribbles'],
                                                 average_dribble_success)
                    self.rate_by_capa(player, offset)
                if player.data['tackles'] >= 5:
                    offset = self.get_offset_per(player.data['tackle_success'] / player.data['tackles'],
                                                 average_tackle_success)
                    self.rate_by_capa(player, offset)
                if player.data['aerials'] >= 5:
                    offset = self.get_offset_per(player.data['aerial_success'] / player.data['aerials'],
                                                 average_aerial_success)
                    self.rate_by_capa(player, offset)
        for player in self.rteam.players:
            if player.location != Location.GK:
                if player.data['passes'] >= 5:
                    offset = self.get_offset_per(player.data['pass_success'] / player.data['passes'],
                                                 average_pass_success)
                    self.rate_by_capa(player, offset)
                if player.data['dribbles'] >= 5:
                    offset = self.get_offset_per(player.data['dribble_success'] / player.data['dribbles'],
                                                 average_dribble_success)
                    self.rate_by_capa(player, offset)
                if player.data['tackles'] >= 5:
                    offset = self.get_offset_per(player.data['tackle_success'] / player.data['tackles'],
                                                 average_tackle_success)
                    self.rate_by_capa(player, offset)
                if player.data['aerials'] >= 5:
                    offset = self.get_offset_per(player.data['aerial_success'] / player.data['aerials'],
                                                 average_aerial_success)
                    self.rate_by_capa(player, offset)
        # 其他加成
        for player in self.lteam.players:
            goals = player.data['goals']
            assists = player.data['assists']
            saves = player.data['save_success']
            player.data['final_rating'] += goals * 1.5 + assists * 1.1 + saves * 0.4
        for player in self.rteam.players:
            goals = player.data['goals']
            assists = player.data['assists']
            saves = player.data['save_success']
            player.data['final_rating'] += goals * 1.5 + assists * 1.1 + saves * 0.4
        for player in self.lteam.players:
            self.perf_rating(player.data['final_rating'], player)
        for player in self.rteam.players:
            self.perf_rating(player.data['final_rating'], player)

    def get_average_actions(self) -> float:
        """
        获取动作数量的均值
        :return: 均值
        """
        _sum = 0
        for player in self.lteam.players:
            _sum += player.data['actions']
        return _sum / 11

    def get_average_capa(self, capa_name: str, is_action=False, action_name: str = None) -> float:
        """
        获取指定数据的平均值
        :param capa_name: 数据名
        :param is_action: 是否是动作
        :param action_name: 如果不是动作，则其相应的动作名
        :return: 均值
        """
        _sum = 0
        count = 0
        for player in self.lteam.players:
            if is_action:
                if player.data[capa_name] < 5:
                    continue
            else:
                if player.data[action_name] < 5:
                    continue
            _sum += player.data[capa_name]
            count += 1  # 说明有一个球员被选中参与评分
        for player in self.rteam.players:
            if is_action:
                if player.data[capa_name] < 5:
                    continue
            else:
                if player.data[action_name] < 5:
                    continue
            _sum += player.data[capa_name]
            count += 1
        if is_action and _sum == 0:
            # 防止分母为零
            _sum = 1
        if count == 0:
            return 1
        else:
            return _sum / count

    @staticmethod
    def get_offset_per(a, b) -> float:
        """
        获取a比b高或低的比例
        """
        if b == 0:
            return 0
        else:
            return (a - b) / b

    @staticmethod
    def rate_by_actions(player, offset):
        """
        动作数量的评分办法
        :param player: 球员实例
        :param offset: 与均值的偏移百分比
        """
        if 0.1 <= offset < 0.2:
            player.data['final_rating'] += 0.3
        if 0.2 <= offset < 0.4:
            player.data['final_rating'] += 0.7
        if 0.4 <= offset < 0.6:
            player.data['final_rating'] += 1.0
        if 0.6 <= offset < 0.8:
            player.data['final_rating'] += 1.5
        if 0.8 <= offset:
            player.data['final_rating'] += 2
        if -0.2 < offset <= -0.1:
            player.data['final_rating'] -= 0.3
        if -0.4 < offset <= -0.2:
            player.data['final_rating'] -= 0.7
        if -0.6 < offset <= -0.4:
            player.data['final_rating'] -= 1.0
        if -0.8 < offset <= -0.6:
            player.data['final_rating'] -= 1.5
        if offset <= -0.8:
            player.data['final_rating'] -= 2

    @staticmethod
    def rate_by_capa(player, offset):
        """
        各项能力数值的评分办法
        :param player: 球员实例
        :param offset: 与均值的偏移值
        """
        if 0.1 <= offset < 0.2:
            player.data['final_rating'] += 0.3
        if 0.2 <= offset < 0.4:
            player.data['final_rating'] += 0.6
        if 0.4 <= offset < 0.6:
            player.data['final_rating'] += 0.9
        if 0.6 <= offset < 0.8:
            player.data['final_rating'] += 1.2
        if 0.8 <= offset:
            player.data['final_rating'] += 1.5
        if -0.2 < offset <= -0.1:
            player.data['final_rating'] -= 0.3
        if -0.4 < offset <= -0.2:
            player.data['final_rating'] -= 0.6
        if -0.6 < offset <= -0.4:
            player.data['final_rating'] -= 1.0
        if -0.8 < offset <= -0.6:
            player.data['final_rating'] -= 1.3
        if -1 < offset <= -0.8:
            player.data['final_rating'] -= 1.6

    @staticmethod
    def perf_rating(rating, player):
        """
        调整评分在正常范围内
        :param rating: 评分
        :param player: 球员实例
        """
        rating = player.data['final_rating']
        if rating < 0:
            rating = 0
        if rating > 10:
            rating = 10
        player.data['final_rating'] = float(utils.retain_decimal(rating))

    def get_highest_rating_player(self):
        """
        获取全场mvp
        :return: mvp球员实例
        """
        player_list = [p for p in self.lteam.players]
        player_list.extend([p for p in self.rteam.players])
        player_list = [(p, p.data['final_rating']) for p in player_list]
        highest_rating_player = max(player_list, key=lambda x: x[1])[0]
        return highest_rating_player
