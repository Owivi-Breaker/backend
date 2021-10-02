from utils import utils, logger
import game_configs
import crud
import schemas
from modules.game_app import Game, Player
from modules.game_app.player_selector import PlayerSelector

import random
from typing import Dict, List, Sequence, Set, Tuple, Optional
import datetime


class Team:
    def __init__(self, game: Game, club_id: int):
        self.game = game
        self.club_id = club_id
        self.team_model = crud.get_club_by_id(db=self.game.db, club_id=self.club_id)
        self.name = self.team_model.name  # 解说用
        self.tactic = dict()  # 战术比重字典
        self.init_tactic()
        self.players: List[Player] = []  # 球员列表
        self.init_players()
        self.score: int = 0  # 本方比分

        # self.data记录俱乐部场上数据
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

    def init_tactic(self):
        """
        初始化战术比重
        """
        self.tactic['wing_cross'] = self.team_model.coach.wing_cross
        self.tactic['under_cutting'] = self.team_model.coach.under_cutting
        self.tactic['pull_back'] = self.team_model.coach.pull_back
        self.tactic['middle_attack'] = self.team_model.coach.middle_attack
        self.tactic['counter_attack'] = self.team_model.coach.counter_attack

    def init_players(self):
        """
        挑选球员，写入self.players中
        """

        player_selector = PlayerSelector(self.club_id, self.game.db)
        players_model, locations_list = player_selector.select_players()
        for player_model, location in zip(players_model, locations_list):
            self.players.append(Player(player_model, location))

    def export_game_team_data_schemas(self, created_time=datetime.datetime.now()) -> schemas.GameTeamDataCreate:
        """
        导出球队数据至GameTeamData
        :param created_time: 创建时间
        :return: schemas.GameTeamData
        """
        data = {
            'created_time': created_time,
            **self.data
        }
        game_team_data = schemas.GameTeamData(**data)
        return game_team_data

    def export_game_team_info_schemas(self, created_time=datetime.datetime.now()) -> schemas.GameTeamInfoCreate:
        """
        导出球队赛信息
        :param created_time: 创建时间
        :return: 球队比赛信息
        """
        data = {
            'created_time': created_time,
            'club_id': self.team_model.id,
            'score': self.score,
        }
        game_team_info = schemas.GameTeamInfo(**data)
        return game_team_info

    def add_script(self, text: str):
        """
        添加解说
        :param text: 解说词
        """
        self.game.add_script(text)

    def set_capa(self, capa_name: str, num):
        """
        重置所有球员的指定能力
        :param capa_name: 能力名
        :param num: 能力值
        """
        for player in self.players:
            player.capa[capa_name] = num

    def get_rival_team(self) -> 'Team':
        """
        获取对手实例
        :return: Team实例
        """
        if self.game.lteam == self:
            return self.game.rteam
        else:
            return self.game.lteam

    def plus_data(self, data_name: str):
        """
        球队战术次数+1
        :param data_name: 战术名
        """
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
        tactic_pro.pop("counter_attack")  # 无防反
        while True:
            tactic_name = utils.select_by_pro(tactic_pro_total) if counter_attack_permitted else utils.select_by_pro(
                tactic_pro)
            if tactic_name == 'wing_cross' and not self.get_location_players(
                    (game_configs.Location.LW, game_configs.Location.RW, game_configs.Location.LB,
                     game_configs.Location.RB)):
                continue
            if tactic_name == 'under_cutting' and not self.get_location_players(
                    (game_configs.Location.LW, game_configs.Location.RW)):
                continue
            if tactic_name == 'pull_back' and not self.get_location_players(
                    (game_configs.Location.LW, game_configs.Location.RW)):
                continue
            if tactic_name == 'middle_attack' and not self.get_location_players((game_configs.Location.CM,)):
                self.shift_location()
            else:
                break

        return tactic_name

    def get_average_capability(self, capa_name: str) -> float:
        """
        计算某能力的队内平均值
        :param capa_name: 能力名
        :return: 队内均值
        """
        average_capa = sum([player.get_capa(capa_name) for player in self.players]) / len(self.players)
        return average_capa

    def shift_location(self):
        """
        所有球员刷新场上位置
        """
        for player in self.players:
            player.shift_location()

    def get_location_players(self, location_tuple: tuple) -> List[Player]:
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
            {attacker: attacker.get_capa('shooting'), defender: defender.get_capa('goalkeeping')})
        if win_player == attacker:
            # 比分直接在这儿改写，省的在每处调用后都要改写比分
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
        # 更新数据，并判定实时体力是否下降
        attacker.plus_data('dribbles', average_stamina)
        defender.plus_data('tackles', average_stamina)
        # 比拼进攻球员的过人与防守球员的抢断
        win_player = utils.select_by_pro(
            {attacker: attacker.get_capa('dribbling'),
             defender: defender.get_capa('interception')})
        if win_player == attacker:
            attacker.plus_data('dribble_success')
            self.add_script('{}过掉了{}'.format(attacker.name, defender.name))
            return True
        else:
            defender.plus_data('tackle_success')
            self.add_script('{}阻截了{}的进攻'.format(defender.name, attacker.name))
            return False

    def sprint_dribble_and_block(self, attackers: List[Player], defenders: List[Player]) -> Tuple[bool, Player]:
        """
        冲刺、过人与抢断，多对多
        :param attackers: 进攻球员组
        :param defenders: 防守球员组
        :return: 进攻是否成功、持球球员
        """
        average_stamina = self.get_rival_team().get_average_capability('stamina')
        if not defenders:
            return True, random.choice(attackers)  # 随机选一个进攻球员持球
        if not attackers:
            return False, random.choice(defenders)  # 随机选一个防守球员持球
        while True:
            attacker = random.choice(attackers)
            defender = random.choice(defenders)
            attacker.plus_data('dribbles', average_stamina)
            defender.plus_data('tackles', average_stamina)
            # 开始数值判定
            win_player = utils.select_by_pro(
                {attacker: attacker.get_capa('dribbling') + attacker.get_capa('pace'),
                 defender: defender.get_capa('interception') + defender.get_capa('pace')})
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
        if not defenders:
            return True, random.choice(attackers)  # 随机选一个进攻球员持球
        if not attackers:
            return False, random.choice(defenders)  # 随机选一个防守球员持球

        self.add_script('球员们尝试争顶')
        average_stamina = self.get_rival_team().get_average_capability('stamina')
        while True:
            attacker = random.choice(attackers)
            defender = random.choice(defenders)
            attacker.plus_data('aerials', average_stamina)
            defender.plus_data('aerials', average_stamina)
            win_player = utils.select_by_pro(
                {attacker: attacker.get_capa('anticipation') + attacker.get_capa('strength'),
                 defender: defender.get_capa('anticipation') + defender.get_capa('strength')})
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

    def pass_ball(self, attacker: Player, defender_average: float, is_long_pass: bool = False) -> bool:
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
            # 若是长传，成功率减半
            win_player = utils.select_by_pro(
                {attacker: attacker.get_capa('passing') / 2,
                 defender_average: defender_average / 2})
        else:
            win_player = utils.select_by_pro(
                {attacker: attacker.get_capa('passing'),
                 defender_average: defender_average / 2})
        if win_player == attacker:
            attacker.plus_data('pass_success')
            return True
        else:
            return False

    def corner_kick(self, attacker: List[Player], defender: List[Player]):
        """
        TODO 角球
        """
        pass

    def wing_cross(self, rival_team: 'Team') -> bool:
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
            # TODO 选择左路还是右路现在是随机实现，可以改
            if flag:
                wings = self.get_location_players((game_configs.Location.LW, game_configs.Location.LB))
                wing_backs = rival_team.get_location_players((game_configs.Location.LB,))
                if wings:
                    break
            else:
                wings = self.get_location_players((game_configs.Location.RW, game_configs.Location.RB))
                wing_backs = rival_team.get_location_players((game_configs.Location.RB,))
                if wings:
                    break

        state, win_player = self.sprint_dribble_and_block(wings, wing_backs)  # 一对一或一对多
        if state:
            # 边锋/卫传中
            self.add_script('{}一脚起球传中'.format(win_player.name))
            state = self.pass_ball(win_player, rival_team.get_average_capability('passing'), is_long_pass=True)
            if state:
                # 争顶
                assister = win_player
                strikers = self.get_location_players((game_configs.Location.ST,))
                if not strikers:
                    return True
                centre_backs = rival_team.get_location_players((game_configs.Location.CB,))
                state, win_player = self.drop_ball(strikers, centre_backs)
                if state:
                    # 射门
                    goal_keeper = rival_team.get_location_players((game_configs.Location.GK,))[0]  # 这个[0]是以防万一。。
                    state = self.shot_and_save(win_player, goal_keeper, assister)
                    if state:
                        # 进球啦！
                        self.plus_data('wing_cross_success')
                else:
                    # 防守球员解围
                    self.add_script('{}将球解围'.format(win_player.name))
                    # 进行一次球权判定
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

    def under_cutting(self, rival_team: 'Team') -> bool:
        """
        边路内切
        :param rival_team: 防守队伍
        :return: 是否交换球权
        """
        self.plus_data('under_cutting')
        self.add_script('\n{}尝试边路内切'.format(self.name))
        # 边锋过边卫
        wing = random.choice(self.get_location_players((game_configs.Location.LW, game_configs.Location.RW)))
        if wing.get_location() == game_configs.Location.LW:
            wing_backs = rival_team.get_location_players((game_configs.Location.RB,))
        elif wing.get_location() == game_configs.Location.RW:
            wing_backs = rival_team.get_location_players((game_configs.Location.LB,))
        else:
            raise ValueError('边锋不存在！')  # 之前都判定过的，应该不会出现这种情况
        self.add_script('{}拿球，尝试人'.format(wing.name))
        state, win_player = self.sprint_dribble_and_block([wing], wing_backs)  # 一对一或一对多
        if state:
            # 边锋内切
            self.add_script('{}尝试内切'.format(win_player.name))
            centre_backs = rival_team.get_location_players((game_configs.Location.CB,))
            while len(centre_backs) > 2:
                # 使防守球员上限不超过2个
                player = random.choice(centre_backs)
                centre_backs.remove(player)
            if not centre_backs:
                # 这一步是防一手那些不带中后卫的憨批阵型
                state = True
            else:
                for centre_back in centre_backs:
                    state = self.dribble_and_block(win_player, centre_back)
            if state:
                # 射门
                goal_keeper = rival_team.get_location_players((game_configs.Location.GK,))[0]
                state = self.shot_and_save(win_player, goal_keeper, None)
                if state:
                    self.plus_data('under_cutting_success')
        return True

    def pull_back(self, rival_team: 'Team') -> bool:
        """
        倒三角
        :param rival_team: 防守队伍
        :return: 是否交换球权
        """
        self.plus_data('pull_back')
        self.add_script('\n{}尝试倒三角传球'.format(self.name))
        # 边锋过边卫
        wing = random.choice(self.get_location_players((game_configs.Location.LW, game_configs.Location.RW)))
        if wing.get_location() == game_configs.Location.LW:
            wing_backs = rival_team.get_location_players((game_configs.Location.RB,))
        elif wing.get_location() == game_configs.Location.RW:
            wing_backs = rival_team.get_location_players((game_configs.Location.LB,))
        else:
            raise ValueError('边锋不存在！')
        self.add_script('{}拿球，尝试过人'.format(wing.name))
        state, win_player = self.sprint_dribble_and_block([wing], wing_backs)  # 一对一或一对多
        if state:
            # 边锋内切
            assister = win_player
            self.add_script('{}尝试内切'.format(win_player.name))
            # 随机选一个中卫
            centre_backs = rival_team.get_location_players((game_configs.Location.CB,))
            if not centre_backs:
                state = True
            else:
                centre_back = random.choice(centre_backs)
                state = self.dribble_and_block(win_player, centre_back)  # 过一个中卫即可
            if state:
                # 倒三角传球
                self.add_script('{}倒三角传中'.format(win_player.name))
                state = self.pass_ball(win_player, rival_team.get_average_capability('passing'))
                if state:
                    shooters = self.get_location_players((game_configs.Location.ST, game_configs.Location.CM))
                    if shooters:
                        return True
                    shooter = random.choice(shooters)
                    goal_keeper = rival_team.get_location_players((game_configs.Location.GK,))[0]
                    state = self.shot_and_save(shooter, goal_keeper, assister)
                    if state:
                        self.plus_data('pull_back_success')
        return True

    def middle_attack(self, rival_team: 'Team') -> bool:
        """
        中路渗透
        :param rival_team: 防守队伍
        :return: 是否交换球权
        """
        self.plus_data('middle_attack')
        self.add_script('\n{}尝试中路渗透'.format(self.name))
        count_dict = {}
        for _ in range(10):
            # 10次循环，若其中有一次循环：所有中场球员传球均失败，即丢失球权，否则传球成功
            midfielders = self.get_location_players((game_configs.Location.CM,))
            while True:
                player = random.choice(midfielders)
                flag = self.pass_ball(player, rival_team.get_average_capability('passing'))
                if flag:
                    # 若传球成功，进入下一次循环
                    count_dict[player] = count_dict.get(player, 0) + 1
                    break
                midfielders.remove(player)
                if not midfielders:
                    self.add_script('{}丢失了球权'.format(self.name))
                    return True
        # 助攻者取成功数最多次的球员
        assister = sorted(count_dict.items(), key=lambda x: x[1], reverse=True)[0][0]
        # 争顶
        strikers = self.get_location_players((game_configs.Location.ST,))
        if not strikers:
            # 中锋都没有，玩个屁的中路渗透
            return True
        centre_backs = rival_team.get_location_players((game_configs.Location.CB,))
        state, win_player = self.drop_ball(strikers, centre_backs)
        if state:
            # 射门
            goal_keeper = rival_team.get_location_players((game_configs.Location.GK,))[0]
            state = self.shot_and_save(win_player, goal_keeper, assister)
            if state:
                self.plus_data('middle_attack_success')
        else:
            # 防守球员解围
            self.add_script('{}将球解围'.format(win_player.name))
            state = rival_team.pass_ball(win_player, self.get_average_capability('passing'), is_long_pass=True)
            if state:
                # 外围争顶
                centre_backs = self.get_location_players((game_configs.Location.CB,))
                if not centre_backs:
                    # 我方外围无中卫，我方丢失球权
                    return True
                strikers = rival_team.get_location_players((game_configs.Location.ST,))
                if not strikers:
                    # 对方外围无前锋，我方仍然持球
                    state = False
                else:
                    state, win_player = rival_team.drop_ball(strikers, centre_backs)
                if state:
                    return True
            self.add_script('进攻方仍然持球')
            return False
        return True

    def counter_attack(self, rival_team: 'Team') -> bool:
        """
        防守反击
        :param rival_team: 防守队伍
        :return: 是否交换球权
        """
        self.plus_data('counter_attack')
        self.add_script('\n{}尝试防守反击'.format(self.name))
        # 随便选一个球员传球
        passing_player = random.choice(
            self.get_location_players(
                (game_configs.Location.GK, game_configs.Location.CB)))
        state = self.pass_ball(passing_player, rival_team.get_average_capability('passing'))
        if state:
            # 过人
            self.add_script('{}一脚长传，直击腹地'.format(passing_player.name))
            assister = passing_player
            strikers = self.get_location_players((game_configs.Location.ST,))
            centre_backs = rival_team.get_location_players((game_configs.Location.CB,))
            if not strikers:
                self.add_script("很可惜，无锋阵容没有中锋进行接应，球权被{}夺去".format(rival_team.name))
                return True
            state, win_player = self.sprint_dribble_and_block(strikers, centre_backs)
            if state:
                # 射门
                goal_keeper = rival_team.get_location_players((game_configs.Location.GK,))[0]
                state = self.shot_and_save(win_player, goal_keeper, assister)
                if state:
                    self.plus_data('counter_attack_success')
        self.add_script('{}持球'.format(rival_team.name))
        return True
