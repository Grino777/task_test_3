# core/settings/settings.py

import os
from pydantic import BaseModel

DB_PASS = os.environ.get("DB_PASS")
DB_LOGIN = os.environ.get("DB_LOGIN")
DB_IP = "localhost"
DB_PORT = os.environ.get("DB_PORT")
BOT_API = os.environ.get("API_ID")
BOT_HASH = os.environ.get("API_HASH")


class DBSettings(BaseModel):
    """Settings class"""

    db_pass: str
    db_login: str
    db_ip: str
    db_port: str
    bot_api: str
    bot_hash: str
    msg_1: str = "Текст 1"
    msg_2: str = "Текст 2"
    msg_3: str = "Текст 3"
    # interval_1: int = 360  # interval in seconds
    # interval_2: int = 2340
    # interval_3: int = 93600
    interval_1: int = 5  # interval in seconds
    interval_2: int = 10
    interval_3: int = 15


settings = DBSettings(
    db_pass=DB_PASS,
    db_login=DB_LOGIN,
    db_ip=DB_IP,
    db_port=DB_PORT,
    bot_api=BOT_API,
    bot_hash=BOT_HASH,
)
