import datetime
from typing import List

import crud
import game_configs
import models
import schemas
from modules import generate_app
from sqlalchemy.orm import Session
from utils import logger


class SaveGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.data = dict()

    def generate(self, save_data: schemas.SaveCreate, user_id: int, gen_type: str) -> models.Save:
        """
        初始化存档
        :param user_id: 用户id
        :param gen_type: 联赛类型
        :param save_data: 存档信息
        :return: 存档实例
        """
        league_generator = generate_app.LeagueGenerator(self.db)
        club_generator = generate_app.ClubGenerator(self.db)
        player_generator = generate_app.PlayerGenerator(self.db)
        coach_generator = generate_app.CoachGenerator(self.db)
        # 生成存档
        self.data = dict(save_data)
        save_model = self.save_in_db(user_id)
        # 生成联赛
        league_list = eval("game_configs.{}".format(gen_type))
        for league in league_list:
            league_create_schemas = schemas.LeagueCreate(
                created_time=datetime.datetime.now(), name=league["name"], points=league["points"], cup=league["cup"]
            )
            league_model = league_generator.generate(league_create_schemas)
            crud.update_league(db=self.db, league_id=league_model.id, attri={"save_id": save_model.id})
            league["id"] = league_model.id
            logger.info("联赛{}生成".format(league["name"]))

            for club in league["clubs"]:
                # 生成俱乐部
                club_create_schemas = schemas.ClubCreate(
                    created_time=datetime.datetime.now(),
                    name=club["name"],
                    finance=club["finance"],
                    reputation=club["reputation"],
                )
                club_model = club_generator.generate(club_create_schemas)
                # 为新增的联赛记录更新save_id字段
                # TODO 创建和添加字段其实可以一气呵成，下同
                crud.update_club(db=self.db, club_id=club_model.id, attri={"league_id": league_model.id})
                logger.info("俱乐部{}生成".format(club["name"]))

                # 随机生成教练
                coach_model = coach_generator.generate()
                crud.update_coach(db=self.db, coach_id=coach_model.id, attri={"club_id": club_model.id})

                # 随机生成球员
                # 随机生成11名适配阵型位置的成年球员
                formation_dict = game_configs.formations[coach_model.formation]
                players_create_schemas: List[schemas.PlayerCreate] = []
                for lo, num in formation_dict.items():
                    for i in range(num):
                        player_create_schemas: schemas.PlayerCreate = player_generator.generate(
                            ori_mean_capa=club["ori_mean_capa"],
                            ori_mean_potential_capa=game_configs.ori_mean_potential_capa,
                            average_age=27,
                            location=lo,
                        )
                        players_create_schemas.append(player_create_schemas)

                for _ in range(7):
                    # 随机生成7名任意位置成年球员
                    player_create_schemas: schemas.PlayerCreate = player_generator.generate(
                        ori_mean_capa=club["ori_mean_capa"],
                        ori_mean_potential_capa=game_configs.ori_mean_potential_capa,
                        average_age=26,
                    )
                    players_create_schemas.append(player_create_schemas)

                for _ in range(6):
                    # 随机生成6名年轻球员
                    player_create_schemas: schemas.PlayerCreate = player_generator.generate()
                    players_create_schemas.append(player_create_schemas)

                # 统一提交24名球员的创建
                crud.create_player_bulk(players=players_create_schemas, club_id=club_model.id)

        for league in league_list:
            # 标记上下游联赛关系
            if league["upper_league"]:
                for target_league in league_list:
                    if target_league["name"] == league["upper_league"]:
                        crud.update_league(
                            db=self.db, league_id=league["id"], attri={"upper_league": target_league["id"]}
                        )
            if league["lower_league"]:
                for target_league in league_list:
                    if target_league["name"] == league["lower_league"]:
                        crud.update_league(
                            db=self.db, league_id=league["id"], attri={"lower_league": target_league["id"]}
                        )
        logger.info("联赛上下游关系标记完成")
        self.data = dict()  # 清空数据
        return save_model

    def save_in_db(self, user_id: int) -> models.Save:
        """
        将生成的俱乐部数据存至数据库
        :return: 俱乐部实例
        """

        data_schemas = schemas.SaveCreate(**self.data)
        save_model = crud.create_save(db=self.db, save=data_schemas)
        save_model.user_id = user_id
        self.db.commit()
        logger.info("存档生成")
        return save_model
