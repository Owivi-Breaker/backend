import json
import os
from pathlib import Path
from typing import List

from pydantic import AnyHttpUrl

with open('./env.json') as f:
    data = json.load(f)


class Settings:
    CWD_URL = str(Path.cwd())  # 根目录
    ENV = os.environ.get("fast_env", "DEV")  # 本次启动环境
    APP_NAME = "FM"
    # api前缀
    API_PREFIX = "/api"
    # jwt密钥,建议随机生成一个
    # SECRET_KEY = "ShsUP9qIP2Xui2GpXRY6y74vSVS0Q2YOXJ22VjwkI"
    # token过期时间
    # ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60
    # 跨域白名单
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:8080"]
    # db配置
    DB_URL = data['DB_URL']
    # 启动端口配置
    PORT = 8080
    # 是否热加载
    RELOAD = True
    # 上传文件存储位置
    # UPLOAD_FOLDER = "D:\\code\\upload_files"
    # if not os.path.exists(UPLOAD_FOLDER):
    #     os.mkdir(UPLOAD_FOLDER)
    # CMDB模板文件存储位置
    # CMDB_FOLDER = "D:\\code\\cmdb_files"
    # if not os.path.exists(CMDB_FOLDER):
    #     os.mkdir(CMDB_FOLDER)


settings = Settings()
