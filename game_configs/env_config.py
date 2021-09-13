from pathlib import Path
import enum
import os
import time
from loguru import logger

# CWD_URL = str(Path.cwd())
#
#
# def init_current_path():
#     """
#     确定根目录，在整个游戏开始前调用
#     """
#     global CWD_URL
#     logger.info("根目录为：{}".format(CWD_URL))
#
#
# SQLALCHEMY_DATABASE_URL = "sqlite:///" + CWD_URL + "/db_file/sql_app.db"
